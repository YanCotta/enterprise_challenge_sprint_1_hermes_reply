"""Maintenance scheduling demo endpoints bridging prediction UI and reporting feeds."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, Security
from pydantic import ValidationError

from apps.api.dependencies import api_key_auth
from core.events.event_models import MaintenancePredictedEvent, MaintenanceScheduledEvent
from data.schemas import (
    MaintenanceScheduleRecord,
    MaintenanceScheduleRequest,
    MaintenanceScheduleResponse,
    ReportRequest,
)

router = APIRouter()

_SCHEDULE_TIMEOUT_SECONDS = 15
logger = logging.getLogger(__name__)


def _ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime for downstream agents."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post(
    "/schedule",
    response_model=MaintenanceScheduleResponse,
    dependencies=[Security(api_key_auth, scopes=["maintenance:schedule"])],
)
async def schedule_maintenance(
    schedule_request: MaintenanceScheduleRequest,
    request: Request,
) -> MaintenanceScheduleResponse:
    """Trigger the SchedulingAgent via the event bus and return the resulting schedule."""
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=503, detail="System coordinator unavailable.")

    if not getattr(coordinator, "event_bus", None):
        raise HTTPException(status_code=503, detail="Event bus unavailable.")

    correlation_id = schedule_request.correlation_id or str(uuid4())

    predicted_failure = _ensure_utc(schedule_request.predicted_failure_date)
    ci_padding_days = max(schedule_request.time_to_failure_days * 0.1, 0.5)
    ci_padding = timedelta(days=ci_padding_days)

    prediction_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id=schedule_request.equipment_id or schedule_request.sensor_id,
        predicted_failure_date=predicted_failure,
        confidence_interval_lower=predicted_failure - ci_padding,
        confidence_interval_upper=predicted_failure + ci_padding,
        prediction_confidence=schedule_request.prediction_confidence,
        time_to_failure_days=schedule_request.time_to_failure_days,
        maintenance_type=schedule_request.maintenance_type,
        prediction_method=schedule_request.prediction_method,
        historical_data_points=schedule_request.historical_data_points,
        model_metrics=schedule_request.model_metrics,
        recommended_actions=schedule_request.recommended_actions or [
            "Inspect equipment housing",
            "Verify calibration",
        ],
        agent_id=schedule_request.prediction_agent_id or "ui_prediction_demo",
        correlation_id=correlation_id,
    )

    # Stash UI context for downstream reporting feeds.
    coordinator.register_schedule_context(
        correlation_id,
        {
            "sensor_id": schedule_request.sensor_id,
            "sensor_type": schedule_request.sensor_type,
            "model_name": schedule_request.model_name,
            "model_version": schedule_request.model_version,
            "trigger_source": schedule_request.trigger_source,
            "maintenance_type": schedule_request.maintenance_type,
            "prediction_confidence": schedule_request.prediction_confidence,
        },
    )

    loop = asyncio.get_running_loop()
    schedule_future: asyncio.Future[MaintenanceScheduledEvent] = loop.create_future()

    async def _capture_scheduled_event(event_obj: MaintenanceScheduledEvent) -> None:
        if event_obj.correlation_id == correlation_id and not schedule_future.done():
            schedule_future.set_result(event_obj)

    await coordinator.event_bus.subscribe(
        MaintenanceScheduledEvent.__name__,
        _capture_scheduled_event,
    )

    try:
        await coordinator.event_bus.publish(prediction_event)
        try:
            scheduled_event = await asyncio.wait_for(
                schedule_future,
                timeout=_SCHEDULE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail="Scheduling agent did not respond before timeout.",
            ) from exc
    finally:
        await coordinator.event_bus.unsubscribe(
            MaintenanceScheduledEvent.__name__,
            _capture_scheduled_event,
        )

    schedule_payload = scheduled_event.model_dump(mode="json")
    schedule_details = schedule_payload.get("schedule_details") or {}

    report_id: Optional[str] = None
    report_summary: Optional[str] = None
    if schedule_request.include_report and coordinator.reporting_agent:
        try:
            report_request = ReportRequest(
                report_type="maintenance_overview",
                format="json",
                parameters={
                    "correlation_id": correlation_id,
                    "equipment_id": schedule_payload.get("equipment_id"),
                    "trigger_source": schedule_request.trigger_source,
                },
                include_charts=False,
            )
            report_result = await asyncio.to_thread(
                coordinator.reporting_agent.generate_report,
                report_request,
            )
            report_id = report_result.report_id
            report_summary = report_result.content[:600]
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "report_generation.failed",
                extra={"correlation_id": correlation_id, "error": str(exc)},
                exc_info=True,
            )
            report_id = None
            report_summary = None

    metadata: Dict[str, Any] = {
        "sensor_id": schedule_request.sensor_id,
        "sensor_type": schedule_request.sensor_type,
        "model_name": schedule_request.model_name,
        "model_version": schedule_request.model_version,
        "trigger_source": schedule_request.trigger_source,
    }

    return MaintenanceScheduleResponse(
        correlation_id=correlation_id,
        status=schedule_details.get("status", "Scheduled"),
        schedule=schedule_details,
        assigned_technician_id=schedule_payload.get("assigned_technician_id")
        or schedule_details.get("assigned_technician_id"),
        scheduled_start_time=schedule_details.get("scheduled_start_time"),
        scheduled_end_time=schedule_details.get("scheduled_end_time"),
        generated_report_id=report_id,
        report_summary=report_summary,
        metadata=metadata,
    )


@router.get(
    "/scheduled",
    response_model=List[MaintenanceScheduleRecord],
    dependencies=[Security(api_key_auth, scopes=["maintenance:read"])],
)
async def list_scheduled_maintenance(
    request: Request,
    limit: int = Query(25, ge=1, le=100),
    correlation_id: Optional[str] = Query(None),
) -> List[MaintenanceScheduleRecord]:
    """Return recent maintenance schedule records captured during the demo pipeline."""
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=503, detail="System coordinator unavailable.")

    raw_records = coordinator.get_recent_maintenance_schedules(
        limit=limit,
        correlation_id=correlation_id,
    )

    if not raw_records:
        return []

    try:
        return [MaintenanceScheduleRecord(**record) for record in raw_records]
    except ValidationError as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serialize maintenance schedules: {exc}",
        ) from exc

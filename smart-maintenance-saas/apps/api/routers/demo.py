import asyncio
import json
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Query

from redis.exceptions import WatchError

from core.redis_client import get_redis_client
from core.events.event_models import (
    SensorDataReceivedEvent,
    AnomalyDetectedEvent,
    AnomalyValidatedEvent,
    MaintenancePredictedEvent,
    MaintenanceScheduledEvent,
    HumanDecisionRequiredEvent,
    HumanDecisionResponseEvent,
    DataProcessedEvent,
    DataProcessingFailedEvent,
)
from data.schemas import DecisionRequest, DecisionType, DecisionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])

DEMO_TTL_SECONDS = 3600

# Redis key helpers
def _demo_key(correlation_id: str) -> str:
    return f"demo:{correlation_id}"

STEP_MAP = {
    "SensorDataReceivedEvent": "ingestion",
    "DataProcessedEvent": "processing",
    "AnomalyDetectedEvent": "anomaly_detection",
    "AnomalyValidatedEvent": "validation",
    "MaintenancePredictedEvent": "prediction",
    "MaintenanceScheduledEvent": "maintenance",
    "HumanDecisionRequiredEvent": "human_decision",
    "HumanDecisionResponseEvent": "human_decision",
}

STEP_ORDER = [
    "ingestion",
    "processing",
    "anomaly_detection",
    "validation",
    "prediction",
    "maintenance",
    "human_decision",
]


def _initial_status(correlation_id: str, include_decision: bool) -> Dict[str, Any]:
    steps = []
    for name in STEP_ORDER:
        if name == "human_decision" and not include_decision:
            continue
        steps.append({
            "name": name,
            "status": "pending",
            "events": 0,
            "started_at": None,
            "completed_at": None,
            "message": "Queued"
        })
    return {
        "correlation_id": correlation_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "steps": steps,
        "events": [],  # rolling buffer
        "metrics": {
            "total_events": 0,
            "last_event_at": None,
            "latency_ms_ingest_to_prediction": None,
        },
        "errors": [],
        "include_decision": include_decision,
    }


def _json_default(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


async def _load_demo_status(correlation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the current demo status from Redis."""
    redis_client = await get_redis_client()
    async with redis_client.get_redis() as redis_conn:
        raw = await redis_conn.get(_demo_key(correlation_id))
        if not raw:
            return None
        return json.loads(raw)


async def _save_demo_status(correlation_id: str, status: Dict[str, Any]) -> None:
    """Persist demo status to Redis with TTL refresh."""
    # Clamp rolling event buffer to avoid unbounded growth
    if len(status.get("events", [])) > 200:
        status["events"] = status["events"][-200:]

    redis_client = await get_redis_client()
    async with redis_client.get_redis() as redis_conn:
        await redis_conn.setex(
            _demo_key(correlation_id),
            DEMO_TTL_SECONDS,
            json.dumps(status, default=_json_default),
        )


async def _update_demo_status(
    correlation_id: str,
    mutator: Callable[[Optional[Dict[str, Any]]], Optional[Dict[str, Any]]],
) -> None:
    """Atomically apply a mutation to the demo status stored in Redis."""
    redis_client = await get_redis_client()
    async with redis_client.get_redis() as redis_conn:
        key = _demo_key(correlation_id)
        while True:
            pipe = redis_conn.pipeline()
            try:
                await pipe.watch(key)
                current_raw = await redis_conn.get(key)
                current_status = json.loads(current_raw) if current_raw else None
                updated_status = mutator(current_status)
                if updated_status is None:
                    await pipe.unwatch()
                    return

                if len(updated_status.get("events", [])) > 200:
                    updated_status["events"] = updated_status["events"][-200:]

                pipe.multi()
                pipe.setex(
                    key,
                    DEMO_TTL_SECONDS,
                    json.dumps(updated_status, default=_json_default),
                )
                await pipe.execute()
                return
            except WatchError:
                # Concurrent update detected; retry mutation
                continue
            finally:
                await pipe.reset()


def _find_step(status: Dict[str, Any], step_name: str):
    for s in status["steps"]:
        if s["name"] == step_name:
            return s
    return None


async def _handle_demo_event(correlation_id: str, event_obj: Any):
    evt_type = event_obj.__class__.__name__
    now_iso = datetime.utcnow().isoformat()

    def _mutate(status: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not status:
            return None

        step_name = STEP_MAP.get(evt_type)

        # Metrics
        status["metrics"]["total_events"] += 1
        status["metrics"]["last_event_at"] = now_iso

        # Step accounting
        if step_name:
            step = _find_step(status, step_name)
            if step:
                if step["status"] == "pending":
                    step["status"] = "running"
                    step["started_at"] = now_iso
                    step["message"] = f"{evt_type} observed"
                step["events"] += 1

                if evt_type == "MaintenancePredictedEvent":
                    ingestion_step = _find_step(status, "ingestion")
                    if ingestion_step and ingestion_step.get("started_at"):
                        t0 = datetime.fromisoformat(ingestion_step["started_at"])
                        t1 = datetime.utcnow()
                        status["metrics"]["latency_ms_ingest_to_prediction"] = int((t1 - t0).total_seconds() * 1000)

                completion_messages = {
                    "MaintenancePredictedEvent": "Prediction complete",
                    "MaintenanceScheduledEvent": "Maintenance scheduled",
                    "HumanDecisionResponseEvent": "Human decision recorded",
                }

                if evt_type in completion_messages:
                    if step["status"] != "complete":
                        step["status"] = "complete"
                        step["completed_at"] = now_iso
                    step["message"] = completion_messages[evt_type]

        # Error events
        if evt_type == "DataProcessingFailedEvent":
            status["errors"].append(
                {
                    "at": now_iso,
                    "agent_id": getattr(event_obj, "agent_id", None),
                    "message": getattr(event_obj, "error_message", "processing failed"),
                }
            )
            status["status"] = "failed"
            status["completed_at"] = now_iso

        # Append simplified event record
        preview = event_obj.dict() if hasattr(event_obj, "dict") else {}
        for key, value in list(preview.items()):
            if isinstance(value, (datetime, date)):
                preview[key] = value.isoformat()
            elif isinstance(value, dict):
                for nested_key, nested_value in list(value.items()):
                    if isinstance(nested_value, (datetime, date)):
                        value[nested_key] = nested_value.isoformat()
                try:
                    serialized = json.dumps(value, default=_json_default)
                except TypeError:
                    value = {
                        nk: (
                            nv.isoformat()
                            if isinstance(nv, (datetime, date))
                            else str(nv)
                        )
                        for nk, nv in value.items()
                    }
                    serialized = json.dumps(value)
                if len(serialized) > 400:
                    preview[key] = {"_truncated": True}

        raw_ts = getattr(event_obj, "timestamp", datetime.utcnow())
        if isinstance(raw_ts, (datetime, date)):
            ts_iso = raw_ts.isoformat()
        else:
            try:
                parsed = datetime.fromisoformat(str(raw_ts))
                ts_iso = parsed.isoformat()
            except Exception:
                ts_iso = datetime.utcnow().isoformat()

        status["events"].append(
            {
                "event_type": evt_type,
                "event_id": str(getattr(event_obj, "event_id", "")),
                "timestamp": ts_iso,
                "correlation_id": getattr(event_obj, "correlation_id", correlation_id),
                "payload": preview,
            }
        )

        prediction_done = any(
            s["name"] == "prediction" and s["status"] == "complete"
            for s in status["steps"]
        )
        decision_required = status.get("include_decision")
        decision_done = (
            not decision_required
            or any(
                s["name"] == "human_decision" and s["status"] == "complete"
                for s in status["steps"]
            )
        )
        if prediction_done and decision_done and status["status"] not in ("complete", "failed"):
            status["status"] = "complete"
            status["completed_at"] = now_iso

        return status

    await _update_demo_status(correlation_id, _mutate)


async def _event_bus_observer(event_obj: Any):
    # Generic observer for all events; route by correlation_id
    correlation_id = getattr(event_obj, 'correlation_id', None)
    if not correlation_id:
        return
    await _handle_demo_event(correlation_id, event_obj)


async def _seed_events(correlation_id: str, count: int, coordinator):
    """Publish synthetic SensorDataReceivedEvent events to kick off real pipeline."""
    from random import random as rnd

    equipment_id = f"demo-sensor-{correlation_id[:4]}"
    for i in range(count):
        raw = {
        "sensor_id": equipment_id,
            "value": round(25 + (rnd() * 2) + (5 if i == count // 2 else 0), 2),
            "unit": "celsius",
            "simulation": True,
            "index": i,
        }
        evt = SensorDataReceivedEvent(raw_data=raw, sensor_id=raw["sensor_id"], correlation_id=correlation_id)
        await coordinator.event_bus.publish(evt)
    # Force anomaly + validation + prediction path if not naturally triggered (lightweight synthetic events)
    now = datetime.utcnow()
    anomaly_alert_payload = {
    "sensor_id": equipment_id,
        "anomaly_type": "temperature_spike",
        "severity": 4,
        "confidence": 0.95,
        "description": "Temperature exceeded the expected baseline during demo run",
        "evidence": {
            "current_value": raw["value"],
            "baseline": 25.0,
            "deviation_magnitude": round(raw["value"] - 25.0, 2),
        },
        "recommended_actions": ["Inspect bearing", "Verify cooling system"],
        "created_at": now.isoformat(),
    }
    triggering_reading_payload = {
    "sensor_id": equipment_id,
        "sensor_type": "temperature",
        "timestamp": now.isoformat(),
        "value": raw["value"],
        "unit": raw["unit"],
        "quality": 0.98,
        "metadata": {
            "equipment_id": equipment_id,
            "source": "golden_path_demo",
        },
    }
    anomaly = AnomalyDetectedEvent(
        anomaly_details={"type": "temperature_spike", "score": 0.95},
        triggering_data={
        "sensor_id": equipment_id,
            "value": raw["value"],
            "unit": raw["unit"],
            "timestamp": now.isoformat(),
        },
        severity="high",
        correlation_id=correlation_id,
    )
    await coordinator.event_bus.publish(anomaly)
    validated = AnomalyValidatedEvent(
        original_anomaly_alert_payload=anomaly_alert_payload,
        triggering_reading_payload=triggering_reading_payload,
        validation_status="CONFIRMED",
        final_confidence=0.93,
        validation_reasons=["threshold_exceeded"],
        agent_id="enhanced_validation_agent",
        correlation_id=correlation_id,
    )
    await coordinator.event_bus.publish(validated)
    failure_date = datetime.utcnow() + timedelta(days=42)
    prediction = MaintenancePredictedEvent(
    original_anomaly_event_id=anomaly.event_id,
    equipment_id=equipment_id,
        predicted_failure_date=failure_date,
        confidence_interval_lower=failure_date - timedelta(days=3),
        confidence_interval_upper=failure_date + timedelta(days=3),
        prediction_confidence=0.88,
        time_to_failure_days=42,
        maintenance_type="preventive",
        prediction_method="demo",
        historical_data_points=count,
        model_metrics={"mae": 0.12, "rmse": 0.18},
        recommended_actions=["inspect bearing"],
        agent_id="prediction_agent_01",
        correlation_id=correlation_id,
    )
    coordinator.register_schedule_context(
        correlation_id,
        {
            "sensor_id": equipment_id,
            "sensor_type": "temperature",
            "trigger_source": "golden_path_demo",
            "maintenance_type": "preventive",
            "prediction_confidence": 0.88,
        },
    )
    await coordinator.event_bus.publish(prediction)


@router.post("/golden-path")
async def start_golden_path_demo(
    request: Request,
    background_tasks: BackgroundTasks,
    sensor_events: int = Query(15, ge=5, le=200),
    include_decision: bool = Query(False, description="If true, inject a human decision requirement stage"),
):
    correlation_id = str(uuid.uuid4())
    status_payload = _initial_status(correlation_id, include_decision)
    await _save_demo_status(correlation_id, status_payload)

    # Access coordinator / event bus from app state
    coordinator = request.app.state.coordinator
    # Ensure global observer subscribed once (idempotent)
    # We can register only once by tagging event bus
    if not hasattr(coordinator.event_bus, "_golden_path_observer_registered"):
        async def observer_wrapper(evt):
            await _event_bus_observer(evt)
        # Subscribe to all known event types (subscribe per type to reduce overhead)
        for evt_type in [
            "SensorDataReceivedEvent","DataProcessedEvent","AnomalyDetectedEvent","AnomalyValidatedEvent",
            "MaintenancePredictedEvent","MaintenanceScheduledEvent","HumanDecisionRequiredEvent","HumanDecisionResponseEvent","DataProcessingFailedEvent"
        ]:
            await coordinator.event_bus.subscribe(evt_type, observer_wrapper)
        coordinator.event_bus._golden_path_observer_registered = True

    # Seed pipeline with synthetic activity
    background_tasks.add_task(_seed_events, correlation_id, sensor_events, coordinator)

    # If decision stage requested, inject decision requirement after prediction via polling task
    if include_decision:
        async def decision_injector():
            # wait until prediction step completes then publish decision required
            for _ in range(30):  # ~30 * 0.5s = 15s timeout
                status = await _load_demo_status(correlation_id)
                if status and any(s["name"] == "prediction" and s["status"] == "complete" for s in status["steps"]):
                    prediction_event = next(
                        (evt for evt in status["events"] if evt.get("event_type") == "MaintenancePredictedEvent"),
                        None,
                    )
                    prediction_event_payload: Dict[str, Any] = prediction_event.get("payload", {}) if prediction_event else {}
                    prediction_event_id = prediction_event.get("event_id") if prediction_event else None

                    recommended_actions = prediction_event_payload.get("recommended_actions") or ["inspect bearing"]
                    if not isinstance(recommended_actions, list):
                        recommended_actions = [str(recommended_actions)]

                    resolved_request_id = (
                        f"maintenance_approval_{prediction_event_id}"
                        if prediction_event_id
                        else f"maintenance_approval_{correlation_id}"
                    )

                    failure_date = prediction_event_payload.get("predicted_failure_date")
                    if isinstance(failure_date, datetime):
                        failure_date_iso = failure_date.isoformat()
                    else:
                        failure_date_iso = str(failure_date) if failure_date else None

                    decision_request = DecisionRequest(
                        request_id=resolved_request_id,
                        decision_type=DecisionType.MAINTENANCE_APPROVAL,
                        context={
                            "equipment_id": prediction_event_payload.get("equipment_id") or f"demo-sensor-{correlation_id[:4]}",
                            "predicted_failure_date": failure_date_iso,
                            "prediction_confidence": prediction_event_payload.get("prediction_confidence", 0.75),
                            "time_to_failure_days": prediction_event_payload.get("time_to_failure_days", 30),
                            "recommended_actions": recommended_actions,
                        },
                        options=["approve", "modify", "reject", "defer"],
                        priority="medium",
                        requester_agent_id="demo_orchestrator",
                        correlation_id=correlation_id,
                    )
                    decision_required_event = HumanDecisionRequiredEvent(
                        payload=decision_request,
                        correlation_id=correlation_id,
                    )
                    await coordinator.event_bus.publish(decision_required_event)

                    await asyncio.sleep(5)
                    response_payload = DecisionResponse(
                        request_id=decision_request.request_id,
                        decision="approved",
                        justification="Auto-approved by demo injector",
                        operator_id="demo_operator",
                        timestamp=datetime.utcnow(),
                        confidence=0.95,
                        additional_notes="Synthetic decision for golden path",
                        correlation_id=correlation_id,
                    )
                    decision_response_event = HumanDecisionResponseEvent(
                        payload=response_payload,
                        correlation_id=correlation_id,
                    )
                    await coordinator.event_bus.publish(decision_response_event)
                    break
                await asyncio.sleep(0.5)

        background_tasks.add_task(decision_injector)

    return {
        "correlation_id": correlation_id,
        "status": "started",
        "status_url": f"/api/v1/demo/golden-path/status/{correlation_id}",
    }


@router.get("/golden-path/status/{correlation_id}")
async def get_golden_path_status(correlation_id: str):
    redis_client = await get_redis_client()
    async with redis_client.get_redis() as r:
        raw = await r.get(_demo_key(correlation_id))
        if not raw:
            raise HTTPException(status_code=404, detail="Demo not found or expired")
        return json.loads(raw)

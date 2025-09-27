import json
import uuid
import logging
import random
from datetime import datetime, date
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Query

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])

DEMO_TTL_SECONDS = 3600

# In-memory active demo registry (lightweight; Redis is canonical persistence)
ACTIVE_DEMOS: Dict[str, Dict[str, Any]] = {}

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


async def _persist_status(correlation_id: str):
    redis_client = await get_redis_client()
    payload = ACTIVE_DEMOS.get(correlation_id)
    if not payload:
        return
    # Truncate events buffer to last 200 for size safety
    if len(payload["events"]) > 200:
        payload["events"] = payload["events"][-200:]
    async with redis_client.get_redis() as r:
        # Use custom default to safely serialize any lingering datetime objects
        await r.setex(f"demo:{correlation_id}", DEMO_TTL_SECONDS, json.dumps(payload, default=_json_default))


def _find_step(status: Dict[str, Any], step_name: str):
    for s in status["steps"]:
        if s["name"] == step_name:
            return s
    return None


async def _handle_demo_event(correlation_id: str, event_obj: Any):
    status = ACTIVE_DEMOS.get(correlation_id)
    if not status:
        return
    evt_type = event_obj.__class__.__name__
    step_name = STEP_MAP.get(evt_type)
    now_iso = datetime.utcnow().isoformat()

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
            # Mark completion on certain terminal events
            if evt_type in {"MaintenancePredictedEvent", "HumanDecisionResponseEvent"}:
                if evt_type == "MaintenancePredictedEvent":
                    # compute latency from first ingestion event
                    ingestion_step = _find_step(status, "ingestion")
                    if ingestion_step and ingestion_step.get("started_at"):
                        t0 = datetime.fromisoformat(ingestion_step["started_at"])
                        t1 = datetime.utcnow()
                        status["metrics"]["latency_ms_ingest_to_prediction"] = int((t1 - t0).total_seconds() * 1000)
                if step["status"] != "complete":
                    step["status"] = "complete"
                    step["completed_at"] = now_iso

    # Error events
    if evt_type == "DataProcessingFailedEvent":
        status["errors"].append({
            "at": now_iso,
            "agent_id": getattr(event_obj, 'agent_id', None),
            "message": getattr(event_obj, 'error_message', 'processing failed')
        })
        status["status"] = "failed"
        status["completed_at"] = now_iso

    # Append simplified event record
    preview = event_obj.dict() if hasattr(event_obj, 'dict') else {}
    # Normalize datetime fields in preview & reduce large dicts
    for k, v in list(preview.items()):
        if isinstance(v, (datetime, date)):
            preview[k] = v.isoformat()
        elif isinstance(v, dict):
            # Convert nested datetime values
            changed = False
            for nk, nv in list(v.items()):
                if isinstance(nv, (datetime, date)):
                    v[nk] = nv.isoformat()
                    changed = True
            try:
                size_candidate = json.dumps(v, default=_json_default)
            except TypeError:
                # Fallback convert everything to str
                v = {kk: (vv.isoformat() if isinstance(vv, (datetime, date)) else str(vv)) for kk, vv in v.items()}
                size_candidate = json.dumps(v)
            if len(size_candidate) > 400:
                preview[k] = {"_truncated": True}
    raw_ts = getattr(event_obj, 'timestamp', datetime.utcnow())
    if isinstance(raw_ts, (datetime, date)):
        ts_iso = raw_ts.isoformat()
    else:
        # Attempt parse if string, otherwise fallback current time
        try:
            parsed = datetime.fromisoformat(str(raw_ts))
            ts_iso = parsed.isoformat()
        except Exception:
            ts_iso = datetime.utcnow().isoformat()
    status["events"].append({
        "event_type": evt_type,
        "event_id": str(getattr(event_obj, 'event_id', '')),
        "timestamp": ts_iso,
        "correlation_id": getattr(event_obj, 'correlation_id', correlation_id),
        "payload": preview,
    })

    # Determine overall completion (prediction + optional decision loop)
    prediction_done = any(s["name"] == "prediction" and s["status"] == "complete" for s in status["steps"])
    decision_required = status.get("include_decision")
    decision_done = not decision_required or any(s["name"] == "human_decision" and s["status"] == "complete" for s in status["steps"])
    if prediction_done and decision_done and status["status"] not in ("complete", "failed"):
        status["status"] = "complete"
        status["completed_at"] = now_iso

    await _persist_status(correlation_id)


async def _event_bus_observer(event_obj: Any):
    # Generic observer for all events; route by correlation_id
    correlation_id = getattr(event_obj, 'correlation_id', None)
    if not correlation_id:
        return
    if correlation_id in ACTIVE_DEMOS:
        await _handle_demo_event(correlation_id, event_obj)


async def _seed_events(correlation_id: str, count: int, coordinator):
    """Publish synthetic SensorDataReceivedEvent events to kick off real pipeline."""
    from random import random as rnd
    for i in range(count):
        raw = {
            "sensor_id": f"demo-sensor-{correlation_id[:4]}",
            "value": round(25 + (rnd() * 2) + (5 if i == count // 2 else 0), 2),
            "unit": "celsius",
            "simulation": True,
            "index": i,
        }
        evt = SensorDataReceivedEvent(raw_data=raw, sensor_id=raw["sensor_id"], correlation_id=correlation_id)
        await coordinator.event_bus.publish(evt)
    # Force anomaly + validation + prediction path if not naturally triggered (lightweight synthetic events)
    anomaly = AnomalyDetectedEvent(
        anomaly_details={"type": "temperature_spike", "score": 0.95},
        triggering_data={"sensor_id": raw["sensor_id"], "value": raw["value"]},
        severity="high",
        correlation_id=correlation_id,
    )
    await coordinator.event_bus.publish(anomaly)
    validated = AnomalyValidatedEvent(
        original_anomaly_alert_payload={"score": 0.95},
        triggering_reading_payload={"sensor_id": raw["sensor_id"], "value": raw["value"]},
        validation_status="CONFIRMED",
        final_confidence=0.93,
        validation_reasons=["threshold_exceeded"],
        agent_id="enhanced_validation_agent",
        correlation_id=correlation_id,
    )
    await coordinator.event_bus.publish(validated)
    prediction = MaintenancePredictedEvent(
        original_anomaly_event_id=anomaly.event_id,
        equipment_id=raw["sensor_id"],
        predicted_failure_date=datetime.utcnow().isoformat(),
        confidence_interval_lower=None,
        confidence_interval_upper=None,
        prediction_confidence=0.88,
        time_to_failure_days=42,
        maintenance_type="preventive",
        prediction_method="demo",
        historical_data_points=count,
        model_metrics={"demo": True},
        recommended_actions=["inspect bearing"],
        agent_id="prediction_agent_01",
        correlation_id=correlation_id,
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
    ACTIVE_DEMOS[correlation_id] = status_payload
    # Persist initial
    await _persist_status(correlation_id)

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
                status = ACTIVE_DEMOS.get(correlation_id)
                if status and any(s["name"] == "prediction" and s["status"] == "complete" for s in status["steps"]):
                    evt = HumanDecisionRequiredEvent(
                        correlation_id=correlation_id,
                        timestamp=datetime.utcnow(),
                        event_id=uuid.uuid4(),
                        # Minimal payload fields with placeholders
                    )
                    await coordinator.event_bus.publish(evt)
                    break
                await asyncio.sleep(0.5)
        import asyncio
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
        raw = await r.get(f"demo:{correlation_id}")
        if not raw:
            raise HTTPException(status_code=404, detail="Demo not found or expired")
        return json.loads(raw)

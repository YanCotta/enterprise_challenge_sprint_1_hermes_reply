from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st  # type: ignore

from lib.api_client import make_api_request, get_latency_samples
from lib.i18n_translations import get_translation, bilingual_text

st.set_page_config(page_title="Prediction", page_icon="🤖")

if "last_schedule_response" not in st.session_state:
    st.session_state.last_schedule_response = None
    st.session_state.last_schedule_sensor = None


@dataclass(frozen=True)
class BaselineModel:
    identifier: str
    label: str
    model_name: str
    mode: str  # 'forecast' or 'anomaly'
    sensor_types: Tuple[str, ...]
    model_version: str = "auto"
    description: str = ""
    default_history: int = 60
    default_horizon: int = 12


BASELINE_MODELS: Tuple[BaselineModel, ...] = (
    BaselineModel(
        identifier="prophet_temperature",
        label="Prophet Forecast (Synthetic Temperature Baseline)",
        model_name="prophet_forecaster_enhanced_sensor-001",
        mode="forecast",
        sensor_types=("temperature",),
        description=(
            "Uses the Prophet-based forecaster trained on synthetic temperature readings. "
            "Ideal for demonstrating short-term projections with our demo dataset."
        ),
        default_history=288,
        default_horizon=12,
    ),
    BaselineModel(
        identifier="isolation_forest_general",
        label="Isolation Forest Anomaly Detector (Synthetic Baseline)",
        model_name="anomaly_detector_refined_v2",
        mode="anomaly",
        sensor_types=("temperature", "pressure", "humidity", "voltage", "vibration"),
        description=(
            "Scores the most recent readings to highlight unusual behavior. "
            "Leverages the Isolation Forest model trained on the same synthetic corpus."
        ),
        default_history=60,
    ),
)


def _format_metric_value(value: Optional[object]) -> str:
    if value is None:
        return "?"
    if isinstance(value, (int, float)):
        return f"{value:.3f}" if isinstance(value, float) else str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        clean = [v for v in value if v is not None]
        if not clean:
            return "?"
        if len(clean) == 1:
            return _format_metric_value(clean[0])
        return ", ".join(_format_metric_value(v) for v in clean)
    return str(value)


@st.cache_data(ttl=180)
def _load_sensor_catalog() -> Dict[str, List[Dict[str, object]]]:
    sensors_resp = make_api_request("GET", "/api/v1/sensors/sensors")
    catalog: List[Dict[str, object]] = []
    if sensors_resp.get("success"):
        for entry in sensors_resp.get("data") or []:
            sensor_id = entry.get("sensor_id")
            if not sensor_id:
                continue
            latest_resp = make_api_request(
                "GET",
                "/api/v1/sensors/readings",
                params={"sensor_id": sensor_id, "limit": 1},
            )
            latest_payload = latest_resp.get("data") if latest_resp.get("success") else None
            latest = latest_payload[0] if latest_payload else None
            catalog.append({"sensor_id": sensor_id, "latest": latest})
    sensor_types = sorted(
        {
            (item.get("latest") or {}).get("sensor_type", "general")
            for item in catalog
            if item.get("latest")
        }
    )
    return {"sensors": catalog, "sensor_types": sensor_types}


def _render_page_header():
    """Render bilingual page header."""
    st.header(get_translation("prediction", "page_title", "en"))
    st.caption(get_translation("prediction", "description", "en"))
    with st.expander("ℹ️ Ajuda / Help"):
        st.write(f"**🇧🇷 PT:** {get_translation('prediction', 'description', 'pt')}")


def _fetch_history(sensor_id: str, limit: int) -> Tuple[List[Dict[str, object]], pd.DataFrame]:
    resp = make_api_request(
        "GET",
        "/api/v1/sensors/readings",
        params={"sensor_id": sensor_id, "limit": limit},
    )
    if not resp.get("success"):
        return [], pd.DataFrame()
    rows = resp.get("data") or []
    history_df = pd.DataFrame(rows)
    if not history_df.empty and "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True, errors="coerce")
        history_df = history_df.sort_values("timestamp")
    return rows, history_df


def _available_models(sensor_type: str) -> List[BaselineModel]:
    return [model for model in BASELINE_MODELS if sensor_type in model.sensor_types]


def _run_forecast(model: BaselineModel, sensor_id: str, horizon: int, history_window: int):
    payload = {
        "sensor_id": sensor_id,
        "model_name": model.model_name,
        "model_version": model.model_version,
        "history_window": history_window,
        "horizon_steps": horizon,
    }
    return make_api_request("POST", "/api/v1/ml/forecast", json_data=payload)


def _run_anomaly(model: BaselineModel, history_rows: List[Dict[str, object]]):
    sanitized = [
        {
            "sensor_id": row.get("sensor_id"),
            "sensor_type": row.get("sensor_type"),
            "value": row.get("value"),
            "unit": row.get("unit"),
            "timestamp": row.get("timestamp"),
            "quality": row.get("quality"),
        }
        for row in history_rows
        if row.get("value") is not None
    ]
    payload = {
        "model_name": model.model_name,
        "model_version": model.model_version,
        "sensor_readings": sanitized,
        "sensitivity": 0.5,
    }
    return make_api_request("POST", "/api/v1/ml/detect_anomaly", json_data=payload)


def _build_schedule_request(
    sensor_id: str,
    sensor_type: str,
    model: BaselineModel,
    forecast_df: pd.DataFrame,
    history_df: pd.DataFrame,
    payload: Dict[str, object],
) -> Optional[Dict[str, object]]:
    """Derive a maintenance schedule request payload from forecast results."""
    if forecast_df.empty:
        return None

    terminal_ts = forecast_df["timestamp"].max()
    if pd.isna(terminal_ts):
        return None

    predicted_failure = pd.to_datetime(terminal_ts, utc=True, errors="coerce")
    if pd.isna(predicted_failure):
        return None

    predicted_failure_dt = predicted_failure.to_pydatetime()
    now_utc = datetime.now(timezone.utc)
    time_to_failure_days = max((predicted_failure_dt - now_utc).total_seconds() / 86400.0, 0.1)

    recommended_actions = payload.get("recommended_actions")
    if not isinstance(recommended_actions, list) or not recommended_actions:
        recommended_actions = [
            "Dispatch technician for preventive inspection",
            "Verify cooling system and sensor calibration",
        ]

    model_metrics = payload.get("model_metrics") if isinstance(payload.get("model_metrics"), dict) else {}

    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "equipment_id": payload.get("equipment_id") or sensor_id,
        "predicted_failure_date": predicted_failure_dt.isoformat(),
        "time_to_failure_days": round(time_to_failure_days, 2),
        "maintenance_type": payload.get("maintenance_type", "preventive"),
        "prediction_method": payload.get("prediction_method") or model.model_name,
        "prediction_confidence": payload.get("prediction_confidence", 0.82),
        "historical_data_points": payload.get("history_points", len(history_df.index)),
        "model_name": payload.get("model_name") or model.model_name,
        "model_version": payload.get("model_version") or model.model_version,
        "model_metrics": model_metrics,
        "recommended_actions": recommended_actions,
        "trigger_source": "prediction_page",
        "correlation_id": payload.get("correlation_id"),
        "prediction_agent_id": payload.get("prediction_agent_id", "ui_prediction_demo"),
        "include_report": True,
        "metadata": {
            "history_points": payload.get("history_points", len(history_df.index)),
            "horizon_steps": payload.get("horizon_steps"),
        },
    }


def render_prediction_page():
    _render_page_header()

    catalog = _load_sensor_catalog()
    sensor_types = catalog.get("sensor_types", [])
    if not sensor_types:
        st.error("No sensors available. Populate the dataset to continue.")
        return

    sensor_type = st.selectbox("Sensor Type", sensor_types)
    sensors_for_type = [item for item in catalog.get("sensors", []) if (item.get("latest") or {}).get("sensor_type") == sensor_type]
    if not sensors_for_type:
        st.warning(f"No sensors with type '{sensor_type}' found.")
        return

    sensor_options = [entry["sensor_id"] for entry in sensors_for_type]
    sensor_id = st.selectbox("Sensor", sensor_options)
    selected_sensor = next((entry for entry in sensors_for_type if entry["sensor_id"] == sensor_id), None)
    latest_state = (selected_sensor or {}).get("latest") or {}

    if st.session_state.get("last_schedule_sensor") != sensor_id:
        st.session_state.last_schedule_sensor = sensor_id
        st.session_state.last_schedule_response = None

    col_state, col_meta = st.columns([2, 1])
    with col_state:
        st.subheader("Current Sensor State")
        st.metric(
            "Last Value",
            _format_metric_value(latest_state.get("value")),
            help="Most recent reading stored in the cloud database.",
        )
        st.caption(
            f"Timestamp: {latest_state.get('timestamp', 'n/a')}  |  Unit: {latest_state.get('unit', 'n/a')}"
        )
    with col_meta:
        st.caption(
            "Artifacts are fetched from S3 via our MLflow registry at inference time, "
            "ensuring you always run the latest validated version."
        )

    models = _available_models(sensor_type)
    if not models:
        st.warning("No baseline models mapped to this sensor type yet.")
        return

    model_labels = [model.label for model in models]
    selected_label = st.selectbox("Baseline Model", model_labels)
    chosen_model = next(model for model in models if model.label == selected_label)

    st.info(chosen_model.description)

    with st.form("baseline_inference_form"):
        if chosen_model.mode == "forecast":
            history_window = st.slider(
                "History Window (readings)",
                min_value=48,
                max_value=720,
                value=min(max(chosen_model.default_history, 48), 720),
                step=12,
                help="Number of trailing readings supplied to the forecaster.",
            )
            horizon = st.slider(
                "Forecast Horizon (steps)",
                min_value=1,
                max_value=96,
                value=min(max(chosen_model.default_horizon, 6), 48),
                help="Prediction steps using the inferred cadence (typically 5-minute intervals).",
            )
        else:
            history_window = st.slider(
                "History Window (readings)",
                min_value=20,
                max_value=240,
                value=min(max(chosen_model.default_history, 40), 120),
                step=10,
                help="Recent readings analysed for anomaly detection.",
            )
            horizon = None

        submitted = st.form_submit_button("Run Inference", use_container_width=True)

    stored_context = st.session_state.get("prediction_last_run")
    if submitted:
        history_rows, history_df = _fetch_history(sensor_id, history_window)
        if not history_rows:
            st.error("Unable to retrieve sensor history for inference.")
            return
    elif chosen_model.mode == "forecast":
        if (
            stored_context
            and stored_context.get("sensor_id") == sensor_id
            and stored_context.get("model_id") == chosen_model.identifier
        ):
            history_records = stored_context.get("history", [])
            forecast_records = stored_context.get("forecast", [])
            history_df = pd.DataFrame(history_records)
            forecast_df = pd.DataFrame(forecast_records)
            if not history_df.empty and "timestamp" in history_df.columns:
                history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True, errors="coerce")
            if not forecast_df.empty and "timestamp" in forecast_df.columns:
                forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"], utc=True, errors="coerce")
            payload = stored_context.get("payload", {})
            metrics = stored_context.get("metrics", {})
            schedule_request = stored_context.get("schedule_request")
        else:
            st.info("Run inference to preview forecast automation and scheduling.")
            st.session_state.last_schedule_response = None
            return
    else:
        if not submitted:
            return

    if chosen_model.mode == "forecast":
        if submitted:
            resp = _run_forecast(chosen_model, sensor_id, horizon or chosen_model.default_horizon, history_window)
            if not resp.get("success"):
                st.error("Forecast request failed")
                st.caption(resp.get("error", "Unknown error"))
                if resp.get("hint"):
                    st.caption(f"Hint: {resp['hint']}")
                return
            payload = resp.get("data", {})
            forecast_points = payload.get("forecast", [])
            forecast_df = pd.DataFrame(forecast_points)
            if not forecast_df.empty:
                forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"], utc=True, errors="coerce")
                forecast_df = forecast_df.sort_values("timestamp")

            st.success(
                f"Forecast generated with {payload.get('model_name')} v{payload.get('model_version')} "
                f"using {payload.get('history_points')} historical readings."
            )

            metrics = payload.get("metrics", {})
        else:
            st.success("Replaying the most recent forecast for this sensor/model combination.")

        met_col1, met_col2, met_col3 = st.columns(3)
        with met_col1:
            st.metric("Cadence (min)", _format_metric_value(payload.get("cadence_minutes")))
        with met_col2:
            st.metric("History Points", _format_metric_value(payload.get("history_points")))
        with met_col3:
            st.metric("Horizon Steps", _format_metric_value(payload.get("horizon_steps")))

        if metrics:
            st.caption(
                f"History window: {metrics.get('history_start', 'n/a')} → {metrics.get('history_end', 'n/a')}"
            )

        if not history_df.empty and not forecast_df.empty:
            history_series = (
                history_df
                .set_index("timestamp")
                ["value"]
                .rename("Historical")
            )
            forecast_series = (
                forecast_df
                .set_index("timestamp")
                ["predicted_value"]
                .rename("Forecast")
            )

            chart_df = pd.concat([history_series, forecast_series], axis=1)
            chart_df = chart_df.apply(pd.to_numeric, errors="coerce")
            chart_df = chart_df.sort_index()
            st.line_chart(chart_df)

        with st.expander("Forecast Table", expanded=False):
            st.dataframe(forecast_df, use_container_width=True)

        with st.expander("Historical Context", expanded=False):
            st.dataframe(history_df, use_container_width=True)

        st.divider()
        st.subheader("Maintenance Automation (Demo Pipeline)")
        st.caption(
            "Trigger the multi-agent scheduling workflow. The maintenance order flows through the SchedulingAgent "
            "and appears automatically on the Reporting Prototype and Golden Path views."
        )

        if submitted:
            schedule_request = _build_schedule_request(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                model=chosen_model,
                forecast_df=forecast_df,
                history_df=history_df,
                payload=payload,
            )
            if schedule_request:
                history_records = history_df.assign(
                    timestamp=history_df["timestamp"].astype(str)
                ).to_dict("records")
                forecast_records = forecast_df.assign(
                    timestamp=forecast_df["timestamp"].astype(str)
                ).to_dict("records")
                st.session_state.prediction_last_run = {
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "model_id": chosen_model.identifier,
                    "mode": chosen_model.mode,
                    "history": history_records,
                    "forecast": forecast_records,
                    "payload": payload,
                    "metrics": metrics,
                    "schedule_request": schedule_request,
                }
                st.session_state.last_schedule_response = None
        else:
            schedule_request = schedule_request or None

        schedule_btn_col, info_col = st.columns([1, 3])
        with schedule_btn_col:
            disabled = schedule_request is None
            trigger_clicked = st.button(
                "Create Maintenance Order",
                type="primary",
                disabled=disabled,
            )
        with info_col:
            if schedule_request is None:
                st.info("Run a forecast with at least one horizon step to enable maintenance scheduling.")
            else:
                st.caption(
                    "We derive a predicted failure window from the forecast horizon, send it through the SchedulingAgent, "
                    "and persist the outcome for downstream reporting."
                )

        if schedule_request and trigger_clicked:
            with st.spinner("Coordinating maintenance schedule via multi-agent pipeline..."):
                schedule_resp = make_api_request(
                    "POST",
                    "/api/v1/maintenance/schedule",
                    json_data=schedule_request,
                )
            if schedule_resp.get("success"):
                st.session_state.last_schedule_response = schedule_resp.get("data")
                st.success("Maintenance order dispatched. Check the Reporting Prototype for the live feed.")
            else:
                st.error(schedule_resp.get("error", "Failed to schedule maintenance."))
                if schedule_resp.get("hint"):
                    st.caption(f"Hint: {schedule_resp['hint']}")

        schedule_data = st.session_state.get("last_schedule_response") or {}
        if schedule_data:
            meta = schedule_data.get("metadata", {})
            schedule_details = schedule_data.get("schedule", {})
            schedule_cols = st.columns(3)
            schedule_cols[0].metric(
                "Schedule Status",
                schedule_data.get("status", "Scheduled"),
            )
            schedule_cols[1].metric(
                "Start",
                schedule_details.get("scheduled_start_time", "pending"),
            )
            schedule_cols[2].metric(
                "Technician",
                schedule_data.get("assigned_technician_id", "TBD"),
            )

            st.caption(
                f"Correlation ID: {schedule_data.get('correlation_id')} — model {meta.get('model_name', 'n/a')}"
            )

            with st.expander("Scheduled Maintenance Payload", expanded=False):
                st.json(schedule_data)

            st.caption(
                "Tip: open the Reporting Prototype page to preview the automatically generated maintenance report feed."
            )

    else:
        resp = _run_anomaly(chosen_model, history_rows)
        if not resp.get("success"):
            st.error("Anomaly detection failed")
            st.caption(resp.get("error", "Unknown error"))
            if resp.get("hint"):
                st.caption(f"Hint: {resp['hint']}")
            return
        payload = resp.get("data", {})
        st.success(
            f"Analyzed {payload.get('total_readings_analyzed')} readings; "
            f"detected {payload.get('anomaly_count')} anomalies."
        )

        anomalies = payload.get("anomalies_detected", [])
        if anomalies:
            anomalies_df = pd.DataFrame(anomalies)
            with st.expander("Detected Anomalies", expanded=True):
                st.dataframe(anomalies_df, use_container_width=True)
        else:
            st.info("No anomalies flagged for the selected window.")

        with st.expander("Analyzed History", expanded=False):
            st.dataframe(history_df, use_container_width=True)

    with st.expander("Recent API Latencies", expanded=False):
        samples = get_latency_samples()[-8:]
        for sample in reversed(samples):
            st.write(
                f"{sample['label']} – {sample['ms']:.0f} ms"
                f" (status={sample.get('status', 'unknown')})"
            )


render_prediction_page()
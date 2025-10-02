import time
from datetime import datetime
import uuid
import streamlit as st

from lib.api_client import make_api_request
from lib.i18n_translations import get_translation, bilingual_text
try:  # backward/forward compatibility
    from lib.api_client import record_latency_sample  # type: ignore
except Exception:  # noqa: BLE001
    def record_latency_sample(label: str, ms: float, **meta):  # type: ignore
        """Fallback no-op if latency recording not available."""
        return

st.set_page_config(page_title="Simulation Console", page_icon="🎮")

HELP_TEXT = """Simulate system conditions to demonstrate drift, anomalies, and baseline data flows.
Each simulation runs async on the backend and ingests synthetic readings. Drift simulations also
trigger an automatic drift check showing full MLOps loop.
"""

def _render_page_header():
    """Render bilingual page header."""
    st.header(get_translation("simulation", "page_title", "en"))
    st.caption(get_translation("simulation", "description", "en"))
    with st.expander("ℹ️ Ajuda / Help"):
        st.write(f"**🇧🇷 PT:** {get_translation('simulation', 'description', 'pt')}")

SIM_TYPES = {
    "Drift": {
        "endpoint": "/api/v1/simulate/drift-event",
        "payload_builder": lambda sensor_id, **kw: {
            "sensor_id": sensor_id,
            "drift_magnitude": kw.get("drift_magnitude", 2.0),
            "num_samples": kw.get("num_samples", 50),
            "base_value": kw.get("base_value", 25.0),
            "noise_level": kw.get("noise_level", 1.0),
        },
        "defaults": {"drift_magnitude": 2.0, "num_samples": 50, "base_value": 25.0, "noise_level": 1.0},
        "description": "Generate a gradual distribution shift (drift) and ingest readings; backend triggers a drift check automatically.",
    },
    "Anomaly": {
        "endpoint": "/api/v1/simulate/anomaly-event",
        "payload_builder": lambda sensor_id, **kw: {
            "sensor_id": sensor_id or "demo-sensor-002",
            "anomaly_magnitude": kw.get("anomaly_magnitude", 5.0),
            "num_anomalies": kw.get("num_anomalies", 10),
        },
        "defaults": {"anomaly_magnitude": 5.0, "num_anomalies": 10},
        "description": "Inject sudden anomalous readings (outliers) to test detection logic.",
    },
    "Normal": {
        "endpoint": "/api/v1/simulate/normal-data",
        "payload_builder": lambda sensor_id, **kw: {
            "sensor_id": sensor_id or "demo-sensor-003",
            "num_samples": kw.get("num_samples", 100),
            "duration_minutes": kw.get("duration_minutes", 60),
        },
        "defaults": {"num_samples": 100, "duration_minutes": 60},
        "description": "Generate baseline readings without anomalies or drift for model context.",
    },
}

if "simulation_runs" not in st.session_state:
    st.session_state.simulation_runs = []  # list of dicts: {id, type, status, started_at, payload, response}


def _launch_simulation(sim_type: str, params: dict):
    meta = SIM_TYPES[sim_type]
    endpoint = meta["endpoint"]
    sensor_identifier = params.get("sensor_id") or f"demo-sensor-{uuid.uuid4().hex[:4]}"
    builder_kwargs = dict(params)
    builder_kwargs.pop("sensor_id", None)
    payload = meta["payload_builder"](sensor_identifier, **builder_kwargs)
    t0 = time.perf_counter()
    resp = make_api_request("POST", endpoint, json_data=payload)
    latency_ms = (time.perf_counter() - t0) * 1000
    record_latency_sample(f"simulate:{sim_type.lower()}", latency_ms, status="ok" if resp.get("success") else "error")
    entry = {
        "id": uuid.uuid4().hex[:8],
        "type": sim_type,
        "payload": payload,
        "started_at": datetime.utcnow().isoformat(),
        "latency_ms": latency_ms,
        "response": resp,
    }
    st.session_state.simulation_runs.insert(0, entry)
    return entry


def _render_runs_table():
    if not st.session_state.simulation_runs:
        st.info("No simulations launched yet.")
        return
    st.subheader("Recent Simulation Runs")
    for run in st.session_state.simulation_runs[:25]:
        status = "✅" if run["response"].get("success") else "❌"
        header = f"{status} {run['type']} • {run['id']} • {run['latency_ms']:.0f} ms"
        with st.expander(header, expanded=False):
            cols = st.columns(4)
            with cols[0]:
                st.caption(f"Started: {run['started_at']}")
            with cols[1]:
                st.caption(
                    f"Events: {run['response'].get('data', {}).get('events_generated', '?') if run['response'].get('success') else '-'}"
                )
            with cols[2]:
                st.caption(
                    f"Correlation: {run['response'].get('data', {}).get('correlation_id', '-') if run['response'].get('success') else '-'}"
                )
            with cols[3]:
                st.caption(
                    f"Simulation ID: {run['response'].get('data', {}).get('simulation_id', '-') if run['response'].get('success') else '-'}"
                )

            st.markdown("**Payload**")
            st.json(run["payload"])

            if run["response"].get("success"):
                st.markdown("**Raw Response**")
                st.json(run["response"]["data"])
            else:
                st.warning(run["response"].get("error", "Unknown error"))


def render_simulation_console():
    _render_page_header()

    tabs = st.tabs(list(SIM_TYPES.keys()))
    for tab, sim_type in zip(tabs, SIM_TYPES.keys()):
        with tab:
            meta = SIM_TYPES[sim_type]
            st.markdown(f"**{sim_type} Simulation** — {meta['description']}")
            defaults = meta["defaults"]
            with st.form(f"form_{sim_type}"):
                sensor_id = st.text_input("Sensor ID (blank = auto)", value="")
                if sim_type == "Drift":
                    d1, d2, d3, d4 = st.columns(4)
                    with d1:
                        drift_magnitude = st.number_input("Drift Magnitude", value=float(defaults['drift_magnitude']), min_value=0.1, max_value=10.0, step=0.1)
                    with d2:
                        num_samples = st.number_input("Num Samples", value=int(defaults['num_samples']), min_value=10, max_value=500, step=10)
                    with d3:
                        base_value = st.number_input("Base Value", value=float(defaults['base_value']))
                    with d4:
                        noise_level = st.number_input("Noise Level", value=float(defaults['noise_level']), min_value=0.0, max_value=10.0, step=0.1)
                    submitted = st.form_submit_button("🚀 Run Drift Simulation", use_container_width=True)
                    if submitted:
                        entry = _launch_simulation("Drift", {
                            "sensor_id": sensor_id,
                            "drift_magnitude": drift_magnitude,
                            "num_samples": num_samples,
                            "base_value": base_value,
                            "noise_level": noise_level,
                        })
                        st.success(f"Launched drift simulation {entry['id']}")
                elif sim_type == "Anomaly":
                    a1, a2 = st.columns(2)
                    with a1:
                        anomaly_magnitude = st.number_input("Anomaly Magnitude", value=float(defaults['anomaly_magnitude']), min_value=0.5, max_value=20.0, step=0.5)
                    with a2:
                        num_anomalies = st.number_input("Num Anomalies", value=int(defaults['num_anomalies']), min_value=1, max_value=200, step=1)
                    submitted = st.form_submit_button("⚡ Run Anomaly Simulation", use_container_width=True)
                    if submitted:
                        entry = _launch_simulation("Anomaly", {
                            "sensor_id": sensor_id,
                            "anomaly_magnitude": anomaly_magnitude,
                            "num_anomalies": num_anomalies,
                        })
                        st.success(f"Launched anomaly simulation {entry['id']}")
                else:  # Normal
                    n1, n2, n3 = st.columns(3)
                    with n1:
                        num_samples = st.number_input("Num Samples", value=int(defaults['num_samples']), min_value=10, max_value=1000, step=10)
                    with n2:
                        duration_minutes = st.number_input("Duration (mins)", value=int(defaults['duration_minutes']), min_value=10, max_value=24*60, step=10)
                    with n3:
                        filler = st.empty()
                    submitted = st.form_submit_button("🌱 Run Normal Simulation", use_container_width=True)
                    if submitted:
                        entry = _launch_simulation("Normal", {
                            "sensor_id": sensor_id,
                            "num_samples": num_samples,
                            "duration_minutes": duration_minutes,
                        })
                        st.success(f"Launched normal simulation {entry['id']}")

    _render_runs_table()


render_simulation_console()

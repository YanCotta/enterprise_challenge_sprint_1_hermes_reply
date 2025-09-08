
Task 1: Final Acceptance Testing Protocol
Responsible: You

Context: This protocol is a manual, comprehensive run-through inspired by your automated E2E tests (tests/e2e/final_system_test.py and test_e2e_full_system_workflow.py). Its purpose is to ensure all components are perfectly integrated before recording the demo.

Step-by-Step Guide:

Phase I: Environment Initialization (Clean Slate Verification)

From your project root, execute docker compose down -v. This command destroys all containers, volumes, and networks, guaranteeing you are testing from a pristine state.

Follow your own reproducibility guide from the new README.md: run dvc pull to ensure data and models are synchronized, then docker compose up --build -d to build and start all services in the background.

Phase II: Data Ingestion & Persistence Integrity

Navigate to the API documentation at http://localhost:8000/docs.

Locate the POST /api/v1/data/ingest endpoint.

Submit a test reading. Use a unique value to easily find it later, for example:

JSON

{
  "event_id": "test-event-001",
  "sensor_id": "sensor_15",
  "timestamp": "2025-09-05T12:00:00Z",
  "value": 99.99,
  "anomaly_score": 0.0
}
Database Verification: Connect to the running PostgreSQL container. You can do this via your IDE's database tools or the command line: docker compose exec db psql -U user -d smart_maintenance. Run the query: SELECT * FROM sensor_readings WHERE value = 99.99;. Confirm the record exists.

Idempotency Test: Submit the exact same JSON payload to the /ingest endpoint a second time. Observe the logs of the api service (docker compose logs -f api). You should see a log message indicating that a duplicate event was detected and handled, proving your idempotency mechanism is working.

Phase III: Core ML & Event-Driven Workflow

In the API docs, execute the POST /api/v1/ml/check_drift endpoint for sensor_id: "sensor_15".

Observe Logs: Monitor the logs (docker compose logs -f api drift_agent retrain_agent).

The api log should show the result of the Kolmogorov-Smirnov test.

If drift is detected, you should see the drift_agent publish a DriftDetectedEvent to a Redis channel.

Subsequently, the retrain_agent should log that it has received this event and is initiating a retraining workflow (or respecting a cooldown period). This confirms the entire event bus integration is functional.

Phase IV: UI and Service Accessibility

Open the Streamlit UI at http://localhost:8501. Confirm that it loads without error and successfully visualizes sensor data.

Open the MLflow UI at http://localhost:5000. Verify that the model registry is populated and you can navigate to the artifacts of a registered model (like the pump-classifier).

Access the Prometheus metrics endpoint at http://localhost:8000/metrics. Confirm that a page of metrics is displayed.

Task 2: Record and Publish the Final Video Demonstration
Responsible: You

Step-by-Step Guide:

Scene Preparation: Arrange your screen with all necessary windows open before you start recording: the final README.md on GitHub, the 08_pump_classification.ipynb notebook, a terminal ready to show docker compose logs, and browser tabs for the running API docs and Streamlit UI.

Scripting: Use your finalized README.md as your script. This ensures your spoken presentation is perfectly aligned with your written report. Perform one practice run-through to check your timing and flow.

Recording: Use screen recording software (OBS Studio, Loom, etc.). Focus on a clear narrative and a steady pace.

Pro Tip for the Demo: When you get to the live demo part, show the docker compose logs -f running in the terminal. Then, submit a new sensor reading from the API docs. The audience will see the structured JSON log appear in real-time in the terminal, which is a very powerful way to demonstrate a live, responsive system.

Final Steps: Upload the video to YouTube as "Unlisted". Copy the share link and paste it prominently at the top of your README.md. Commit this final change with a message like docs: Add final presentation video link.


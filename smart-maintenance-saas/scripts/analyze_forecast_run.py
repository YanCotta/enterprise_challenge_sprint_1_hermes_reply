# smart-maintenance-saas/scripts/analyze_forecast_run.py
import mlflow
import os
import pandas as pd

def analyze_latest_prophet_run():
    """
    Connects to MLflow, fetches the latest Prophet run, and prints a performance summary.
    """
    try:
        # Use the same logic as our notebooks to find the MLflow server
        tracking_uri = "http://mlflow:5000" if os.getenv("DOCKER_ENV") == "true" else "http://localhost:5000"
        mlflow.set_tracking_uri(tracking_uri)

        experiment_name = "Forecasting Models"
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if not experiment:
            print(f"ERROR: Experiment '{experiment_name}' not found.")
            return

        # Fetch all runs from the experiment, sort by start time, get the latest
        runs_df = mlflow.search_runs(experiment_ids=[experiment.experiment_id], order_by=["start_time DESC"])
        if runs_df.empty:
            print(f"ERROR: No runs found in experiment '{experiment_name}'.")
            return

        latest_run_row = runs_df.iloc[0]
        run_id = latest_run_row["run_id"]
        latest_run = mlflow.get_run(run_id)

        print("---" * 15)
        print(f"🔬 Analysis for MLflow Run: {run_id}")
        print(f"✨ Model Type: {latest_run.data.params.get('model_type', 'N/A')}")
        print(f"👤 Run Name: {latest_run.info.run_name}")
        print("---" * 15)

        metrics = latest_run.data.metrics
        mae = metrics.get("mae", 0)
        naive_mae = metrics.get("naive_mae", 0)

        print("\n📊 Key Performance Metrics:")
        print(f"  - Prophet MAE:      {mae:.4f}")
        print(f"  - Naive MAE (Baseline): {naive_mae:.4f}")

        if naive_mae > 0:
            improvement = ((naive_mae - mae) / naive_mae) * 100
            print(f"\n  - ✅ Improvement over Baseline: {improvement:.2f}%")
        else:
            print("\n  - ⚠️ Could not calculate improvement over baseline.")

        print("\n📋 All Logged Metrics:")
        # Use pandas for nice formatting
        metrics_series = pd.Series(metrics)
        print(metrics_series.to_string())

        print("\n---" * 15)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    analyze_latest_prophet_run()
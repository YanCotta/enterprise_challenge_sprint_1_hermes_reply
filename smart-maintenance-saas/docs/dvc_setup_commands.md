# DVC Setup Commands

## 1. Add all real-world datasets to DVC:

```bash
# Add each real-world dataset directory
dvc add data/AI4I_2020_uci_dataset
dvc add data/kaggle_pump_sensor_data  
dvc add data/MIMII_sound_dataset
dvc add data/nasa_bearing_dataset
dvc add data/XJTU_SY_bearing_datasets

# Add MLflow artifacts and models
dvc add mlflow_data
dvc add mlflow_db
```

## 2. Configure remote storage (example for Google Drive):

```bash
# Replace <FOLDER_ID> with your actual Google Drive folder ID
dvc remote add -d myremote gdrive://<FOLDER_ID>
```

## 3. Commit and push changes:

```bash
# Add DVC files to git
git add .
git commit -m "feat: Integrate DVC for comprehensive data and model versioning"

# Push data to DVC remote
dvc push
```

Note: The synthetic dataset `sensor_data.csv` is already under DVC control via `sensor_data.csv.dvc`.
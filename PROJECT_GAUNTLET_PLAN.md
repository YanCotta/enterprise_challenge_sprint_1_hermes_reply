# **Project Gauntlet: The Master Plan**

This multi-day sprint will replace our synthetic data with a suite of real-world datasets, benchmark multiple ML algorithms, and apply advanced feature engineering to create a highly credible and robust predictive maintenance platform.

### **Guiding Principles:**

  * **You are the project lead.** The copilot is your partner. You will run all commands and give the "green light" at each step.
  * **One challenge at a time.** We will tackle each data type (tabular, vibration, audio) in a separate phase to ensure our analysis is clear and methodical.
  * **Document as we go.** We will use MLflow extensively and create final documentation to capture our findings.

-----

### **Phase 0: Housekeeping & Preparation**

**Goal:** Prepare the repository for the new data and document our sources.

#### **▶️ Prompt for Copilot: Phase 0**

-----

**Objective:** Prepare our project for "Project Gauntlet". This involves updating our `.gitignore` to exclude the large new datasets and adding a reference to these datasets in our `changelog` for tracking purposes.

**Important Reminders:**

  * I, the user, will run all terminal commands. Please provide the commands for me to execute.
  * Wait for my "green light" after you present your proposed changes.

-----

**Step 0.1: Update `.gitignore`**

  * **Your Task:** Please open the `smart-maintenance-saas/.gitignore` file and append the following lines to it. This will prevent us from accidentally committing gigabytes of data to our Git repository.

    ```gitignore
    # Project Gauntlet - Real-World Datasets
    data/AI4I_2020_uci_dataset/
    data/kaggle_pump_sensor_data/
    data/MIMII_sound_dataset/
    data/nasa_bearing_dataset/
    data/XJTU_SY_bearing_datasets/
    ```

  * **Present the changes and wait for my approval.**

-----

**Step 0.2: Update Changelog with Data Sources**

  * **Your Task:** Once I approve the `.gitignore` changes, please open the `30-day-sprint-changelog.md` file and append a new section for today. This will serve as our reference for the data we've downloaded.

    ```markdown
    ## 2025-08-18 (Day 11 Kick-off) – Project Gauntlet: Data Acquisition

    ### New Real-World Datasets Acquired
    - **Objective**: Pivoted from synthetic data to a suite of real-world datasets to rigorously benchmark the platform's capabilities.
    - **Datasets Downloaded**:
      - **AI4I 2020 UCI Dataset**: `data/AI4I_2020_uci_dataset/ai4i2020.csv`
      - **Kaggle Pump Sensor Data**: `data/kaggle_pump_sensor_data/sensor_maintenance_data.csv`
      - **NASA Bearing Dataset**: `data/nasa_bearing_dataset/4. Bearings/IMS.7z`
      - **XJTU-SY Bearing Datasets**: `data/XJTU_SY_bearing_datasets/`
      - **MIMII Sound Dataset**: `data/MIMII_sound_dataset/`
    ```

  * **Present the changes and wait for my final approval for this phase.**

-----

-----

### **Phase 1: The Classification Gauntlet (AI4I Dataset)**

**Goal:** Find the best classification algorithm for predicting machine failure from structured, tabular sensor data.

### **Master Guardrail Snippet for Copilot Prompts**

**CRITICAL WORKFLOW REMINDERS (Read First):**

- **Clean Environment Start:** The user has cleaned their Docker environment. Your first instruction in this new phase must be to guide the user to bring the full Docker stack up with a fresh build.

-   **Important notes and guardrails for all phases below:**

- **Robust Dependency Management:** If a new dependency is needed (like librosa), the process is:
    1. I will instruct the user to run `poetry add <package>`.
    2. You will then verify that `pyproject.toml` and `poetry.lock` have been updated.
    3. The subsequent `docker compose up -d --build` command will then correctly use the updated lock file to build the image, ensuring consistency.

- **Validate Before Running:** If we edit any YAML (`docker-compose.yml`) or script (`Makefile`), you must first instruct the user to run a validation command (e.g., `docker compose config`) to catch syntax errors before we attempt a full build or execution.

- **Path Awareness:** Remember, the project is located in the `smart-maintenance-saas` subdirectory. All commands you provide must reflect this (e.g., `cd smart-maintenance-saas && ...` or assume the user is already in that directory).

- **Interactive Collaboration:** This is a partnership. At every step where you propose new code, a new command, or a new file, you must wait for my explicit "green light" before proceeding to the next step. I will run all terminal commands.

#### **▶️ Prompt for Copilot: Phase 1**

-----

**Objective:** Begin the "Classification Gauntlet". We will use the **AI4I 2020 Dataset** to train, evaluate, and compare multiple baseline models. In the next phase, we will see how much advanced feature engineering can improve their performance.

-----

**Step 1.1: Setup (User Task)**

  * **To Me, the User:** I need you to create the new notebook for this phase.
    1.  **Create the Notebook File:** Create a new, empty file at `smart-maintenance-saas/notebooks/05_classification_benchmark.ipynb`.
    2.  **Paste Initial Content:** Open it in a text editor and paste the JSON content I've provided below.
    3.  **Confirm:** Let me know when you're done.

NOTEBOOK CODE

-----

**Step 1.2: Baseline Model Training (Copilot Task)**

  * Once I give you the green light, your task is to write the Python code for a new notebook cell. This code should benchmark our baseline models (`RandomForestClassifier`, `SVC`, `LGBMClassifier`) on the preprocessed (but not yet feature-engineered) data. For each model, it must create a tagged MLflow run, log all results, and register the model.
  * **Present the code to me for review.** Explain the process and wait for my approval.

-----

**Step 1.3: Advanced Feature Engineering (Copilot Task)**

  * After the baseline models are trained and logged, your next task is to propose and write the code for a new cell that applies advanced feature engineering (e.g., rolling statistics on key numerical columns).
  * **Present the feature engineering code to me.** Explain the new features you're creating and wait for my approval.

-----

**Step 1.4: Feature-Engineered Model Training (Copilot Task)**

  * Once I approve the feature engineering, your task is to write the code for a final cell. This code will re-train the same suite of models (`RandomForestClassifier`, `SVC`, `LGBMClassifier`) on the *new, enriched* dataset.
  * It must log these as new runs to the same MLflow experiment, clearly tagged (e.g., `features: engineered`) so we can compare them to the baselines.
  * **Present this final block of code to me for review.**

-----

**Step 1.5: Execution (User Task)**

  * After all code is approved, you will guide me on how to update the `Makefile` and run the full notebook.
  * We will then verify all runs (baseline and engineered) in the MLflow UI together.

Ready to begin the Classification Gauntlet?

-----

### **Phase 2: The Vibration Gauntlet (NASA & XJTU Datasets)**

**Goal:** Tackle raw vibration signal data. This is a significant step up in complexity, as we must perform signal processing to extract meaningful features before we can train our models.

#### **▶️ Prompt for Copilot: Phase 2**

-----

**Objective:** Begin the "Vibration Gauntlet". We will work with the **NASA Bearing Dataset** to build a pipeline that can process raw time-series vibration signals, extract statistical and frequency-domain features, and train unsupervised anomaly detection models.

-----

**Step 2.1: Data Preparation & Setup (User Task)**

  * **To Me, the User:** This phase requires you to decompress the datasets and create the new notebook.
    1.  **Extract NASA Dataset:** The `nasa_bearing_dataset/4. Bearings/IMS.7z` file is a 7-Zip archive. You will need a tool like `p7zip` (Linux/macOS) or 7-Zip (Windows) to extract its contents into the `nasa_bearing_dataset` folder.
    2.  **Extract XJTU-SY Dataset:** The `XJTU_SY_bearing_datasets` files are multi-part RAR archives. Ensure all `.rar` parts are in the same directory, then use a tool like `unrar` or 7-Zip to extract the first part (`.part01.rar`), which will automatically combine them all.
    3.  **Create the Notebook File:** Create a new, empty file at `smart-maintenance-saas/notebooks/06_vibration_benchmark.ipynb`.
    4.  **Paste Initial Content:** Open it in a text editor and paste this initial JSON content. This sets up our environment and necessary libraries for signal processing.
        ```json
        {
         "cells": [
          {
           "cell_type": "code",
           "execution_count": null,
           "metadata": {},
           "outputs": [],
           "source": [
            "import pandas as pd\n",
            "import numpy as np\n",
            "import mlflow\n",
            "from scipy.stats import kurtosis, skew\n",
            "from scipy.fft import fft\n",
            "from sklearn.ensemble import IsolationForest\n",
            "from sklearn.svm import OneClassSVM\n",
            "from sklearn.preprocessing import StandardScaler\n",
            "import os\n",
            "import glob\n",
            "\n",
            "tracking_uri = \"http://mlflow:5000\" if os.getenv(\"DOCKER_ENV\") == \"true\" else \"http://localhost:5000\"\n",
            "mlflow.set_tracking_uri(tracking_uri)\n",
            "mlflow.set_experiment(\"Vibration Gauntlet (NASA)\")\n",
            "\n",
            "print(f\"MLflow tracking URI set to: {mlflow.get_tracking_uri()}\")"
           ]
          }
         ],
         "metadata": {},\n",
         "nbformat": 4,\n",
         "nbformat_minor": 2\n",
        }
        ```
    5.  **Confirm:** Let me know when you have completed these steps.

-----

**Step 2.2: Signal Processing & Feature Extraction (Copilot Task)**

  * Once I give you the green light, your task is to write the Python code for a new cell. This is the most critical part of this phase. The code must:
    1.  Define a function to load the NASA bearing data files. These are typically text files where each row is a vibration reading.
    2.  Define a feature extraction function that takes a window of the raw signal (e.g., 2048 data points) and calculates key statistical and frequency-domain features.
          * **Statistical Features:** RMS (Root Mean Square), Kurtosis, Skewness, Peak-to-Peak value.
          * **Frequency Features (using FFT - Fast Fourier Transform):** The frequency and amplitude of the dominant peak.
    3.  Process all the data files, applying this feature extraction to generate a structured DataFrame where each row represents a time window and each column is an engineered feature.
  * **Present this complex code to me for review.** Explain what each feature represents in the context of machine health (e.g., "Kurtosis can indicate the 'peakiness' of a signal, which often increases when a bearing starts to fail"). Wait for my approval.

-----

**Step 2.3: Anomaly Detection Model Training (Copilot Task)**

  * After I approve the feature extraction, your next task is to write the code for a new cell that trains our anomaly detection models (`IsolationForest`, `OneClassSVM`) on the new feature set.
  * For each model, it must create an MLflow run, log the model parameters, and register the model. Since this is unsupervised, there won't be traditional metrics like accuracy, but you should log summary statistics of the resulting anomaly scores.
  * **Present the model training code to me for review.**

-----

**Step 2.4: Execution (User Task)**

  * After all code is approved, you will guide me on updating the `Makefile` with a new `run-vibration-benchmark` target and then running the notebook. We will then verify the results in the MLflow UI.

Ready to begin the Vibration Gauntlet?

-----

### **Phase 3: The Audio Gauntlet (MIMII Dataset)**

**Goal:** Work with our final data modality, audio, to detect anomalies in machine sounds. This requires audio-specific libraries and feature extraction techniques.

#### **▶️ Prompt for Copilot: Phase 3**

-----

**Objective:** Begin the "Audio Gauntlet". We will use the **MIMII Sound Dataset** (`6_dB_valve` and `6_dB_pump`) to build a pipeline that can process `.wav` files, extract industry-standard audio features (MFCCs), and train anomaly detection models.

-----

**Step 3.1: Environment & Setup (User & Copilot Task)**

  * **To You, Copilot:** Our first step is to add a new, critical dependency for audio processing: `librosa`.
      * **User Action:** Please instruct me to run the following command to add `librosa` and its dependencies to our project:
        ```bash
        poetry add librosa
        ```
  * **To Me, the User:** While that installs, I need you to create the notebook.
    1.  **Create the Notebook File:** Create a new, empty file at `smart-maintenance-saas/notebooks/07_audio_benchmark.ipynb`.
    2.  **Paste Initial Content:** Open it in a text editor and paste this initial JSON content.
        ```json
        {
         "cells": [
          {
           "cell_type": "code",
           "execution_count": null,
           "metadata": {},
           "outputs": [],
           "source": [
            "import pandas as pd\n",
            "import numpy as np\n",
            "import mlflow\n",
            "import librosa\n",
            "from sklearn.ensemble import IsolationForest\n",
            "from sklearn.preprocessing import StandardScaler\n",
            "import os\n",
            "import glob\n",
            "\n",
            "tracking_uri = \"http://mlflow:5000\" if os.getenv(\"DOCKER_ENV\") == \"true\" else \"http://localhost:5000\"\n",
            "mlflow.set_tracking_uri(tracking_uri)\n",
            "mlflow.set_experiment(\"Audio Gauntlet (MIMII)\")\n",
            "\n",
            "print(f\"MLflow tracking URI set to: {mlflow.get_tracking_uri()}\")"
           ]
          }
         ],
         "metadata": {},\n",
         "nbformat": 4,\n",
         "nbformat_minor": 2\n",
        }
        ```
    3.  **Confirm:** Let me know when you have completed these steps.

-----

**Step 3.2: Audio Feature Extraction (Copilot Task)**

  * Once I confirm the setup is complete, your task is to write the Python code for a new cell that processes the audio data. This code must:
    1.  Define a function to load `.wav` files using `librosa`.
    2.  Define a feature extraction function that takes an audio signal and calculates its **Mel-Frequency Cepstral Coefficients (MFCCs)**. You should take the mean of the MFCCs over time to get a single feature vector for each audio clip.
    3.  Create a loop that goes through the MIMII directory structure (`normal` and `abnormal` folders), processes each `.wav` file, and builds a labeled DataFrame of audio features.
  * **Present this code to me for review.** Explain briefly what MFCCs are (e.g., "they are a representation of the short-term power spectrum of a sound, widely used in audio processing"). Wait for my approval.

-----

**Step 3.3: Model Training on Audio Features (Copilot Task)**

  * After I approve the feature extraction, write the code for a new cell to train a classification model (like `RandomForestClassifier`) on the MFCC features to distinguish between "normal" and "abnormal" sounds.
  * This code must log the run to MLflow with a full classification report and register the model.
  * **Present the model training code to me for review.**

-----

**Step 3.4: Execution (User Task)**

  * After all code is approved, you will guide me on updating the `Makefile` with a `run-audio-benchmark` target and running the notebook. We will verify the results in the MLflow UI.

Ready to begin the Audio Gauntlet?

-----

### **Phase 4: Final Analysis & Documentation**

**Goal:** Consolidate all our findings from the gauntlets into a final report and produce the project's key documentation.

#### **▶️ Prompt for Copilot: Phase 4**

-----

**Objective:** Conclude "Project Gauntlet". We will programmatically analyze all the experiments we've logged to MLflow, declare our champion models, and generate the final documentation that showcases our comprehensive work.

-----

**Step 4.1: Setup (User Task)**

  * **To Me, the User:** I need you to create our final analysis notebook.
    1.  **Create the Notebook File:** Create a new, empty file at `smart-maintenance-saas/notebooks/08_final_analysis.ipynb`.
    2.  **Paste Initial Content:** Open it in a text editor and paste this initial JSON content.
        ```json
        {
         "cells": [
          {
           "cell_type": "code",
           "execution_count": null,
           "metadata": {},
           "outputs": [],
           "source": [
            "import mlflow\n",
            "import pandas as pd\n",
            "import plotly.express as px\n",
            "\n",
            "pd.set_option('display.max_rows', 100)\n",
            "\n",
            "tracking_uri = \"http://mlflow:5000\" if os.getenv(\"DOCKER_ENV\") == \"true\" else \"http://localhost:5000\"\n",
            "mlflow.set_tracking_uri(tracking_uri)\n",
            "\n",
            "print(f\"Connected to MLflow at: {mlflow.get_tracking_uri()}\")"
           ]
          }
         ],
         "metadata": {},\n",
         "nbformat": 4,\n",
         "nbformat_minor": 2\n",
        }
        ```
    3.  **Confirm:** Let me know when you are done.

-----

**Step 4.2: Comprehensive Analysis Script (Copilot Task)**

  * Once I give you the green light, your task is to write the Python code for a new cell that performs our final analysis. This code must:
    1.  Use `mlflow.search_runs()` to fetch all runs from our three gauntlet experiments: "Classification Gauntlet (AI4I)", "Vibration Gauntlet (NASA)", and "Audio Gauntlet (MIMII)".
    2.  Combine the results into clean pandas DataFrames.
    3.  Generate summary tables and plots (using `plotly.express`) that clearly show:
          * The performance comparison of baseline vs. feature-engineered models in the classification task.
          * The results of the different anomaly detection models for the vibration and audio tasks.
    4.  Programmatically identify and print the "Champion Model" for each gauntlet based on the best performance metrics.
  * **Present this analysis code to me for review.**

-----

**Step 4.3: Final Documentation Generation (Copilot Task)**

  * After we run the analysis and agree on the champions, your final coding task is to generate the complete markdown content for our `docs/REAL_WORLD_DATASETS.md` file.
  * This document should summarize everything we've done in Project Gauntlet, including the datasets used, the feature engineering techniques applied, the models benchmarked, our champion model findings, and the final "Bring Your Own Data" disclaimer.
  * **Present the full markdown text to me.**

-----

**Step 4.4: Finalization (User Task)**

  * Once I approve the markdown, I will manually create the `docs/REAL_WORLD_DATASETS.md` file and paste the content.
  * You will then provide me with the final, massive changelog entry that summarizes the entirety of "Project Gauntlet."
  * With that, this epic sprint will be complete, and we will be ready to proceed to the original Day 11.


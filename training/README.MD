# Model Training

This directory contains code and instructions for training object detection models.

## Directory Structure

```
training/
├── checkout_counter/     # Training code for checkout counter detection
│   ├── train_checkout_model.py
│   └── modified_data.yaml (generated)
└── data/                 # Datasets (not included in git)
    └── checkout counter.v1i.yolov8/
        ├── test/
        ├── train/
        ├── valid/
        └── data.yaml
```

## Server Deployment

When deploying to a server, the following files need to be manually transferred as they are not included in git:

### 1. Dataset
The complete dataset must be manually transferred to the server:
```bash
scp -r "training/data/checkout counter.v1i.yolov8" user@server:/path/to/training/data/
```

### 2. Base Model
Download the base YOLOv8 model directly on the server:
```bash
cd /path/to/training/checkout_counter
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt
```

### 3. Environment Setup
Install the required dependencies on the server:
```bash
pip install ultralytics opencv-python pyyaml
```

### 4. Training
Run the training script on the server:
```bash
cd /path/to/training/checkout_counter
python train_checkout_model.py
```

### 5. Model Retrieval
After training completes, copy the trained model back to your local machine:
```bash
scp user@server:/path/to/training/checkout_counter/runs/detect/checkout_model/weights/best.pt ./local/path/
```

## Notes
- Training outputs will be saved in `runs/detect/checkout_model/`
- The best model will be at `runs/detect/checkout_model/weights/best.pt`
- Training parameters can be adjusted in the `train_checkout_model.py` script

# 🔍 Running Test Modules with -m

When you're testing Python modules like `test_person_tracker.py` or `test_checkout_monitoring.py`, it's best to use the `-m` flag from the project root. This ensures proper module resolution (especially for relative imports like `from services.footpath.tracker import PersonTracker`).

## ✅ Why use -m?
Python's `-m` flag tells it to treat the target as a module inside a package, so relative imports work correctly. If you just run the file directly (e.g., `python3 models_testing/test_person_tracker.py`), you'll often get errors like:

```bash
ModuleNotFoundError: No module named 'services'

## ▶️ Usage

Make sure you're in the project root directory, then run the desired test module like this:

```bash
python3 -m models_testing.test_person_tracker
or
python3 -m models_testing.test_checkout_monitoring

cd vt-camera-streamapi-backend
python3 -m models_testing.test_person_tracker
python3 -m models_testing.test_checkout_monitoring
```

That's it! 🚀

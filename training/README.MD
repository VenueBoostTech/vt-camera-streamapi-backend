# Model Training & Services

This directory contains code and instructions for training object detection models and associated analytical services.

## Directory Structure

```
training/
├── checkout_counter/     # Training code for checkout counter detection
│   ├── train_checkout_model.py
│   └── modified_data.yaml (generated)
├── people_counter/
│   ├── train_people_counter.py
│   └── modified_people_data.yaml
├── face_detection/
│   ├── train_face_detection_model.py
│   └── modified_data.yaml
├── general_object_detection/
│   ├── train_general_object_detection.py
│   └── modified_data.yaml
├── vehicle_detection/
│   ├── train_vehicle_detection.py
│   └── modified_data.yaml
├── ppe_detection/
│   ├── train_ppe_detection.py
│   └── modified_data.yaml
└── data/                 # Datasets (not included in git)
    ├── checkout counter.v1i.yolov8/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── shoplifting.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── demographics.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── vehicle_detection.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── ppe_detection.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── face_detection.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── general_object_detection.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── people_counter.v1i.yolov11/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml
    ├── checkout_counter.v1i.yolov8/
    │   ├── test/
    │   ├── train/
    │   ├── valid/
    │   └── data.yaml

services/
├── footpath/
│   └── tracker.py        # Person tracking service
├── checkout_monitoring.py # Checkout counter monitoring service
└── heatmap_generator.py   # Heatmap generation service
└── shoplifting_detection.py # Shoplifting detection service
└── demographics_detector.py # Demographics detection service
└── general_object_detector.py # General object detection service
└── people_counter.py # People counter service
└── vehicle_detector.py # Vehicle detection service
└── ppe_detector.py # PPE detection service
└── face_detector.py # Face detection service
```

## Server Deployment

When deploying to a server, the following files need to be manually transferred as they are not included in git:

### 1. Dataset
The complete dataset must be manually transferred to the server:
```bash
scp -r "training/data/checkout counter.v1i.yolov8" user@server:/path/to/training/data/
scp -r "training/data/shoplifting.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/demographics.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/People Detection -General-.v8i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/vehicle_detection.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/ppe_detection.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/face_detection.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/general_object_detection.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/people_counter.v1i.yolov11" user@server:/path/to/training/data/
scp -r "training/data/checkout_counter.v1i.yolov8" user@server:/path/to/training/data/
```

### 2. Base Model
Download the base YOLOv8 model directly on the server:
```bash
cd /path/to/training/checkout_counter
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/shoplifting_detection
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/demographics_detector
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/people_counter
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/vehicle_detector
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/ppe_detector
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/face_detector
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -o yolov8s.pt

cd /path/to/training/general_object_detector
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

cd /path/to/training/shoplifting_detection
python train_shoplifting_model.py

cd /path/to/training/demographics_detector
python train_demographics.py

cd /path/to/training/people_counter
python train_people_counter.py

cd /path/to/training/vehicle_detector
python train_vehicle_detector.py

cd /path/to/training/ppe_detector
python train_ppe_detector.py

cd /path/to/training/face_detector
python train_face_detector.py

cd /path/to/training/general_object_detector
python train_general_object_detector.py
```

### 5. Model Retrieval
After training completes, copy the trained model back to your local machine:
```bash
scp user@server:/path/to/training/checkout_counter/runs/detect/checkout_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/shoplifting_detection/runs/detect/shoplifting_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/demographics_detector/runs/detect/demographics_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/people_counter/runs/detect/people_counter_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/vehicle_detector/runs/detect/vehicle_detector_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/ppe_detector/runs/detect/ppe_detector_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/face_detector/runs/detect/face_detector_model/weights/best.pt ./local/path/

scp user@server:/path/to/training/general_object_detector/runs/detect/general_object_detector_model/weights/best.pt ./local/path/
```

## Available Services

The project includes these analytical services:

1. **Person Tracker**: Tracks people movement across frames
2. **Checkout Counter Monitor**: Analyzes checkout counter usage and queues
3. **Heatmap Generator**: Creates density heatmaps from tracking data
4. **Shoplifting Detector**: Detects suspicious shoplifting behaviors
5. **Demographics Detector**: Analyzes age and gender distributions
6. **General Object Detector**: Detects and tracks various objects
7. **People Counter**: Counts people entering and exiting spaces
8. **Vehicle Detector**: Detects and tracks vehicles
9. **PPE Detector**: Detects the use of personal protective equipment
10. **Face Detector**: Detects and tracks faces

## Testing Services

You can test these services using the test modules in the `models_testing` directory:

```bash
python3 -m models_testing.test_person_tracker
python3 -m models_testing.test_checkout_monitoring
python3 -m models_testing.test_heatmap_generator
python3 -m models_testing.test_shoplifting_detector
python3 -m models_testing.test_demographics_detector
python3 -m models_testing.test_people_counter
python3 -m models_testing.test_vehicle_detector
python3 -m models_testing.test_ppe_detector
python3 -m models_testing.test_face_detector
python3 -m models_testing.test_general_object_detector
```

## Notes
- Training outputs will be saved in `runs/detect/checkout_model/`
- The best model will be at `runs/detect/checkout_model/weights/best.pt`
- Training parameters can be adjusted in the `train_checkout_model.py` script
- Models are stored in a central `training_models` directory
- Service outputs (heatmaps, videos, etc.) are stored in `models_testing/outputs`
- Shoplifting detector outputs are stored in `models_testing/outputs/shoplifting`
- Demographics detector outputs are stored in `models_testing/outputs/demographics`
- General object detector outputs are stored in `models_testing/outputs/general_object`
- Vehicle detector outputs are stored in `models_testing/outputs/vehicle`
- PPE detector outputs are stored in `models_testing/outputs/ppe`
- Face detector outputs are stored in `models_testing/outputs/face`

# 🔍 Running Test Modules with -m

When you're testing Python modules like `test_person_tracker.py` or `test_checkout_monitoring.py`, it's best to use the `-m` flag from the project root. This ensures proper module resolution (especially for relative imports like `from services.footpath.tracker import PersonTracker`).

## ✅ Why use -m?
Python's `-m` flag tells it to treat the target as a module inside a package, so relative imports work correctly. If you just run the file directly (e.g., `python3 models_testing/test_person_tracker.py`), you'll often get errors like:

```bash
ModuleNotFoundError: No module named 'services'
```

## ▶️ Usage

Make sure you're in the project root directory, then run the desired test module like this:

```bash
python3 -m models_testing.test_person_tracker
```
or
```bash
python3 -m models_testing.test_checkout_monitoring
```
or
```bash
python3 -m models_testing.test_heatmap_generator
```

or
```bash
python3 -m models_testing.test_shoplifting_detector
```

or
```bash
python3 -m models_testing.test_demographics_detector
```

or
```bash
python3 -m models_testing.test_people_counter
```

or
```bash
python3 -m models_testing.test_vehicle_detector
```

or
```bash
python3 -m models_testing.test_ppe_detector
```

or
```bash
python3 -m models_testing.test_face_detector
```

or
```bash
python3 -m models_testing.test_general_object_detector
```

From project root:
```bash
cd vt-camera-streamapi-backend
python3 -m models_testing.test_person_tracker
python3 -m models_testing.test_checkout_monitoring
python3 -m models_testing.test_heatmap_generator
python3 -m models_testing.test_shoplifting_detector
python3 -m models_testing.test_demographics_detector
python3 -m models_testing.test_people_counter
python3 -m models_testing.test_vehicle_detector
python3 -m models_testing.test_ppe_detector
python3 -m models_testing.test_face_detector
python3 -m models_testing.test_general_object_detector
```

That's it! 🚀


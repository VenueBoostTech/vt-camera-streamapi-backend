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
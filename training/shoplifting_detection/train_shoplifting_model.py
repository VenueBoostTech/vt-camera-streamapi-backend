from ultralytics import YOLO
import os
import yaml
import shutil

# Get absolute paths for project structure
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(current_dir))  # vt-camera-streamapi-backend root
models_dir = os.path.join(project_dir, 'training_models')
os.makedirs(models_dir, exist_ok=True)

# Path to your dataset.yaml file
dataset_path = os.path.join(current_dir, '../data/shoplifting.v1i.yolov11/data.yaml')
dataset_dir = os.path.dirname(os.path.abspath(dataset_path))

# Start with a pre-trained YOLOv8 model from central models directory
model_path = os.path.join(models_dir, 'yolov8x.pt')
model = YOLO(model_path)

# Check if dataset.yaml exists
if not os.path.exists(dataset_path):
    print(f"Error: Dataset file {dataset_path} not found!")
    print(f"Current directory: {current_dir}")
    print(f"Looking for: {dataset_path}")
    exit(1)

# Load and modify the dataset.yaml with correct paths
try:
    with open(dataset_path, 'r') as f:
        dataset_config = yaml.safe_load(f)
    
    # Update paths to be absolute
    dataset_config['train'] = os.path.join(dataset_dir, 'train/images')
    dataset_config['val'] = os.path.join(dataset_dir, 'valid/images')
    dataset_config['test'] = os.path.join(dataset_dir, 'test/images')
    
    # Verify paths exist
    for path_key in ['train', 'val', 'test']:
        path = dataset_config[path_key]
        if not os.path.exists(path):
            print(f"Warning: {path_key} path does not exist: {path}")
    
    # Save modified config
    modified_yaml_path = os.path.join(current_dir, 'modified_data.yaml')
    with open(modified_yaml_path, 'w') as f:
        yaml.dump(dataset_config, f)
    
    print(f"Created modified dataset config with absolute paths: {modified_yaml_path}")
    print(f"Dataset config: {dataset_config}")
except Exception as e:
    print(f"Error loading dataset config: {str(e)}")
    exit(1)

# Train the model with shoplifting-specific parameters
print("Starting shoplifting detection model training...")
results = model.train(
    data=modified_yaml_path,
    epochs=100,               # More epochs for complex behavior detection
    imgsz=640,                # Standard image size
    batch=8,                  # Adjust based on your GPU memory
    patience=20,              # More patience for convergence
    name='shoplifting_model', # Model name
    project=os.path.join(project_dir, 'runs/detect'),  # Set explicit output path
    pretrained=True,          # Use pretrained weights
    optimizer='Adam',         # Adam optimizer often works well for behavior detection
    lr0=0.001,                # Lower learning rate for fine-tuning
    cos_lr=True,              # Cosine learning rate schedule
    augment=True,             # Data augmentation
    mixup=0.1,                # Mixup augmentation
    flipud=0.1,               # Vertical flip augmentation
    mosaic=1.0,               # Mosaic augmentation
    degrees=10.0,             # Rotation augmentation
    translate=0.1,            # Translation augmentation
    scale=0.5,                # Scale augmentation
    shear=2.0,                # Shear augmentation
    perspective=0.0,          # Perspective augmentation
    copy_paste=0.0,           # Copy-paste augmentation
    rect=False,               # Rectangular training
    multi_scale=True         # Multi-scale training
)

# Save the trained model to the central models directory too
best_model_path = os.path.join(project_dir, 'runs/detect/shoplifting_model/weights/best.pt')
if os.path.exists(best_model_path):
    shoplifting_model_path = os.path.join(models_dir, 'shoplifting_detector.pt')
    shutil.copy(best_model_path, shoplifting_model_path)
    print(f"Model also saved to central models directory: {shoplifting_model_path}")

print(f"Training completed. Model saved to {os.path.join(project_dir, 'runs/detect/shoplifting_model')}")
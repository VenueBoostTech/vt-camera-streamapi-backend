from ultralytics import YOLO
import os
import yaml

# Get absolute paths for project structure
current_dir = os.path.dirname(os.path.abspath(__file__))  # checkout_counter directory
project_dir = os.path.dirname(os.path.dirname(current_dir))  # vt-camera-streamapi-backend root
models_dir = os.path.join(project_dir, 'training_models')
os.makedirs(models_dir, exist_ok=True)

# Path to your dataset.yaml file
dataset_path = os.path.join(current_dir, '../data/checkout counter.v1i.yolov8/data.yaml')
dataset_dir = os.path.dirname(os.path.abspath(dataset_path))

# Start with a pre-trained YOLOv8 model from central models directory
model_path = os.path.join(models_dir, 'yolov8s.pt')
model = YOLO(model_path)  # Use yolov8n.pt for even faster training

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

# Train the model
print("Starting model training...")
results = model.train(
    data=modified_yaml_path,
    epochs=50,
    imgsz=640,
    batch=8,
    patience=10,
    name='checkout_model',
    project=os.path.join(project_dir, 'runs/detect')  # Set explicit output path
)

# Save the trained model to the central models directory too
best_model_path = os.path.join(project_dir, 'runs/detect/checkout_model/weights/best.pt')
if os.path.exists(best_model_path):
    import shutil
    checkout_model_path = os.path.join(models_dir, 'checkout_counter.pt')
    shutil.copy(best_model_path, checkout_model_path)
    print(f"Model also saved to central models directory: {checkout_model_path}")

print(f"Training completed. Model saved to {os.path.join(project_dir, 'runs/detect/checkout_model')}")
from ultralytics import YOLO
import os
import yaml
import shutil

# Setup directories
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(current_dir))  # Root of vt-camera-streamapi-backend
models_dir = os.path.join(project_dir, 'training_models')
os.makedirs(models_dir, exist_ok=True)

# Path to dataset.yaml
dataset_path = os.path.join(current_dir, '../data/People Detection -General-.v8i.yolov11/data.yaml')
dataset_dir = os.path.dirname(os.path.abspath(dataset_path))

# Load pre-trained YOLOv8 model
model_path = os.path.join(models_dir, 'yolov8n.pt')  # You can use yolov8s.pt if needed
model = YOLO(model_path)

# Validate dataset.yaml
if not os.path.exists(dataset_path):
    print(f"Error: Dataset file {dataset_path} not found!")
    print(f"Current directory: {current_dir}")
    print(f"Looking for: {dataset_path}")
    exit(1)

# Load and patch dataset config
try:
    with open(dataset_path, 'r') as f:
        dataset_config = yaml.safe_load(f)

    dataset_config['train'] = os.path.join(dataset_dir, 'train/images')
    dataset_config['val'] = os.path.join(dataset_dir, 'valid/images')
    dataset_config['test'] = os.path.join(dataset_dir, 'test/images')

    # Validate paths
    for path_key in ['train', 'val', 'test']:
        path = dataset_config[path_key]
        if not os.path.exists(path):
            print(f"Warning: {path_key} path does not exist: {path}")

    # Save modified YAML
    modified_yaml_path = os.path.join(current_dir, 'modified_people_data.yaml')
    with open(modified_yaml_path, 'w') as f:
        yaml.dump(dataset_config, f)

    print(f"✅ Modified dataset.yaml saved to: {modified_yaml_path}")
    print(f"Dataset config: {dataset_config}")

except Exception as e:
    print(f"Error loading dataset config: {str(e)}")
    exit(1)

# Train the model
print("🚀 Starting people counting model training...")
results = model.train(
    data=modified_yaml_path,
    epochs=60,
    imgsz=640,
    batch=8,
    patience=10,
    name='people_counter_model',
    project=os.path.join(project_dir, 'runs/detect'),
    pretrained=True,
    optimizer='Adam',
    lr0=0.001,
    cos_lr=True,
    augment=True,
    mixup=0.1,
    flipud=0.1,
    mosaic=1.0,
    degrees=5.0,
    translate=0.05,
    scale=0.4,
    shear=1.5,
    perspective=0.0,
    copy_paste=0.0,
    rect=False,
    multi_scale=True
)

# Save model to central location
best_model_path = os.path.join(project_dir, 'runs/detect/people_counter_model/weights/best.pt')
if os.path.exists(best_model_path):
    final_model_path = os.path.join(models_dir, 'people_counter.pt')
    shutil.copy(best_model_path, final_model_path)
    print(f"✅ Final model copied to: {final_model_path}")

print(f"🎉 Training complete! Model saved at: {os.path.join(project_dir, 'runs/detect/people_counter_model')}")

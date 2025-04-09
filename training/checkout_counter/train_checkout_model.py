# from ultralytics import YOLO
# import os
# import yaml

# # Path to your dataset.yaml file (from the downloaded Roboflow dataset)
# dataset_path = '../data/checkout counter.v1i.yolov8/data.yaml'

# # Start with a pre-trained YOLOv8 model (smaller for faster training)
# model = YOLO('yolov8s.pt')  # Use yolov8n.pt for even faster training

# # Check if dataset.yaml exists
# if not os.path.exists(dataset_path):
#     print(f"Error: Dataset file {dataset_path} not found!")
#     exit(1)

# # Load the dataset.yaml to ensure it's properly formatted
# try:
#     with open(dataset_path, 'r') as f:
#         dataset_config = yaml.safe_load(f)
#     print(f"Dataset config: {dataset_config}")
# except Exception as e:
#     print(f"Error loading dataset config: {str(e)}")
#     exit(1)

# # Train the model
# print("Starting model training...")
# results = model.train(
#     data=dataset_path,
#     epochs=50,           # Adjust based on your needs
#     imgsz=640,           # Image size
#     batch=8,             # Reduce if you have memory issues
#     patience=10,         # Early stopping patience
#     name='checkout_model'
# )

# # Display training results
# print(f"Training completed. Model saved to {os.path.join('runs', 'detect', 'checkout_model')}")


from ultralytics import YOLO
import os
import yaml

# Path to your dataset.yaml file
dataset_path = '../data/checkout counter.v1i.yolov8/data.yaml'
dataset_dir = os.path.dirname(os.path.abspath(dataset_path))

# Start with a pre-trained YOLOv8 model (smaller for faster training)
model = YOLO('yolov8s.pt')  # Use yolov8n.pt for even faster training

# Check if dataset.yaml exists
if not os.path.exists(dataset_path):
    print(f"Error: Dataset file {dataset_path} not found!")
    exit(1)

# Load and modify the dataset.yaml with correct paths
try:
    with open(dataset_path, 'r') as f:
        dataset_config = yaml.safe_load(f)
    
    # Update paths to be absolute
    dataset_config['train'] = os.path.join(dataset_dir, 'train/images')
    dataset_config['val'] = os.path.join(dataset_dir, 'valid/images')
    dataset_config['test'] = os.path.join(dataset_dir, 'test/images')
    
    # Save modified config
    modified_yaml_path = 'modified_data.yaml'
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
    name='checkout_model'
)

print(f"Training completed. Model saved to {os.path.join('runs', 'detect', 'checkout_model')}")
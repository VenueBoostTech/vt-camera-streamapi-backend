from ultralytics import YOLO
import os
import yaml
import shutil
import argparse
import torch
from pathlib import Path

def parse_arguments():
    """Parse command line arguments for vehicle detection model training"""
    parser = argparse.ArgumentParser(description='Train vehicle detection model')
    parser.add_argument('--data_path', type=str, 
                        default='training/data/vehicle-detection-.v2i.yolov11/data.yaml',
                        help='Path to dataset YAML file')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size for training')
    parser.add_argument('--img_size', type=int, default=640,
                        help='Image size for training')
    parser.add_argument('--model_size', type=str, default='m',
                        choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLOv8 model size (n, s, m, l, x)')
    parser.add_argument('--patience', type=int, default=20,
                        help='Early stopping patience')
    parser.add_argument('--device', type=str, default='',
                        help='Device to use (cuda, cpu, or leave empty for auto)')
    return parser.parse_args()

def setup_paths(data_path):
    """Setup and validate all necessary paths for training"""
    # Get absolute paths for project structure
    current_dir = os.path.dirname(os.path.abspath(__file__))  # vehicle_detection directory
    project_dir = os.path.dirname(os.path.dirname(current_dir))  # vt-camera-streamapi-backend root
    models_dir = os.path.join(project_dir, 'training_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Resolve dataset path
    if not os.path.isabs(data_path):
        data_path = os.path.join(project_dir, data_path)
    
    dataset_dir = os.path.dirname(os.path.abspath(data_path))
    
    # Create output directories
    run_dir = os.path.join(project_dir, 'runs/detect')
    os.makedirs(run_dir, exist_ok=True)
    
    return {
        'project_dir': project_dir,
        'models_dir': models_dir,
        'dataset_path': data_path,
        'dataset_dir': dataset_dir,
        'run_dir': run_dir
    }

def prepare_dataset(paths):
    """Prepare and validate the dataset configuration"""
    dataset_path = paths['dataset_path']
    dataset_dir = paths['dataset_dir']
    
    # Check if dataset.yaml exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file {dataset_path} not found!")
        print(f"Looking for: {dataset_path}")
        return None
    
    # Load and modify the dataset.yaml with correct paths
    try:
        with open(dataset_path, 'r') as f:
            dataset_config = yaml.safe_load(f)
        
        # Update paths to be absolute
        dataset_config['train'] = os.path.join(dataset_dir, 'train/images')
        dataset_config['val'] = os.path.join(dataset_dir, 'valid/images')
        dataset_config['test'] = os.path.join(dataset_dir, 'test/images')
        
        # Standardize class names if needed (some Roboflow exports have unusual naming)
        if 'names' in dataset_config:
            # Check if there are unusual class names and replace them with standard names
            standard_classes = ['car', 'truck', 'motorcycle', 'bus', 'bicycle']
            if any("Object Detection" in name for name in dataset_config['names']):
                print("Standardizing class names for vehicle detection...")
                # Replace with standard vehicle class names (adjust based on actual content)
                dataset_config['names'] = standard_classes[:len(dataset_config['names'])]
                print(f"Updated class names: {dataset_config['names']}")
        
        # Verify paths exist
        for path_key in ['train', 'val', 'test']:
            path = dataset_config[path_key]
            if not os.path.exists(path):
                print(f"Warning: {path_key} path does not exist: {path}")
        
        # Save modified config
        modified_yaml_path = os.path.join(os.path.dirname(dataset_path), 'modified_data.yaml')
        with open(modified_yaml_path, 'w') as f:
            yaml.dump(dataset_config, f)
        
        print(f"Created modified dataset config with absolute paths: {modified_yaml_path}")
        print(f"Dataset config: {dataset_config}")
        
        return modified_yaml_path
    except Exception as e:
        print(f"Error loading dataset config: {str(e)}")
        return None

def load_model(paths, model_size, device):
    """Download YOLOv8 model if not in training_models and use it from there."""
    model_name = f'yolov8{model_size}.pt'
    model_path = os.path.join(paths['models_dir'], model_name)

    # Set device if specified
    if device:
        os.environ['CUDA_VISIBLE_DEVICES'] = device if device != 'cpu' else ''

    if os.path.exists(model_path):
        print(f"Loading model from: {model_path}")
        return YOLO(model_path)

    # Step 1: Download to current dir using YOLO(model_name)
    print(f"Downloading YOLOv8 model: {model_name}")
    temp_model = YOLO(model_name)

    # Step 2: Move downloaded model to training_models/
    downloaded_model_path = os.path.join(os.getcwd(), model_name)
    if os.path.exists(downloaded_model_path):
        os.rename(downloaded_model_path, model_path)
        print(f"Moved model to: {model_path}")
    else:
        print(f"Warning: Expected model not found at {downloaded_model_path}")

    # Step 3: Load from final path
    return YOLO(model_path)

def train_model(model, dataset_path, args, paths):
    """Train the vehicle detection model"""
    print("Starting vehicle detection model training...")
    
    # Configure training parameters - optimized for vehicle detection
    results = model.train(
        data=dataset_path,
        epochs=args.epochs,
        imgsz=args.img_size,
        batch=args.batch_size,
        patience=args.patience,
        name='vehicle_detection_model',
        project=paths['run_dir'],
        pretrained=True,
        optimizer='Adam',
        lr0=0.001,
        lrf=0.01,  # Final learning rate factor
        cos_lr=True,
        augment=True,
        mixup=0.1,  # Some mixup for vehicle detection
        flipud=0.0,  # No vertical flips for vehicles (usually upright)
        fliplr=0.5,  # Horizontal flips are okay
        mosaic=1.0,  # Full mosaic augmentation
        degrees=5.0,  # Limited rotation (vehicles usually have standard orientations)
        translate=0.2,  # More translation augmentation
        scale=0.5,   # More scale variation for vehicles of different sizes
        shear=2.0,   # Some shear augmentation
        perspective=0.0,  # Limited perspective change
        hsv_h=0.015,     # Slight hue variation
        hsv_s=0.5,       # Saturation variation
        hsv_v=0.4,       # Value variation
        multi_scale=True,
        rect=False,       # No rectangular training
        resume=False
    )
    
    return results

def save_model(paths):
    """Save the trained model to the central models directory"""
    best_model_path = os.path.join(paths['run_dir'], 'vehicle_detection_model/weights/best.pt')
    
    if os.path.exists(best_model_path):
        vehicle_detection_model_path = os.path.join(paths['models_dir'], 'vehicle_detector.pt')
        shutil.copy(best_model_path, vehicle_detection_model_path)
        print(f"Model saved to central models directory: {vehicle_detection_model_path}")
        return vehicle_detection_model_path
    else:
        print(f"Warning: Best model not found at {best_model_path}")
        return None

def validate_model(model_path):
    """Validate the trained model on test data"""
    if model_path and os.path.exists(model_path):
        print(f"Validating trained model: {model_path}")
        model = YOLO(model_path)
        
        # Run validation
        results = model.val()
        
        print("Validation results:")
        print(f"mAP50-95: {results.box.map}")
        print(f"mAP50: {results.box.map50}")
        print(f"Precision: {results.box.p}")
        print(f"Recall: {results.box.r}")
        
        # Class-wise performance
        print("\nClass-wise performance:")
        for i, ap in enumerate(results.box.ap_class_index):
            class_name = results.names[i]
            class_ap50 = results.box.ap50[i]
            class_ap = results.box.ap[i]
            print(f"{class_name}: mAP50={class_ap50:.4f}, mAP50-95={class_ap:.4f}")
        
        return results
    else:
        print("No model available for validation")
        return None

def main():
    """Main function to train vehicle detection model"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup paths
    paths = setup_paths(args.data_path)
    
    # Prepare dataset
    dataset_path = prepare_dataset(paths)
    if dataset_path is None:
        print("Dataset preparation failed. Exiting.")
        return
    
    # Load model
    model = load_model(paths, args.model_size, args.device)
    
    # Train model
    results = train_model(model, dataset_path, args, paths)
    
    # Save model
    model_path = save_model(paths)
    
    # Validate model
    validate_model(model_path)
    
    print(f"Training completed. Model saved to {os.path.join(paths['run_dir'], 'vehicle_detection_model')}")

if __name__ == "__main__":
    main()
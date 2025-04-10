import cv2
import numpy as np
import json
import os
import sys

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate up one level to the project root
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Import the service
from services.general_object_detector import GeneralObjectDetector

def test_general_object_detector(video_path, output_path=None, target_classes=None):
    """Test the general object detector with a video file"""
    # Construct the correct absolute path to the video
    if not os.path.isabs(video_path):
        video_path = os.path.join(project_root, "training_assets", "videos", video_path)
    
    if output_path and not os.path.isabs(output_path):
        output_dir = os.path.join(project_root, "models_testing", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_path)
    
    # Initialize the detector
    detector = GeneralObjectDetector(confidence_threshold=0.4)
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer if output path is specified
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    skip_frames = 2  # Process every nth frame
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for efficiency
        if frame_count % skip_frames != 0:
            frame_count += 1
            continue
        
        # Process frame for object detection
        detections = detector.detect(frame, classes=target_classes)
        
        # Annotate frame
        annotated_frame = detector.annotate_frame(frame, detections)
        
        # Add frame counter
        cv2.putText(annotated_frame, f"Frame: {frame_count}", (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
        cv2.putText(annotated_frame, f"Frame: {frame_count}", (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display the frame
        cv2.imshow('General Object Detection', annotated_frame)
        
        # Write to output if specified
        if writer:
            writer.write(annotated_frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
        
        # Print progress every 30 frames
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames")
            stats = detector.get_statistics()
            print(f"Detected objects: {json.dumps(stats['currently_visible'], indent=2)}")
    
    # Release resources
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    # Save final data
    if output_path:
        data_path = output_path.replace('.mp4', '_detections.json')
        detector.save_analytics(data_path)
        print(f"Detection data saved to {data_path}")
    
    return detector

if __name__ == "__main__":
    # Test with video and optionally filter for specific classes
    video_path = "general_test.mp4"  # Update with your test video
    output_path = "object_detection_output.mp4"
    target_classes = None  # Set to specific class indices to filter, e.g. [0, 2, 3] for person, car, motorcycle
    test_general_object_detector(video_path, output_path, target_classes)
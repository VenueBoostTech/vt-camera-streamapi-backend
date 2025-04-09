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

# Now import the PersonTracker
from services.footpath.tracker import PersonTracker

# Define zones for a test store layout
zones = {
    'entrance': [(100, 400), (200, 400), (200, 500), (100, 500)],
    'checkout': [(600, 100), (700, 100), (700, 180), (600, 180)],
    'clothing': [(150, 200), (350, 200), (350, 350), (150, 350)]
}

def test_with_video(video_path, output_path=None):
    # Get project root directory for consistent paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # Corrected: go up one level

    print(f"Project root: {project_root}")

    # Construct the correct absolute path to the video
    video_path = os.path.join(project_root, "training_assets", "videos", "person_tracker.mp4")


    if output_path and not os.path.isabs(output_path):
        output_path = os.path.join(project_root, output_path)
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Initialize the tracker with test zones
    tracker = PersonTracker(confidence_threshold=0.4, zones=zones)
    
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
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame
        detections = tracker.update(frame)
        
        # Annotate frame
        annotated_frame = tracker.annotate_frame(frame, detections)
        
        # Display info
        stats = tracker.get_statistics()
        info_text = f"Frame: {frame_count} | Detections: {stats['total_detections']} | Tracks: {stats['total_tracks']}"
        cv2.putText(annotated_frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display the frame
        cv2.imshow('Tracking', annotated_frame)
        
        # Write to output if specified
        if writer:
            writer.write(annotated_frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
        
        # Print progress every 10 frames
        if frame_count % 10 == 0:
            print(f"Processed {frame_count} frames")
            print(f"Current statistics: {json.dumps(stats, indent=2)}")
    
    # Release resources
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    # Export final data
    tracking_data = tracker.export_tracking_data(format='json')
    print("\nFinal statistics:")
    print(json.dumps(stats, indent=2))
    
    # Save tracking data to file
    if output_path:
        data_path = output_path.replace('.mp4', '_data.json')
        with open(data_path, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        print(f"Tracking data saved to {data_path}")

if __name__ == "__main__":
    # Test with a video file - replace with your test video path
    video_path = "person_tracker.mp4"
    output_path = "person_tracker_output.mp4"
    test_with_video(video_path, output_path)
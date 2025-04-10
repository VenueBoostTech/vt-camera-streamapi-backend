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

# Import the services
from services.footpath.tracker import PersonTracker
from services.heatmap_generator import HeatmapGenerator

def test_heatmap_generator(video_path, output_path=None):
    """Test the heatmap generator with a video file"""
    # Construct the correct absolute path to the video
    if not os.path.isabs(video_path):
        video_path = os.path.join(project_root, "training_assets", "videos", video_path)
    
    if output_path and not os.path.isabs(output_path):
        output_dir = os.path.join(project_root, "models_testing", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_path)
    
    # Initialize the tracker and heatmap generator
    tracker = PersonTracker(confidence_threshold=0.4)
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Initialize heatmap generator with correct resolution
    heatmap_generator = HeatmapGenerator(frame_resolution=(height, width), 
                                        decay_factor=0.95, 
                                        blur_size=15)
    
    # Setup video writer if output path is specified
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    skip_frames = 1  # Process every nth frame
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for efficiency
        if frame_count % skip_frames != 0:
            frame_count += 1
            continue
        
        # Process frame for person detection and tracking
        detections = tracker.update(frame)
        
        # Get tracks
        tracks = tracker.get_active_tracks()
        
        # Update heatmap
        heatmap_generator.update(detections=detections, tracks=tracks)
        
        # Get heatmap overlay
        heatmap_overlay = heatmap_generator.overlay_heatmap(frame, alpha=0.5)
        
        # Add frame information
        info_text = f"Frame: {frame_count} | Persons: {len(detections.xyxy) if hasattr(detections, 'xyxy') else 0}"
        cv2.putText(heatmap_overlay, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add hotspot information
        hotspots = heatmap_generator.get_hotspots()
        hotspot_text = f"Hotspots: {len(hotspots)}"
        cv2.putText(heatmap_overlay, hotspot_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw hotspots
        for i, hotspot in enumerate(hotspots):
            x1, y1, x2, y2 = hotspot['bbox']
            intensity = hotspot['normalized_intensity']
            color = (0, int(255 * (1-intensity)), int(255 * intensity))
            cv2.rectangle(heatmap_overlay, (x1, y1), (x2, y2), color, 2)
            cv2.putText(heatmap_overlay, f"H{i+1}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Display the frame
        cv2.imshow('Heatmap', heatmap_overlay)
        
        # Write to output if specified
        if writer:
            writer.write(heatmap_overlay)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
        
        # Print progress every 30 frames
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames")
            hotspots = heatmap_generator.get_hotspots()
            print(f"Found {len(hotspots)} hotspots")
    
    # Release resources
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    # Save final heatmap
    if output_path:
        heatmap_image_path = output_path.replace('.mp4', '_heatmap.jpg')
        heatmap_generator.save(heatmap_image_path)
        print(f"Heatmap saved to {heatmap_image_path}")
        
        # Save heatmap data
        heatmap_data_path = output_path.replace('.mp4', '_heatmap_data.json')
        heatmap_generator.save_export_data(heatmap_data_path)
        print(f"Heatmap data saved to {heatmap_data_path}")
    
    return heatmap_generator

if __name__ == "__main__":
    # Test with video
    video_path = "person_tracker.mp4"
    output_path = "heatmap_output.mp4"
    test_heatmap_generator(video_path, output_path)
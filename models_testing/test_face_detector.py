import sys
import os
import cv2
import numpy as np
import json
import argparse
from datetime import datetime

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate up one level to the project root
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Import the face detector
from services.face_detector import FaceDetector

def test_face_detector(video_path, model_path=None, output_path=None, confidence=0.4, blur_faces=True):
    """Test the face detector with a video file"""
    # Construct the correct absolute path to the video
    if not os.path.isabs(video_path):
        video_path = os.path.join(project_root, "training_assets", "videos", video_path)
    
    if output_path and not os.path.isabs(output_path):
        output_dir = os.path.join(project_root, "models_testing", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_path)
    
    # Initialize the face detector
    detector = FaceDetector(model_path=model_path, confidence_threshold=confidence, blur_faces=blur_faces)
    
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
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for efficiency
            if frame_count % skip_frames != 0:
                frame_count += 1
                continue
            
            # Process frame for face detection
            detections = detector.detect(frame)
            
            # Annotate frame
            annotated_frame = detector.annotate_frame(frame, detections)
            
            # Add info text
            stats = detector.get_statistics()
            info_text = f"Frame: {frame_count} | Visible Faces: {len(detector.tracked_faces)} | Total Unique: {stats['historical_stats']['total_unique_faces']}"
            cv2.putText(annotated_frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show privacy status
            privacy_status = "ON" if detector.privacy_mode else "OFF"
            blur_status = "ON" if detector.blur_faces else "OFF"
            cv2.putText(annotated_frame, f"Privacy: {privacy_status} | Blur: {blur_status}", 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Face Detection', annotated_frame)
            
            # Write to output if specified
            if writer:
                writer.write(annotated_frame)
            
            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit
                break
            elif key == ord('b'):  # Toggle blur
                detector.blur_faces = not detector.blur_faces
                print(f"Face blur: {'ON' if detector.blur_faces else 'OFF'}")
            elif key == ord('p'):  # Toggle privacy mode
                detector.set_privacy_mode(not detector.privacy_mode)
                print(f"Privacy mode: {'ON' if detector.privacy_mode else 'OFF'}")
            
            frame_count += 1
            
            # Print progress every 50 frames
            if frame_count % 50 == 0:
                print(f"Processed {frame_count} frames")
                current_stats = stats["current_stats"]
                print(f"Current tracked faces: {current_stats['active_faces']}")
                print(f"Average face size: {current_stats['avg_face_size']:.2f} pixels")
                print(f"Average time in frame: {current_stats['avg_time_in_frame']:.2f} frames")
                print("-" * 50)
    
    except KeyboardInterrupt:
        print("Processing interrupted by user")
    
    finally:
        # Release resources
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        # Save final data
        if output_path:
            data_path = output_path.replace('.mp4', '_face_detection.json')
            detector.save_analytics(data_path)
            print(f"Face detection data saved to {data_path}")
        
        # Print final statistics
        final_stats = detector.get_statistics()
        print("\nFinal face detection statistics:")
        print(json.dumps(final_stats, indent=2))
        
        return detector

def parse_args():
    parser = argparse.ArgumentParser(description="Test face detector on video")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--model", type=str, default=None, help="Path to face detection model")
    parser.add_argument("--output", type=str, default=None, help="Path to output video file")
    parser.add_argument("--confidence", type=float, default=0.4, help="Detection confidence threshold")
    parser.add_argument("--blur", action="store_true", help="Blur detected faces for privacy")
    parser.add_argument("--no-blur", dest="blur", action="store_false", help="Don't blur faces")
    parser.set_defaults(blur=True)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    test_face_detector(
        video_path=args.video,
        model_path=args.model,
        output_path=args.output,
        confidence=args.confidence,
        blur_faces=args.blur
    )
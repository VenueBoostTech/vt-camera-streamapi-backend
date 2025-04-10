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

# Import the PPE detector
from services.ppe_detector import PPEDetector

def test_ppe_detector(video_path, model_path=None, output_path=None, confidence=0.4, rule='default'):
    """Test the PPE detector with a video file"""
    # Construct the correct absolute path to the video
    if not os.path.isabs(video_path):
        video_path = os.path.join(project_root, "training_assets", "videos", video_path)
    
    if output_path and not os.path.isabs(output_path):
        output_dir = os.path.join(project_root, "models_testing", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_path)
    
    # Initialize the PPE detector
    detector = PPEDetector(model_path=model_path, confidence_threshold=confidence)
    
    # Set compliance rule
    if rule in detector.compliance_rules:
        detector.set_compliance_rule(rule)
        print(f"Using compliance rule: '{rule}' - Required PPE: {detector.compliance_rules[rule]}")
    else:
        print(f"Warning: Rule '{rule}' not found. Using default rule.")
        print(f"Available rules: {list(detector.compliance_rules.keys())}")
    
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
            
            # Process frame for PPE detection
            detections = detector.detect(frame)
            
            # Annotate frame
            annotated_frame = detector.annotate_frame(frame, detections)
            
            # Add info text
            stats = detector.get_statistics()
            info_text = f"Frame: {frame_count} | Rule: {detector.active_rule} | Compliance: {stats['compliance_rate']:.1f}%"
            cv2.putText(annotated_frame, info_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('PPE Detection', annotated_frame)
            
            # Write to output if specified
            if writer:
                writer.write(annotated_frame)
            
            # Key controls
            key = cv2.waitKey(1) & 0xFF
            
            # Change compliance rules with keys 1-4
            if key == ord('1'):
                detector.set_compliance_rule('default')
                print(f"Rule set to 'default': {detector.compliance_rules['default']}")
            elif key == ord('2'):
                detector.set_compliance_rule('construction')
                print(f"Rule set to 'construction': {detector.compliance_rules['construction']}")
            elif key == ord('3'):
                detector.set_compliance_rule('laboratory')
                print(f"Rule set to 'laboratory': {detector.compliance_rules['laboratory']}")
            elif key == ord('4'):
                detector.set_compliance_rule('factory')
                print(f"Rule set to 'factory': {detector.compliance_rules['factory']}")
            elif key == ord('q'):
                break
            
            frame_count += 1
            
            # Print progress every 50 frames
            if frame_count % 50 == 0:
                print(f"Processed {frame_count} frames")
                print(f"Current statistics:")
                print(f"  - Tracked persons: {stats['current_stats']['active_persons']}")
                print(f"  - Compliance rate: {stats['compliance_rate']:.1f}%")
                
                # Print missing PPE stats
                print("  - Missing PPE:")
                for ppe_type, data in stats['current_stats']['missing_ppe'].items():
                    print(f"    - {ppe_type}: {data['count']} persons ({data['percentage']:.1f}%)")
                
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
            data_path = output_path.replace('.mp4', '_ppe_detection.json')
            detector.save_analytics(data_path)
            print(f"PPE detection data saved to {data_path}")
        
        # Print final statistics
        final_stats = detector.get_statistics()
        print("\nFinal PPE detection statistics:")
        print(f"Rule: {detector.active_rule} - Required PPE: {detector.compliance_rules[detector.active_rule]}")
        print(f"Compliance rate: {final_stats['compliance_rate']:.1f}%")
        print(f"Total persons tracked: {final_stats['historical_stats']['total_persons']}")
        print(f"Compliant persons: {final_stats['historical_stats']['compliant_persons']} ({final_stats['historical_stats']['compliant_persons'] / final_stats['historical_stats']['total_persons'] * 100 if final_stats['historical_stats']['total_persons'] > 0 else 0:.1f}%)")
        print(f"Non-compliant persons: {final_stats['historical_stats']['non_compliant_persons']} ({final_stats['historical_stats']['non_compliant_persons'] / final_stats['historical_stats']['total_persons'] * 100 if final_stats['historical_stats']['total_persons'] > 0 else 0:.1f}%)")
        
        return detector

def parse_args():
    parser = argparse.ArgumentParser(description="Test PPE detector on video")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--model", type=str, default=None, help="Path to PPE detection model")
    parser.add_argument("--output", type=str, default=None, help="Path to output video file")
    parser.add_argument("--confidence", type=float, default=0.4, help="Detection confidence threshold")
    parser.add_argument("--rule", type=str, default="default", 
                        choices=["default", "construction", "laboratory", "factory"],
                        help="Compliance rule to use")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    test_ppe_detector(
        video_path=args.video,
        model_path=args.model,
        output_path=args.output,
        confidence=args.confidence,
        rule=args.rule
    )
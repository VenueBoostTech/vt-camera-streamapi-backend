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

# Import the vehicle detector
from services.vehicle_detector import VehicleDetector

def test_vehicle_detector(video_path, model_path=None, output_path=None, confidence=0.4):
    """Test the vehicle detector with a video file"""
    # Construct the correct absolute path to the video
    if not os.path.isabs(video_path):
        video_path = os.path.join(project_root, "training_assets", "videos", video_path)
    
    if output_path and not os.path.isabs(output_path):
        output_dir = os.path.join(project_root, "models_testing", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_path)
    
    # Initialize the vehicle detector
    detector = VehicleDetector(model_path=model_path, confidence_threshold=confidence)
    
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
    
    # Add a default parking area (adjust according to your video)
    default_area_id = detector.add_parking_area(
        int(width * 0.1),   # x1
        int(height * 0.6),  # y1
        int(width * 0.9),   # x2
        int(height * 0.9),  # y2
        "Parking Area"
    )
    
    # Add a default counting line
    default_line_id = detector.add_counting_line(
        0, int(height * 0.5),  # x1, y1
        width, int(height * 0.5),  # x2, y2
        "Horizontal Line"
    )
    
    # Estimate parking capacity after some frames
    capacity_estimated = False
    
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
            
            # Process frame for vehicle detection
            detections = detector.detect(frame)
            
            # Estimate parking capacity after some frames
            if frame_count == 30 and not capacity_estimated:
                detector.estimate_parking_capacity()
                capacity_estimated = True
            
            # Annotate frame
            annotated_frame = detector.annotate_frame(frame, detections)
            
            # Add info text
            stats = detector.get_statistics()
            info_text = f"Frame: {frame_count} | Vehicles: {len(detector.tracked_vehicles)}"
            
            cv2.putText(annotated_frame, info_text, (10, height - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Vehicle Detection', annotated_frame)
            
            # Write to output if specified
            if writer:
                writer.write(annotated_frame)
            
            # Key controls
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('p'):
                # Add parking area with mouse selection
                print("Select parking area by clicking and dragging...")
                roi = cv2.selectROI("Select Parking Area", frame, False, False)
                if roi[2] > 0 and roi[3] > 0:  # If valid selection
                    area_id = detector.add_parking_area(roi[0], roi[1], roi[0] + roi[2], roi[1] + roi[3])
                    print(f"Added parking area {area_id}")
                    
                    # Estimate capacity based on current vehicles
                    detector.estimate_parking_capacity()
                cv2.destroyWindow("Select Parking Area")
            
            elif key == ord('l'):
                # Add counting line with mouse selection
                print("Select counting line by clicking two points...")
                points = []
                
                def line_selection(event, x, y, flags, param):
                    if event == cv2.EVENT_LBUTTONDOWN:
                        points.append([x, y])
                        # Draw point on the image
                        cv2.circle(param, (x, y), 5, (0, 255, 0), -1)
                        cv2.imshow("Select Counting Line", param)
                        
                        if len(points) == 2:
                            # Draw line
                            cv2.line(param, (points[0][0], points[0][1]), (points[1][0], points[1][1]), (0, 255, 0), 2)
                            cv2.imshow("Select Counting Line", param)
                
                line_frame = frame.copy()
                cv2.imshow("Select Counting Line", line_frame)
                cv2.setMouseCallback("Select Counting Line", line_selection, line_frame)
                
                # Wait for selection to complete
                while len(points) < 2:
                    if cv2.waitKey(100) & 0xFF == 27:  # ESC to cancel
                        break
                
                cv2.destroyWindow("Select Counting Line")
                
                if len(points) == 2:
                    line_id = detector.add_counting_line(points[0][0], points[0][1], points[1][0], points[1][1])
                    print(f"Added counting line {line_id}")
            
            elif key == ord('q'):
                break
            
            frame_count += 1
            
            # Print progress every 50 frames
            if frame_count % 50 == 0:
                print(f"Processed {frame_count} frames")
                current_stats = stats["current_stats"]
                print(f"Current vehicles: {current_stats['active_vehicles']}")
                
                # Print vehicle type distribution
                print("Vehicle types:")
                for vehicle_type, count in current_stats['vehicle_counts'].items():
                    print(f"  - {vehicle_type}: {count}")
                
                # Print parking occupancy
                if detector.parking_areas:
                    print("Parking areas:")
                    for area in detector.parking_areas:
                        print(f"  - {area['name']}: {area['occupied']}/{area['capacity']}")
                
                # Print line counts
                if detector.counting_lines:
                    print("Counting lines:")
                    for line in detector.counting_lines:
                        print(f"  - {line['name']}: {line['total']} vehicles")
                
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
            data_path = output_path.replace('.mp4', '_vehicle_detection.json')
            detector.save_analytics(data_path)
            print(f"Vehicle detection data saved to {data_path}")
        
        # Print final statistics
        final_stats = detector.get_statistics()
        print("\nFinal vehicle detection statistics:")
        print(f"Total vehicles tracked: {final_stats['historical_stats']['total_vehicles']}")
        
        # Print vehicle type distribution
        print("\nVehicle type distribution:")
        for vehicle_type, percentage in final_stats['current_stats']['vehicle_distribution'].items():
            count = final_stats['current_stats']['vehicle_counts'].get(vehicle_type, 0)
            print(f"  - {vehicle_type}: {count} vehicles ({percentage:.1f}%)")
        
        # Print parking statistics
        if detector.parking_areas:
            print("\nParking areas:")
            for area in detector.parking_areas:
                occupancy = (area['occupied'] / area['capacity']) * 100 if area['capacity'] > 0 else 0
                print(f"  - {area['name']}: {area['occupied']}/{area['capacity']} ({occupancy:.1f}% full)")
        
        # Print line count statistics
        if detector.counting_lines:
            print("\nCounting lines:")
            for line in detector.counting_lines:
                print(f"  - {line['name']}: {line['total']} total vehicles")
                for vehicle_type, count in line['counts'].items():
                    print(f"    - {vehicle_type}: {count} vehicles")
        
        return detector

def parse_args():
    parser = argparse.ArgumentParser(description="Test vehicle detector on video")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--model", type=str, default=None, help="Path to vehicle detection model")
    parser.add_argument("--output", type=str, default=None, help="Path to output video file")
    parser.add_argument("--confidence", type=float, default=0.4, help="Detection confidence threshold")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    test_vehicle_detector(
        video_path=args.video,
        model_path=args.model,
        output_path=args.output,
        confidence=args.confidence
    )
import cv2
import numpy as np
import json
import datetime
from services.checkout_monitoring import CheckoutMonitoringService
from services.footpath.tracker import PersonTracker

def test_checkout_monitoring(video_path, model_path=None, output_path=None):
    """Test the checkout monitoring service with a video file"""
    # Initialize services
    checkout_service = CheckoutMonitoringService(model_path=model_path, confidence_threshold=0.4)
    person_tracker = PersonTracker(confidence_threshold=0.4)
    
    # Open video file
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
    skip_frames = 2  # Process every nth frame for efficiency
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for efficiency
        if frame_count % skip_frames != 0:
            frame_count += 1
            continue
        
        # Process frame for person detection and tracking
        person_detections = person_tracker.update(frame)
        
        # Process frame for checkout counter detection
        checkout_detections = checkout_service.detect_checkout_counters(frame)
        
        # Analyze interactions between people and checkout counters
        checkout_service.analyze_customer_interactions(person_detections)
        
        # Annotate frame with checkout information
        checkout_annotated = checkout_service.annotate_frame(frame, person_detections)
        
        # Display info
        analytics = checkout_service.get_analytics()
        active_counters = sum(1 for status in checkout_service.checkout_statuses.values() 
                              if status['status'] in ["ACTIVE", "BUSY", "CROWDED", "OVERLOADED"])
        
        info_text = f"Frame: {frame_count} | Checkouts: {len(checkout_service.checkout_counters)} | Active: {active_counters}"
        cv2.putText(checkout_annotated, info_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Add queue info
        y_pos = 60
        for checkout_id, status in checkout_service.checkout_statuses.items():
            status_text = f"{checkout_id}: {status['status']} - Queue: {int(status['queue_length'])} - Customers: {status['customers']}"
            cv2.putText(checkout_annotated, status_text, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            y_pos += 25
        
        # Display the frame
        cv2.imshow('Checkout Monitoring', checkout_annotated)
        
        # Write to output if specified
        if writer:
            writer.write(checkout_annotated)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
        
        # Print progress every 50 frames
        if frame_count % 50 == 0:
            print(f"Processed {frame_count} frames")
            print(f"Current checkout analytics: {json.dumps(analytics['overall_stats'], indent=2)}")
    
    # Release resources
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    # Save final analytics
    if output_path:
        analytics_path = output_path.replace('.mp4', '_checkout_analytics.json')
        checkout_service.save_analytics(analytics_path)
        print(f"Checkout analytics saved to {analytics_path}")
    
    # Print final statistics
    print("\nFinal checkout analytics:")
    print(json.dumps(checkout_service.get_analytics(), indent=2))
    
    return checkout_service.get_analytics()

if __name__ == "__main__":
    # Update these paths for your environment
    video_path = "test-video.mp4"  # Your test video
    model_path = "checkout_counter_model.pt"  # Your Roboflow model
    output_path = "checkout_monitoring_output.mp4"
    
    test_checkout_monitoring(video_path, model_path, output_path)
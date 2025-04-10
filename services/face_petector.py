from ultralytics import YOLO
import cv2
import numpy as np
import torch
import os
import json
import time
from datetime import datetime
from collections import defaultdict, deque
import sys

class FaceDetector:
    """
    A class to detect and track faces in video frames using a YOLO-based model.
    Designed to work with privacy considerations in retail environments.
    """
    
    def __init__(self, model_path=None, confidence_threshold=0.35, min_tracking_confidence=0.4, blur_faces=False):
        """
        Initialize the face detector.
        
        Args:
            model_path: Path to the YOLO face detection model
            confidence_threshold: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence to maintain tracking
            blur_faces: Whether to automatically blur detected faces for privacy
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Default to the pre-trained model if none specified
        if model_path is None:
            # Look for the model in standard locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/face_detector.pt'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/face_detection.pt'),
                'face_detector.pt'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path is None:
                raise FileNotFoundError("Could not find face detector model. Please specify model_path.")
                
        print(f"Loading face detection model from: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.min_tracking_confidence = min_tracking_confidence
        self.blur_faces = blur_faces
        
        # Tracking variables
        self.next_face_id = 1
        self.tracked_faces = {}  # dict to store tracked face info
        self.face_histories = defaultdict(lambda: deque(maxlen=30))  # Store history of face positions
        
        # Analytics variables
        self.face_history = []
        self.session_start_time = datetime.now()
        self.frame_count = 0
        self.total_detections = 0
        
        # Time periods (store counts for every 5 minute interval)
        self.time_period_stats = []
        self.current_period_start = self.session_start_time
        self.period_face_count = 0
        self.PERIOD_LENGTH_SECONDS = 300  # 5 minutes
        
        # Privacy settings - control what data is stored
        self.privacy_mode = True  # When true, no actual face images are stored
        
    def detect(self, frame):
        """
        Detect faces in a frame.
        
        Args:
            frame: OpenCV image frame
            
        Returns:
            A list of detection dictionaries with face info
        """
        self.frame_count += 1
        
        # Run detection with the YOLO model
        results = self.model.track(frame, persist=True, conf=self.confidence_threshold)
        
        detections = []
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            # Extract bounding boxes, confidence scores and track IDs
            boxes = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes.xyxy is not None else []
            confidences = results[0].boxes.conf.cpu().numpy() if results[0].boxes.conf is not None else []
            track_ids = results[0].boxes.id.int().cpu().numpy() if results[0].boxes.id is not None else []
            
            for i in range(len(boxes)):
                if confidences[i] < self.confidence_threshold:
                    continue
                    
                box = boxes[i].astype(int)
                
                # Create face detection entry
                detection = {
                    "bbox": [int(b) for b in box],  # x1, y1, x2, y2
                    "confidence": float(confidences[i]),
                    "tracking_id": int(track_ids[i]) if len(track_ids) > i else None
                }
                
                # Calculate face dimensions and position
                width = box[2] - box[0]
                height = box[3] - box[1]
                center_x = (box[0] + box[2]) / 2
                center_y = (box[1] + box[3]) / 2
                
                detection["face_size"] = max(width, height)
                detection["face_position"] = (center_x, center_y)
                
                # Update tracking
                self._update_tracking(detection, frame)
                detections.append(detection)
            
            self.total_detections += len(detections)
                
        # Check if we need to close the current time period
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.current_period_start).total_seconds()
        
        if elapsed_seconds >= self.PERIOD_LENGTH_SECONDS:
            # Add current period to history
            period_stats = {
                "start_time": self.current_period_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "unique_faces": len(self.tracked_faces),
                "total_detections": self.period_face_count
            }
            
            self.time_period_stats.append(period_stats)
            
            # Reset for next period
            self.current_period_start = current_time
            self.period_face_count = 0
            
        return detections
    
    def _update_tracking(self, detection, frame):
        """
        Update face tracking with new detection information.
        In privacy mode, this doesn't store actual face images.
        """
        tracking_id = detection.get("tracking_id")
        
        if tracking_id is None:
            # Generate new ID if not tracked by YOLO
            tracking_id = self.next_face_id
            self.next_face_id += 1
            detection["tracking_id"] = tracking_id
        
        # Get or create face tracking entry
        if tracking_id not in self.tracked_faces:
            face_data = {
                "first_seen": self.frame_count,
                "last_seen": self.frame_count,
                "detection_count": 1,
                "positions": [detection["face_position"]],
                "sizes": [detection["face_size"]],
                "confidence_history": [detection["confidence"]]
            }
            
            # Store face embedding or features if not in privacy mode
            if not self.privacy_mode:
                # Extract face region
                bbox = detection["bbox"]
                face_img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                
                # Store small version of the face (or could compute embedding here)
                if face_img.size > 0:
                    face_small = cv2.resize(face_img, (32, 32))  # Small enough to be privacy-friendly
                    face_data["face_thumbnail"] = face_small
            
            self.tracked_faces[tracking_id] = face_data
        else:
            face = self.tracked_faces[tracking_id]
            face["last_seen"] = self.frame_count
            face["detection_count"] += 1
            face["positions"].append(detection["face_position"])
            face["sizes"].append(detection["face_size"])
            face["confidence_history"].append(detection["confidence"])
            
            # Limit stored positions to prevent memory issues
            if len(face["positions"]) > 50:
                face["positions"] = face["positions"][-50:]
                face["sizes"] = face["sizes"][-50:]
                face["confidence_history"] = face["confidence_history"][-50:]
        
        # Add current position to history for this face
        self.face_histories[tracking_id].append({
            "frame": self.frame_count,
            "position": detection["face_position"],
            "size": detection["face_size"]
        })
    
    def cleanup_tracking(self, max_frames_missing=30):
        """Remove tracked faces that haven't been seen for a while"""
        to_remove = []
        for face_id, face in self.tracked_faces.items():
            if self.frame_count - face["last_seen"] > max_frames_missing:
                to_remove.append(face_id)
                
        for face_id in to_remove:
            # Log face data before removing
            face = self.tracked_faces[face_id]
            
            # Calculate face movement and duration
            duration_frames = face["last_seen"] - face["first_seen"]
            avg_size = sum(face["sizes"]) / len(face["sizes"]) if face["sizes"] else 0
            
            # Movement calculation - distance between first and last position
            movement = 0
            if len(face["positions"]) >= 2:
                first_pos = face["positions"][0]
                last_pos = face["positions"][-1]
                movement = np.sqrt((last_pos[0] - first_pos[0])**2 + (last_pos[1] - first_pos[1])**2)
            
            face_data = {
                "face_id": face_id,
                "first_seen": face["first_seen"],
                "last_seen": face["last_seen"],
                "duration_frames": duration_frames,
                "avg_confidence": sum(face["confidence_history"]) / len(face["confidence_history"]),
                "avg_size": avg_size,
                "movement_pixels": movement
            }
            self.face_history.append(face_data)
            
            # Remove tracking data
            del self.tracked_faces[face_id]
            if face_id in self.face_histories:
                del self.face_histories[face_id]
    
    def annotate_frame(self, frame, detections=None, show_ids=True, blur_faces=None):
        """
        Draw bounding boxes on the frame and optionally blur faces.
        
        Args:
            frame: OpenCV image frame
            detections: Optional pre-computed detections, if None will run detection
            show_ids: Whether to show tracking IDs
            blur_faces: Override instance blur_faces setting
            
        Returns:
            Annotated frame
        """
        if detections is None:
            detections = self.detect(frame)
            
        annotated = frame.copy()
        
        # Use parameter blur_faces if provided, otherwise use instance setting
        should_blur = self.blur_faces if blur_faces is None else blur_faces
        
        # Draw each detection
        for detection in detections:
            box = detection["bbox"]
            tracking_id = detection["tracking_id"]
            confidence = detection["confidence"]
            
            # Choose color based on tracking ID or confidence
            color_id = tracking_id % 10 if tracking_id is not None else int(confidence * 10)
            colors = [
                (0, 255, 0),    # Green
                (255, 0, 0),    # Blue
                (0, 0, 255),    # Red
                (255, 255, 0),  # Cyan
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Yellow
                (128, 0, 0),    # Dark blue
                (0, 128, 0),    # Dark green
                (0, 0, 128),    # Dark red
                (128, 128, 0)   # Olive
            ]
            color = colors[color_id]
            
            # Blur the face if requested
            if should_blur:
                face_region = annotated[box[1]:box[3], box[0]:box[2]]
                if face_region.size > 0:  # Make sure the region is valid
                    # Apply blur - adjust kernel size based on face size
                    blur_kernel = max(5, min(int(detection["face_size"] / 10), 45))
                    # Ensure kernel is odd
                    if blur_kernel % 2 == 0:
                        blur_kernel += 1
                    face_region = cv2.GaussianBlur(face_region, (blur_kernel, blur_kernel), 0)
                    annotated[box[1]:box[3], box[0]:box[2]] = face_region
            
            # Draw bounding box
            cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            if show_ids and tracking_id is not None:
                info_text = f"ID: {tracking_id} ({confidence:.2f})"
                
                # Draw text background
                text_size = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(annotated, 
                             (box[0], box[1] - text_size[1] - 10),
                             (box[0] + text_size[0], box[1]),
                             color, -1)
                             
                # Draw text
                cv2.putText(annotated, info_text,
                           (box[0], box[1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw statistics on frame
        stats = self.get_statistics()
        y_pos = 30
        cv2.putText(annotated, f"Faces: {len(self.tracked_faces)} visible, {stats['total_unique_faces']} total",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Show privacy mode
        privacy_status = "ON" if self.privacy_mode else "OFF"
        cv2.putText(annotated, f"Privacy mode: {privacy_status}",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def get_statistics(self):
        """
        Get face detection statistics for the current session.
        
        Returns:
            Dictionary with face detection statistics
        """
        # Clean up tracking data first
        self.cleanup_tracking()
        
        # Compute current statistics
        total_active_faces = len(self.tracked_faces)
        historical_faces = len(self.face_history)
        total_unique_faces = total_active_faces + historical_faces
        
        # Calculate average face size and time in frame
        avg_size = 0
        avg_duration = 0
        
        if total_unique_faces > 0:
            # Calculate from historical data
            total_size = 0
            total_duration = 0
            
            for face in self.face_history:
                total_duration += face["duration_frames"]
                total_size += face["avg_size"]
            
            # Add current active faces
            for face in self.tracked_faces.values():
                current_duration = self.frame_count - face["first_seen"]
                total_duration += current_duration
                avg_face_size = sum(face["sizes"]) / len(face["sizes"]) if face["sizes"] else 0
                total_size += avg_face_size
            
            avg_size = total_size / total_unique_faces
            avg_duration = total_duration / total_unique_faces
        
        # Generate statistics object
        stats = {
            "session_info": {
                "start_time": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_frames_processed": self.frame_count,
                "total_detections": self.total_detections
            },
            "current_stats": {
                "active_faces": total_active_faces,
                "avg_face_size": avg_size,
                "avg_time_in_frame": avg_duration
            },
            "historical_stats": {
                "completed_tracks": historical_faces,
                "total_unique_faces": total_unique_faces
            },
            "time_period_stats": self.time_period_stats
        }
        
        return stats
    
    def save_analytics(self, output_path="face_detection_analytics.json"):
        """Save analytics data to a JSON file"""
        stats = self.get_statistics()
        
        # Add face tracking data
        all_face_data = []
        
        # Add historical faces (completed tracks)
        all_face_data.extend(self.face_history)
        
        # Add current faces in privacy-friendly way
        for face_id, face in self.tracked_faces.items():
            face_data = {
                "face_id": face_id,
                "first_seen": face["first_seen"],
                "last_seen": face["last_seen"],
                "duration_frames": face["last_seen"] - face["first_seen"],
                "avg_confidence": sum(face["confidence_history"]) / len(face["confidence_history"]),
                "avg_size": sum(face["sizes"]) / len(face["sizes"]) if face["sizes"] else 0
            }
            
            # Calculate movement stats (total distance traveled)
            if len(face["positions"]) >= 2:
                total_movement = 0
                for i in range(1, len(face["positions"])):
                    prev_pos = face["positions"][i-1]
                    curr_pos = face["positions"][i]
                    movement = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                    total_movement += movement
                face_data["total_movement_pixels"] = total_movement
            
            all_face_data.append(face_data)
        
        stats["face_details"] = all_face_data
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Face detection analytics saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving face detection analytics: {str(e)}")
            return False
    
    def set_privacy_mode(self, enabled=True):
        """Enable or disable privacy mode"""
        self.privacy_mode = enabled
        # If enabling privacy mode, clear any stored face images
        if enabled:
            for face_id, face in self.tracked_faces.items():
                if "face_thumbnail" in face:
                    del face["face_thumbnail"]
        return self.privacy_mode

# Usage example
if __name__ == "__main__":
    # Check if video path is provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = 0  # Use default camera
    
    # Parse blur argument if provided
    blur_faces = True
    if len(sys.argv) > 2 and sys.argv[2].lower() in ['false', '0', 'no']:
        blur_faces = False
    
    # Initialize detector
    detector = FaceDetector(blur_faces=blur_faces)
    
    # Open video capture
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video source {video_path}")
        exit()
    
    # Process video frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Detect faces
        detections = detector.detect(frame)
        
        # Annotate frame
        annotated_frame = detector.annotate_frame(frame, detections)
        
        # Display result
        cv2.imshow("Face Detection", annotated_frame)
        
        # Toggle blur with 'b' key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('b'):
            detector.blur_faces = not detector.blur_faces
            print(f"Face blur: {'ON' if detector.blur_faces else 'OFF'}")
        elif key == ord('p'):
            detector.set_privacy_mode(not detector.privacy_mode)
            print(f"Privacy mode: {'ON' if detector.privacy_mode else 'OFF'}")
        elif key == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    # Save statistics
    detector.save_analytics("face_detection_analytics.json")
    print("Final face detection statistics:")
    print(json.dumps(detector.get_statistics(), indent=2))
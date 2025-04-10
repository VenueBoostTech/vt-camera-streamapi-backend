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

class DemographicsDetector:
    """
    A class to detect and analyze demographics (age groups and gender) in video frames
    using a YOLO-based model with custom classifications.
    """
    
    # Age group definitions
    AGE_GROUPS = {
        0: "child",        # 0-12
        1: "teenager",     # 13-19
        2: "young_adult",  # 20-35
        3: "adult",        # 36-50
        4: "senior"        # 51+
    }
    
    # Gender definitions
    GENDERS = {
        0: "male",
        1: "female"
    }
    
    def __init__(self, model_path=None, confidence_threshold=0.35, min_tracking_confidence=0.4):
        """
        Initialize the demographics detector.
        
        Args:
            model_path: Path to the YOLO model trained for demographics detection
            confidence_threshold: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence to maintain tracking
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Default to the pre-trained model if none specified
        if model_path is None:
            # Look for the model in standard locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/demographics_detector.pt'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/demographics.pt'),
                'demographics_detector.pt'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path is None:
                raise FileNotFoundError("Could not find demographics detector model. Please specify model_path.")
                
        print(f"Loading demographics model from: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.min_tracking_confidence = min_tracking_confidence
        
        # Tracking variables
        self.next_person_id = 1
        self.tracked_persons = {}  # dict to store tracked person info
        self.person_histories = defaultdict(lambda: deque(maxlen=30))  # Store history of demographic classifications
        
        # Analytics variables
        self.demographics_history = []
        self.session_start_time = datetime.now()
        self.frame_count = 0
        self.total_detections = 0
        self.demographics_counts = {
            "gender": {
                "male": 0,
                "female": 0
            },
            "age_group": {
                "child": 0,
                "teenager": 0,
                "young_adult": 0,
                "adult": 0,
                "senior": 0
            }
        }
        
        # Time periods (store counts for every 5 minute interval)
        self.time_period_stats = []
        self.current_period_start = self.session_start_time
        self.period_demographics = self._create_empty_demographics_stats()
        self.PERIOD_LENGTH_SECONDS = 300  # 5 minutes
        
    def _create_empty_demographics_stats(self):
        """Create an empty statistics dictionary for demographics"""
        return {
            "gender": {
                "male": 0,
                "female": 0
            },
            "age_group": {
                "child": 0,
                "teenager": 0,
                "young_adult": 0,
                "adult": 0, 
                "senior": 0
            },
            "total_unique_people": 0
        }
    
    def detect(self, frame):
        """
        Detect people and their demographics in a frame.
        
        Args:
            frame: OpenCV image frame
            
        Returns:
            A list of detection dictionaries with person info and demographics
        """
        self.frame_count += 1
        
        # Run detection with the YOLO model
        results = self.model.track(frame, persist=True, conf=self.confidence_threshold)
        
        detections = []
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            # Extract bounding boxes, confidence scores and class indices
            boxes = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes.xyxy is not None else []
            confidences = results[0].boxes.conf.cpu().numpy() if results[0].boxes.conf is not None else []
            track_ids = results[0].boxes.id.int().cpu().numpy() if results[0].boxes.id is not None else []
            
            # If we have class prediction data (age_groups and gender)
            if hasattr(results[0], 'keypoints') and results[0].keypoints is not None:
                keypoints = results[0].keypoints.data.cpu().numpy()
            else:
                keypoints = None
                
            # Extract class data if available (separate models might predict age/gender as classes)
            classes = results[0].boxes.cls.cpu().numpy() if results[0].boxes.cls is not None else []
            
            for i in range(len(boxes)):
                if confidences[i] < self.confidence_threshold:
                    continue
                    
                box = boxes[i].astype(int)
                
                # Create person detection entry
                detection = {
                    "bbox": [int(b) for b in box],  # x1, y1, x2, y2
                    "confidence": float(confidences[i]),
                    "tracking_id": int(track_ids[i]) if len(track_ids) > i else None
                }
                
                # Extract demographics from classification heads or separate models
                # This is a placeholder - your actual model might output this differently
                if len(classes) > i:
                    age_class = int(classes[i]) % len(self.AGE_GROUPS)
                    gender_class = int(classes[i]) // len(self.AGE_GROUPS) 
                    
                    detection["age_group"] = self.AGE_GROUPS.get(age_class, "unknown")
                    detection["gender"] = self.GENDERS.get(gender_class, "unknown")
                else:
                    # Fallback when classification data isn't available
                    detection["age_group"] = "unknown"
                    detection["gender"] = "unknown"
                
                # Update tracking
                self._update_tracking(detection)
                detections.append(detection)
                
                # Update statistics
                if detection["tracking_id"] is not None:
                    gender = detection["gender"]
                    age_group = detection["age_group"]
                    
                    if gender in self.demographics_counts["gender"]:
                        self.demographics_counts["gender"][gender] += 1
                        
                    if age_group in self.demographics_counts["age_group"]:
                        self.demographics_counts["age_group"][age_group] += 1
                    
                    # Update period statistics
                    if gender in self.period_demographics["gender"]:
                        self.period_demographics["gender"][gender] += 1
                        
                    if age_group in self.period_demographics["age_group"]:
                        self.period_demographics["age_group"][age_group] += 1
            
            self.total_detections += len(detections)
                
        # Check if we need to close the current time period
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.current_period_start).total_seconds()
        
        if elapsed_seconds >= self.PERIOD_LENGTH_SECONDS:
            # Add current period to history
            self.period_demographics["start_time"] = self.current_period_start.strftime("%Y-%m-%d %H:%M:%S")
            self.period_demographics["end_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.period_demographics["total_unique_people"] = len(self.tracked_persons)
            
            self.time_period_stats.append(self.period_demographics)
            
            # Reset for next period
            self.current_period_start = current_time
            self.period_demographics = self._create_empty_demographics_stats()
            
        return detections
    
    def _update_tracking(self, detection):
        """Update person tracking with new detection information"""
        tracking_id = detection.get("tracking_id")
        
        if tracking_id is None:
            # Generate new ID if not tracked by YOLO
            tracking_id = self.next_person_id
            self.next_person_id += 1
            detection["tracking_id"] = tracking_id
        
        # Get or create person tracking entry
        if tracking_id not in self.tracked_persons:
            self.tracked_persons[tracking_id] = {
                "first_seen": self.frame_count,
                "last_seen": self.frame_count,
                "age_votes": defaultdict(int),
                "gender_votes": defaultdict(int),
                "final_age_group": detection["age_group"],
                "final_gender": detection["gender"],
                "detection_count": 1
            }
        else:
            person = self.tracked_persons[tracking_id]
            person["last_seen"] = self.frame_count
            person["detection_count"] += 1
            
            # Add votes for current demographics
            person["age_votes"][detection["age_group"]] += 1
            person["gender_votes"][detection["gender"]] += 1
            
            # Update final demographics based on majority voting
            # This prevents fluctuations in predictions
            if person["detection_count"] > 5:
                # Age group
                max_age_votes = 0
                for age_group, votes in person["age_votes"].items():
                    if votes > max_age_votes:
                        max_age_votes = votes
                        person["final_age_group"] = age_group
                
                # Gender
                max_gender_votes = 0
                for gender, votes in person["gender_votes"].items():
                    if votes > max_gender_votes:
                        max_gender_votes = votes
                        person["final_gender"] = gender
                        
                # Update the current detection with stabilized demographics
                detection["age_group"] = person["final_age_group"]
                detection["gender"] = person["final_gender"]
        
        # Add current demographics to history for this person
        self.person_histories[tracking_id].append({
            "frame": self.frame_count,
            "age_group": detection["age_group"],
            "gender": detection["gender"]
        })
    
    def cleanup_tracking(self, max_frames_missing=30):
        """Remove tracked persons that haven't been seen for a while"""
        to_remove = []
        for person_id, person in self.tracked_persons.items():
            if self.frame_count - person["last_seen"] > max_frames_missing:
                to_remove.append(person_id)
                
        for person_id in to_remove:
            # Log demographics data for this person before removing
            person = self.tracked_persons[person_id]
            person_data = {
                "person_id": person_id,
                "first_seen": person["first_seen"],
                "last_seen": person["last_seen"],
                "duration_frames": person["last_seen"] - person["first_seen"],
                "age_group": person["final_age_group"],
                "gender": person["final_gender"]
            }
            self.demographics_history.append(person_data)
            
            # Remove tracking data
            del self.tracked_persons[person_id]
            if person_id in self.person_histories:
                del self.person_histories[person_id]
    
    def annotate_frame(self, frame, detections=None, show_demographics=True, show_ids=True):
        """
        Draw bounding boxes and demographics information on the frame.
        
        Args:
            frame: OpenCV image frame
            detections: Optional pre-computed detections, if None will run detection
            show_demographics: Whether to show demographics text
            show_ids: Whether to show tracking IDs
            
        Returns:
            Annotated frame
        """
        if detections is None:
            detections = self.detect(frame)
            
        annotated = frame.copy()
        
        # Age group colors - different colors for different age groups
        age_colors = {
            "child": (0, 255, 0),        # Green
            "teenager": (0, 255, 255),   # Yellow
            "young_adult": (0, 165, 255), # Orange
            "adult": (0, 0, 255),        # Red
            "senior": (128, 0, 128),     # Purple
            "unknown": (128, 128, 128)   # Gray
        }
        
        # Gender indicators
        gender_symbols = {
            "male": "♂",
            "female": "♀",
            "unknown": "?"
        }
        
        # Draw each detection
        for detection in detections:
            box = detection["bbox"]
            tracking_id = detection["tracking_id"]
            age_group = detection["age_group"]
            gender = detection["gender"]
            
            # Get the color based on age group
            color = age_colors.get(age_group, (128, 128, 128))
            
            # Draw bounding box
            cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            if show_demographics or show_ids:
                info_text = ""
                
                if show_ids and tracking_id is not None:
                    info_text += f"ID: {tracking_id} "
                
                if show_demographics:
                    gender_symbol = gender_symbols.get(gender, "?")
                    info_text += f"{gender_symbol} {age_group}"
                
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
        cv2.putText(annotated, f"Demographics: {len(self.tracked_persons)} unique people",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Show gender distribution
        male_percent = stats["current_stats"]["gender_distribution"].get("male", 0)
        female_percent = stats["current_stats"]["gender_distribution"].get("female", 0)
        cv2.putText(annotated, f"Gender: {male_percent:.1f}% M, {female_percent:.1f}% F",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Show top age group
        top_age = stats["current_stats"]["top_age_group"]
        age_percent = stats["current_stats"]["age_distribution"].get(top_age, 0)
        cv2.putText(annotated, f"Top age: {top_age} ({age_percent:.1f}%)",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def get_statistics(self):
        """
        Get demographics statistics for the current session.
        
        Returns:
            Dictionary with demographic statistics
        """
        # Clean up tracking data first
        self.cleanup_tracking()
        
        # Compute current statistics
        total_people = len(self.tracked_persons)
        gender_counts = {"male": 0, "female": 0, "unknown": 0}
        age_counts = {age: 0 for age in self.AGE_GROUPS.values()}
        age_counts["unknown"] = 0
        
        # Count current demographics
        for person in self.tracked_persons.values():
            gender = person["final_gender"]
            age_group = person["final_age_group"]
            
            if gender in gender_counts:
                gender_counts[gender] += 1
            else:
                gender_counts["unknown"] += 1
                
            if age_group in age_counts:
                age_counts[age_group] += 1
            else:
                age_counts["unknown"] += 1
        
        # Calculate percentages
        gender_distribution = {}
        for gender, count in gender_counts.items():
            if gender != "unknown":  # Exclude unknown from percentage calculation
                if total_people > 0:
                    gender_distribution[gender] = (count / total_people) * 100
                else:
                    gender_distribution[gender] = 0
        
        age_distribution = {}
        for age, count in age_counts.items():
            if age != "unknown":  # Exclude unknown from percentage calculation
                if total_people > 0:
                    age_distribution[age] = (count / total_people) * 100
                else:
                    age_distribution[age] = 0
        
        # Find top age group
        top_age = "unknown"
        top_age_count = 0
        for age, count in age_counts.items():
            if age != "unknown" and count > top_age_count:
                top_age = age
                top_age_count = count
        
        # Compute historical stats from completed tracking
        historical_total = len(self.demographics_history)
        historical_gender = {"male": 0, "female": 0, "unknown": 0}
        historical_age = {age: 0 for age in self.AGE_GROUPS.values()}
        historical_age["unknown"] = 0
        
        for person in self.demographics_history:
            gender = person["gender"]
            age = person["age_group"]
            
            if gender in historical_gender:
                historical_gender[gender] += 1
            else:
                historical_gender["unknown"] += 1
                
            if age in historical_age:
                historical_age[age] += 1
            else:
                historical_age["unknown"] += 1
        
        # Calculate historical percentages
        historical_gender_distribution = {}
        historical_age_distribution = {}
        
        if historical_total > 0:
            for gender, count in historical_gender.items():
                if gender != "unknown":
                    historical_gender_distribution[gender] = (count / historical_total) * 100
                    
            for age, count in historical_age.items():
                if age != "unknown":
                    historical_age_distribution[age] = (count / historical_total) * 100
        
        # Generate statistics object
        stats = {
            "session_info": {
                "start_time": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_frames_processed": self.frame_count,
                "total_detections": self.total_detections
            },
            "current_stats": {
                "active_people": total_people,
                "gender_distribution": gender_distribution,
                "age_distribution": age_distribution,
                "top_age_group": top_age
            },
            "historical_stats": {
                "total_unique_people": historical_total + total_people,
                "completed_tracks": historical_total,
                "gender_distribution": historical_gender_distribution,
                "age_distribution": historical_age_distribution
            },
            "time_period_stats": self.time_period_stats
        }
        
        return stats
    
    def save_analytics(self, output_path="demographics_analytics.json"):
        """Save analytics data to a JSON file"""
        stats = self.get_statistics()
        
        # Add any currently tracked people to historical data for complete stats
        for person_id, person in self.tracked_persons.items():
            person_data = {
                "person_id": person_id,
                "first_seen": person["first_seen"],
                "last_seen": person["last_seen"],
                "duration_frames": person["last_seen"] - person["first_seen"],
                "age_group": person["final_age_group"],
                "gender": person["final_gender"]
            }
            stats["demographics_detail"] = self.demographics_history + [person_data]
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Demographics analytics saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving demographics analytics: {str(e)}")
            return False

# Usage example
if __name__ == "__main__":
    # Check if video path is provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = 0  # Use default camera
    
    # Initialize detector
    detector = DemographicsDetector()
    
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
            
        # Detect demographics
        detections = detector.detect(frame)
        
        # Annotate frame
        annotated_frame = detector.annotate_frame(frame, detections)
        
        # Display result
        cv2.imshow("Demographics Analysis", annotated_frame)
        
        # Break if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    # Save statistics
    detector.save_analytics("demographics_analytics.json")
    print("Final demographics statistics:")
    print(json.dumps(detector.get_statistics(), indent=2))
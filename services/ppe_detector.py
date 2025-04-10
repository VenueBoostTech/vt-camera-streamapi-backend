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

class PPEDetector:
    """
    A class to detect and analyze Personal Protective Equipment (PPE) in video frames
    using a YOLO-based model with PPE classifications.
    """
    
    # Default PPE item colors for visualization
    PPE_COLORS = {
        'Helmet': (0, 0, 255),      # Red
        'Vest': (0, 165, 255),      # Orange
        'Glove': (0, 255, 255),     # Yellow
        'Boots': (0, 128, 0),       # Green
        'Mask': (255, 0, 0),        # Blue
        'Glass': (255, 0, 255),     # Magenta
        'Ear-protection': (128, 0, 128),  # Purple
        'Person': (192, 192, 192),  # Silver/Gray
    }
    
    def __init__(self, model_path=None, confidence_threshold=0.35, min_tracking_confidence=0.4):
        """
        Initialize the PPE detector.
        
        Args:
            model_path: Path to the YOLO model trained for PPE detection
            confidence_threshold: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence to maintain tracking
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Default to the pre-trained model if none specified
        if model_path is None:
            # Look for the model in standard locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/ppe_detector.pt'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/ppe_detection.pt'),
                'ppe_detector.pt'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path is None:
                raise FileNotFoundError("Could not find PPE detector model. Please specify model_path.")
                
        print(f"Loading PPE detection model from: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.min_tracking_confidence = min_tracking_confidence
        
        # Get class names from the model
        self.class_names = self.model.names
        
        # Tracking variables
        self.next_person_id = 1
        self.tracked_persons = {}  # dict to store tracked person info with their PPE
        self.person_histories = defaultdict(lambda: deque(maxlen=30))  # Store history of PPE for each person
        
        # Analytics variables
        self.detection_history = []
        self.session_start_time = datetime.now()
        self.frame_count = 0
        self.total_detections = 0
        
        # PPE compliance tracking
        self.ppe_counts = {ppe_type: 0 for ppe_type in self.PPE_COLORS.keys()}
        self.person_count = 0
        
        # Time periods (store counts for every 5 minute interval)
        self.time_period_stats = []
        self.current_period_start = self.session_start_time
        self.period_detections = {ppe_type: 0 for ppe_type in self.PPE_COLORS.keys()}
        self.PERIOD_LENGTH_SECONDS = 300  # 5 minutes
        
        # Compliance rules - required PPE per location/scenario
        # This can be customized based on specific workplace requirements
        self.compliance_rules = {
            'construction': ['Helmet', 'Vest', 'Boots'],
            'laboratory': ['Glass', 'Glove', 'Mask'],
            'factory': ['Helmet', 'Ear-protection', 'Vest'],
            'default': ['Helmet', 'Vest']  # Default minimum requirements
        }
        
        # Active compliance rule
        self.active_rule = 'default'
    
    def detect(self, frame):
        """
        Detect PPE items in a frame.
        
        Args:
            frame: OpenCV image frame
            
        Returns:
            A list of detection dictionaries with PPE info
        """
        self.frame_count += 1
        
        # Run detection with the YOLO model
        results = self.model.track(frame, persist=True, conf=self.confidence_threshold)
        
        detections = []
        persons = []  # Keep track of persons separately for PPE association
        
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            # Extract bounding boxes, confidence scores, class IDs, and track IDs
            boxes = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes.xyxy is not None else []
            confidences = results[0].boxes.conf.cpu().numpy() if results[0].boxes.conf is not None else []
            class_ids = results[0].boxes.cls.cpu().numpy() if results[0].boxes.cls is not None else []
            track_ids = results[0].boxes.id.int().cpu().numpy() if results[0].boxes.id is not None else []
            
            # Process all detections
            for i in range(len(boxes)):
                if confidences[i] < self.confidence_threshold:
                    continue
                    
                box = boxes[i].astype(int)
                class_id = int(class_ids[i])
                class_name = self.class_names[class_id]
                
                # Create detection entry
                detection = {
                    "bbox": [int(b) for b in box],  # x1, y1, x2, y2
                    "confidence": float(confidences[i]),
                    "class_id": class_id,
                    "class_name": class_name,
                    "tracking_id": int(track_ids[i]) if len(track_ids) > i else None
                }
                
                # Add detection
                detections.append(detection)
                
                # Update PPE count
                if class_name in self.ppe_counts:
                    self.ppe_counts[class_name] += 1
                    self.period_detections[class_name] += 1
                
                # Collect person detections for later processing
                if class_name == 'Person':
                    persons.append(detection)
            
            # Update total detection count
            self.total_detections += len(detections)
            self.person_count += len(persons)
            
            # Associate PPE with persons
            self._associate_ppe_with_persons(persons, detections)
                
        # Check if we need to close the current time period
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.current_period_start).total_seconds()
        
        if elapsed_seconds >= self.PERIOD_LENGTH_SECONDS:
            # Add current period to history
            period_stats = {
                "start_time": self.current_period_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "ppe_detections": dict(self.period_detections),
                "person_count": len(self.tracked_persons)
            }
            
            self.time_period_stats.append(period_stats)
            
            # Reset for next period
            self.current_period_start = current_time
            self.period_detections = {ppe_type: 0 for ppe_type in self.PPE_COLORS.keys()}
            
        return detections
    
    def _associate_ppe_with_persons(self, persons, all_detections):
        """
        Associate detected PPE items with person detections.
        This helps track which person has which PPE items.
        """
        # First, group detections by class name (excluding persons)
        ppe_detections = {}
        for detection in all_detections:
            if detection["class_name"] != "Person":
                if detection["class_name"] not in ppe_detections:
                    ppe_detections[detection["class_name"]] = []
                ppe_detections[detection["class_name"]].append(detection)
        
        # For each person, find associated PPE items
        for person in persons:
            person_bbox = person["bbox"]
            person_id = person["tracking_id"]
            
            # Initialize or update person tracking entry
            if person_id not in self.tracked_persons:
                # New person
                person_data = {
                    "first_seen": self.frame_count,
                    "last_seen": self.frame_count,
                    "detection_count": 1,
                    "current_ppe": {},
                    "ppe_history": {ppe_type: 0 for ppe_type in self.PPE_COLORS.keys()}
                }
                self.tracked_persons[person_id] = person_data
            else:
                # Update existing person
                self.tracked_persons[person_id]["last_seen"] = self.frame_count
                self.tracked_persons[person_id]["detection_count"] += 1
            
            # Clear current PPE for this update
            self.tracked_persons[person_id]["current_ppe"] = {}
            
            # Check for each PPE type
            for ppe_type, detections in ppe_detections.items():
                for ppe in detections:
                    ppe_bbox = ppe["bbox"]
                    
                    # Check if PPE is associated with this person
                    # Simple heuristic: Check for overlap or proximity
                    if self._is_ppe_associated_with_person(person_bbox, ppe_bbox):
                        # Associate PPE with person
                        if ppe_type not in self.tracked_persons[person_id]["current_ppe"]:
                            self.tracked_persons[person_id]["current_ppe"][ppe_type] = []
                        
                        self.tracked_persons[person_id]["current_ppe"][ppe_type].append({
                            "confidence": ppe["confidence"],
                            "bbox": ppe["bbox"]
                        })
                        
                        # Update PPE history for this person
                        self.tracked_persons[person_id]["ppe_history"][ppe_type] += 1
            
            # Update history record for this person
            self.person_histories[person_id].append({
                "frame": self.frame_count,
                "current_ppe": dict(self.tracked_persons[person_id]["current_ppe"])
            })
    
    def _is_ppe_associated_with_person(self, person_bbox, ppe_bbox):
        """
        Determine if a PPE item is associated with a person based on bbox proximity.
        
        Args:
            person_bbox: Person bounding box [x1, y1, x2, y2]
            ppe_bbox: PPE item bounding box [x1, y1, x2, y2]
            
        Returns:
            Boolean indicating if the PPE is likely associated with the person
        """
        # Check for overlap
        def overlap(box1, box2):
            x1_max = max(box1[0], box2[0])
            y1_max = max(box1[1], box2[1])
            x2_min = min(box1[2], box2[2])
            y2_min = min(box1[3], box2[3])
            
            if x1_max < x2_min and y1_max < y2_min:
                return True
            return False
        
        # Check if PPE is contained within person bbox with some margin
        def is_contained(person, ppe, margin=0.2):
            # Calculate expanded person bbox
            p_width = person[2] - person[0]
            p_height = person[3] - person[1]
            
            expanded_person = [
                person[0] - int(p_width * margin),
                person[1] - int(p_height * margin),
                person[2] + int(p_width * margin),
                person[3] + int(p_height * margin)
            ]
            
            return (ppe[0] >= expanded_person[0] and ppe[1] >= expanded_person[1] and
                    ppe[2] <= expanded_person[2] and ppe[3] <= expanded_person[3])
        
        # Check proximity if not contained
        def is_proximate(person, ppe, threshold=1.5):
            # Calculate centers
            p_center_x = (person[0] + person[2]) / 2
            p_center_y = (person[1] + person[3]) / 2
            
            ppe_center_x = (ppe[0] + ppe[2]) / 2
            ppe_center_y = (ppe[1] + ppe[3]) / 2
            
            # Calculate normalized distance
            p_size = max(person[2] - person[0], person[3] - person[1])
            distance = np.sqrt((p_center_x - ppe_center_x)**2 + (p_center_y - ppe_center_y)**2) / p_size
            
            return distance < threshold
        
        # Check various association methods
        if overlap(person_bbox, ppe_bbox):
            return True
        
        if is_contained(person_bbox, ppe_bbox):
            return True
        
        if is_proximate(person_bbox, ppe_bbox):
            return True
        
        return False
    
    def cleanup_tracking(self, max_frames_missing=30):
        """Remove tracked persons that haven't been seen for a while"""
        to_remove = []
        for person_id, person in self.tracked_persons.items():
            if self.frame_count - person["last_seen"] > max_frames_missing:
                to_remove.append(person_id)
                
        for person_id in to_remove:
            # Log data before removing
            person = self.tracked_persons[person_id]
            
            # Calculate PPE compliance
            compliance_status = self.check_compliance(person["current_ppe"], self.active_rule)
            
            # Calculate PPE statistics
            ppe_stats = {}
            for ppe_type, count in person["ppe_history"].items():
                if count > 0:
                    # Calculate percentage of frames this PPE was detected
                    detection_frames = person["last_seen"] - person["first_seen"] + 1
                    percentage = (count / detection_frames) * 100 if detection_frames > 0 else 0
                    ppe_stats[ppe_type] = {
                        "count": count, 
                        "percentage": percentage
                    }
            
            person_data = {
                "person_id": person_id,
                "first_seen": person["first_seen"],
                "last_seen": person["last_seen"],
                "duration_frames": person["last_seen"] - person["first_seen"],
                "ppe_stats": ppe_stats,
                "compliance": compliance_status
            }
            self.detection_history.append(person_data)
            
            # Remove tracking data
            del self.tracked_persons[person_id]
            if person_id in self.person_histories:
                del self.person_histories[person_id]
    
    def check_compliance(self, current_ppe, rule_key='default'):
        """
        Check if a person complies with PPE requirements.
        
        Args:
            current_ppe: Dictionary of current PPE for the person
            rule_key: Which compliance rule to check against
            
        Returns:
            Dictionary with compliance status and details
        """
        required_ppe = self.compliance_rules.get(rule_key, self.compliance_rules['default'])
        
        # Initialize compliance data
        compliance = {
            "status": True,  # Assume compliant until proven otherwise
            "rule": rule_key,
            "required": required_ppe,
            "missing": [],
            "present": [],
            "score": 0.0
        }
        
        # Check for each required PPE
        for ppe in required_ppe:
            if ppe in current_ppe and current_ppe[ppe]:
                compliance["present"].append(ppe)
            else:
                compliance["missing"].append(ppe)
                compliance["status"] = False
        
        # Calculate compliance score (percentage of required PPE that is present)
        if required_ppe:
            compliance["score"] = (len(compliance["present"]) / len(required_ppe)) * 100
        
        return compliance
    
    def set_compliance_rule(self, rule_key):
        """Set the active compliance rule"""
        if rule_key in self.compliance_rules:
            self.active_rule = rule_key
            return True
        return False
    
    def add_compliance_rule(self, rule_key, required_ppe):
        """Add a new compliance rule"""
        self.compliance_rules[rule_key] = required_ppe
        return True
    
    def annotate_frame(self, frame, detections=None, show_compliance=True, show_labels=True, show_confidence=False):
        """
        Draw bounding boxes and PPE information on the frame.
        
        Args:
            frame: OpenCV image frame
            detections: Optional pre-computed detections, if None will run detection
            show_compliance: Whether to show compliance status for each person
            show_labels: Whether to show class labels
            show_confidence: Whether to show confidence scores
            
        Returns:
            Annotated frame
        """
        if detections is None:
            detections = self.detect(frame)
            
        annotated = frame.copy()
        
        # Group detections by class
        class_detections = defaultdict(list)
        for detection in detections:
            class_detections[detection["class_name"]].append(detection)
        
        # First, draw all non-person objects
        for class_name, class_dets in class_detections.items():
            if class_name == "Person":
                continue
                
            color = self.PPE_COLORS.get(class_name, (128, 128, 128))  # Default gray for unknown
            
            for detection in class_dets:
                box = detection["bbox"]
                confidence = detection["confidence"]
                
                # Draw bounding box
                cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 2)
                
                if show_labels:
                    label_text = class_name
                    if show_confidence:
                        label_text += f" {confidence:.2f}"
                        
                    # Draw text background
                    text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                    cv2.rectangle(annotated, 
                                 (box[0], box[1] - text_size[1] - 10),
                                 (box[0] + text_size[0], box[1]),
                                 color, -1)
                                 
                    # Draw text
                    cv2.putText(annotated, label_text,
                               (box[0], box[1] - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Now draw persons with compliance status
        if "Person" in class_detections:
            for detection in class_detections["Person"]:
                box = detection["bbox"]
                confidence = detection["confidence"]
                tracking_id = detection["tracking_id"]
                
                if tracking_id is not None and tracking_id in self.tracked_persons:
                    person = self.tracked_persons[tracking_id]
                    current_ppe = person["current_ppe"]
                    
                    # Check compliance
                    compliance = self.check_compliance(current_ppe, self.active_rule)
                    
                    # Set color based on compliance
                    if compliance["status"]:
                        color = (0, 255, 0)  # Green for compliant
                    else:
                        color = (0, 0, 255)  # Red for non-compliant
                    
                    # Draw person bounding box
                    cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 2)
                    
                    if show_labels:
                        label_text = f"Person #{tracking_id}"
                        if show_confidence:
                            label_text += f" {confidence:.2f}"
                        
                        # Draw text background
                        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(annotated, 
                                     (box[0], box[1] - text_size[1] - 10),
                                     (box[0] + text_size[0], box[1]),
                                     color, -1)
                                     
                        # Draw text
                        cv2.putText(annotated, label_text,
                                   (box[0], box[1] - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                    
                    # Show compliance information
                    if show_compliance:
                        # Draw compliance status
                        if compliance["status"]:
                            status_text = "COMPLIANT"
                        else:
                            missing_text = ", ".join(compliance["missing"])
                            status_text = f"NON-COMPLIANT: Missing {missing_text}"
                        
                        # Position at bottom of person bbox
                        y_pos = box[3] + 20
                        
                        # Draw text background
                        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(annotated, 
                                     (box[0], y_pos - text_size[1] - 5),
                                     (box[0] + text_size[0], y_pos + 5),
                                     color, -1)
                        
                        # Draw compliance text
                        cv2.putText(annotated, status_text,
                                   (box[0], y_pos),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                        
                        # Draw score bar
                        bar_length = 50
                        bar_height = 5
                        filled_length = int(bar_length * compliance["score"] / 100)
                        
                        # Bar position (under compliance text)
                        bar_x = box[0]
                        bar_y = y_pos + 10
                        
                        # Draw background (gray)
                        cv2.rectangle(annotated, (bar_x, bar_y), (bar_x + bar_length, bar_y + bar_height), (128, 128, 128), -1)
                        
                        # Draw filled portion (green to red based on score)
                        if compliance["score"] > 0:
                            # Color based on score (green at 100%, red at 0%)
                            g = int(255 * (compliance["score"] / 100))
                            r = int(255 * (1 - compliance["score"] / 100))
                            bar_color = (0, g, r)
                            cv2.rectangle(annotated, (bar_x, bar_y), (bar_x + filled_length, bar_y + bar_height), bar_color, -1)
                else:
                    # Draw untracked persons in gray
                    cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), (192, 192, 192), 2)
                    
                    if show_labels:
                        label_text = "Person"
                        if show_confidence:
                            label_text += f" {confidence:.2f}"
                        
                        # Draw text background
                        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(annotated, 
                                     (box[0], box[1] - text_size[1] - 10),
                                     (box[0] + text_size[0], box[1]),
                                     (192, 192, 192), -1)
                                     
                        # Draw text
                        cv2.putText(annotated, label_text,
                                   (box[0], box[1] - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw overall statistics
        stats = self.get_statistics()
        y_pos = 30
        
        # Draw title
        cv2.putText(annotated, f"PPE Detection - Rule: {self.active_rule}",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Draw compliance rate
        compliance_rate = stats["compliance_rate"]
        cv2.putText(annotated, f"Compliance Rate: {compliance_rate:.1f}%",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Draw person count
        cv2.putText(annotated, f"Persons: {len(self.tracked_persons)} visible, {stats['total_persons']} total",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                   
        return annotated
    
    def get_statistics(self):
        """
        Get PPE detection statistics for the current session.
        
        Returns:
            Dictionary with PPE detection statistics
        """
        # Clean up tracking data first
        self.cleanup_tracking()
        
        # Compute current statistics
        total_active_persons = len(self.tracked_persons)
        historical_persons = len(self.detection_history)
        total_persons = total_active_persons + historical_persons
        
        # Calculate compliance rate
        compliant_count = 0
        non_compliant_count = 0
        
        # Count from active persons
        for person in self.tracked_persons.values():
            compliance = self.check_compliance(person["current_ppe"], self.active_rule)
            if compliance["status"]:
                compliant_count += 1
            else:
                non_compliant_count += 1
        
        # Count from history
        for person in self.detection_history:
            if person["compliance"]["status"]:
                compliant_count += 1
            else:
                non_compliant_count += 1
        
        # Calculate compliance rate
        compliance_rate = 0
        if total_persons > 0:
            compliance_rate = (compliant_count / total_persons) * 100
        
        # Calculate PPE type distribution
        ppe_distribution = {}
        for ppe_type in self.PPE_COLORS.keys():
            if ppe_type == "Person":
                continue
                
            count = self.ppe_counts[ppe_type]
            percentage = (count / self.total_detections) * 100 if self.total_detections > 0 else 0
            
            ppe_distribution[ppe_type] = {
                "count": count,
                "percentage": percentage
            }
        
        # Missing PPE analysis
        missing_ppe = {}
        required_ppe = self.compliance_rules[self.active_rule]
        
        for ppe_type in required_ppe:
            missing_count = 0
            
            # Check active persons
            for person in self.tracked_persons.values():
                if ppe_type not in person["current_ppe"] or not person["current_ppe"][ppe_type]:
                    missing_count += 1
            
            # Check history
            for person in self.detection_history:
                if ppe_type in person["compliance"]["missing"]:
                    missing_count += 1
            
            missing_percentage = (missing_count / total_persons) * 100 if total_persons > 0 else 0
            
            missing_ppe[ppe_type] = {
                "count": missing_count,
                "percentage": missing_percentage
            }
        
        # Generate statistics object
        stats = {
            "session_info": {
                "start_time": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_frames_processed": self.frame_count,
                "total_detections": self.total_detections,
                "active_rule": self.active_rule,
                "required_ppe": required_ppe
            },
            "current_stats": {
                "active_persons": total_active_persons,
                "compliance_rate": compliance_rate,
                "ppe_distribution": ppe_distribution,
                "missing_ppe": missing_ppe
            },
            "historical_stats": {
                "total_persons": total_persons,
                "compliant_persons": compliant_count,
                "non_compliant_persons": non_compliant_count
            },
            "time_period_stats": self.time_period_stats,
            "compliance_rate": compliance_rate
        }
        
        return stats
    
    def save_analytics(self, output_path="ppe_detection_analytics.json"):
        """Save analytics data to a JSON file"""
        stats = self.get_statistics()
        
        # Add person tracking data
        all_person_data = []
        
        # Add historical persons (completed tracks)
        all_person_data.extend(self.detection_history)
        
        # Add current active persons
        for person_id, person in self.tracked_persons.items():
            compliance = self.check_compliance(person["current_ppe"], self.active_rule)
            
            # Calculate PPE statistics
            ppe_stats = {}
            for ppe_type, count in person["ppe_history"].items():
                if count > 0:
                    # Calculate percentage of frames this PPE was detected
                    detection_frames = person["last_seen"] - person["first_seen"] + 1
                    percentage = (count / detection_frames) * 100 if detection_frames > 0 else 0
                    ppe_stats[ppe_type] = {
                        "count": count, 
                        "percentage": percentage
                    }
            
            person_data = {
                "person_id": person_id,
                "first_seen": person["first_seen"],
                "last_seen": person["last_seen"],
                "duration_frames": person["last_seen"] - person["first_seen"],
                "ppe_stats": ppe_stats,
                "compliance": compliance
            }
            all_person_data.append(person_data)
        
        stats["person_details"] = all_person_data
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"PPE detection analytics saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving PPE detection analytics: {str(e)}")
            return False

# Usage example
if __name__ == "__main__":
    # Check if video path is provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = 0  # Use default camera
    
    # Parse rule argument if provided
    rule = 'default'
    if len(sys.argv) > 2:
        rule = sys.argv[2]
    
    # Initialize detector
    detector = PPEDetector()
    
    # Set compliance rule
    if rule in detector.compliance_rules:
        detector.set_compliance_rule(rule)
    else:
        print(f"Warning: Rule '{rule}' not found. Using default rule.")
        print(f"Available rules: {list(detector.compliance_rules.keys())}")
    
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
            
        # Detect PPE
        detections = detector.detect(frame)
        
        # Annotate frame
        annotated_frame = detector.annotate_frame(frame, detections)
        
        # Display result
        cv2.imshow("PPE Detection", annotated_frame)
        
        # Handle key press
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
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    # Save statistics
    detector.save_analytics("ppe_detection_analytics.json")
    print("Final PPE detection statistics:")
    print(json.dumps(detector.get_statistics(), indent=2))
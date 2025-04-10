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

class VehicleDetector:
    """
    A class to detect and track vehicles in video frames
    using a YOLO-based model with vehicle classifications.
    """
    
    # Default vehicle colors for visualization
    VEHICLE_COLORS = {
        'car': (0, 255, 0),        # Green
        'truck': (0, 0, 255),      # Red
        'motorcycle': (255, 0, 0), # Blue
        'bus': (0, 165, 255),      # Orange
        'bicycle': (255, 0, 255),  # Magenta
    }
    
    # Standardized class names (in case Roboflow export has unusual names)
    CLASS_NAMES_MAP = {
        'Object Detection - v1 2024-04-29 2-21pm': 'car',
        'Object Detection - v1 2024-07-18 6-30am': 'truck'
    }
    
    def __init__(self, model_path=None, confidence_threshold=0.35, min_tracking_confidence=0.4):
        """
        Initialize the vehicle detector.
        
        Args:
            model_path: Path to the YOLO model trained for vehicle detection
            confidence_threshold: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence to maintain tracking
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Default to the pre-trained model if none specified
        if model_path is None:
            # Look for the model in standard locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/vehicle_detector.pt'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '../training_models/vehicle_detection.pt'),
                'vehicle_detector.pt'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path is None:
                raise FileNotFoundError("Could not find vehicle detector model. Please specify model_path.")
                
        print(f"Loading vehicle detection model from: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.min_tracking_confidence = min_tracking_confidence
        
        # Get class names from the model and standardize them if needed
        self.class_names = {}
        for idx, name in self.model.names.items():
            if name in self.CLASS_NAMES_MAP:
                # Map unusual names to standard vehicle classes
                self.class_names[idx] = self.CLASS_NAMES_MAP[name]
            else:
                self.class_names[idx] = name
                
        print(f"Vehicle detector initialized with classes: {self.class_names}")
        
        # Tracking variables
        self.next_vehicle_id = 1
        self.tracked_vehicles = {}  # dict to store tracked vehicle info
        self.vehicle_histories = defaultdict(lambda: deque(maxlen=30))  # Store history of vehicle positions
        
        # Analytics variables
        self.detection_history = []
        self.session_start_time = datetime.now()
        self.frame_count = 0
        self.total_detections = 0
        
        # Vehicle type counts
        self.vehicle_counts = {vehicle_type: 0 for vehicle_type in self.VEHICLE_COLORS.keys()}
        
        # Time periods (store counts for every 5 minute interval)
        self.time_period_stats = []
        self.current_period_start = self.session_start_time
        self.period_detections = {vehicle_type: 0 for vehicle_type in self.VEHICLE_COLORS.keys()}
        self.PERIOD_LENGTH_SECONDS = 300  # 5 minutes
        
        # Parking area definition (can be set by the user)
        self.parking_areas = []  # List of [x1, y1, x2, y2] regions
        
        # Traffic counting
        self.counting_lines = []  # List of [[x1, y1], [x2, y2], "name"] lines
        self.line_counts = defaultdict(lambda: defaultdict(int))  # line_name -> vehicle_type -> count
    
    def add_parking_area(self, x1, y1, x2, y2, name=None):
        """Add a parking area region to monitor"""
        area_id = len(self.parking_areas)
        area = {
            "id": area_id,
            "name": name if name else f"Parking Area {area_id+1}",
            "bbox": [x1, y1, x2, y2],
            "capacity": 0,  # Will be estimated based on size
            "occupied": 0
        }
        self.parking_areas.append(area)
        return area_id
    
    def add_counting_line(self, x1, y1, x2, y2, name=None):
        """Add a line for counting vehicles crossing it"""
        line_id = len(self.counting_lines)
        line = {
            "id": line_id,
            "name": name if name else f"Line {line_id+1}",
            "points": [[x1, y1], [x2, y2]],
            "counts": {vehicle_type: 0 for vehicle_type in self.VEHICLE_COLORS.keys()},
            "total": 0
        }
        self.counting_lines.append(line)
        return line_id
    
    def detect(self, frame):
        """
        Detect vehicles in a frame.
        
        Args:
            frame: OpenCV image frame
            
        Returns:
            A list of detection dictionaries with vehicle info
        """
        self.frame_count += 1
        
        # Run detection with the YOLO model
        results = self.model.track(frame, persist=True, conf=self.confidence_threshold)
        
        detections = []
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
                
                # Get class name with fallback to index if not found
                if class_id in self.class_names:
                    class_name = self.class_names[class_id]
                else:
                    class_name = f"vehicle_{class_id}"
                
                # Create detection entry
                detection = {
                    "bbox": [int(b) for b in box],  # x1, y1, x2, y2
                    "confidence": float(confidences[i]),
                    "class_id": class_id,
                    "class_name": class_name,
                    "tracking_id": int(track_ids[i]) if len(track_ids) > i else None
                }
                
                # Calculate vehicle size and position
                width = box[2] - box[0]
                height = box[3] - box[1]
                center_x = (box[0] + box[2]) / 2
                center_y = (box[1] + box[3]) / 2
                
                detection["size"] = width * height
                detection["position"] = (center_x, center_y)
                
                # Check if in any parking area
                detection["in_parking"] = self._check_in_parking_areas(detection)
                
                # Update tracking
                self._update_tracking(detection)
                detections.append(detection)
                
                # Update vehicle count by type
                if class_name in self.vehicle_counts:
                    self.vehicle_counts[class_name] += 1
                    self.period_detections[class_name] += 1
            
            self.total_detections += len(detections)
            
            # Update line crossing counts
            self._update_line_crossings(detections)
                
        # Check if we need to close the current time period
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.current_period_start).total_seconds()
        
        if elapsed_seconds >= self.PERIOD_LENGTH_SECONDS:
            # Add current period to history
            period_stats = {
                "start_time": self.current_period_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_detections": dict(self.period_detections),
                "parking_occupancy": self._get_parking_occupancy(),
                "line_counts": {line["name"]: dict(line["counts"]) for line in self.counting_lines}
            }
            
            self.time_period_stats.append(period_stats)
            
            # Reset for next period
            self.current_period_start = current_time
            self.period_detections = {vehicle_type: 0 for vehicle_type in self.VEHICLE_COLORS.keys()}
            
        return detections
    
    def _check_in_parking_areas(self, detection):
        """Check if a vehicle is within any defined parking area"""
        vehicle_bbox = detection["bbox"]
        vehicle_center = detection["position"]
        
        for area in self.parking_areas:
            area_bbox = area["bbox"]
            
            # Check if vehicle center is within parking area
            if (area_bbox[0] <= vehicle_center[0] <= area_bbox[2] and 
                area_bbox[1] <= vehicle_center[1] <= area_bbox[3]):
                return area["id"]
        
        return None
    
    def _update_tracking(self, detection):
        """Update vehicle tracking with new detection information"""
        tracking_id = detection.get("tracking_id")
        
        if tracking_id is None:
            # Generate new ID if not tracked by YOLO
            tracking_id = self.next_vehicle_id
            self.next_vehicle_id += 1
            detection["tracking_id"] = tracking_id
        
        # Get or create vehicle tracking entry
        if tracking_id not in self.tracked_vehicles:
            vehicle_data = {
                "first_seen": self.frame_count,
                "last_seen": self.frame_count,
                "class_name": detection["class_name"],
                "detection_count": 1,
                "positions": [detection["position"]],
                "sizes": [detection["size"]],
                "confidences": [detection["confidence"]],
                "in_parking_history": [detection["in_parking"]],
                "crossed_lines": set()
            }
            
            self.tracked_vehicles[tracking_id] = vehicle_data
        else:
            vehicle = self.tracked_vehicles[tracking_id]
            vehicle["last_seen"] = self.frame_count
            vehicle["detection_count"] += 1
            vehicle["positions"].append(detection["position"])
            vehicle["sizes"].append(detection["size"])
            vehicle["confidences"].append(detection["confidence"])
            vehicle["in_parking_history"].append(detection["in_parking"])
            
            # Limit stored positions to prevent memory issues
            if len(vehicle["positions"]) > 50:
                vehicle["positions"] = vehicle["positions"][-50:]
                vehicle["sizes"] = vehicle["sizes"][-50:]
                vehicle["confidences"] = vehicle["confidences"][-50:]
                vehicle["in_parking_history"] = vehicle["in_parking_history"][-50:]
        
        # Add current position to history for this vehicle
        self.vehicle_histories[tracking_id].append({
            "frame": self.frame_count,
            "position": detection["position"],
            "in_parking": detection["in_parking"]
        })
    
    def _update_line_crossings(self, detections):
        """Update line crossing counts for vehicles"""
        if not self.counting_lines:
            return
            
        # Process each vehicle
        for detection in detections:
            tracking_id = detection.get("tracking_id")
            
            if tracking_id is None or tracking_id not in self.tracked_vehicles:
                continue
                
            vehicle = self.tracked_vehicles[tracking_id]
            
            # Need at least two positions to detect crossing
            if len(vehicle["positions"]) < 2:
                continue
                
            # Get current and previous positions
            current_pos = vehicle["positions"][-1]
            prev_pos = vehicle["positions"][-2]
            
            # Check for each counting line
            for line in self.counting_lines:
                # Skip if already counted for this line
                if line["id"] in vehicle["crossed_lines"]:
                    continue
                    
                # Check if vehicle crossed this line
                line_points = line["points"]
                if self._line_crossing_check(prev_pos, current_pos, line_points[0], line_points[1]):
                    # Vehicle crossed the line!
                    vehicle["crossed_lines"].add(line["id"])
                    
                    # Update counts
                    vehicle_type = vehicle["class_name"]
                    if vehicle_type in line["counts"]:
                        line["counts"][vehicle_type] += 1
                    else:
                        line["counts"][vehicle_type] = 1
                        
                    line["total"] += 1
    
    def _line_crossing_check(self, p1, p2, line_p1, line_p2):
        """
        Check if line segment p1->p2 crosses line segment line_p1->line_p2
        Using line segment intersection formula
        """
        # Convert to numpy arrays for easier calculation
        p1 = np.array(p1)
        p2 = np.array(p2)
        line_p1 = np.array(line_p1)
        line_p2 = np.array(line_p2)
        
        # Line segment intersection check
        s1 = p2 - p1
        s2 = line_p2 - line_p1
        
        s = (-s1[1] * (p1[0] - line_p1[0]) + s1[0] * (p1[1] - line_p1[1])) / (-s2[0] * s1[1] + s1[0] * s2[1])
        t = ( s2[0] * (p1[1] - line_p1[1]) - s2[1] * (p1[0] - line_p1[0])) / (-s2[0] * s1[1] + s1[0] * s2[1])
        
        return (s >= 0 and s <= 1 and t >= 0 and t <= 1)
    
    def _get_parking_occupancy(self):
        """Get the current occupancy status of all parking areas"""
        parking_status = []
        
        for area in self.parking_areas:
            # Count vehicles in this parking area
            occupied = 0
            for vehicle in self.tracked_vehicles.values():
                # Check if vehicle's latest position is in this parking area
                if vehicle["in_parking_history"] and vehicle["in_parking_history"][-1] == area["id"]:
                    occupied += 1
            
            # Update area's occupied count
            area["occupied"] = occupied
            
            # Add status to result
            parking_status.append({
                "id": area["id"],
                "name": area["name"],
                "occupied": occupied,
                "capacity": area["capacity"],
                "occupancy_rate": (occupied / area["capacity"]) * 100 if area["capacity"] > 0 else 0
            })
        
        return parking_status
    
    def cleanup_tracking(self, max_frames_missing=30):
        """Remove tracked vehicles that haven't been seen for a while"""
        to_remove = []
        for vehicle_id, vehicle in self.tracked_vehicles.items():
            if self.frame_count - vehicle["last_seen"] > max_frames_missing:
                to_remove.append(vehicle_id)
                
        for vehicle_id in to_remove:
            # Log data before removing
            vehicle = self.tracked_vehicles[vehicle_id]
            
            # Calculate movement stats
            total_distance = 0
            avg_speed = 0
            
            if len(vehicle["positions"]) >= 2:
                for i in range(1, len(vehicle["positions"])):
                    prev_pos = vehicle["positions"][i-1]
                    curr_pos = vehicle["positions"][i]
                    distance = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                    total_distance += distance
                
                # Simple speed estimation (distance per frame)
                detection_frames = vehicle["last_seen"] - vehicle["first_seen"] + 1
                avg_speed = total_distance / detection_frames if detection_frames > 0 else 0
            
            # Determine parking status
            parked = False
            parking_area_id = None
            
            # If in parking for majority of detections
            parking_history = vehicle["in_parking_history"]
            if parking_history and any(p is not None for p in parking_history):
                # Count frames in parking
                parking_frames = sum(1 for p in parking_history if p is not None)
                parking_ratio = parking_frames / len(parking_history)
                
                if parking_ratio > 0.5:  # If in parking more than 50% of the time
                    parked = True
                    # Get most frequent parking area
                    parking_counts = {}
                    for p in parking_history:
                        if p is not None:
                            parking_counts[p] = parking_counts.get(p, 0) + 1
                    
                    # Find most common parking area
                    if parking_counts:
                        parking_area_id = max(parking_counts, key=parking_counts.get)
            
            vehicle_data = {
                "vehicle_id": vehicle_id,
                "class_name": vehicle["class_name"],
                "first_seen": vehicle["first_seen"],
                "last_seen": vehicle["last_seen"],
                "duration_frames": vehicle["last_seen"] - vehicle["first_seen"],
                "total_distance": total_distance,
                "avg_speed": avg_speed,
                "parked": parked,
                "parking_area_id": parking_area_id,
                "crossed_lines": list(vehicle["crossed_lines"])
            }
            self.detection_history.append(vehicle_data)
            
            # Remove tracking data
            del self.tracked_vehicles[vehicle_id]
            if vehicle_id in self.vehicle_histories:
                del self.vehicle_histories[vehicle_id]
    
    def annotate_frame(self, frame, detections=None, show_labels=True, show_tracks=True, show_parking=True, show_counting=True):
        """
        Draw bounding boxes, tracks, and other information on the frame.
        
        Args:
            frame: OpenCV image frame
            detections: Optional pre-computed detections, if None will run detection
            show_labels: Whether to show class labels
            show_tracks: Whether to show vehicle tracks
            show_parking: Whether to show parking areas
            show_counting: Whether to show counting lines
            
        Returns:
            Annotated frame
        """
        if detections is None:
            detections = self.detect(frame)
            
        annotated = frame.copy()
        
        # First draw parking areas
        if show_parking and self.parking_areas:
            for area in self.parking_areas:
                bbox = area["bbox"]
                
                # Determine color based on occupancy
                if area["capacity"] > 0:
                    occupancy_rate = (area["occupied"] / area["capacity"])
                    if occupancy_rate < 0.5:  # Less than 50% full
                        color = (0, 255, 0)  # Green
                    elif occupancy_rate < 0.9:  # Less than 90% full
                        color = (0, 165, 255)  # Orange
                    else:  # 90% or more full
                        color = (0, 0, 255)  # Red
                else:
                    color = (128, 128, 128)  # Gray for undefined capacity
                
                # Draw area rectangle
                cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                
                # Draw label with occupancy
                label = f"{area['name']}: {area['occupied']}"
                if area["capacity"] > 0:
                    label += f"/{area['capacity']}"
                
                cv2.putText(annotated, label, (bbox[0], bbox[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw counting lines
        if show_counting and self.counting_lines:
            for line in self.counting_lines:
                points = line["points"]
                
                # Draw line
                cv2.line(annotated, 
                         (points[0][0], points[0][1]), 
                         (points[1][0], points[1][1]), 
                         (255, 255, 255), 2)
                
                # Draw label with count
                mid_x = (points[0][0] + points[1][0]) // 2
                mid_y = (points[0][1] + points[1][1]) // 2
                label = f"{line['name']}: {line['total']}"
                
                # Draw text with background for better visibility
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(annotated, 
                             (mid_x - 5, mid_y - text_size[1] - 5),
                             (mid_x + text_size[0] + 5, mid_y + 5),
                             (0, 0, 0), -1)
                
                cv2.putText(annotated, label, (mid_x, mid_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw vehicle tracks if enabled
        if show_tracks:
            for vehicle_id, vehicle in self.tracked_vehicles.items():
                if len(vehicle["positions"]) < 2:
                    continue
                
                # Get track color based on vehicle class
                class_name = vehicle["class_name"]
                color = self.VEHICLE_COLORS.get(class_name, (255, 255, 255))  # White for unknown classes
                
                # Draw the track (last N positions)
                track_length = min(20, len(vehicle["positions"]))
                for i in range(1, track_length):
                    # Get current and previous positions
                    prev_pos = vehicle["positions"][-i]
                    curr_pos = vehicle["positions"][-(i+1)]
                    
                    # Draw line segment
                    cv2.line(annotated, 
                             (int(prev_pos[0]), int(prev_pos[1])), 
                             (int(curr_pos[0]), int(curr_pos[1])), 
                             color, 2)
        
        # Draw vehicles
        for detection in detections:
            box = detection["bbox"]
            class_name = detection["class_name"]
            tracking_id = detection["tracking_id"]
            confidence = detection["confidence"]
            
            # Get color based on vehicle class
            color = self.VEHICLE_COLORS.get(class_name, (255, 255, 255))  # White for unknown classes
            
            # Draw bounding box
            cv2.rectangle(annotated, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            if show_labels:
                label_text = f"{class_name} #{tracking_id}" if tracking_id else class_name
                label_text += f" {confidence:.2f}"
                
                # Draw label with background
                text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(annotated, 
                             (box[0], box[1] - text_size[1] - 10),
                             (box[0] + text_size[0], box[1]),
                             color, -1)
                             
                cv2.putText(annotated, label_text,
                           (box[0], box[1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw overall statistics
        stats = self.get_statistics()
        y_pos = 30
        
        # Draw title
        cv2.putText(annotated, "Vehicle Detection",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_pos += 30
        
        # Draw vehicle counts
        cv2.putText(annotated, f"Total Vehicles: {len(self.tracked_vehicles)}",
                   (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += 25
        
        # Show counts by type (limit to top 3 for space)
        sorted_counts = sorted(stats["current_stats"]["vehicle_counts"].items(), 
                              key=lambda x: x[1], reverse=True)
        
        for i, (vehicle_type, count) in enumerate(sorted_counts[:3]):
            color = self.VEHICLE_COLORS.get(vehicle_type, (255, 255, 255))
            cv2.putText(annotated, f"{vehicle_type}: {count}",
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_pos += 25
        
        return annotated
    
    def get_statistics(self):
        """
        Get vehicle detection statistics for the current session.
        
        Returns:
            Dictionary with vehicle detection statistics
        """
        # Clean up tracking data first
        self.cleanup_tracking()
        
        # Compute current statistics
        total_active_vehicles = len(self.tracked_vehicles)
        historical_vehicles = len(self.detection_history)
        total_vehicles = total_active_vehicles + historical_vehicles
        
        # Count vehicles by type
        vehicle_type_counts = defaultdict(int)
        for vehicle in self.tracked_vehicles.values():
            vehicle_type = vehicle["class_name"]
            vehicle_type_counts[vehicle_type] += 1
        
        # Calculate vehicle type distribution
        vehicle_distribution = {}
        if total_active_vehicles > 0:
            for vehicle_type, count in vehicle_type_counts.items():
                percentage = (count / total_active_vehicles) * 100
                vehicle_distribution[vehicle_type] = percentage
        
        # Get parking statistics
        parking_stats = self._get_parking_occupancy()
        
        # Get line crossing statistics
        line_stats = []
        for line in self.counting_lines:
            line_data = {
                "name": line["name"],
                "total": line["total"],
                "counts_by_type": dict(line["counts"])
            }
            line_stats.append(line_data)
        
        # Calculate speed statistics
        avg_speeds = {}
        speed_distributions = {}
        
        # Process tracked vehicles
        for vehicle in self.tracked_vehicles.values():
            if len(vehicle["positions"]) >= 2:
                # Calculate total distance and speed
                total_distance = 0
                for i in range(1, len(vehicle["positions"])):
                    prev_pos = vehicle["positions"][i-1]
                    curr_pos = vehicle["positions"][i]
                    distance = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                    total_distance += distance
                
                # Simple speed estimation (distance per frame)
                detection_frames = vehicle["last_seen"] - vehicle["first_seen"] + 1
                avg_speed = total_distance / detection_frames if detection_frames > 0 else 0
                
                # Update average speed for this vehicle type
                vehicle_type = vehicle["class_name"]
                if vehicle_type not in avg_speeds:
                    avg_speeds[vehicle_type] = []
                avg_speeds[vehicle_type].append(avg_speed)
        
        # Calculate average speeds by vehicle type
        avg_speed_by_type = {}
        for vehicle_type, speeds in avg_speeds.items():
            if speeds:
                avg_speed_by_type[vehicle_type] = sum(speeds) / len(speeds)
            else:
                avg_speed_by_type[vehicle_type] = 0
        
        # Generate statistics object
        stats = {
            "session_info": {
                "start_time": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_frames_processed": self.frame_count,
                "total_detections": self.total_detections
            },
            "current_stats": {
                "active_vehicles": total_active_vehicles,
                "vehicle_counts": dict(vehicle_type_counts),
                "vehicle_distribution": vehicle_distribution,
                "parking": parking_stats,
                "line_counts": line_stats,
                "avg_speed_by_type": avg_speed_by_type
            },
            "historical_stats": {
                "total_vehicles": total_vehicles,
                "historical_vehicles": historical_vehicles
            },
            "time_period_stats": self.time_period_stats
        }
        
        return stats
    
    def save_analytics(self, output_path="vehicle_detection_analytics.json"):
        """Save analytics data to a JSON file"""
        stats = self.get_statistics()
        
        # Add vehicle tracking data
        all_vehicle_data = []
        
        # Add historical vehicles
        all_vehicle_data.extend(self.detection_history)
        
        # Add current active vehicles
        for vehicle_id, vehicle in self.tracked_vehicles.items():
            # Calculate movement stats
            total_distance = 0
            avg_speed = 0
            
            if len(vehicle["positions"]) >= 2:
                for i in range(1, len(vehicle["positions"])):
                    prev_pos = vehicle["positions"][i-1]
                    curr_pos = vehicle["positions"][i]
                    distance = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                    total_distance += distance
                
                # Simple speed estimation
                detection_frames = vehicle["last_seen"] - vehicle["first_seen"] + 1
                avg_speed = total_distance / detection_frames if detection_frames > 0 else 0
            
            # Determine parking status
            parked = False
            parking_area_id = None
            
            # If in parking for majority of detections
            parking_history = vehicle["in_parking_history"]
            if parking_history and any(p is not None for p in parking_history):
                # Count frames in parking
                parking_frames = sum(1 for p in parking_history if p is not None)
                parking_ratio = parking_frames / len(parking_history)
                
                if parking_ratio > 0.5:  # If in parking more than 50% of the time
                    parked = True
                    # Get most frequent parking area
                    parking_counts = {}
                    for p in parking_history:
                        if p is not None:
                            parking_counts[p] = parking_counts.get(p, 0) + 1
                    
                    # Find most common parking area
                    if parking_counts:
                        parking_area_id = max(parking_counts, key=parking_counts.get)
            
            vehicle_data = {
                "vehicle_id": vehicle_id,
                "class_name": vehicle["class_name"],
                "first_seen": vehicle["first_seen"],
                "last_seen": vehicle["last_seen"],
                "duration_frames": vehicle["last_seen"] - vehicle["first_seen"],
                "total_distance": total_distance,
                "avg_speed": avg_speed,
                "parked": parked,
                "parking_area_id": parking_area_id,
                "crossed_lines": list(vehicle["crossed_lines"])
            }
            all_vehicle_data.append(vehicle_data)
        
        stats["vehicle_details"] = all_vehicle_data
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Vehicle detection analytics saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving vehicle detection analytics: {str(e)}")
            return False
    
    def estimate_parking_capacity(self):
        """Estimate parking capacity based on current vehicle sizes"""
        if not self.parking_areas or not self.tracked_vehicles:
            return
        
        # Get average vehicle size
        vehicle_sizes = []
        for vehicle in self.tracked_vehicles.values():
            if vehicle["sizes"]:
                vehicle_sizes.append(np.mean(vehicle["sizes"]))
        
        if not vehicle_sizes:
            return
        
        avg_vehicle_size = np.mean(vehicle_sizes)
        
        # Add some margin for spaces between vehicles
        vehicle_size_with_margin = avg_vehicle_size * 1.2
        
        # Estimate capacity for each parking area
        for area in self.parking_areas:
            bbox = area["bbox"]
            area_width = bbox[2] - bbox[0]
            area_height = bbox[3] - bbox[1]
            area_size = area_width * area_height
            
            # Estimate how many vehicles can fit
            estimated_capacity = int(area_size / vehicle_size_with_margin)
            
            # Update the area's capacity
            area["capacity"] = max(1, estimated_capacity)  # Minimum capacity of 1
            
            print(f"Estimated capacity for {area['name']}: {area['capacity']} vehicles")

# Usage example
if __name__ == "__main__":
    # Check if video path is provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = 0  # Use default camera
    
    # Initialize detector
    detector = VehicleDetector()
    
    # Add a sample parking area if using a default video
    if video_path != 0:
        # We'll add a sample parking area - this should be adapted to your specific video
        detector.add_parking_area(100, 100, 500, 400, "Parking Lot A")
        
        # Add a counting line
        detector.add_counting_line(0, 300, 640, 300, "Horizontal Line")
    
    # Open video capture
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video source {video_path}")
        exit()
    
    # Get video dimensions for ROI selection
    ret, first_frame = cap.read()
    if not ret:
        print("Failed to read first frame")
        exit()
    
    frame_height, frame_width = first_frame.shape[:2]
    
    # Process video frames
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process every other frame for speed
        if frame_count % 2 == 0:
            # Detect vehicles
            detections = detector.detect(frame)
            
            # Annotate frame
            annotated_frame = detector.annotate_frame(frame, detections)
            
            # Display result
            cv2.imshow("Vehicle Detection", annotated_frame)
        
        frame_count += 1
        
        # Handle key press
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
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    
    # Save statistics
    detector.save_analytics("vehicle_detection_analytics.json")
    print("Final vehicle detection statistics:")
    print(json.dumps(detector.get_statistics(), indent=2))
import cv2
import numpy as np
from ultralytics import YOLO
import datetime
import os
import json

class GeneralObjectDetector:
    def __init__(self, model_path=None, confidence_threshold=0.5):
        """Initialize the general object detection service"""
        # Set up model path
        if model_path is None:
            project_root = self._get_project_root()
            models_dir = os.path.join(project_root, 'training_models')
            os.makedirs(models_dir, exist_ok=True)
            model_path = os.path.join(models_dir, 'yolov8x.pt')  # Using YOLOv8x for best detection quality

        # Load the model
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        
        # Store detection history
        self.detections = []
        self.detection_counts = {}
        self.tracked_objects = {}
        
        # Analysis
        self.total_frames_processed = 0
        self.last_analysis_time = datetime.datetime.now()
        
        # COCO class names (80 classes)
        self.class_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 
                           'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 
                           'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 
                           'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 
                           'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 
                           'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
                           'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
                           'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 
                           'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 
                           'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
    
    def _get_project_root(self):
        """Get project root directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to project root (assuming this file is in services/)
        project_root = os.path.dirname(current_dir)
        return project_root
        
    def detect(self, frame, classes=None):
        """Detect objects in frame"""
        # Run detection with YOLO
        results = self.model(
            frame, 
            conf=self.confidence_threshold,
            classes=classes  # Filter for specific classes if provided
        )
        
        # Process detections
        current_detections = []
        current_time = datetime.datetime.now()
        
        if results and len(results) > 0:
            result = results[0]
            
            for i, (box, conf, cls) in enumerate(zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls)):
                # Extract coordinates
                x1, y1, x2, y2 = map(int, box.tolist())
                
                # Get class information
                class_id = int(cls.item())
                class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                
                # Update class counts
                if class_name not in self.detection_counts:
                    self.detection_counts[class_name] = 0
                self.detection_counts[class_name] += 1
                
                # Create detection object
                detection = {
                    'id': f"detection_{len(self.detections) + i + 1}",
                    'bbox': (x1, y1, x2, y2),
                    'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                    'area': (x2 - x1) * (y2 - y1),
                    'confidence': conf.item(),
                    'class_id': class_id,
                    'class_name': class_name,
                    'timestamp': current_time.isoformat(),
                    'frame_id': self.total_frames_processed
                }
                
                current_detections.append(detection)
                self.detections.append(detection)
                
                # Simple object tracking based on class and position
                object_key = f"{class_name}_{len(self.tracked_objects)}"
                if class_name in self.tracked_objects:
                    # Check if this detection matches any existing tracked object
                    matched = False
                    for obj_id, obj in self.tracked_objects.items():
                        if obj['class_name'] == class_name:
                            prev_x, prev_y = obj['last_position']
                            curr_x, curr_y = detection['center']
                            # Calculate distance between current and last position
                            distance = np.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
                            # If close enough, consider it the same object
                            if distance < 100:  # Threshold in pixels
                                self.tracked_objects[obj_id]['detection_count'] += 1
                                self.tracked_objects[obj_id]['last_position'] = detection['center']
                                self.tracked_objects[obj_id]['last_seen'] = current_time
                                detection['track_id'] = obj_id
                                matched = True
                                break
                    
                    if not matched:
                        # New object
                        object_key = f"{class_name}_{len(self.tracked_objects)}"
                        self.tracked_objects[object_key] = {
                            'class_name': class_name,
                            'first_seen': current_time,
                            'last_seen': current_time,
                            'last_position': detection['center'],
                            'detection_count': 1,
                            'confidence': conf.item()
                        }
                        detection['track_id'] = object_key
                else:
                    # First instance of this class
                    self.tracked_objects[object_key] = {
                        'class_name': class_name,
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'last_position': detection['center'],
                        'detection_count': 1,
                        'confidence': conf.item()
                    }
                    detection['track_id'] = object_key
        
        # Limit detection history
        if len(self.detections) > 1000:
            self.detections = self.detections[-1000:]
            
        self.total_frames_processed += 1
        return current_detections
    
    def annotate_frame(self, frame, detections=None):
        """Annotate frame with detection results"""
        if detections is None:
            detections = self.detect(frame)
            
        annotated_frame = frame.copy()
        
        # Create color map for different classes
        color_map = {}
        
        # Draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Generate a consistent color for each class
            if class_name not in color_map:
                # Generate a random color (but consistent for the same class)
                hue = hash(class_name) % 360
                # HSV to RGB conversion for vibrant colors
                h = hue / 360.0
                s = 0.9
                v = 0.9
                
                # HSV to RGB conversion
                if s == 0.0:
                    r = g = b = v
                else:
                    h *= 6.0
                    i = int(h)
                    f = h - i
                    p = v * (1.0 - s)
                    q = v * (1.0 - s * f)
                    t = v * (1.0 - s * (1.0 - f))
                    
                    if i == 0:
                        r, g, b = v, t, p
                    elif i == 1:
                        r, g, b = q, v, p
                    elif i == 2:
                        r, g, b = p, v, t
                    elif i == 3:
                        r, g, b = p, q, v
                    elif i == 4:
                        r, g, b = t, p, v
                    else:
                        r, g, b = v, p, q
                        
                color_map[class_name] = (int(b*255), int(g*255), int(r*255))
            
            color = color_map[class_name]
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Add label with class and confidence
            label = f"{class_name}: {confidence:.2f}"
            label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            y1 = max(y1, label_size[1])
            
            # Create filled rectangle for text background
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
            
            # Add text
            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Add tracking ID if available
            if 'track_id' in detection:
                track_label = f"ID: {detection['track_id'].split('_')[-1]}"
                cv2.putText(annotated_frame, track_label, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add summary stats
        total_objects = len(detections)
        if total_objects > 0:
            # Get top 3 most common objects
            class_count = {}
            for det in detections:
                cls = det['class_name']
                if cls not in class_count:
                    class_count[cls] = 0
                class_count[cls] += 1
                
            # Sort by count
            sorted_classes = sorted(class_count.items(), key=lambda x: x[1], reverse=True)
            top_classes = sorted_classes[:3]
            
            # Create summary text
            summary = f"Objects: {total_objects} | "
            summary += " | ".join([f"{cls}: {count}" for cls, count in top_classes])
            
            # Add to frame
            cv2.putText(annotated_frame, summary, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
            cv2.putText(annotated_frame, summary, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated_frame
    
    def get_statistics(self):
        """Get detection statistics"""
        # Cleanup old tracked objects
        current_time = datetime.datetime.now()
        for obj_id in list(self.tracked_objects.keys()):
            obj = self.tracked_objects[obj_id]
            last_seen = datetime.datetime.fromisoformat(obj['last_seen'].isoformat())
            if (current_time - last_seen).total_seconds() > 60:  # Remove if not seen for 60 seconds
                self.tracked_objects.pop(obj_id, None)
        
        # Calculate statistics
        class_counts = {}
        for cls, count in self.detection_counts.items():
            if count > 0:
                class_counts[cls] = count
                
        # Calculate currently visible objects
        visible_objects = {}
        for det in self.detections[-30:]:  # Consider last 30 detections as "currently visible"
            cls = det['class_name']
            if cls not in visible_objects:
                visible_objects[cls] = 0
            visible_objects[cls] += 1
        
        return {
            'total_frames_processed': self.total_frames_processed,
            'total_detections': len(self.detections),
            'detection_counts': class_counts,
            'tracked_objects': len(self.tracked_objects),
            'currently_visible': visible_objects
        }
    
    def export_data(self, format='json'):
        """Export detection data"""
        if format == 'json':
            data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'statistics': self.get_statistics(),
                'recent_detections': self.detections[-50:] if self.detections else [],
                'object_tracks': {k: v for k, v in self.tracked_objects.items() if isinstance(v.get('last_seen'), datetime.datetime)},
            }
            
            # Convert datetime objects to strings for JSON serialization
            for obj_id, obj in data['object_tracks'].items():
                obj['first_seen'] = obj['first_seen'].isoformat()
                obj['last_seen'] = obj['last_seen'].isoformat()
            
            return data
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def save_analytics(self, output_path=None):
        """Save analytics data to file"""
        if output_path is None:
            # Create default output directory if it doesn't exist
            os.makedirs('object_detection_analytics', exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'object_detection_analytics/detection_data_{timestamp}.json'
        
        # Export data and save to file
        data = self.export_data(format='json')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
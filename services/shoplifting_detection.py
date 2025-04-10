import cv2
import numpy as np
from ultralytics import YOLO
import datetime
import json
import os

class ShopliftingDetector:
    def __init__(self, model_path=None, confidence_threshold=0.5):
        """Initialize the shoplifting detection service"""
        # Set up model path
        if model_path is None:
            project_root = self._get_project_root()
            models_dir = os.path.join(project_root, 'training_models')
            model_path = os.path.join(models_dir, 'shoplifting_detector.pt')
            
            # If model doesn't exist, use YOLOv8 base model as fallback
            if not os.path.exists(model_path):
                model_path = os.path.join(models_dir, 'yolov8s.pt')
                print(f"Shoplifting model not found, using base model: {model_path}")
        
        # Load the model
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        
        # Store detection history
        self.detections = []
        self.alerts = []
        
        # Class mapping
        self.class_names = ['normal', 'shoplifting']
        
        # Initialize analytics
        self.last_analysis_time = datetime.datetime.now()
        self.total_frames_processed = 0
        self.detection_counts = {class_name: 0 for class_name in self.class_names}
        
        # Alert configuration
        self.alert_cooldown = 10  # seconds between alerts
        self.last_alert_time = None
    
    def _get_project_root(self):
        """Get project root directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to project root (assuming this file is in services/)
        project_root = os.path.dirname(current_dir)
        return project_root
        
    def detect(self, frame):
        """Detect shoplifting behavior in the frame"""
        # Run model on frame
        results = self.model(frame, conf=self.confidence_threshold)
        
        # Process detections
        current_detections = []
        current_time = datetime.datetime.now()
        
        if results and len(results) > 0:
            # Get the first result
            result = results[0]
            
            # Process each detection
            for i, (box, conf, cls) in enumerate(zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls)):
                if conf >= self.confidence_threshold:
                    # Extract bounding box coordinates
                    x1, y1, x2, y2 = box.tolist()
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    
                    # Get class information
                    class_id = int(cls.item())
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                    
                    # Create detection record
                    detection = {
                        'id': f"detection_{len(self.detections) + i + 1}",
                        'bbox': (x1, y1, x2, y2),
                        'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                        'confidence': conf.item(),
                        'class_id': class_id,
                        'class_name': class_name,
                        'timestamp': current_time.isoformat(),
                        'frame_id': self.total_frames_processed
                    }
                    
                    current_detections.append(detection)
                    self.detections.append(detection)
                    self.detection_counts[class_name] += 1
                    
                    # Create alert for shoplifting behaviors
                    if class_name == 'shoplifting' and conf.item() >= self.confidence_threshold:
                        # Check if we're in cooldown period
                        if self.last_alert_time is None or \
                           (current_time - self.last_alert_time).total_seconds() > self.alert_cooldown:
                            alert = {
                                'id': f"alert_{len(self.alerts) + 1}",
                                'type': 'SHOPLIFTING_DETECTED',
                                'confidence': conf.item(),
                                'bbox': (x1, y1, x2, y2),
                                'timestamp': current_time.isoformat(),
                                'frame_id': self.total_frames_processed,
                                'severity': 'HIGH' if conf.item() > 0.75 else 'MEDIUM'
                            }
                            self.alerts.append(alert)
                            self.last_alert_time = current_time
        
        # Limit history to recent items only
        if len(self.detections) > 1000:
            self.detections = self.detections[-1000:]
            
        self.total_frames_processed += 1
        return current_detections
        
    def annotate_frame(self, frame, detections=None):
        """Annotate frame with detection results"""
        # If detections are not provided, run detection
        if detections is None:
            detections = self.detect(frame)
            
        annotated_frame = frame.copy()
        
        # Draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Choose color based on class (red for shoplifting, green for normal)
            if class_name == 'shoplifting':
                color = (0, 0, 255)  # Red for shoplifting
                thickness = 3        # Thicker lines for shoplifting
            else:
                color = (0, 255, 0)  # Green for normal behavior
                thickness = 2        # Normal lines for normal behavior
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Add label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add alert notification if there are recent alerts
        if self.alerts and (datetime.datetime.now() - datetime.datetime.fromisoformat(self.alerts[-1]['timestamp'])).total_seconds() < 5:
            # Add red alert banner
            cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], 40), (0, 0, 255), -1)
            cv2.putText(annotated_frame, "ALERT: Shoplifting Behavior Detected!", 
                       (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add statistics
        stats = self.get_statistics()
        stats_text = f"Normal: {stats['detection_counts']['normal']} | Shoplifting: {stats['detection_counts']['shoplifting']} | Alerts: {len(self.alerts)}"
        cv2.putText(annotated_frame, stats_text, (10, frame.shape[0]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated_frame
    
    def get_recent_alerts(self, max_age_seconds=3600):
        """Get recent alerts within the specified time window"""
        current_time = datetime.datetime.now()
        recent_alerts = []
        
        for alert in self.alerts:
            alert_time = datetime.datetime.fromisoformat(alert['timestamp'])
            if (current_time - alert_time).total_seconds() <= max_age_seconds:
                recent_alerts.append(alert)
                
        return recent_alerts
    
    def get_statistics(self):
        """Get detection statistics"""
        return {
            'total_frames_processed': self.total_frames_processed,
            'total_detections': len(self.detections),
            'detection_counts': self.detection_counts,
            'total_alerts': len(self.alerts),
            'recent_alerts': len(self.get_recent_alerts(max_age_seconds=300))  # Alerts in last 5 minutes
        }
    
    def export_data(self, format='json'):
        """Export detection data"""
        if format == 'json':
            data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'statistics': self.get_statistics(),
                'recent_detections': self.detections[-50:] if self.detections else [],
                'alerts': self.get_recent_alerts(),
                'class_distribution': {
                    class_name: count / max(1, len(self.detections)) 
                    for class_name, count in self.detection_counts.items()
                }
            }
            
            return data
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def save_analytics(self, output_path=None):
        """Save analytics data to file"""save_analytics
        if output_path is None:
            # Create default output directory if it doesn't exist
            os.makedirs('shoplifting_analytics', exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'shoplifting_analytics/detection_data_{timestamp}.json'
        
        # Export data and save to file
        data = self.export_data(format='json')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
import cv2
import numpy as np
import json
import os
from collections import defaultdict
import datetime
from ultralytics import YOLO
import supervision as sv

class PersonTracker:
    def __init__(self, frame_resolution=(1920, 1080), confidence_threshold=0.5, zones=None):
        # Set up a central models directory, two levels up from the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'training_models') # two levels up
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, 'yolov8x.pt')
        
        # Download the model if it doesn't exist
        if not os.path.exists(model_path):
            print(f"Downloading YOLOv8x model to {model_path}...")
            YOLO('yolov8x.pt').save(model_path)
            print("Download complete.")

        # Initialize YOLO model for person detection
        self.model = YOLO(model_path)

        # Initialize tracker
        self.tracker = sv.ByteTrack()

        # Store tracking history
        self.tracks = defaultdict(list)
        self.frame_resolution = frame_resolution
        
        # New parameters
        self.confidence_threshold = confidence_threshold
        self.zones = zones or {}  # Format: {'zone_name': polygon_coordinates}
        self.zone_counts = defaultdict(int)
        self.zone_visits = defaultdict(set)  # Track unique visitors per zone

        # Initialize statistics
        self.reset_statistics()
        
    def reset_statistics(self):
        """Reset tracking statistics"""
        self.total_detections = 0
        self.active_tracks = set()
        self.zone_counts = defaultdict(int)
        self.zone_visits = defaultdict(set)

    def update(self, frame):
        """Process a new frame and update tracking"""
        # Run YOLO detection
        results = self.model(frame, classes=[0])  # class 0 is person

        # Get detections in supervision format - updated for newer supervision versions
        detections = sv.Detections.from_ultralytics(results[0])
    
        # Apply confidence threshold
        mask = detections.confidence >= self.confidence_threshold
        detections = detections[mask]

        # Update tracking
        detections = self.tracker.update_with_detections(detections)

        # Update tracking history
        self._update_tracks(detections)
        
        # Update zone analysis
        self._update_zones(detections)

        return detections

    def _update_tracks(self, detections):
        """Update tracking history"""
        timestamp = datetime.datetime.now()

        for det, track_id in zip(detections.xyxy, detections.tracker_id):
            if track_id < 0:
                continue

            # Calculate center point
            center_x = (det[0] + det[2]) / 2
            center_y = (det[1] + det[3]) / 2

            # Store track data
            self.tracks[track_id].append({
                'position': (center_x, center_y),
                'timestamp': timestamp,
                'bbox': det.tolist()
            })

            # Update statistics
            self.total_detections += 1
            self.active_tracks.add(track_id)
    
    def _update_zones(self, detections):
        """Update zone-based analysis"""
        if not self.zones:
            return
            
        for det, track_id in zip(detections.xyxy, detections.tracker_id):
            if track_id < 0:
                continue
                
            # Calculate center point
            center_x = (det[0] + det[2]) / 2
            center_y = (det[1] + det[3]) / 2
            point = (center_x, center_y)
            
            # Check which zone the point is in
            for zone_name, polygon in self.zones.items():
                if self._point_in_polygon(point, polygon):
                    self.zone_counts[zone_name] += 1
                    self.zone_visits[zone_name].add(track_id)  # Track unique visits

    def _point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    def get_tracks(self, min_length=5):
        """Get all tracks with minimum length"""
        return {
            track_id: positions
            for track_id, positions in self.tracks.items()
            if len(positions) >= min_length
        }

    def get_active_tracks(self):
        """Get currently active tracks"""
        current_time = datetime.datetime.now()
        active_tracks = {}

        for track_id, positions in self.tracks.items():
            if positions:
                last_seen = positions[-1]['timestamp']
                if (current_time - last_seen).total_seconds() < 5:  # Active in last 5 seconds
                    active_tracks[track_id] = positions

        return active_tracks

    def clear_old_tracks(self, max_age_seconds=3600):
        """Clear old tracking data"""
        current_time = datetime.datetime.now()
        for track_id in list(self.tracks.keys()):
            if len(self.tracks[track_id]) > 0:
                age = (current_time - self.tracks[track_id][-1]['timestamp']).total_seconds()
                if age > max_age_seconds:
                    del self.tracks[track_id]
                    if track_id in self.active_tracks:
                        self.active_tracks.remove(track_id)

    def get_statistics(self):
        """Get current tracking statistics"""
        stats = {
            'total_detections': self.total_detections,
            'active_tracks': len(self.active_tracks),
            'total_tracks': len(self.tracks)
        }
        
        # Add zone statistics
        if self.zones:
            stats['zones'] = {
                zone_name: {
                    'unique_visitors': len(visitors),
                    'total_detections': self.zone_counts[zone_name]
                }
                for zone_name, visitors in self.zone_visits.items()
            }
        
        return stats
    
    def annotate_frame(self, frame, detections):
        """Annotate frame with bounding boxes, IDs and movement traces"""
        # Make a copy of the frame
        annotated_frame = frame.copy()
        
        # Draw bounding boxes and IDs manually
        if hasattr(detections, 'xyxy') and detections.xyxy is not None:
            for i, bbox in enumerate(detections.xyxy):
                # Convert to integers
                x1, y1, x2, y2 = map(int, bbox)
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Add ID text if available
                if hasattr(detections, 'tracker_id') and detections.tracker_id is not None and i < len(detections.tracker_id):
                    tracker_id = detections.tracker_id[i]
                    if tracker_id is not None:
                        cv2.putText(annotated_frame, f"ID: {tracker_id}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw zones
        if self.zones:
            for zone_name, polygon in self.zones.items():
                points = np.array(polygon, dtype=np.int32)
                cv2.polylines(annotated_frame, [points], True, (0, 255, 0), 2)
                
                # Add zone name and count
                count = len(self.zone_visits[zone_name])
                center_x = sum(p[0] for p in polygon) // len(polygon)
                center_y = sum(p[1] for p in polygon) // len(polygon)
                cv2.putText(annotated_frame, f"{zone_name}: {count}", (center_x, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
        return annotated_frame
    
    def export_tracking_data(self, format='json'):
        """Export tracking data for visualization"""
        if format == 'json':
            # Convert to serializable format
            export_data = {
                'tracks': {},
                'zones': {},
                'statistics': self.get_statistics()
            }
            
            # Process tracks
            for track_id, positions in self.tracks.items():
                export_data['tracks'][str(track_id)] = [
                    {
                        'position': pos['position'],
                        'timestamp': pos['timestamp'].isoformat(),
                        'bbox': pos['bbox']
                    }
                    for pos in positions
                ]
            
            # Process zone data
            export_data['zones'] = {
                zone_name: {
                    'visits': len(visitors),
                    'total_detections': self.zone_counts[zone_name]
                }
                for zone_name, visitors in self.zone_visits.items()
            }
            
            return export_data
        
        elif format == 'csv':
            # Prepare CSV format data
            rows = []
            header = ['track_id', 'timestamp', 'x', 'y', 'zone']
            
            for track_id, positions in self.tracks.items():
                for pos in positions:
                    x, y = pos['position']
                    timestamp = pos['timestamp'].isoformat()
                    
                    # Determine zone
                    current_zone = "unknown"
                    for zone_name, polygon in self.zones.items():
                        if self._point_in_polygon((x, y), polygon):
                            current_zone = zone_name
                            break
                    
                    rows.append([track_id, timestamp, x, y, current_zone])
            
            return header, rows
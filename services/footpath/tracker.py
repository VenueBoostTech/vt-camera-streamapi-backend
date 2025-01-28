import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict
import datetime

class PersonTracker:
    def __init__(self, frame_resolution=(1920, 1080)):
        # Initialize YOLO model for person detection
        self.model = YOLO('yolov8x.pt')

        # Initialize tracker
        self.tracker = sv.ByteTrack()

        # Store tracking history
        self.tracks = defaultdict(list)
        self.frame_resolution = frame_resolution

        # Initialize statistics
        self.reset_statistics()

    def reset_statistics(self):
        """Reset tracking statistics"""
        self.total_detections = 0
        self.active_tracks = set()

    def update(self, frame):
        """Process a new frame and update tracking"""
        # Run YOLO detection
        results = self.model(frame, classes=[0])  # class 0 is person

        # Get detections in supervision format
        detections = sv.Detections.from_yolov8(results[0])

        # Update tracking
        detections = self.tracker.update_with_detections(detections)

        # Update tracking history
        self._update_tracks(detections)

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
        return {
            'total_detections': self.total_detections,
            'active_tracks': len(self.active_tracks),
            'total_tracks': len(self.tracks)
        }
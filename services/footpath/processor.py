import cv2
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from models.camera import Camera
from models.footpath import FootpathAnalytics, FootpathPattern
from .tracker import PersonTracker
from .analyzer import FootpathAnalyzer

class CameraProcessor:
    def __init__(self, camera: Camera, db: Session):
        self.camera = camera
        self.db = db
        self.frame_resolution = None

        # Initialize tracker and analyzer
        self.tracker = None
        self.analyzer = None

        # Initialize processing state
        self.last_analytics_save = datetime.now()
        self.last_pattern_analysis = datetime.now()
        self.is_processing = False

    def start_processing(self):
        """Start camera processing"""
        if self.is_processing:
            return

        # Open video stream
        cap = cv2.VideoCapture(self.camera.rtsp_url)
        if not cap.isOpened():
            raise Exception(f"Could not open camera stream: {self.camera.rtsp_url}")

        # Get frame resolution
        ret, frame = cap.read()
        if not ret:
            raise Exception("Could not read frame from camera")

        self.frame_resolution = frame.shape[:2]

        # Initialize tracker and analyzer
        self.tracker = PersonTracker(self.frame_resolution)
        self.analyzer = FootpathAnalyzer(
            self.frame_resolution,
            self.camera.zone.polygon if self.camera.zone else None
        )

        self.is_processing = True

        try:
            while self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    break

                # Process frame
                self.process_frame(frame)

                # Periodic tasks
                current_time = datetime.now()

                # Save analytics every 5 minutes
                if (current_time - self.last_analytics_save).total_seconds() >= 300:
                    self.save_analytics()
                    self.last_analytics_save = current_time

                # Analyze patterns every 15 minutes
                if (current_time - self.last_pattern_analysis).total_seconds() >= 900:
                    self.analyze_patterns()
                    self.last_pattern_analysis = current_time

                # Clean up old tracks every hour
                if (current_time - self.last_cleanup).total_seconds() >= 3600:
                    self.cleanup()
                    self.last_cleanup = current_time

        finally:
            cap.release()
            self.is_processing = False

    def stop_processing(self):
        """Stop camera processing"""
        self.is_processing = False

    def process_frame(self, frame):
        """Process a single frame"""
        # Update tracking
        detections = self.tracker.update(frame)

        # Get current tracks
        tracks = self.tracker.get_tracks()

        # Update analytics
        self.analyzer.analyze_tracks(tracks)

        return detections

    def save_analytics(self):
        """Save current analytics to database"""
        if not self.camera.zone:
            return

        # Get analytics data
        analytics_data = self.analyzer.get_analytics()

        # Create analytics entry
        analytics = FootpathAnalytics(
            zone_id=self.camera.zone.id,
            business_id=self.camera.business_id,
            property_id=self.camera.property_id,
            traffic_count=self.tracker.total_detections,
            unique_visitors=analytics_data['unique_visitors'],
            avg_dwell_time=analytics_data['avg_dwell_time'],
            max_dwell_time=analytics_data['max_dwell_time'],
            total_dwell_time=analytics_data['total_dwell_time'],
            heatmap_data=self.analyzer.get_heatmap().tolist()
        )

        self.db.add(analytics)
        self.db.commit()

        # Reset analytics state
        self.analyzer.reset()
        self.tracker.reset_statistics()

    def analyze_patterns(self):
        """Analyze and save movement patterns"""
        if not self.camera.zone:
            return

        # Find patterns
        patterns = self.analyzer.find_patterns()

        if patterns:
            # Create pattern entry
            pattern = FootpathPattern(
                zone_id=self.camera.zone.id,
                business_id=self.camera.business_id,
                property_id=self.camera.property_id,
                pattern_type='movement_clusters',
                pattern_data={'patterns': patterns},
                frequency=len(patterns),
                confidence=0.8  # Could be calculated based on cluster metrics
            )

            self.db.add(pattern)
            self.db.commit()

    def cleanup(self):
        """Clean up resources and old data"""
        if self.tracker:
            self.tracker.clear_old_tracks()

    def get_current_statistics(self) -> dict:
        """Get current processing statistics"""
        if not self.tracker or not self.analyzer:
            return {
                "status": "not_initialized",
                "camera_id": self.camera.id
            }

        tracking_stats = self.tracker.get_statistics()
        analytics_stats = self.analyzer.get_analytics()

        return {
            "status": "active" if self.is_processing else "stopped",
            "camera_id": self.camera.id,
            "tracking": tracking_stats,
            "analytics": analytics_stats,
            "last_analytics_save": self.last_analytics_save.isoformat(),
            "last_pattern_analysis": self.last_pattern_analysis.isoformat()
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_processing()
        if self.tracker:
            self.cleanup()
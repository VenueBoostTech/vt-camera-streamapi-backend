import cv2
import numpy as np
from sqlalchemy.orm import Session
import datetime
import time
import traceback
from typing import Optional, Dict, Any
from models.camera import Camera
from models.footpath import FootpathAnalytics, FootpathPattern
from services.monitoring.logger import monitor
from .tracker import PersonTracker
from .analyzer import FootpathAnalyzer

class CameraProcessor:
    def __init__(self, camera: Camera, db: Session):
        """Initialize camera processor"""
        self.camera = camera
        self.db = db
        self.frame_resolution = None

        # Initialize tracker and analyzer
        self.tracker = None
        self.analyzer = None

        # Initialize processing state
        self.last_analytics_save = datetime.datetime.now()
        self.last_pattern_analysis = datetime.datetime.now()
        self.last_cleanup = datetime.datetime.now()
        self.is_processing = False
        self.total_frames_processed = 0
        self.processing_times = []

        # Initialize monitoring
        self.monitor = monitor
        self.monitor.log_camera_status(
            camera_id=camera.id,
            business_id=camera.business_id,
            status="initialized"
        )

    def start_processing(self):
        """Start camera processing"""
        if self.is_processing:
            return

        try:
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
            self.monitor.log_camera_status(
                camera_id=self.camera.id,
                business_id=self.camera.business_id,
                status="active"
            )

            while self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    self.monitor.log_error(
                        camera_id=self.camera.id,
                        error_type="frame_read_error",
                        error_msg="Failed to read frame from camera"
                    )
                    break

                # Process frame
                self.process_frame(frame)
                self.total_frames_processed += 1

                # Periodic tasks
                current_time = datetime.datetime.now()

                # Save analytics every 5 minutes
                if (current_time - self.last_analytics_save).total_seconds() >= 300:
                    self.save_analytics()
                    self.last_analytics_save = current_time

                # Analyze patterns every 15 minutes
                if (current_time - self.last_pattern_analysis).total_seconds() >= 900:
                    self.analyze_patterns()
                    self.last_pattern_analysis = current_time

                # Cleanup every hour
                if (current_time - self.last_cleanup).total_seconds() >= 3600:
                    self.cleanup()
                    self.last_cleanup = current_time

        except Exception as e:
            self.monitor.log_error(
                camera_id=self.camera.id,
                error_type="processing_error",
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )
            raise
        finally:
            cap.release()
            self.is_processing = False
            self.monitor.log_camera_status(
                camera_id=self.camera.id,
                business_id=self.camera.business_id,
                status="stopped"
            )

    def stop_processing(self):
        """Stop camera processing"""
        self.is_processing = False

    def process_frame(self, frame) -> dict:
        """Process a single frame"""
        start_time = time.time()

        try:
            # Update tracking
            detections = self.tracker.update(frame)

            # Get current tracks
            tracks = self.tracker.get_tracks()

            # Update analytics
            self.analyzer.analyze_tracks(tracks)

            # Calculate and log processing time
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            self.monitor.log_processing_time(self.camera.id, processing_time)

            # Log analytics data
            if tracks:
                analytics_data = self.analyzer.get_analytics()
                self.monitor.log_analytics(
                    camera_id=self.camera.id,
                    zone_id=self.camera.zone.id if self.camera.zone else "no_zone",
                    analytics_data=analytics_data
                )

            return {
                "detections": detections,
                "tracks": len(tracks),
                "processing_time": processing_time
            }

        except Exception as e:
            self.monitor.log_error(
                camera_id=self.camera.id,
                error_type="frame_processing_error",
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )
            raise

    def save_analytics(self):
        """Save current analytics to database"""
        if not self.camera.zone:
            return

        try:
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

        except Exception as e:
            self.monitor.log_error(
                camera_id=self.camera.id,
                error_type="analytics_save_error",
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )
            self.db.rollback()

    def analyze_patterns(self):
        """Analyze and save movement patterns"""
        if not self.camera.zone:
            return

        try:
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

        except Exception as e:
            self.monitor.log_error(
                camera_id=self.camera.id,
                error_type="pattern_analysis_error",
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )
            self.db.rollback()

    def cleanup(self):
        """Clean up resources and old data"""
        try:
            if self.tracker:
                self.tracker.clear_old_tracks()

            # Clear processing time history
            if len(self.processing_times) > 1000:
                self.processing_times = self.processing_times[-1000:]

        except Exception as e:
            self.monitor.log_error(
                camera_id=self.camera.id,
                error_type="cleanup_error",
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = {
            "camera_id": self.camera.id,
            "status": "active" if self.is_processing else "stopped",
            "total_frames_processed": self.total_frames_processed,
            "avg_processing_time": np.mean(self.processing_times) if self.processing_times else 0,
            "last_analytics_save": self.last_analytics_save.isoformat(),
            "last_pattern_analysis": self.last_pattern_analysis.isoformat(),
            "last_cleanup": self.last_cleanup.isoformat()
        }

        if self.tracker:
            stats.update(self.tracker.get_statistics())

        if self.analyzer:
            stats.update(self.analyzer.get_analytics())

        return stats

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_processing()
        if self.tracker:
            self.cleanup()
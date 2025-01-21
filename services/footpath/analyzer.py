import numpy as np
from scipy.spatial import distance
from sklearn.cluster import DBSCAN
from collections import defaultdict
import datetime
import cv2
import json

class FootpathAnalyzer:
    def __init__(self, frame_resolution, zone_polygon=None):
        self.frame_resolution = frame_resolution
        self.zone_polygon = np.array(json.loads(zone_polygon)) if zone_polygon else None

        # Initialize analytics containers
        self.heatmap = np.zeros(frame_resolution, dtype=np.float32)
        self.zone_visitors = set()
        self.dwell_times = defaultdict(float)
        self.path_segments = []

    def analyze_tracks(self, tracks):
        """Analyze a set of tracks to generate insights"""
        current_time = datetime.datetime.now()

        for track_id, positions in tracks.items():
            if len(positions) < 2:
                continue

            # Update heatmap
            self._update_heatmap(positions)

            # Analyze dwell time if zone defined
            if self.zone_polygon is not None:
                self._analyze_dwell_time(track_id, positions)

            # Record path segment
            self._record_path_segment(track_id, positions)

    def _update_heatmap(self, positions):
        """Update heatmap with track positions"""
        for point in positions:
            x, y = point['position']
            y = int(y)
            x = int(x)
            if 0 <= y < self.frame_resolution[0] and 0 <= x < self.frame_resolution[1]:
                self.heatmap[y, x] += 1

    def _analyze_dwell_time(self, track_id, positions):
        """Analyze time spent in zone"""
        in_zone = False
        zone_entry_time = None

        for point in positions:
            position = point['position']
            timestamp = point['timestamp']

            # Check if point is in zone
            if self._point_in_zone(position):
                self.zone_visitors.add(track_id)
                if not in_zone:
                    # Just entered zone
                    in_zone = True
                    zone_entry_time = timestamp
            elif in_zone:
                # Just exited zone
                in_zone = False
                if zone_entry_time:
                    dwell_time = (timestamp - zone_entry_time).total_seconds()
                    self.dwell_times[track_id] += dwell_time

    def _record_path_segment(self, track_id, positions):
        """Record path segment for pattern analysis"""
        segment = {
            'track_id': track_id,
            'points': [(p['position'][0], p['position'][1]) for p in positions],
            'timestamps': [p['timestamp'] for p in positions],
            'duration': (positions[-1]['timestamp'] - positions[0]['timestamp']).total_seconds()
        }
        self.path_segments.append(segment)

    def _point_in_zone(self, point):
        """Check if point is inside zone polygon"""
        if self.zone_polygon is None:
            return True
        return cv2.pointPolygonTest(self.zone_polygon, tuple(point), False) >= 0

    def get_heatmap(self):
        """Get normalized heatmap"""
        if np.max(self.heatmap) > 0:
            normalized = (self.heatmap * 255 / np.max(self.heatmap)).astype(np.uint8)
            return cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        return np.zeros((*self.frame_resolution, 3), dtype=np.uint8)

    def get_analytics(self):
        """Get current analytics data"""
        return {
            'unique_visitors': len(self.zone_visitors),
            'avg_dwell_time': np.mean(list(self.dwell_times.values())) if self.dwell_times else 0,
            'max_dwell_time': max(self.dwell_times.values()) if self.dwell_times else 0,
            'total_dwell_time': sum(self.dwell_times.values()),
            'total_paths': len(self.path_segments)
        }

    def find_patterns(self, min_frequency=2):
        """Find common movement patterns"""
        if len(self.path_segments) < min_frequency:
            return []

        # Extract path points for clustering
        all_points = []
        for segment in self.path_segments:
            all_points.extend(segment['points'])

        # Perform clustering
        clustering = DBSCAN(eps=50, min_samples=min_frequency).fit(np.array(all_points))

        # Analyze clusters
        patterns = []
        for label in set(clustering.labels_):
            if label >= 0:  # Ignore noise (-1)
                cluster_points = np.array([p for p, l in zip(all_points, clustering.labels_) if l == label])
                center = np.mean(cluster_points, axis=0)

                pattern = {
                    'center': center.tolist(),
                    'point_count': len(cluster_points),
                    'frequency': len(set(clustering.labels_ == label))
                }
                patterns.append(pattern)

        return patterns

    def reset(self):
        """Reset analytics state"""
        self.heatmap.fill(0)
        self.zone_visitors.clear()
        self.dwell_times.clear()
        self.path_segments.clear()
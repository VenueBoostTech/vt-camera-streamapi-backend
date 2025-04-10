import cv2
import numpy as np
import os
import json
import datetime

class HeatmapGenerator:
    def __init__(self, frame_resolution=(1920, 1080), decay_factor=0.95, blur_size=15):
        """Initialize the heatmap generator service"""
        self.frame_resolution = frame_resolution
        self.heatmap = np.zeros(frame_resolution, dtype=np.float32)
        self.decay_factor = decay_factor  # Factor for historical data decay
        self.blur_size = blur_size  # Size of Gaussian blur for smoothing
        self.position_history = []  # Track positions for historical analysis
        self.last_update = datetime.datetime.now()
        
    def update(self, detections=None, positions=None, tracks=None):
        """Update heatmap with new detection data"""
        current_time = datetime.datetime.now()
        time_diff = (current_time - self.last_update).total_seconds()
        
        # Apply decay to historical data based on time difference
        decay = self.decay_factor ** max(1, time_diff)
        self.heatmap *= decay
        
        # Add new data from detections
        if detections is not None and hasattr(detections, 'xyxy'):
            for bbox in detections.xyxy:
                x1, y1, x2, y2 = map(int, bbox)
                # Use the center point of each detection
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Ensure coordinates are within frame bounds
                if 0 <= center_y < self.frame_resolution[0] and 0 <= center_x < self.frame_resolution[1]:
                    # Add intensity to the heatmap at this point
                    self.heatmap[center_y, center_x] += 1.0
                    self.position_history.append({
                        'position': (center_x, center_y),
                        'timestamp': current_time.isoformat()
                    })
        
        # Add data from explicit positions
        if positions is not None:
            for pos in positions:
                x, y = pos
                x, y = int(x), int(y)
                if 0 <= y < self.frame_resolution[0] and 0 <= x < self.frame_resolution[1]:
                    self.heatmap[y, x] += 1.0
                    self.position_history.append({
                        'position': (x, y),
                        'timestamp': current_time.isoformat()
                    })
        
        # Add data from tracks
        if tracks is not None:
            for track_id, track_data in tracks.items():
                if len(track_data) > 0:
                    # Get the most recent position
                    latest_pos = track_data[-1].get('position')
                    if latest_pos:
                        x, y = latest_pos
                        x, y = int(x), int(y)
                        if 0 <= y < self.frame_resolution[0] and 0 <= x < self.frame_resolution[1]:
                            self.heatmap[y, x] += 1.0
        
        # Apply Gaussian blur to smooth the heatmap
        if np.max(self.heatmap) > 0:  # Only blur if there's data
            self.heatmap = cv2.GaussianBlur(self.heatmap, (self.blur_size, self.blur_size), 0)
        
        self.last_update = current_time
        return self.heatmap
    
    def get_colored_heatmap(self, alpha=0.7):
        """Get a colored visualization of the heatmap"""
        if np.max(self.heatmap) > 0:
            # Normalize to 0-255 range
            normalized = (self.heatmap * 255 / np.max(self.heatmap)).astype(np.uint8)
            
            # Apply colormap (JET, INFERNO, PLASMA, etc.)
            colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
            return colored
        else:
            # Return empty colored frame if no data
            return np.zeros((self.frame_resolution[0], self.frame_resolution[1], 3), dtype=np.uint8)
    
    def overlay_heatmap(self, frame, alpha=0.7):
        """Overlay the heatmap on a frame"""
        # Get colored heatmap
        heatmap_colored = self.get_colored_heatmap()
        
        # Resize frame if needed
        if frame.shape[:2] != self.frame_resolution:
            frame = cv2.resize(frame, (self.frame_resolution[1], self.frame_resolution[0]))
        
        # Create overlay
        overlay = cv2.addWeighted(frame, 1-alpha, heatmap_colored, alpha, 0)
        return overlay
    
    def get_hotspots(self, threshold=0.7, min_area=100):
        """Get hotspot regions from the heatmap"""
        if np.max(self.heatmap) == 0:
            return []
        
        # Normalize heatmap
        normalized = self.heatmap / np.max(self.heatmap)
        
        # Threshold to create binary image
        binary = (normalized > threshold).astype(np.uint8) * 255
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by area and extract bounding boxes
        hotspots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(contour)
                avg_intensity = np.mean(self.heatmap[y:y+h, x:x+w])
                hotspots.append({
                    'bbox': (x, y, x+w, y+h),
                    'area': area,
                    'intensity': float(avg_intensity),
                    'normalized_intensity': float(avg_intensity / np.max(self.heatmap))
                })
        
        # Sort by intensity (highest first)
        hotspots.sort(key=lambda x: x['intensity'], reverse=True)
        return hotspots
    
    def reset(self):
        """Reset the heatmap"""
        self.heatmap = np.zeros(self.frame_resolution, dtype=np.float32)
        self.position_history = []
        self.last_update = datetime.datetime.now()
    
    def save(self, output_path):
        """Save the heatmap as an image"""
        colored = self.get_colored_heatmap()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        cv2.imwrite(output_path, colored)
        return output_path
    
    def export_data(self, format='numpy'):
        """Export the heatmap data in various formats"""
        if format == 'numpy':
            return self.heatmap
        elif format == 'normalized':
            if np.max(self.heatmap) > 0:
                return self.heatmap / np.max(self.heatmap)
            return self.heatmap
        elif format == 'json':
            # Convert to a more JSON-friendly format
            # (sparse representation to save space)
            sparse_data = []
            y_indices, x_indices = np.where(self.heatmap > 0.1)  # Threshold to ignore near-zero values
            for y, x in zip(y_indices, x_indices):
                sparse_data.append({
                    'x': int(x),
                    'y': int(y),
                    'value': float(self.heatmap[y, x])
                })
            
            # Add hotspots
            hotspots = self.get_hotspots()
            
            return {
                'timestamp': datetime.datetime.now().isoformat(),
                'resolution': self.frame_resolution,
                'max_value': float(np.max(self.heatmap)),
                'data': sparse_data,
                'hotspots': hotspots
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def save_export_data(self, output_path=None):
        """Save exported data to a JSON file"""
        if output_path is None:
            # Create default output directory
            os.makedirs('heatmap_data', exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'heatmap_data/heatmap_{timestamp}.json'
        
        # Export data and save to file
        data = self.export_data(format='json')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
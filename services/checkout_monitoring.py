import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict
import datetime
import json
import os

class CheckoutMonitoringService:
    def __init__(self, model_path=None, confidence_threshold=0.5):
        """Initialize the checkout monitoring service"""
        # Load the checkout counter detection model from Roboflow
        if model_path is None:
            model_path = "checkout_counter_model.pt"  # Default model path
        
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        
        # Store checkout counter locations
        self.checkout_counters = []
        
        # Track usage statistics
        self.checkout_usage = defaultdict(lambda: {
            'total_visits': 0,
            'average_time': 0,
            'current_customers': 0,
            'busy_periods': [],
            'history': []
        })
        
        # Queue monitoring
        self.queue_lengths = defaultdict(list)
        self.queue_thresholds = {
            'short': 1,     # 1 person
            'normal': 3,    # 2-3 people
            'long': 5,      # 4-5 people
            'very_long': 6  # 6+ people
        }
        
        # Initialize analytics
        self.last_analysis_time = datetime.datetime.now()
        self.checkout_statuses = {}

    def detect_checkout_counters(self, frame):
        """Detect checkout counters in the frame"""
        # Run model to detect checkout counters
        results = self.model(frame)
        
        # Process detections
        detections = sv.Detections.from_ultralytics(results[0])
        
        # Filter by confidence
        mask = detections.confidence >= self.confidence_threshold
        detections = detections[mask]
        
        # Update checkout counter locations
        if len(detections.xyxy) > 0:
            self.checkout_counters = []
            for i, bbox in enumerate(detections.xyxy):
                checkout_id = f"checkout_{i+1}"
                x1, y1, x2, y2 = map(int, bbox)
                
                # Store checkout counter information
                counter_info = {
                    'id': checkout_id,
                    'bbox': (x1, y1, x2, y2),
                    'center': ((x1 + x2) // 2, (y1 + y2) // 2),
                    'area': (x2 - x1) * (y2 - y1),
                    'timestamp': datetime.datetime.now()
                }
                
                self.checkout_counters.append(counter_info)
                
                # Initialize checkout statistics if new
                if checkout_id not in self.checkout_usage:
                    self.checkout_usage[checkout_id] = {
                        'total_visits': 0,
                        'average_time': 0,
                        'current_customers': 0,
                        'busy_periods': [],
                        'history': []
                    }
        
        return detections

    def analyze_customer_interactions(self, person_detections):
        """Analyze interactions between customers and checkout counters"""
        current_time = datetime.datetime.now()
        
        # Reset current customer counts
        for checkout_id in self.checkout_usage:
            self.checkout_usage[checkout_id]['current_customers'] = 0
        
        # Track queue lengths for each checkout
        checkout_queues = defaultdict(int)
        
        # Check each person against checkout areas
        for person_id, bbox in enumerate(person_detections.xyxy):
            px1, py1, px2, py2 = map(int, bbox)
            person_center = ((px1 + px2) // 2, (py1 + py2) // 2)
            
            # Check interaction with each checkout counter
            for counter in self.checkout_counters:
                cx1, cy1, cx2, cy2 = counter['bbox']
                checkout_id = counter['id']
                
                # Define an extended area around the checkout (for queue detection)
                queue_area_x1 = cx1 - (cx2 - cx1)  # Extend left by counter width
                queue_area_y1 = cy1
                queue_area_x2 = cx2
                queue_area_y2 = cy2 + (cy2 - cy1) * 2  # Extend down by 2x counter height
                
                # Check if person is at counter
                if (cx1 <= person_center[0] <= cx2 and 
                    cy1 <= person_center[1] <= cy2):
                    # Person is at the checkout counter
                    self.checkout_usage[checkout_id]['current_customers'] += 1
                    
                    # Log visit if not already logged
                    visit_entry = {
                        'person_id': person_id,
                        'start_time': current_time.isoformat(),
                        'end_time': None
                    }
                    
                    # Check if this is a new visit
                    if not any(v['person_id'] == person_id and v['end_time'] is None 
                              for v in self.checkout_usage[checkout_id]['history']):
                        self.checkout_usage[checkout_id]['history'].append(visit_entry)
                        self.checkout_usage[checkout_id]['total_visits'] += 1
                
                # Check if person is in queue area
                elif (queue_area_x1 <= person_center[0] <= queue_area_x2 and 
                      queue_area_y1 <= person_center[1] <= queue_area_y2):
                    # Person is in queue area
                    checkout_queues[checkout_id] += 1
        
        # Update queue lengths
        for checkout_id, queue_length in checkout_queues.items():
            self.queue_lengths[checkout_id].append({
                'timestamp': current_time.isoformat(),
                'length': queue_length
            })
            
            # Keep only last 100 measurements
            if len(self.queue_lengths[checkout_id]) > 100:
                self.queue_lengths[checkout_id] = self.queue_lengths[checkout_id][-100:]
        
        # Update checkout statuses
        self._update_checkout_statuses()
        
        return self.checkout_statuses

    def _update_checkout_statuses(self):
        """Update the status of each checkout based on current data"""
        current_time = datetime.datetime.now()
        
        for checkout_id in self.checkout_usage:
            # Get current customers and recent queue lengths
            current_customers = self.checkout_usage[checkout_id]['current_customers']
            
            # Calculate average queue length over last 5 measurements
            recent_queue_lengths = [
                q['length'] for q in self.queue_lengths.get(checkout_id, [])[-5:]
            ]
            avg_queue_length = sum(recent_queue_lengths) / max(len(recent_queue_lengths), 1)
            
            # Determine status
            if current_customers == 0 and avg_queue_length == 0:
                status = "INACTIVE"
            elif current_customers > 0 and avg_queue_length <= self.queue_thresholds['short']:
                status = "ACTIVE"
            elif avg_queue_length <= self.queue_thresholds['normal']:
                status = "BUSY"
            elif avg_queue_length <= self.queue_thresholds['long']:
                status = "CROWDED"
            else:
                status = "OVERLOADED"
            
            # Store status
            self.checkout_statuses[checkout_id] = {
                'status': status,
                'customers': current_customers,
                'queue_length': avg_queue_length,
                'timestamp': current_time.isoformat()
            }
            
            # Check if this is a busy period
            if status in ["CROWDED", "OVERLOADED"]:
                # Record busy period if not already in one
                if not self.checkout_usage[checkout_id]['busy_periods'] or \
                   self.checkout_usage[checkout_id]['busy_periods'][-1].get('end_time') is not None:
                    self.checkout_usage[checkout_id]['busy_periods'].append({
                        'start_time': current_time.isoformat(),
                        'end_time': None,
                        'max_queue': avg_queue_length
                    })
                else:
                    # Update existing busy period
                    busy_period = self.checkout_usage[checkout_id]['busy_periods'][-1]
                    busy_period['max_queue'] = max(busy_period['max_queue'], avg_queue_length)
            elif status in ["INACTIVE", "ACTIVE"] and self.checkout_usage[checkout_id]['busy_periods'] and \
                 self.checkout_usage[checkout_id]['busy_periods'][-1].get('end_time') is None:
                # End busy period
                self.checkout_usage[checkout_id]['busy_periods'][-1]['end_time'] = current_time.isoformat()

    def annotate_frame(self, frame, person_detections=None):
        """Annotate the frame with checkout counter information"""
        annotated_frame = frame.copy()
        
        # Draw checkout counter boxes
        for counter in self.checkout_counters:
            x1, y1, x2, y2 = counter['bbox']
            checkout_id = counter['id']
            
            # Get status color
            status = self.checkout_statuses.get(checkout_id, {}).get('status', 'UNKNOWN')
            if status == "INACTIVE":
                color = (128, 128, 128)  # Gray
            elif status == "ACTIVE":
                color = (0, 255, 0)  # Green
            elif status == "BUSY":
                color = (0, 255, 255)  # Yellow
            elif status == "CROWDED":
                color = (0, 165, 255)  # Orange
            else:  # OVERLOADED
                color = (0, 0, 255)  # Red
            
            # Draw checkout area
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw queue area (extended area)
            queue_area_x1 = x1 - (x2 - x1)
            queue_area_y1 = y1
            queue_area_x2 = x2
            queue_area_y2 = y2 + (y2 - y1) * 2
            cv2.rectangle(annotated_frame, 
                         (queue_area_x1, queue_area_y1), 
                         (queue_area_x2, queue_area_y2), 
                         color, 1, cv2.LINE_DASH)
            
            # Add status label
            queue_length = self.checkout_statuses.get(checkout_id, {}).get('queue_length', 0)
            customers = self.checkout_statuses.get(checkout_id, {}).get('customers', 0)
            label = f"{checkout_id}: {status} (Q:{int(queue_length)}, C:{customers})"
            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw person detections if provided
        if person_detections is not None and hasattr(person_detections, 'xyxy'):
            for i, bbox in enumerate(person_detections.xyxy):
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
        
        return annotated_frame

    def get_analytics(self):
        """Get analytics data for reporting"""
        analytics = {
            'checkout_counters': len(self.checkout_counters),
            'counters': {},
            'overall_stats': {
                'total_visits': 0,
                'busy_counters': 0,
                'inactive_counters': 0
            }
        }
        
        # Collect data for each checkout
        for checkout_id, data in self.checkout_usage.items():
            status = self.checkout_statuses.get(checkout_id, {}).get('status', 'UNKNOWN')
            queue_length = self.checkout_statuses.get(checkout_id, {}).get('queue_length', 0)
            
            # Calculate average wait time from history if available
            wait_times = []
            for visit in data['history']:
                if visit['end_time'] is not None:
                    start = datetime.datetime.fromisoformat(visit['start_time'])
                    end = datetime.datetime.fromisoformat(visit['end_time'])
                    wait_times.append((end - start).total_seconds())
            
            avg_wait_time = sum(wait_times) / max(len(wait_times), 1) if wait_times else 0
            
            # Add checkout stats
            analytics['counters'][checkout_id] = {
                'status': status,
                'total_visits': data['total_visits'],
                'current_queue': queue_length,
                'current_customers': data['current_customers'],
                'average_wait_time': avg_wait_time,
                'busy_periods': len(data['busy_periods'])
            }
            
            # Update overall stats
            analytics['overall_stats']['total_visits'] += data['total_visits']
            if status in ["CROWDED", "OVERLOADED"]:
                analytics['overall_stats']['busy_counters'] += 1
            elif status == "INACTIVE":
                analytics['overall_stats']['inactive_counters'] += 1
        
        return analytics

    def export_data(self, format='json'):
        """Export checkout monitoring data"""
        if format == 'json':
            data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'checkout_counters': [
                    {
                        'id': counter['id'],
                        'bbox': counter['bbox'],
                        'center': counter['center']
                    }
                    for counter in self.checkout_counters
                ],
                'checkout_usage': self.checkout_usage,
                'queue_lengths': {k: v[-10:] for k, v in self.queue_lengths.items()},
                'checkout_statuses': self.checkout_statuses,
                'analytics': self.get_analytics()
            }
            
            return data
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def save_analytics(self, output_path=None):
        """Save analytics data to file"""
        if output_path is None:
            # Create default output directory if it doesn't exist
            os.makedirs('checkout_analytics', exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'checkout_analytics/checkout_data_{timestamp}.json'
        
        # Export data and save to file
        data = self.export_data(format='json')
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
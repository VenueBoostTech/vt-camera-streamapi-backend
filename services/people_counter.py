# services/people_counter.py
import cv2
import os
import datetime
from ultralytics import YOLO

class PeopleCounter:
    def __init__(self, model_path=None, confidence_threshold=0.5):
        if model_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base, 'training_models', 'people_counter', 'weights', 'best.pt')

        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.total_people_detected = 0
        self.detections = []

    def detect(self, frame):
        results = self.model(frame, conf=self.confidence_threshold)
        count = 0
        detections = []

        if results:
            for box, conf, cls in zip(results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls):
                if int(cls.item()) == 0:  # class 0 is 'person' in COCO
                    x1, y1, x2, y2 = map(int, box.tolist())
                    detections.append({'bbox': (x1, y1, x2, y2), 'confidence': conf.item()})
                    count += 1

        self.total_people_detected += count
        self.detections.append({'timestamp': datetime.datetime.now().isoformat(), 'count': count})
        return detections, count

    def annotate_frame(self, frame, detections):
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, f"Person: {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.putText(annotated, f"People this frame: {len(detections)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(annotated, f"Total counted: {self.total_people_detected}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return annotated

    def get_summary(self):
        return {
            'total_detected': self.total_people_detected,
            'frame_detections': self.detections
        }

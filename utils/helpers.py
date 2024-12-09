import json
from datetime import datetime

def parse_bbox(bbox_str: str) -> dict:
    """Parse a bbox string into a dictionary."""
    try:
        return json.loads(bbox_str)
    except json.JSONDecodeError:
        return {}

def format_datetime(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 string."""
    return dt.isoformat()

def calculate_intersection_over_union(boxA, boxB):
    """Calculate the Intersection over Union (IoU) of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou
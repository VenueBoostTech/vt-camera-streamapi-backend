from .camera import Camera
from .entry_log import EntryLog
from .exit_log import ExitLog
from .smoking_detection import SmokingDetection
from .threat_detection import ThreatDetection
from .vehicle_detection import VehicleDetection
from .tracking_log import TrackingLog
from .environment import SmokeDetection
from .security import ThreatDetection, SleepingDetection
from .staff import Staff, WorkSession, Activity, Break
from .vehicle import Vehicle, ParkingSpot, ValetRequest
from .property import Property, Zone

from sqlalchemy.ext.declarative import declarative_base
# Make sure all models are imported here

__all__ = [
   "Camera",
   "EntryLog",
   "ExitLog",
   "SmokingDetection",
   "ThreatDetection",
   "VehicleDetection",
   "TrackingLog",
   "SmokeDetection",
   "ThreatDetection",
   "SleepingDetection",
   "Staff",
   "WorkSession",
   "Activity",
   "Break",
   "Vehicle",
   "ParkingSpot",
   "ValetRequest",
   "Property",
   "Zone"
]

Base = declarative_base()
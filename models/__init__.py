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
from .property import Property, Building, Floor
from .zone import Zone
from .behavior import Behavior
from .pattern import Pattern
from .spaceAnalytics import SpaceAnalytics
from .heatmapData import HeatmapData
from .demographics import Demographics
from .securityEvent import SecurityEvent
from .detection import Detection
from .incident import Incident
from .parkingEvent import ParkingEvent
from .parkingAnalytics import ParkingAnalytics

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
   "Zone",
   "Behavior",
   "Pattern",
   "SpaceAnalytics",
   "HeatmapData",
   "Demographics",
   "SecurityEvent",
   "Detection",
   "Incident",
   "ParkingEvent",
   "ParkingAnalytics",
   "Floor",
   "Building"
]

Base = declarative_base()
"""
Z-areo Non-Profit OBD2 Data Collection System
============================================

This module provides comprehensive OBD2 data collection capabilities including:
- ELM327 adapter support
- Bidirectional scanner communication
- Virtual CAN sniffer integration
- Mobile phone integration
- Data privacy and compliance features

For Z-areo non-profit vehicle data collection and analysis.
"""

from .core import OBD2Manager
from .scanner import BidirectionalScanner
from .can_sniffer import VirtualCANSniffer
from .data_collector import DataCollector
from .mobile_bridge import MobileBridge
from .compliance import ComplianceManager

__version__ = "1.0.0"
__author__ = "Z-areo Non-Profit Data Collection Team"

__all__ = [
    "OBD2Manager",
    "BidirectionalScanner", 
    "VirtualCANSniffer",
    "DataCollector",
    "MobileBridge",
    "ComplianceManager"
]
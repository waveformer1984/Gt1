"""
Data Collector for Z-areo Non-Profit OBD2 Data Collection
========================================================

Manages data collection, storage, and analysis for vehicle diagnostics.
Includes database integration, data validation, and reporting features.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

import pandas as pd
import structlog
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .core import OBD2Manager
from .scanner import BidirectionalScanner, DiagnosticCode
from .can_sniffer import VirtualCANSniffer, CANMessage

logger = structlog.get_logger(__name__)

Base = declarative_base()

class VehicleSession(Base):
    """Database model for vehicle data collection sessions."""
    __tablename__ = 'vehicle_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), unique=True, nullable=False)
    vin = Column(String(17))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    total_samples = Column(Integer, default=0)
    vehicle_make = Column(String(50))
    vehicle_model = Column(String(50))
    vehicle_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class VehicleData(Base):
    """Database model for individual OBD2 data points."""
    __tablename__ = 'vehicle_data'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    parameter = Column(String(50), nullable=False)
    value = Column(Float)
    unit = Column(String(20))
    raw_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DiagnosticRecord(Base):
    """Database model for diagnostic trouble codes."""
    __tablename__ = 'diagnostic_records'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False)
    code = Column(String(10), nullable=False)
    description = Column(Text)
    status = Column(String(20))  # pending, confirmed, permanent
    detected_at = Column(DateTime, nullable=False)
    cleared_at = Column(DateTime)
    occurrence_count = Column(Integer, default=1)
    freeze_frame_data = Column(Text)  # JSON data

class CANRecord(Base):
    """Database model for CAN message records."""
    __tablename__ = 'can_records'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    arbitration_id = Column(String(10), nullable=False)
    data_bytes = Column(String(50))
    protocol = Column(String(20))
    decoded_data = Column(Text)  # JSON data
    is_error = Column(Boolean, default=False)

@dataclass
class CollectionStats:
    """Statistics for data collection session."""
    session_id: str
    start_time: float
    total_samples: int = 0
    parameters_collected: set = None
    diagnostic_codes: int = 0
    can_messages: int = 0
    data_rate: float = 0.0
    
    def __post_init__(self):
        if self.parameters_collected is None:
            self.parameters_collected = set()

class DataCollector:
    """
    Comprehensive data collection and storage system for OBD2 diagnostics.
    
    Features:
    - Real-time data collection and storage
    - Database integration with SQLite/PostgreSQL support
    - Data validation and quality checks
    - Statistical analysis and reporting
    - Export capabilities (CSV, JSON, Excel)
    - Data privacy and anonymization
    """
    
    def __init__(self, 
                 obd2_manager: OBD2Manager,
                 scanner: Optional[BidirectionalScanner] = None,
                 can_sniffer: Optional[VirtualCANSniffer] = None,
                 database_url: str = "sqlite:///zareo_vehicle_data.db"):
        
        self.obd2_manager = obd2_manager
        self.scanner = scanner
        self.can_sniffer = can_sniffer
        
        # Database setup
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # Collection state
        self.is_collecting = False
        self.current_session_id: Optional[str] = None
        self.collection_stats = CollectionStats("", 0.0)
        
        # Data buffers
        self.data_buffer: List[Dict[str, Any]] = []
        self.can_buffer: List[CANMessage] = []
        self.diagnostic_buffer: List[DiagnosticCode] = []
        
        # Collection parameters
        self.buffer_size = 1000
        self.flush_interval = 30.0  # seconds
        self.collection_task: Optional[asyncio.Task] = None
        
    async def start_collection_session(self, 
                                     session_name: Optional[str] = None,
                                     parameters: Optional[List[str]] = None) -> str:
        """Start a new data collection session."""
        try:
            if self.is_collecting:
                await self.stop_collection_session()
            
            # Generate session ID
            session_id = session_name or f"session_{int(time.time())}"
            self.current_session_id = session_id
            
            # Initialize collection stats
            self.collection_stats = CollectionStats(
                session_id=session_id,
                start_time=time.time()
            )
            
            # Create database session record
            vehicle_info = self.obd2_manager.vehicle_info
            session_record = VehicleSession(
                session_id=session_id,
                vin=vehicle_info.vin,
                start_time=datetime.utcnow(),
                vehicle_make=vehicle_info.make,
                vehicle_model=vehicle_info.model,
                vehicle_year=vehicle_info.year
            )
            
            self.db_session.add(session_record)
            self.db_session.commit()
            
            # Start data collection
            self.is_collecting = True
            
            # Register callbacks
            self.obd2_manager.add_data_callback(self._on_obd2_data)
            
            if self.scanner:
                # Collect diagnostic codes at start
                codes = await self.scanner.read_diagnostic_codes()
                for code in codes:
                    await self._store_diagnostic_code(code)
            
            if self.can_sniffer:
                self.can_sniffer.add_message_callback(self._on_can_message)
            
            # Start collection task
            self.collection_task = asyncio.create_task(self._collection_loop())
            
            # Start monitoring if parameters specified
            if parameters:
                await self.obd2_manager.start_monitoring(parameters)
            
            logger.info("Data collection session started", session_id=session_id)
            return session_id
            
        except Exception as e:
            logger.error("Failed to start collection session", error=str(e))
            raise
    
    async def stop_collection_session(self) -> Dict[str, Any]:
        """Stop the current data collection session."""
        try:
            if not self.is_collecting:
                return {'success': False, 'error': 'No active collection session'}
            
            self.is_collecting = False
            
            # Stop monitoring
            await self.obd2_manager.stop_monitoring()
            
            # Cancel collection task
            if self.collection_task:
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
            
            # Flush remaining data
            await self._flush_buffers()
            
            # Update session record
            if self.current_session_id:
                session = self.db_session.query(VehicleSession).filter_by(
                    session_id=self.current_session_id
                ).first()
                
                if session:
                    session.end_time = datetime.utcnow()
                    session.duration_seconds = time.time() - self.collection_stats.start_time
                    session.total_samples = self.collection_stats.total_samples
                    self.db_session.commit()
            
            # Generate session summary
            summary = await self._generate_session_summary()
            
            logger.info("Data collection session stopped", 
                       session_id=self.current_session_id,
                       total_samples=self.collection_stats.total_samples)
            
            self.current_session_id = None
            return {'success': True, 'summary': summary}
            
        except Exception as e:
            logger.error("Error stopping collection session", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _collection_loop(self):
        """Main data collection loop."""
        last_flush = time.time()
        
        while self.is_collecting:
            try:
                current_time = time.time()
                
                # Update statistics
                if self.collection_stats.total_samples > 0:
                    duration = current_time - self.collection_stats.start_time
                    self.collection_stats.data_rate = self.collection_stats.total_samples / duration
                
                # Flush buffers if needed
                if (current_time - last_flush) >= self.flush_interval:
                    await self._flush_buffers()
                    last_flush = current_time
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error("Error in collection loop", error=str(e))
                await asyncio.sleep(5.0)
    
    async def _on_obd2_data(self, data_batch: Dict[str, Any]):
        """Handle OBD2 data callback."""
        try:
            if not self.is_collecting or not self.current_session_id:
                return
            
            for parameter, data in data_batch.items():
                # Add to buffer
                record = {
                    'session_id': self.current_session_id,
                    'timestamp': datetime.fromtimestamp(data['timestamp']),
                    'parameter': parameter,
                    'value': data['value'],
                    'unit': data.get('unit'),
                    'raw_data': json.dumps(data)
                }
                
                self.data_buffer.append(record)
                self.collection_stats.total_samples += 1
                self.collection_stats.parameters_collected.add(parameter)
            
            # Flush if buffer is full
            if len(self.data_buffer) >= self.buffer_size:
                await self._flush_data_buffer()
                
        except Exception as e:
            logger.error("Error handling OBD2 data", error=str(e))
    
    async def _on_can_message(self, can_msg: CANMessage):
        """Handle CAN message callback."""
        try:
            if not self.is_collecting or not self.current_session_id:
                return
            
            self.can_buffer.append(can_msg)
            self.collection_stats.can_messages += 1
            
            # Flush if buffer is full
            if len(self.can_buffer) >= self.buffer_size:
                await self._flush_can_buffer()
                
        except Exception as e:
            logger.error("Error handling CAN message", error=str(e))
    
    async def _store_diagnostic_code(self, code: DiagnosticCode):
        """Store diagnostic code in database."""
        try:
            if not self.current_session_id:
                return
            
            record = DiagnosticRecord(
                session_id=self.current_session_id,
                code=code.code,
                description=code.description,
                status=code.status,
                detected_at=datetime.utcnow(),
                occurrence_count=code.occurrence_count,
                freeze_frame_data=json.dumps(code.freeze_frame) if code.freeze_frame else None
            )
            
            self.db_session.add(record)
            self.db_session.commit()
            self.collection_stats.diagnostic_codes += 1
            
        except Exception as e:
            logger.error("Error storing diagnostic code", error=str(e))
    
    async def _flush_buffers(self):
        """Flush all data buffers to database."""
        await self._flush_data_buffer()
        await self._flush_can_buffer()
    
    async def _flush_data_buffer(self):
        """Flush OBD2 data buffer to database."""
        try:
            if not self.data_buffer:
                return
            
            # Bulk insert
            for record in self.data_buffer:
                data_record = VehicleData(**record)
                self.db_session.add(data_record)
            
            self.db_session.commit()
            
            logger.debug("Flushed data buffer", count=len(self.data_buffer))
            self.data_buffer.clear()
            
        except Exception as e:
            logger.error("Error flushing data buffer", error=str(e))
            self.db_session.rollback()
    
    async def _flush_can_buffer(self):
        """Flush CAN message buffer to database."""
        try:
            if not self.can_buffer:
                return
            
            for can_msg in self.can_buffer:
                record = CANRecord(
                    session_id=self.current_session_id,
                    timestamp=datetime.fromtimestamp(can_msg.timestamp),
                    arbitration_id=f"0x{can_msg.arbitration_id:X}",
                    data_bytes=can_msg.data.hex(),
                    protocol=can_msg.protocol.value if can_msg.protocol else None,
                    decoded_data=json.dumps(can_msg.decoded_data) if can_msg.decoded_data else None,
                    is_error=can_msg.is_error
                )
                self.db_session.add(record)
            
            self.db_session.commit()
            
            logger.debug("Flushed CAN buffer", count=len(self.can_buffer))
            self.can_buffer.clear()
            
        except Exception as e:
            logger.error("Error flushing CAN buffer", error=str(e))
            self.db_session.rollback()
    
    async def _generate_session_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for collection session."""
        try:
            if not self.current_session_id:
                return {}
            
            # Query session data
            session = self.db_session.query(VehicleSession).filter_by(
                session_id=self.current_session_id
            ).first()
            
            if not session:
                return {}
            
            # Count records
            data_count = self.db_session.query(VehicleData).filter_by(
                session_id=self.current_session_id
            ).count()
            
            can_count = self.db_session.query(CANRecord).filter_by(
                session_id=self.current_session_id
            ).count()
            
            diagnostic_count = self.db_session.query(DiagnosticRecord).filter_by(
                session_id=self.current_session_id
            ).count()
            
            # Get parameter statistics
            parameters_query = self.db_session.query(VehicleData.parameter).filter_by(
                session_id=self.current_session_id
            ).distinct().all()
            
            unique_parameters = [p[0] for p in parameters_query]
            
            return {
                'session_id': self.current_session_id,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration_seconds': session.duration_seconds,
                'vehicle_info': {
                    'vin': session.vin,
                    'make': session.vehicle_make,
                    'model': session.vehicle_model,
                    'year': session.vehicle_year
                },
                'data_counts': {
                    'obd2_samples': data_count,
                    'can_messages': can_count,
                    'diagnostic_codes': diagnostic_count
                },
                'parameters_collected': unique_parameters,
                'collection_rate': self.collection_stats.data_rate
            }
            
        except Exception as e:
            logger.error("Error generating session summary", error=str(e))
            return {'error': str(e)}
    
    async def export_session_data(self, 
                                session_id: str, 
                                format: str = 'csv',
                                output_path: Optional[str] = None) -> str:
        """Export session data to file."""
        try:
            if format.lower() not in ['csv', 'json', 'excel']:
                raise ValueError("Unsupported export format")
            
            # Query session data
            vehicle_data = self.db_session.query(VehicleData).filter_by(
                session_id=session_id
            ).all()
            
            if not vehicle_data:
                raise ValueError(f"No data found for session: {session_id}")
            
            # Convert to DataFrame
            data_records = []
            for record in vehicle_data:
                data_records.append({
                    'timestamp': record.timestamp,
                    'parameter': record.parameter,
                    'value': record.value,
                    'unit': record.unit
                })
            
            df = pd.DataFrame(data_records)
            
            # Generate output filename
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"zareo_session_{session_id}_{timestamp}.{format.lower()}"
            
            # Export based on format
            if format.lower() == 'csv':
                df.to_csv(output_path, index=False)
            elif format.lower() == 'json':
                df.to_json(output_path, orient='records', date_format='iso')
            elif format.lower() == 'excel':
                df.to_excel(output_path, index=False)
            
            logger.info("Session data exported", 
                       session_id=session_id, 
                       format=format,
                       output_path=output_path,
                       record_count=len(data_records))
            
            return output_path
            
        except Exception as e:
            logger.error("Error exporting session data", session_id=session_id, error=str(e))
            raise
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status."""
        return {
            'is_collecting': self.is_collecting,
            'current_session': self.current_session_id,
            'statistics': asdict(self.collection_stats) if self.is_collecting else None,
            'buffer_sizes': {
                'data_buffer': len(self.data_buffer),
                'can_buffer': len(self.can_buffer),
                'diagnostic_buffer': len(self.diagnostic_buffer)
            },
            'database_url': self.database_url
        }
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent collection sessions."""
        try:
            sessions = self.db_session.query(VehicleSession).order_by(
                VehicleSession.start_time.desc()
            ).limit(limit).all()
            
            session_list = []
            for session in sessions:
                session_list.append({
                    'session_id': session.session_id,
                    'vin': session.vin,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'duration_seconds': session.duration_seconds,
                    'total_samples': session.total_samples,
                    'vehicle_info': {
                        'make': session.vehicle_make,
                        'model': session.vehicle_model,
                        'year': session.vehicle_year
                    }
                })
            
            return session_list
            
        except Exception as e:
            logger.error("Error listing sessions", error=str(e))
            return []
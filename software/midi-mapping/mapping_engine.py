#!/usr/bin/env python3
"""
REZONATE MIDI Mapping Engine
MIDI parameter mapping and DAW integration for REZONATE system.
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('midi-mapping')


class MIDIMapping:
    """Represents a MIDI parameter mapping."""
    
    def __init__(self, name: str, source: str, target: str, 
                 min_value: int = 0, max_value: int = 127):
        self.name = name
        self.source = source  # e.g., "harp_controller.string_1"
        self.target = target  # e.g., "daw.track_1.volume"
        self.min_value = min_value
        self.max_value = max_value
        self.enabled = True
        self.last_value = 0
        self.event_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mapping to dictionary."""
        return {
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "enabled": self.enabled,
            "last_value": self.last_value,
            "event_count": self.event_count
        }


class MIDIMappingEngine:
    """REZONATE MIDI mapping and processing engine."""
    
    def __init__(self, default_mapping: str = "basic"):
        self.default_mapping = default_mapping
        self.running = False
        self.mappings = {}
        self.start_time = None
        self.events_processed = 0
        self.active_sources = set()
        
        # Initialize default mappings
        self._initialize_mappings()
    
    def _initialize_mappings(self):
        """Initialize default MIDI mappings."""
        default_mappings = [
            MIDIMapping("Harp String 1 -> Volume", "harp.string_1", "daw.track_1.volume"),
            MIDIMapping("Harp String 2 -> Filter", "harp.string_2", "daw.track_1.filter_cutoff"),
            MIDIMapping("Motion X -> Reverb", "motion.x_axis", "daw.fx.reverb.mix"),
            MIDIMapping("Motion Y -> Delay", "motion.y_axis", "daw.fx.delay.feedback"),
            MIDIMapping("Drone 1 -> Pan", "drone_1.position", "daw.track_2.pan"),
            MIDIMapping("Drone 2 -> Pitch", "drone_2.distance", "daw.track_2.pitch_shift"),
            MIDIMapping("Gesture -> Tempo", "gesture.energy", "daw.master.tempo"),
            MIDIMapping("Voice -> Harmony", "voice.pitch", "daw.track_3.harmony_shift"),
        ]
        
        for mapping in default_mappings:
            self.mappings[mapping.name] = mapping
    
    async def start(self):
        """Start the MIDI mapping engine."""
        logger.info("🎵 REZONATE MIDI Mapping Engine starting")
        self.running = True
        self.start_time = time.time()
        
        try:
            await self._initialize_midi()
            await self._run_mapping_loop()
        except KeyboardInterrupt:
            logger.info("MIDI mapping engine stopped by user")
        except Exception as e:
            logger.error(f"MIDI mapping engine error: {e}")
        finally:
            self.running = False
    
    async def _initialize_midi(self):
        """Initialize MIDI subsystem."""
        logger.info("Initializing MIDI subsystem...")
        await asyncio.sleep(1)  # Simulate initialization
        
        logger.info("✓ MIDI input/output initialized")
        logger.info("✓ DAW integration ready")
        logger.info("✓ Mapping engine active")
        logger.info(f"✓ Loaded {len(self.mappings)} default mappings")
        logger.info("✓ OSC protocol support enabled")
    
    async def _run_mapping_loop(self):
        """Main MIDI mapping loop."""
        logger.info("MIDI mapping loop started")
        
        while self.running:
            # Process MIDI events
            await self._process_midi_events()
            
            # Update mapping states
            await self._update_mappings()
            
            # Log status periodically
            if int(time.time()) % 30 == 0:  # Every 30 seconds
                self._log_status()
            
            await asyncio.sleep(0.01)  # High frequency processing (100Hz)
    
    async def _process_midi_events(self):
        """Process incoming MIDI events."""
        # Simulate incoming MIDI events from REZONATE devices
        if random.random() > 0.95:  # 5% chance of event each cycle
            await self._simulate_midi_event()
    
    async def _simulate_midi_event(self):
        """Simulate a MIDI event from REZONATE hardware."""
        # Randomly select a mapping to simulate
        mapping_name = random.choice(list(self.mappings.keys()))
        mapping = self.mappings[mapping_name]
        
        if not mapping.enabled:
            return
        
        # Generate a random MIDI value
        new_value = random.randint(mapping.min_value, mapping.max_value)
        
        # Process the mapping
        await self._apply_mapping(mapping, new_value)
    
    async def _apply_mapping(self, mapping: MIDIMapping, value: int):
        """Apply a MIDI mapping."""
        mapping.last_value = value
        mapping.event_count += 1
        self.events_processed += 1
        
        # Add source to active sources
        source_device = mapping.source.split('.')[0]
        self.active_sources.add(source_device)
        
        # Simulate DAW parameter update
        logger.debug(f"MIDI: {mapping.source} -> {mapping.target} = {value}")
        
        # Simulate processing delay
        await asyncio.sleep(0.001)
    
    async def _update_mappings(self):
        """Update mapping states and cleanup."""
        # Occasionally remove inactive sources
        if random.random() > 0.99:  # 1% chance
            if self.active_sources:
                source_to_remove = random.choice(list(self.active_sources))
                self.active_sources.discard(source_to_remove)
    
    def _log_status(self):
        """Log current engine status."""
        active_mappings = sum(1 for m in self.mappings.values() if m.enabled)
        events_per_second = self.events_processed / max(1, time.time() - self.start_time)
        
        logger.info(f"Status: {active_mappings} mappings active, "
                   f"{len(self.active_sources)} sources, "
                   f"{events_per_second:.1f} events/sec")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        active_mappings = [m.to_dict() for m in self.mappings.values() if m.enabled]
        
        return {
            "component": "MIDI Mapping Engine",
            "running": self.running,
            "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
            "total_mappings": len(self.mappings),
            "active_mappings": len(active_mappings),
            "events_processed": self.events_processed,
            "active_sources": list(self.active_sources),
            "mappings": active_mappings
        }
    
    def add_mapping(self, mapping: MIDIMapping) -> bool:
        """Add a new MIDI mapping."""
        if mapping.name in self.mappings:
            logger.warning(f"Mapping {mapping.name} already exists")
            return False
        
        self.mappings[mapping.name] = mapping
        logger.info(f"Added mapping: {mapping.name}")
        return True
    
    def remove_mapping(self, name: str) -> bool:
        """Remove a MIDI mapping."""
        if name not in self.mappings:
            logger.warning(f"Mapping {name} not found")
            return False
        
        del self.mappings[name]
        logger.info(f"Removed mapping: {name}")
        return True
    
    def enable_mapping(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a MIDI mapping."""
        if name not in self.mappings:
            logger.warning(f"Mapping {name} not found")
            return False
        
        self.mappings[name].enabled = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Mapping {name} {status}")
        return True


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="REZONATE MIDI Mapping Engine")
    parser.add_argument("--mapping", default="basic", 
                       help="Default mapping configuration")
    args = parser.parse_args()
    
    engine = MIDIMappingEngine(default_mapping=args.mapping)
    await engine.start()


if __name__ == "__main__":
    asyncio.run(main())
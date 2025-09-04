#!/usr/bin/env python3
"""
Splunk Logger for NMEA Parser
Handles sending parsed NMEA data to Splunk for analysis and storage.
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from queue import Queue, Empty
import logging

# Splunk SDK imports with fallback
try:
    import splunklib.client as client
    import splunklib.results as results
    from splunklib.binding import HTTPError
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False
    client = None
    results = None
    HTTPError = Exception

from splunk_config import SplunkConfig

# Set up logging
logger = logging.getLogger(__name__)

class SplunkLogger:
    """
    Handles sending NMEA data to Splunk with batching and error handling
    """
    
    def __init__(self, config: SplunkConfig):
        """Initialize the Splunk logger with configuration"""
        self.config = config
        self.service = None
        self.index = None
        self.connected = False
        
        # Batching system
        self.event_queue = Queue()
        self.batch_thread = None
        self.shutdown_event = threading.Event()
        self.stats = {
            'events_sent': 0,
            'events_failed': 0,
            'batches_sent': 0,
            'connection_errors': 0,
            'last_error': None
        }
        
        # Check if Splunk SDK is available
        if not SPLUNK_AVAILABLE:
            raise ImportError(
                "Splunk SDK not available. Install with: pip install splunk-sdk"
            )
    
    def connect(self) -> bool:
        """Establish connection to Splunk"""
        try:
            # Validate configuration
            is_valid, error = self.config.validate()
            if not is_valid:
                logger.error(f"Invalid Splunk configuration: {error}")
                return False
            
            # Create Splunk service connection
            connection_params = self.config.get_connection_params()
            self.service = client.connect(**connection_params)
            
            # Test the connection
            self.service.info()  # This will raise an exception if connection fails
            
            # Get or create the index
            try:
                self.index = self.service.indexes[self.config.index]
            except KeyError:
                logger.warning(f"Index '{self.config.index}' not found. Creating it...")
                self.service.indexes.create(self.config.index)
                self.index = self.service.indexes[self.config.index]
            
            self.connected = True
            logger.info(f"Connected to Splunk at {self.config.host}:{self.config.port}")
            logger.info(f"Using index: {self.config.index}")
            
            # Start batch processing thread
            self._start_batch_thread()
            
            return True
            
        except HTTPError as e:
            error_msg = f"Splunk HTTP error: {e}"
            logger.error(error_msg)
            self.stats['last_error'] = error_msg
            self.stats['connection_errors'] += 1
            return False
            
        except Exception as e:
            error_msg = f"Failed to connect to Splunk: {e}"
            logger.error(error_msg)
            self.stats['last_error'] = error_msg
            self.stats['connection_errors'] += 1
            return False
    
    def disconnect(self):
        """Disconnect from Splunk and cleanup resources"""
        logger.info("Disconnecting from Splunk...")
        
        # Signal shutdown and wait for batch thread to finish
        self.shutdown_event.set()
        if self.batch_thread and self.batch_thread.is_alive():
            self.batch_thread.join(timeout=5)
        
        # Send any remaining events
        self._flush_remaining_events()
        
        self.connected = False
        self.service = None
        self.index = None
        
        logger.info("Disconnected from Splunk")
    
    def log_nmea_data(self, parsed_data: Dict, raw_sentence: str = None):
        """Queue NMEA data for sending to Splunk"""
        if not self.connected:
            logger.warning("Not connected to Splunk. Data will be lost.")
            return False
        
        # Create Splunk event
        event = self._create_splunk_event(parsed_data, raw_sentence)
        
        # Add to queue for batch processing
        try:
            self.event_queue.put_nowait(event)
            return True
        except Exception as e:
            logger.error(f"Failed to queue event: {e}")
            return False
    
    def log_summary_data(self, summary_data: Dict):
        """Send summary data to Splunk"""
        if not self.connected:
            logger.warning("Not connected to Splunk. Summary data will be lost.")
            return False
        
        # Create summary event
        event = {
            'event': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': 'nmea_summary',
                'data': summary_data
            },
            'source': self.config.source,
            'sourcetype': f"{self.config.sourcetype}:summary"
        }
        
        try:
            self.event_queue.put_nowait(event)
            return True
        except Exception as e:
            logger.error(f"Failed to queue summary event: {e}")
            return False
    
    def _create_splunk_event(self, parsed_data: Dict, raw_sentence: str = None) -> Dict:
        """Create a Splunk event from parsed NMEA data"""
        event_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'nmea_sentence',
            'sentence_type': parsed_data.get('type', 'unknown'),
            'parsed_data': parsed_data
        }
        
        # Add raw sentence if provided
        if raw_sentence:
            event_data['raw_sentence'] = raw_sentence
        
        # Add location data if available
        if 'latitude' in parsed_data and 'longitude' in parsed_data:
            event_data['location'] = {
                'lat': parsed_data['latitude'],
                'lon': parsed_data['longitude']
            }
            
            # Add altitude if available
            if 'altitude' in parsed_data:
                event_data['location']['alt'] = parsed_data['altitude']
        
        # Add time information if available
        if 'time' in parsed_data:
            event_data['nmea_time'] = parsed_data['time']
        
        if 'date' in parsed_data:
            event_data['nmea_date'] = parsed_data['date']
        
        return {
            'event': event_data,
            'source': self.config.source,
            'sourcetype': self.config.sourcetype
        }
    
    def _start_batch_thread(self):
        """Start the background thread for batch processing"""
        self.batch_thread = threading.Thread(
            target=self._batch_processor,
            name="SplunkBatchProcessor",
            daemon=True
        )
        self.batch_thread.start()
        logger.info("Started Splunk batch processing thread")
    
    def _batch_processor(self):
        """Background thread that processes events in batches"""
        batch = []
        last_send_time = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                # Try to get an event with timeout
                try:
                    event = self.event_queue.get(timeout=1)
                    batch.append(event)
                except Empty:
                    pass
                
                # Send batch if it's full or timeout reached
                current_time = time.time()
                should_send = (
                    len(batch) >= self.config.batch_size or
                    (batch and (current_time - last_send_time) >= self.config.batch_timeout)
                )
                
                if should_send and batch:
                    self._send_batch(batch)
                    batch = []
                    last_send_time = current_time
                    
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                time.sleep(1)
        
        # Send any remaining events before shutdown
        if batch:
            self._send_batch(batch)
    
    def _send_batch(self, events: List[Dict]):
        """Send a batch of events to Splunk"""
        if not self.connected or not self.index:
            logger.warning("Not connected to Splunk, dropping batch")
            self.stats['events_failed'] += len(events)
            return
        
        try:
            # Convert events to JSON strings
            json_events = []
            for event in events:
                json_events.append(json.dumps(event))
            
            # Submit to Splunk
            self.index.submit('\n'.join(json_events))
            
            # Update stats
            self.stats['events_sent'] += len(events)
            self.stats['batches_sent'] += 1
            
            logger.debug(f"Successfully sent batch of {len(events)} events to Splunk")
            
        except Exception as e:
            error_msg = f"Failed to send batch to Splunk: {e}"
            logger.error(error_msg)
            self.stats['events_failed'] += len(events)
            self.stats['last_error'] = error_msg
    
    def _flush_remaining_events(self):
        """Send any remaining events in the queue"""
        remaining_events = []
        
        # Collect all remaining events
        try:
            while True:
                event = self.event_queue.get_nowait()
                remaining_events.append(event)
        except Empty:
            pass
        
        # Send them if any exist
        if remaining_events:
            logger.info(f"Flushing {len(remaining_events)} remaining events")
            self._send_batch(remaining_events)
    
    def get_stats(self) -> Dict:
        """Get statistics about Splunk logging"""
        return self.stats.copy()
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test the Splunk connection"""
        try:
            if not self.connected:
                return False, "Not connected to Splunk"
            
            # Try to get server info
            info = self.service.info()
            server_name = info.get('serverName', 'unknown')
            version = info.get('version', 'unknown')
            
            return True, f"Connected to {server_name} (version {version})"
            
        except Exception as e:
            return False, str(e)

def create_splunk_logger(config: Optional[SplunkConfig] = None) -> Optional[SplunkLogger]:
    """Factory function to create and connect a Splunk logger"""
    if not SPLUNK_AVAILABLE:
        logger.error("Splunk SDK not available. Install with: pip install splunk-sdk")
        return None
    
    if config is None:
        config = SplunkConfig()
    
    splunk_logger = SplunkLogger(config)
    
    if splunk_logger.connect():
        return splunk_logger
    else:
        logger.error("Failed to connect to Splunk")
        return None

if __name__ == "__main__":
    # Demo the Splunk logger
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config and logger
    config = SplunkConfig()
    print(f"Testing Splunk connection to {config.host}:{config.port}")
    
    splunk_logger = create_splunk_logger(config)
    
    if splunk_logger:
        # Test connection
        is_connected, message = splunk_logger.test_connection()
        print(f"Connection test: {'✅' if is_connected else '❌'} {message}")
        
        # Send test data
        test_data = {
            'type': 'GPGGA',
            'time': '123456.0',
            'latitude': 47.558472,
            'longitude': -52.752907,
            'fix_quality': 'GPS fix (SPS)',
            'num_satellites': 8
        }
        
        print("Sending test NMEA data...")
        success = splunk_logger.log_nmea_data(test_data, "$GPGGA,123456.0,4733.508,N,05245.175,W,1,08,1.0,545.4,M,46.9,M,,*47")
        print(f"Send result: {'✅' if success else '❌'}")
        
        # Wait a bit for batch processing
        time.sleep(2)
        
        # Show stats
        stats = splunk_logger.get_stats()
        print("\nSplunk Logger Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Disconnect
        splunk_logger.disconnect()
    else:
        print("❌ Failed to create Splunk logger")
        sys.exit(1)

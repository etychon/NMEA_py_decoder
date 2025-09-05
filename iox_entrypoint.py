#!/usr/bin/env python3
"""
IOx Entry Point for NMEA Parser
Handles IOx-specific initialization and configuration
"""

import os
import sys
import json
import time
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, '/app')

# Import the main NMEA parser
from nmea_parser import NMEAParser, UDPReceiver, create_argument_parser
from iox_config import IOxConfig
from web_interface import NMEAWebServer

class IOxNMEAService:
    """IOx service wrapper for NMEA Parser"""
    
    def __init__(self):
        self.config = IOxConfig()
        self.nmea_parser = NMEAParser()
        self.udp_receiver = None
        self.web_server = None
        self.running = False
        self.stats = {
            'start_time': None,
            'sentences_processed': 0,
            'last_position': None,
            'uptime_seconds': 0
        }
        
        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _setup_logging(self):
        """Configure logging for IOx environment"""
        log_level = os.getenv('NMEA_LOG_LEVEL', 'INFO').upper()
        log_file = '/app/logs/nmea_parser.log'
        
        # Create logs directory if it doesn't exist
        Path('/app/logs').mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        
    def start(self):
        """Start the NMEA service"""
        self.logger.info("Starting IOx NMEA Parser Service")
        self.logger.info(f"Configuration: {self.config.get_summary()}")
        
        self.running = True
        self.stats['start_time'] = time.time()
        
        try:
            # Start web interface
            self.web_server = NMEAWebServer(
                port=self.config.health_check_port,
                host='0.0.0.0'
            )
            if not self.web_server.start():
                self.logger.warning("Failed to start web interface")
            
            if self.config.mode == 'udp':
                self._start_udp_mode()
            elif self.config.mode == 'file':
                self._start_file_mode()
            else:
                self.logger.error(f"Unknown mode: {self.config.mode}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
            
        return True
        
    def _start_udp_mode(self):
        """Start UDP receiver mode"""
        self.logger.info(f"Starting UDP receiver on port {self.config.udp_port}")
        
        # Create UDP receiver
        self.udp_receiver = UDPReceiver(
            port=self.config.udp_port,
            host=self.config.udp_host,
            buffer_size=self.config.udp_buffer_size
        )
        
        # Set up callbacks
        self.udp_receiver.set_data_callback(self._process_nmea_sentence)
        self.udp_receiver.set_error_callback(self._handle_error)
        
        # Set up position tracking if enabled
        if self.config.track_position:
            self.nmea_parser.add_position_callback(self._position_callback)
            
        # Start UDP receiver
        if not self.udp_receiver.start():
            raise RuntimeError("Failed to start UDP receiver")
            
        self.logger.info("UDP receiver started successfully")
        
        # Main service loop
        self._service_loop()
        
    def _start_file_mode(self):
        """Start file processing mode"""
        if not self.config.input_file or not os.path.exists(self.config.input_file):
            raise RuntimeError(f"Input file not found: {self.config.input_file}")
            
        self.logger.info(f"Processing file: {self.config.input_file}")
        
        try:
            with open(self.config.input_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not self.running:
                        break
                        
                    line = line.strip()
                    if line and line.startswith('$'):
                        self._process_nmea_sentence(line)
                        
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            
        self.logger.info("File processing completed")
        
    def _process_nmea_sentence(self, sentence: str):
        """Process a single NMEA sentence"""
        try:
            result = self.nmea_parser.parse_sentence(sentence)
            if result:
                self.stats['sentences_processed'] += 1
                
                # Log position updates
                if result.get('type') in ['GGA', 'RMC'] and result.get('latitude') and result.get('longitude'):
                    self.stats['last_position'] = {
                        'latitude': result['latitude'],
                        'longitude': result['longitude'],
                        'altitude': result.get('altitude'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                # Log to file if verbose logging enabled
                if self.config.verbose_logging:
                    self.logger.debug(f"Parsed {result['type']}: {result}")
                    
        except Exception as e:
            self.logger.error(f"Error processing sentence '{sentence}': {e}")
            
    def _position_callback(self, position_info):
        """Handle position updates"""
        lat = position_info.get('latitude')
        lon = position_info.get('longitude')
        alt = position_info.get('altitude')
        
        if lat and lon:
            self.logger.info(f"Position update: {lat:.6f}°, {lon:.6f}°" + 
                           (f", {alt:.1f}m" if alt else ""))
            
            # Check movement if enabled
            if 'movement' in position_info:
                movement = position_info['movement']
                if movement['is_moving']:
                    self.logger.info(f"Movement: {movement['distance_m']:.1f}m at {movement['bearing_deg']:.1f}°, "
                                   f"{movement['speed_knots']:.1f} knots")
                                   
    def _handle_error(self, error_msg: str):
        """Handle errors from UDP receiver"""
        self.logger.error(f"UDP Error: {error_msg}")
        
    def _service_loop(self):
        """Main service loop"""
        last_stats_time = time.time()
        
        while self.running:
            try:
                time.sleep(1)
                
                # Update uptime
                self.stats['uptime_seconds'] = time.time() - self.stats['start_time']
                
                # Log periodic statistics
                current_time = time.time()
                if current_time - last_stats_time >= self.config.stats_interval:
                    self._log_statistics()
                    last_stats_time = current_time
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in service loop: {e}")
                time.sleep(5)  # Brief pause before continuing
                
    def _log_statistics(self):
        """Log service statistics"""
        stats = self.get_stats()
        self.logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        
        # Save stats to file for web interface
        try:
            stats_file = Path('/app/logs/stats.json')
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
        
    def stop(self):
        """Stop the service"""
        self.logger.info("Stopping NMEA service...")
        self.running = False
        
        if self.udp_receiver:
            self.udp_receiver.stop()
            
        if self.web_server:
            self.web_server.stop()
            
        # Force processing of any pending blocks
        self.nmea_parser.force_block_processing()
        
        self.logger.info("NMEA service stopped")
        
    def get_stats(self):
        """Get service statistics"""
        stats = self.stats.copy()
        
        # Add UDP receiver stats if available
        if self.udp_receiver:
            udp_stats = self.udp_receiver.get_stats()
            stats.update({
                'udp_packets_received': udp_stats.get('packets_received', 0),
                'udp_bytes_received': udp_stats.get('bytes_received', 0),
                'udp_parse_errors': udp_stats.get('parse_errors', 0)
            })
            
        # Add NMEA parser stats
        if self.nmea_parser.position:
            lat, lon, alt = self.nmea_parser.position
            stats['current_position'] = {
                'latitude': lat,
                'longitude': lon,
                'altitude': alt
            }
            
        if self.nmea_parser.satellites:
            stats['satellite_count'] = sum(len(sats) for sats in self.nmea_parser.satellites.values())
            
        return stats
        
    def health_check(self):
        """Perform health check for IOx monitoring"""
        try:
            # Check if service is running
            if not self.running:
                return False, "Service not running"
                
            # Check UDP receiver if in UDP mode
            if self.config.mode == 'udp' and self.udp_receiver:
                if not self.udp_receiver.is_running():
                    return False, "UDP receiver not running"
                    
            # Check if we've received data recently (if in UDP mode)
            if self.config.mode == 'udp' and self.udp_receiver:
                udp_stats = self.udp_receiver.get_stats()
                if udp_stats.get('last_packet_time'):
                    time_since_last = time.time() - udp_stats['last_packet_time']
                    if time_since_last > 300:  # 5 minutes
                        return False, f"No data received for {time_since_last:.0f} seconds"
                        
            return True, "Service healthy"
            
        except Exception as e:
            return False, f"Health check error: {e}"

def main():
    """Main entry point for IOx service"""
    service = IOxNMEAService()
    
    try:
        # Start the service
        if service.start():
            service.logger.info("NMEA service started successfully")
            
            # Keep the service running
            while service.running:
                time.sleep(1)
        else:
            service.logger.error("Failed to start NMEA service")
            sys.exit(1)
            
    except KeyboardInterrupt:
        service.logger.info("Service interrupted by user")
    except Exception as e:
        service.logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        service.stop()
        
    service.logger.info("IOx NMEA service exited")

if __name__ == "__main__":
    main()

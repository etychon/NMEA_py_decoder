#!/usr/bin/env python3
"""
IOx Configuration Management for NMEA Parser
Handles environment variables and configuration for Cisco IOx deployment
"""

import os
import json
import logging
from typing import Dict, Any, Optional

class IOxConfig:
    """Configuration manager for IOx deployment"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.logger = logging.getLogger(__name__)
        
        # Service mode configuration
        self.mode = os.getenv('NMEA_MODE', 'udp').lower()
        
        # UDP configuration
        self.udp_port = int(os.getenv('NMEA_UDP_PORT', '4001'))
        self.udp_host = os.getenv('NMEA_UDP_HOST', '0.0.0.0')
        self.udp_buffer_size = int(os.getenv('NMEA_UDP_BUFFER_SIZE', '4096'))
        
        # File input configuration
        self.input_file = os.getenv('NMEA_INPUT_FILE', '/app/examples/basic_gps.nmea')
        
        # Output configuration
        self.continuous = self._get_bool_env('NMEA_CONTINUOUS', True)
        self.json_output = self._get_bool_env('NMEA_JSON_OUTPUT', False)
        self.verbose_logging = self._get_bool_env('NMEA_VERBOSE_LOGGING', False)
        
        # Position tracking
        self.track_position = self._get_bool_env('NMEA_TRACK_POSITION', True)
        self.min_movement = float(os.getenv('NMEA_MIN_MOVEMENT', '1.0'))
        
        # Geofencing (JSON format)
        self.geofences = self._parse_geofences()
        
        # Statistics and monitoring
        self.stats_interval = int(os.getenv('NMEA_STATS_INTERVAL', '300'))  # 5 minutes
        
        # Splunk integration
        self.splunk_enabled = self._get_bool_env('NMEA_SPLUNK_ENABLED', False)
        self.splunk_config = self._get_splunk_config()
        
        # IOx specific settings
        self.health_check_port = int(os.getenv('NMEA_HEALTH_PORT', '8080'))
        self.log_retention_days = int(os.getenv('NMEA_LOG_RETENTION_DAYS', '7'))
        
        # Validate configuration
        self._validate_config()
        
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
        
    def _parse_geofences(self) -> list:
        """Parse geofences from environment variable"""
        geofences_json = os.getenv('NMEA_GEOFENCES', '[]')
        try:
            geofences = json.loads(geofences_json)
            # Validate geofence format
            valid_geofences = []
            for fence in geofences:
                if all(key in fence for key in ['lat', 'lon', 'radius', 'name']):
                    valid_geofences.append({
                        'lat': float(fence['lat']),
                        'lon': float(fence['lon']),
                        'radius': float(fence['radius']),
                        'name': str(fence['name'])
                    })
                else:
                    self.logger.warning(f"Invalid geofence format: {fence}")
            return valid_geofences
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing geofences JSON: {e}")
            return []
            
    def _get_splunk_config(self) -> Dict[str, Any]:
        """Get Splunk configuration from environment"""
        return {
            'host': os.getenv('SPLUNK_HOST', 'localhost'),
            'port': int(os.getenv('SPLUNK_PORT', '8089')),
            'username': os.getenv('SPLUNK_USERNAME', 'admin'),
            'password': os.getenv('SPLUNK_PASSWORD', 'changeme'),
            'scheme': os.getenv('SPLUNK_SCHEME', 'https'),
            'index': os.getenv('SPLUNK_INDEX', 'nmea_data'),
            'source': os.getenv('SPLUNK_SOURCE', 'nmea_parser_iox'),
            'sourcetype': os.getenv('SPLUNK_SOURCETYPE', 'nmea:json'),
            'verify_ssl': self._get_bool_env('SPLUNK_VERIFY_SSL', False),
            'timeout': int(os.getenv('SPLUNK_TIMEOUT', '30')),
            'batch_size': int(os.getenv('SPLUNK_BATCH_SIZE', '100')),
            'batch_timeout': int(os.getenv('SPLUNK_BATCH_TIMEOUT', '10'))
        }
        
    def _validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate mode
        if self.mode not in ['udp', 'file']:
            errors.append(f"Invalid mode: {self.mode}. Must be 'udp' or 'file'")
            
        # Validate UDP port
        if not (1 <= self.udp_port <= 65535):
            errors.append(f"Invalid UDP port: {self.udp_port}. Must be 1-65535")
            
        # Validate file input if in file mode
        if self.mode == 'file' and not os.path.exists(self.input_file):
            self.logger.warning(f"Input file not found: {self.input_file}")
            
        # Validate movement threshold
        if self.min_movement < 0:
            errors.append(f"Invalid min_movement: {self.min_movement}. Must be >= 0")
            
        # Validate stats interval
        if self.stats_interval < 10:
            errors.append(f"Invalid stats_interval: {self.stats_interval}. Must be >= 10 seconds")
            
        if errors:
            error_msg = "Configuration validation errors:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
            
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            'mode': self.mode,
            'udp_port': self.udp_port if self.mode == 'udp' else None,
            'udp_host': self.udp_host if self.mode == 'udp' else None,
            'input_file': self.input_file if self.mode == 'file' else None,
            'track_position': self.track_position,
            'geofences_count': len(self.geofences),
            'splunk_enabled': self.splunk_enabled,
            'continuous': self.continuous,
            'json_output': self.json_output,
            'stats_interval': self.stats_interval
        }
        
    def get_nmea_parser_args(self) -> Dict[str, Any]:
        """Get arguments for NMEA parser in the format it expects"""
        args = {
            'udp': self.udp_port if self.mode == 'udp' else None,
            'udp_host': self.udp_host,
            'udp_buffer': self.udp_buffer_size,
            'filename': self.input_file if self.mode == 'file' else None,
            'continuous': self.continuous,
            'json': self.json_output,
            'verbose': self.verbose_logging,
            'track_position': self.track_position,
            'min_movement': self.min_movement,
            'geofence': self._format_geofences_for_parser(),
            'splunk': self.splunk_enabled,
            'no_color': True,  # Disable colors in IOx environment
            'interactive': False
        }
        
        # Remove None values
        return {k: v for k, v in args.items() if v is not None}
        
    def _format_geofences_for_parser(self) -> list:
        """Format geofences for the NMEA parser"""
        formatted = []
        for fence in self.geofences:
            formatted.append([
                str(fence['lat']),
                str(fence['lon']),
                str(fence['radius']),
                fence['name']
            ])
        return formatted if formatted else None
        
    def save_to_file(self, filepath: str):
        """Save current configuration to file"""
        config_data = {
            'timestamp': os.environ.get('TIMESTAMP', 'unknown'),
            'iox_app_name': os.environ.get('IOX_APP_NAME', 'nmea-parser'),
            'configuration': self.get_summary(),
            'environment_variables': {
                k: v for k, v in os.environ.items() 
                if k.startswith(('NMEA_', 'SPLUNK_', 'IOX_'))
            }
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            
    @classmethod
    def create_sample_env_file(cls, filepath: str = '/app/sample.env'):
        """Create a sample environment file with all configuration options"""
        sample_config = """# NMEA Parser IOx Configuration
# Copy this file to .env and modify as needed

# Service Mode: 'udp' or 'file'
NMEA_MODE=udp

# UDP Configuration (for udp mode)
NMEA_UDP_PORT=4001
NMEA_UDP_HOST=0.0.0.0
NMEA_UDP_BUFFER_SIZE=4096

# File Input (for file mode)
NMEA_INPUT_FILE=/app/examples/basic_gps.nmea

# Output Configuration
NMEA_CONTINUOUS=true
NMEA_JSON_OUTPUT=false
NMEA_VERBOSE_LOGGING=false

# Position Tracking
NMEA_TRACK_POSITION=true
NMEA_MIN_MOVEMENT=1.0

# Geofencing (JSON array format)
# NMEA_GEOFENCES='[{"lat": 50.612, "lon": 5.587, "radius": 100, "name": "Home Base"}]'

# Statistics and Monitoring
NMEA_STATS_INTERVAL=300

# Splunk Integration (optional)
NMEA_SPLUNK_ENABLED=false
SPLUNK_HOST=splunk.company.com
SPLUNK_PORT=8089
SPLUNK_USERNAME=nmea_user
SPLUNK_PASSWORD=secure_password
SPLUNK_INDEX=nmea_data
SPLUNK_VERIFY_SSL=false

# IOx Specific
NMEA_HEALTH_PORT=8080
NMEA_LOG_RETENTION_DAYS=7

# Python Configuration
PYTHONUNBUFFERED=1
NMEA_LOG_LEVEL=INFO
"""
        
        try:
            with open(filepath, 'w') as f:
                f.write(sample_config)
            print(f"Sample environment file created: {filepath}")
        except Exception as e:
            print(f"Failed to create sample env file: {e}")

def main():
    """Test configuration loading"""
    try:
        config = IOxConfig()
        print("Configuration loaded successfully:")
        print(json.dumps(config.get_summary(), indent=2))
        
        # Create sample env file
        IOxConfig.create_sample_env_file()
        
    except Exception as e:
        print(f"Configuration error: {e}")

if __name__ == "__main__":
    main()

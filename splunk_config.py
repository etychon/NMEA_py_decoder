#!/usr/bin/env python3
"""
Splunk Configuration for NMEA Parser
Contains configuration settings and connection parameters for Splunk integration.
"""

import os
from typing import Dict, Optional

class SplunkConfig:
    """Configuration class for Splunk connection parameters"""
    
    def __init__(self):
        """Initialize configuration with default values and environment variables"""
        # Default Splunk connection parameters
        self.host = os.getenv('SPLUNK_HOST', 'localhost')
        self.port = int(os.getenv('SPLUNK_PORT', '8089'))
        self.username = os.getenv('SPLUNK_USERNAME', 'admin')
        self.password = os.getenv('SPLUNK_PASSWORD', 'changeme')
        self.scheme = os.getenv('SPLUNK_SCHEME', 'https')
        
        # Splunk indexing parameters
        self.index = os.getenv('SPLUNK_INDEX', 'nmea_data')
        self.source = os.getenv('SPLUNK_SOURCE', 'nmea_parser')
        self.sourcetype = os.getenv('SPLUNK_SOURCETYPE', 'nmea:json')
        
        # Connection settings
        self.verify_ssl = os.getenv('SPLUNK_VERIFY_SSL', 'false').lower() == 'true'
        self.timeout = int(os.getenv('SPLUNK_TIMEOUT', '30'))
        
        # Batch settings for performance
        self.batch_size = int(os.getenv('SPLUNK_BATCH_SIZE', '100'))
        self.batch_timeout = int(os.getenv('SPLUNK_BATCH_TIMEOUT', '10'))
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary format"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': '***',  # Don't expose password in logs
            'scheme': self.scheme,
            'index': self.index,
            'source': self.source,
            'sourcetype': self.sourcetype,
            'verify_ssl': self.verify_ssl,
            'timeout': self.timeout,
            'batch_size': self.batch_size,
            'batch_timeout': self.batch_timeout
        }
    
    def get_connection_params(self) -> Dict:
        """Get connection parameters for Splunk SDK"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'scheme': self.scheme
        }
    
    @classmethod
    def from_file(cls, config_file: str) -> 'SplunkConfig':
        """Load configuration from a file (future enhancement)"""
        # This could be implemented to read from JSON/YAML config files
        config = cls()
        # TODO: Implement file-based configuration loading
        return config
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration parameters"""
        if not self.host:
            return False, "Splunk host is required"
        
        if not self.username or not self.password:
            return False, "Splunk username and password are required"
        
        if not (1 <= self.port <= 65535):
            return False, f"Invalid port number: {self.port}"
        
        if self.scheme not in ['http', 'https']:
            return False, f"Invalid scheme: {self.scheme}. Must be 'http' or 'https'"
        
        if not self.index:
            return False, "Splunk index name is required"
        
        return True, None

# Example configuration for different environments
EXAMPLE_CONFIGS = {
    'development': {
        'SPLUNK_HOST': 'localhost',
        'SPLUNK_PORT': '8089',
        'SPLUNK_USERNAME': 'admin',
        'SPLUNK_PASSWORD': 'changeme',
        'SPLUNK_INDEX': 'nmea_dev',
        'SPLUNK_VERIFY_SSL': 'false'
    },
    'production': {
        'SPLUNK_HOST': 'splunk.company.com',
        'SPLUNK_PORT': '8089',
        'SPLUNK_USERNAME': 'nmea_service',
        'SPLUNK_PASSWORD': 'secure_password',
        'SPLUNK_INDEX': 'maritime_data',
        'SPLUNK_VERIFY_SSL': 'true'
    },
    'cloud': {
        'SPLUNK_HOST': 'input-prd-p-xyz.cloud.splunk.com',
        'SPLUNK_PORT': '8088',  # HEC port
        'SPLUNK_INDEX': 'nmea_maritime',
        'SPLUNK_VERIFY_SSL': 'true'
    }
}

def print_config_help():
    """Print help information about configuration options"""
    print("Splunk Configuration Options:")
    print("=" * 50)
    print()
    print("Environment Variables:")
    print("  SPLUNK_HOST         - Splunk server hostname/IP (default: localhost)")
    print("  SPLUNK_PORT         - Splunk management port (default: 8089)")
    print("  SPLUNK_USERNAME     - Splunk username (default: admin)")
    print("  SPLUNK_PASSWORD     - Splunk password (default: changeme)")
    print("  SPLUNK_SCHEME       - Connection scheme http/https (default: https)")
    print("  SPLUNK_INDEX        - Target index name (default: nmea_data)")
    print("  SPLUNK_SOURCE       - Source field value (default: nmea_parser)")
    print("  SPLUNK_SOURCETYPE   - Sourcetype field value (default: nmea:json)")
    print("  SPLUNK_VERIFY_SSL   - Verify SSL certificates (default: false)")
    print("  SPLUNK_TIMEOUT      - Connection timeout in seconds (default: 30)")
    print("  SPLUNK_BATCH_SIZE   - Events per batch (default: 100)")
    print("  SPLUNK_BATCH_TIMEOUT - Batch timeout in seconds (default: 10)")
    print()
    print("Example usage:")
    print("  export SPLUNK_HOST=splunk.company.com")
    print("  export SPLUNK_USERNAME=nmea_user")
    print("  export SPLUNK_PASSWORD=secure_password")
    print("  export SPLUNK_INDEX=maritime_data")
    print("  python3 nmea_parser.py --splunk data.nmea")

if __name__ == "__main__":
    # Demo the configuration system
    config = SplunkConfig()
    print("Current Splunk Configuration:")
    print("-" * 30)
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    
    print()
    is_valid, error = config.validate()
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print(f"❌ Configuration error: {error}")
    
    print()
    print_config_help()

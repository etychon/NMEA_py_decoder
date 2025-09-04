#!/usr/bin/env python3
"""
Splunk Integration Demo for NMEA Parser
Demonstrates how to use the NMEA parser with Splunk integration.
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path to import nmea_parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_json_output():
    """Demonstrate JSON output format"""
    print("=" * 60)
    print("JSON OUTPUT DEMO")
    print("=" * 60)
    print()
    
    # Import here to avoid dependency issues
    from nmea_parser import NMEAParser
    
    # Sample NMEA sentences
    sample_sentences = [
        "$GPGGA,183730.0,4733.508324,N,05245.174442,W,1,03,500.0,62.9,M,12.0,M,,*75",
        "$GPRMC,183730.0,A,4733.508324,N,05245.174442,W,12.5,285.0,270417,0.0,E,A*13",
        "$GPGSV,2,1,07,07,37,305,22,09,24,262,18,21,23,049,20,30,02,314,24*74"
    ]
    
    parser = NMEAParser()
    
    # Parse the sentences
    for sentence in sample_sentences:
        result = parser.parse_sentence(sentence)
        print(f"Parsed: {sentence}")
        print(f"Result: {result}")
        print()
    
    # Show JSON output
    print("JSON Output:")
    print("-" * 40)
    json_data = parser.to_json()
    print(json_data)
    print()
    
    # Show summary dictionary (what gets sent to Splunk)
    print("Summary Data (sent to Splunk):")
    print("-" * 40)
    summary = parser.get_summary_dict()
    print(json.dumps(summary, indent=2))

def demo_splunk_configuration():
    """Demonstrate Splunk configuration options"""
    print("=" * 60)
    print("SPLUNK CONFIGURATION DEMO")
    print("=" * 60)
    print()
    
    try:
        from splunk_config import SplunkConfig, EXAMPLE_CONFIGS
        
        # Show current configuration
        config = SplunkConfig()
        print("Current Configuration:")
        print("-" * 30)
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
        
        print()
        is_valid, error = config.validate()
        status = "✅ Valid" if is_valid else f"❌ Invalid: {error}"
        print(f"Configuration status: {status}")
        
        print()
        print("Example Configurations:")
        print("-" * 30)
        for env_name, env_config in EXAMPLE_CONFIGS.items():
            print(f"\n{env_name.upper()} Environment:")
            for key, value in env_config.items():
                print(f"  export {key}={value}")
                
    except ImportError:
        print("Splunk configuration not available (splunk-sdk not installed)")

def demo_batch_processing():
    """Demonstrate how batch processing would work"""
    print("=" * 60)
    print("BATCH PROCESSING DEMO")
    print("=" * 60)
    print()
    
    # Simulate batch processing
    events = []
    
    # Create sample events
    for i in range(5):
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'nmea_sentence',
            'sentence_type': 'GPGGA',
            'parsed_data': {
                'type': 'GGA',
                'time': f'18:37:{30+i}.000',
                'latitude': 47.558472 + (i * 0.001),
                'longitude': -52.752907 + (i * 0.001),
                'fix_quality': 'GPS fix (SPS)',
                'num_satellites': 8
            },
            'location': {
                'lat': 47.558472 + (i * 0.001),
                'lon': -52.752907 + (i * 0.001)
            }
        }
        events.append(event)
    
    print("Sample batch of events that would be sent to Splunk:")
    print("-" * 50)
    
    for i, event in enumerate(events, 1):
        print(f"Event {i}:")
        print(json.dumps(event, indent=2))
        print()
    
    print(f"Batch size: {len(events)} events")
    print("In production, these would be sent to Splunk in batches for efficiency")

def demo_splunk_searches():
    """Show example Splunk searches"""
    print("=" * 60)
    print("SPLUNK SEARCH EXAMPLES")
    print("=" * 60)
    print()
    
    searches = {
        "Track vessel movement": """
index=nmea_data event_type=nmea_sentence location.lat=* location.lon=*
| eval _time=strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
| timechart span=1m avg(location.lat) as latitude avg(location.lon) as longitude
        """.strip(),
        
        "Monitor GPS signal quality": """
index=nmea_data parsed_data.fix_quality=*
| stats count by parsed_data.fix_quality
| sort -count
        """.strip(),
        
        "Alert on position changes": """
index=nmea_data event_type=nmea_sentence location.lat=* location.lon=*
| streamstats current=f last(location.lat) as prev_lat last(location.lon) as prev_lon
| eval distance=sqrt(pow(location.lat-prev_lat,2)+pow(location.lon-prev_lon,2))
| where distance > 0.001
| table _time location.lat location.lon distance
        """.strip(),
        
        "Satellite constellation usage": """
index=nmea_data parsed_data.satellites{}
| spath parsed_data.satellites{}
| mvexpand parsed_data.satellites{}
| spath input="parsed_data.satellites{}"
| stats avg(snr) as avg_snr count as satellite_count by constellation
        """.strip()
    }
    
    for title, search in searches.items():
        print(f"{title}:")
        print("-" * len(title))
        print(search)
        print()

def main():
    """Run all demos"""
    print("NMEA Parser - Splunk Integration Demo")
    print("=" * 60)
    print()
    
    demos = [
        ("JSON Output Format", demo_json_output),
        ("Splunk Configuration", demo_splunk_configuration),
        ("Batch Processing", demo_batch_processing),
        ("Splunk Search Examples", demo_splunk_searches)
    ]
    
    for title, demo_func in demos:
        try:
            demo_func()
            print("\n" + "=" * 60 + "\n")
        except Exception as e:
            print(f"Error in {title}: {e}")
            print("\n" + "=" * 60 + "\n")
    
    print("Demo complete!")
    print()
    print("To use Splunk integration:")
    print("1. Install splunk-sdk: pip install splunk-sdk")
    print("2. Configure environment variables (see --splunk-config)")
    print("3. Test connection: python3 nmea_parser.py --splunk-test")
    print("4. Send data: python3 nmea_parser.py data.nmea --splunk")

if __name__ == "__main__":
    main()

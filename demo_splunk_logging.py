#!/usr/bin/env python3
"""
Demo script showing human-readable Splunk logging for different NMEA sentence types
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_splunk_logging():
    """Demonstrate human-readable Splunk logging"""
    print("🔗 SPLUNK INTEGRATION - Human-Readable Logging Demo")
    print("=" * 60)
    print()
    
    print("This demo shows the human-readable log output that appears")
    print("whenever NMEA data is sent to Splunk.")
    print()
    
    print("📋 SAMPLE OUTPUT:")
    print("-" * 30)
    print()
    
    # Simulate the log output
    print("📤 Splunk: GGA Position 47.558472°, -52.752907°, 62.9m at 18:37:30.000")
    print("📤 Splunk: GSV Satellites - 7 total, 4 with signal")
    print("📤 Splunk: GSA Fix - 3D fix, 3 satellites, HDOP 500.0")
    print("📤 Splunk: RMC Position 47.558472°, -52.752907° at 18:37:30.000")
    print("📤 Splunk: VTG Velocity - 22.4 knots @ 84.4°")
    print("📤 Splunk: PSTIS sentence")
    print("📤 Splunk: Summary - Position 47.558472°, -52.752907°, 62.9m")
    print("📤 Splunk: Summary - 2 constellations, 18 visible, 8 used")
    print("📤 Splunk: Summary - GPS fix (SPS), 3 satellites, HDOP 500.0")
    print("📤 Splunk: Summary data sent to index 'main'")
    print()
    
    print("🎯 LOG MESSAGE TYPES:")
    print("-" * 25)
    print()
    
    print("📍 Position Data (GGA/RMC):")
    print("   • Shows coordinates with precision")
    print("   • Includes altitude when available")
    print("   • Shows NMEA timestamp")
    print()
    
    print("🛰️  Satellite Data (GSV):")
    print("   • Total satellites in view")
    print("   • Count of satellites with signal")
    print("   • Constellation-specific data")
    print()
    
    print("🔧 Fix Data (GSA):")
    print("   • Fix type (2D/3D/No fix)")
    print("   • Number of satellites used")
    print("   • HDOP (accuracy) values")
    print()
    
    print("🚀 Velocity Data (VTG):")
    print("   • Speed in knots")
    print("   • Course/heading in degrees")
    print("   • Only shown when data available")
    print()
    
    print("📊 Summary Data:")
    print("   • Final position summary")
    print("   • Constellation statistics")
    print("   • Fix quality information")
    print("   • Target Splunk index")
    print()
    
    print("🔧 CONFIGURATION:")
    print("-" * 20)
    print()
    
    print("Set these environment variables for Splunk:")
    print("export SPLUNK_HOST=192.168.2.3")
    print("export SPLUNK_PORT=8089")
    print("export SPLUNK_USERNAME=admin")
    print("export SPLUNK_PASSWORD=\"your_password\"")
    print("export SPLUNK_INDEX=main")
    print("export SPLUNK_SCHEME=https")
    print("export SPLUNK_VERIFY_SSL=false")
    print()
    
    print("📝 USAGE EXAMPLES:")
    print("-" * 20)
    print()
    
    print("1. File processing with Splunk logging:")
    print("   python3 nmea_parser.py data.nmea --splunk")
    print()
    
    print("2. UDP streaming with Splunk logging:")
    print("   python3 nmea_parser.py --udp 4001 --splunk --continuous")
    print()
    
    print("3. Position tracking + Splunk logging:")
    print("   python3 nmea_parser.py --udp 4001 --track-position --splunk")
    print()
    
    print("✨ BENEFITS:")
    print("-" * 15)
    print()
    
    print("✅ Immediate feedback - see what's being sent to Splunk")
    print("✅ Debug assistance - verify data parsing is correct")
    print("✅ Monitoring capability - track data flow in real-time")
    print("✅ Quality assurance - ensure important data isn't lost")
    print("✅ Operational visibility - understand system behavior")
    print()
    
    print("🎊 The human-readable logs appear alongside the normal")
    print("   NMEA parsing output, giving you complete visibility")
    print("   into both local processing and Splunk integration!")

if __name__ == "__main__":
    demo_splunk_logging()

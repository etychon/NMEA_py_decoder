#!/usr/bin/env python3
"""
Real-time Position Processing Demo for NMEA Parser
Demonstrates various position processing callbacks and real-time coordinate handling.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add current directory to path to import nmea_parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nmea_parser import NMEAParser

class PositionTracker:
    """Example position tracking class with various processing capabilities"""
    
    def __init__(self):
        self.positions = []
        self.track_start_time = None
        self.total_distance = 0.0
        self.max_speed = 0.0
        self.geofence_alerts = []
        
        # Define some example geofences (lat, lon, radius_meters, name)
        self.geofences = [
            (50.6124, 5.5868, 100, "Home Base"),
            (50.6130, 5.5870, 50, "Waypoint Alpha"),
            (50.6120, 5.5860, 75, "Safety Zone")
        ]
    
    def process_position(self, position_info):
        """Main position processing callback"""
        if not position_info.get('latitude') or not position_info.get('longitude'):
            return
        
        self.positions.append(position_info)
        
        # Initialize tracking
        if self.track_start_time is None:
            self.track_start_time = datetime.now()
            print(f"🎯 {self._colorize('Position tracking started', 'success')}")
            self._print_position_details(position_info, is_first=True)
            return
        
        # Process movement
        if 'movement' in position_info:
            self._process_movement(position_info)
        
        # Check geofences
        self._check_geofences(position_info)
        
        # Print position update
        self._print_position_details(position_info)
    
    def _process_movement(self, position_info):
        """Process movement data"""
        movement = position_info['movement']
        
        # Update total distance
        self.total_distance += movement['distance_m']
        
        # Update max speed
        if movement['speed_knots'] > self.max_speed:
            self.max_speed = movement['speed_knots']
        
        # Movement alerts
        if movement['is_moving']:
            if movement['speed_knots'] > 10:  # > 10 knots
                print(f"⚠️  {self._colorize('High speed detected:', 'warning')} {movement['speed_knots']:.1f} knots")
            
            if movement['distance_m'] > 100:  # > 100m jump
                print(f"🚨 {self._colorize('Large position jump:', 'error')} {movement['distance_m']:.1f}m")
    
    def _check_geofences(self, position_info):
        """Check if position is within any geofences"""
        lat = position_info['latitude']
        lon = position_info['longitude']
        
        for fence_lat, fence_lon, radius, name in self.geofences:
            # Simple distance calculation for demo
            distance = self._calculate_distance(lat, lon, fence_lat, fence_lon)
            
            if distance <= radius:
                alert_key = f"{name}_{lat:.6f}_{lon:.6f}"
                if alert_key not in self.geofence_alerts:
                    self.geofence_alerts.append(alert_key)
                    print(f"📍 {self._colorize('Entered geofence:', 'info')} {name} ({distance:.1f}m from center)")
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Simple distance calculation (same as in NMEAParser)"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371000  # Earth's radius in meters
    
    def _print_position_details(self, position_info, is_first=False):
        """Print formatted position information"""
        lat = position_info['latitude']
        lon = position_info['longitude']
        alt = position_info.get('altitude')
        quality = position_info.get('fix_quality', 'Unknown')
        sats = position_info.get('num_satellites', 0)
        
        prefix = "🎯" if is_first else "📍"
        
        print(f"{prefix} {self._colorize('Position Update:', 'header')}")
        print(f"   Coordinates: {self._colorize(f'{lat:.6f}°, {lon:.6f}°', 'data')}")
        if alt is not None:
            print(f"   Altitude: {self._colorize(f'{alt:.1f}m', 'data')}")
        print(f"   Quality: {self._colorize(quality, 'info')} ({sats} satellites)")
        
        if 'movement' in position_info and not is_first:
            movement = position_info['movement']
            distance_text = f"{movement['distance_m']:.1f}m"
            bearing_text = f"{movement['bearing_deg']:.1f}°"
            speed_text = f"{movement['speed_knots']:.1f} knots"
            
            print(f"   Distance: {self._colorize(distance_text, 'data')}")
            print(f"   Bearing: {self._colorize(bearing_text, 'data')}")
            print(f"   Speed: {self._colorize(speed_text, 'data')}")
            if movement['is_moving']:
                print(f"   Status: {self._colorize('MOVING', 'success')}")
            else:
                print(f"   Status: {self._colorize('STATIONARY', 'warning')}")
        
        print()
    
    def _colorize(self, text, color_type):
        """Simple colorization (would use parser's colors in real implementation)"""
        colors = {
            'header': '\033[96m\033[1m',  # Bright cyan
            'success': '\033[92m\033[1m', # Bright green
            'warning': '\033[93m\033[1m', # Bright yellow
            'error': '\033[91m\033[1m',   # Bright red
            'info': '\033[97m\033[1m',    # Bright white
            'data': '\033[92m',           # Green
            'reset': '\033[0m'            # Reset
        }
        return f"{colors.get(color_type, '')}{text}{colors['reset']}"
    
    def get_tracking_summary(self):
        """Get tracking summary"""
        if not self.positions:
            return "No positions tracked"
        
        duration = (datetime.now() - self.track_start_time).total_seconds()
        
        summary = f"""
{self._colorize('=== TRACKING SUMMARY ===', 'header')}
Duration: {self._colorize(f'{duration:.1f}s', 'data')}
Total positions: {self._colorize(str(len(self.positions)), 'data')}
Total distance: {self._colorize(f'{self.total_distance:.1f}m', 'data')}
Max speed: {self._colorize(f'{self.max_speed:.1f} knots', 'data')}
Geofence entries: {self._colorize(str(len(self.geofence_alerts)), 'data')}
        """
        return summary

class LivePositionDisplay:
    """Simple live position display callback"""
    
    def __init__(self):
        self.position_count = 0
    
    def process_position(self, position_info):
        """Display position in a compact format"""
        self.position_count += 1
        lat = position_info.get('latitude', 0)
        lon = position_info.get('longitude', 0)
        
        # Show position with movement indicator
        movement_indicator = ""
        if 'movement' in position_info:
            if position_info['movement']['is_moving']:
                speed = position_info['movement']['speed_knots']
                movement_indicator = f" 🚀 {speed:.1f}kts"
            else:
                movement_indicator = " ⚓ STATIONARY"
        
        print(f"[{self.position_count:03d}] {lat:.6f}, {lon:.6f}{movement_indicator}")

class GeofenceMonitor:
    """Geofence monitoring callback"""
    
    def __init__(self, geofences):
        self.geofences = geofences  # List of (lat, lon, radius, name, callback)
        self.inside_zones = set()
    
    def process_position(self, position_info):
        """Monitor geofence entries and exits"""
        lat = position_info.get('latitude')
        lon = position_info.get('longitude')
        
        if not lat or not lon:
            return
        
        current_zones = set()
        
        for fence_lat, fence_lon, radius, name in self.geofences:
            distance = self._calculate_distance(lat, lon, fence_lat, fence_lon)
            
            if distance <= radius:
                current_zones.add(name)
                
                # Entry event
                if name not in self.inside_zones:
                    print(f"🟢 ENTERED: {name} (distance: {distance:.1f}m)")
        
        # Exit events
        for zone in self.inside_zones - current_zones:
            print(f"🔴 EXITED: {zone}")
        
        self.inside_zones = current_zones
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371000

def demo_position_processing():
    """Demonstrate position processing with file data"""
    print("=" * 60)
    print("POSITION PROCESSING DEMO - FILE MODE")
    print("=" * 60)
    print()
    
    # Create parser and position tracker
    parser = NMEAParser()
    tracker = PositionTracker()
    
    # Register the position callback
    parser.add_position_callback(tracker.process_position)
    
    print("Processing multi-constellation NMEA data...")
    print()
    
    # Process the test file
    try:
        with open('test_multi_constellation.nmea', 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and line.startswith('$'):
                    result = parser.parse_sentence(line)
                    # Position processing happens automatically via callback
    except FileNotFoundError:
        print("❌ Test file not found. Please run with UDP mode instead.")
        return
    
    # Show tracking summary
    print(tracker.get_tracking_summary())

def demo_live_position_callbacks():
    """Show different types of position callbacks"""
    print("=" * 60)
    print("LIVE POSITION CALLBACKS DEMO")
    print("=" * 60)
    print()
    
    # Create parser
    parser = NMEAParser()
    
    # Create different callback handlers
    tracker = PositionTracker()
    live_display = LivePositionDisplay()
    
    # Define geofences
    geofences = [
        (50.6124, 5.5868, 100, "Home Base"),
        (50.6130, 5.5870, 50, "Waypoint Alpha"),
    ]
    geofence_monitor = GeofenceMonitor(geofences)
    
    # Register multiple callbacks
    parser.add_position_callback(tracker.process_position)
    parser.add_position_callback(live_display.process_position)
    parser.add_position_callback(geofence_monitor.process_position)
    
    print("Registered position callbacks:")
    print("  📊 Position Tracker - Full tracking with movement analysis")
    print("  📱 Live Display - Compact position updates")
    print("  🏠 Geofence Monitor - Zone entry/exit alerts")
    print()
    print("All callbacks will be triggered for each new position received.")
    print()
    
    return parser, tracker

def main():
    """Run position processing demonstrations"""
    print("NMEA Parser - Real-time Position Processing Demo")
    print("=" * 60)
    print()
    
    print("This demo shows how to process GPS coordinates in real-time")
    print("every time a new position is received from NMEA data.")
    print()
    
    # Demo 1: File processing
    demo_position_processing()
    
    print("\n" + "=" * 60 + "\n")
    
    # Demo 2: Show callback system
    parser, tracker = demo_live_position_callbacks()
    
    print("Example Usage with UDP streaming:")
    print()
    print("1. Start UDP receiver with position processing:")
    print("   python3 position_processor_demo.py --udp 4001")
    print()
    print("2. Send test data:")
    print("   python3 udp_test_sender.py --moving --interval 0.5")
    print()
    print("3. Watch real-time position processing:")
    print("   - Distance calculations")
    print("   - Speed and bearing")
    print("   - Geofence monitoring")
    print("   - Movement detection")
    print()
    
    print("Position Processing Features:")
    print("✅ Real-time coordinate processing")
    print("✅ Movement detection and analysis")
    print("✅ Distance and bearing calculations")
    print("✅ Speed computation from position changes")
    print("✅ Geofence monitoring")
    print("✅ Position history tracking")
    print("✅ Multiple callback support")
    print("✅ Error-resistant callback system")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--udp":
        # UDP mode - integrate with real parser
        from nmea_parser import main as nmea_main
        
        # This would need integration with the main parser
        # For now, just run the demo
        print("UDP mode would integrate with main parser...")
        main()
    else:
        main()

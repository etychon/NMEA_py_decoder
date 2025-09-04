#!/usr/bin/env python3
"""
NMEA Parser - Converts NMEA sentences to human-readable format
Supports GPS position, time, satellite information, and more.
"""

import sys
import re
import json
import argparse
import socket
import threading
import time
import signal
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Callable
import math

# Color support
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Automatically reset colors after each print
    COLOR_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not available
    class MockColor:
        def __getattr__(self, name):
            return ''
    
    Fore = MockColor()
    Back = MockColor()
    Style = MockColor()
    COLOR_AVAILABLE = False

# Splunk integration support
try:
    from splunk_config import SplunkConfig
    from splunk_logger import SplunkLogger, create_splunk_logger
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False
    SplunkConfig = None
    SplunkLogger = None
    create_splunk_logger = None

class NMEAParser:
    def __init__(self):
        # Color utility methods
        self.colors = {
            'header': Fore.CYAN + Style.BRIGHT,
            'subheader': Fore.BLUE + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'warning': Fore.YELLOW + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'info': Fore.WHITE + Style.BRIGHT,
            'data': Fore.GREEN,
            'label': Fore.MAGENTA,
            'separator': Fore.CYAN,
            'reset': Style.RESET_ALL
        }
        
        # Position processing callbacks
        self.position_callbacks = []
        self.last_position = None
        self.position_history = []
        
        self.parsers = {
            'GPGGA': self.parse_gga,
            'GNGGA': self.parse_gga,
            'GPRMC': self.parse_rmc,
            'GNRMC': self.parse_rmc,
            'GPGSA': self.parse_gsa,
            'GNGSA': self.parse_gsa,
            'GPGSV': self.parse_gsv,
            'GLGSV': self.parse_gsv,
            'GAGSV': self.parse_gsv,
            'GBGSV': self.parse_gsv,
            'GPVTG': self.parse_vtg,
            'GNVTG': self.parse_vtg,
            'GNGNS': self.parse_gns,
            'PQXFI': self.parse_pqxfi,
        }
        
        # Store parsed data
        self.position = None
        self.time_info = None
        self.satellites = {}
        self.fix_info = None
        self.velocity = None
        
    def parse_sentence(self, sentence: str) -> Dict:
        """Parse a single NMEA sentence"""
        if not sentence.startswith('$'):
            return {}
            
        # Remove $ and split by comma
        parts = sentence[1:].split(',')
        if not parts:
            return {}
            
        sentence_type = parts[0]
        
        # Remove checksum if present
        if '*' in parts[-1]:
            parts[-1] = parts[-1].split('*')[0]
            
        if sentence_type in self.parsers:
            return self.parsers[sentence_type](parts)
        
        return {'type': sentence_type, 'raw': sentence}
    
    def parse_gga(self, parts: List[str]) -> Dict:
        """Parse GGA sentence - Global Positioning System Fix Data"""
        if len(parts) < 15:
            return {}
            
        result = {
            'type': 'GGA',
            'time': self.parse_time(parts[1]) if parts[1] else None,
            'latitude': self.parse_coordinate(parts[2], parts[3]) if parts[2] and parts[3] else None,
            'longitude': self.parse_coordinate(parts[4], parts[5]) if parts[4] and parts[5] else None,
            'fix_quality': self.get_fix_quality(parts[6]) if parts[6] else None,
            'num_satellites': int(parts[7]) if parts[7] else 0,
            'hdop': float(parts[8]) if parts[8] else None,
            'altitude': float(parts[9]) if parts[9] else None,
            'altitude_units': parts[10] if parts[10] else None,
            'geoid_height': float(parts[11]) if parts[11] else None,
            'geoid_units': parts[12] if parts[12] else None,
        }
        
        # Update stored data
        if result['latitude'] and result['longitude']:
            self.position = (result['latitude'], result['longitude'], result.get('altitude'))
            
            # Process new position in real-time
            self._process_new_position(result)
            
        if result['time']:
            self.time_info = result['time']
        if result['num_satellites']:
            self.fix_info = {
                'satellites': result['num_satellites'],
                'quality': result['fix_quality'],
                'hdop': result['hdop']
            }
            
        return result
    
    def parse_rmc(self, parts: List[str]) -> Dict:
        """Parse RMC sentence - Recommended Minimum Navigation Information"""
        if len(parts) < 13:
            return {}
            
        result = {
            'type': 'RMC',
            'time': self.parse_time(parts[1]) if parts[1] else None,
            'status': 'Active' if parts[2] == 'A' else 'Void',
            'latitude': self.parse_coordinate(parts[3], parts[4]) if parts[3] and parts[4] else None,
            'longitude': self.parse_coordinate(parts[5], parts[6]) if parts[5] and parts[6] else None,
            'speed_knots': float(parts[7]) if parts[7] else None,
            'course': float(parts[8]) if parts[8] else None,
            'date': self.parse_date(parts[9]) if parts[9] else None,
            'magnetic_variation': float(parts[10]) if parts[10] else None,
            'mag_var_direction': parts[11] if parts[11] else None,
        }
        
        # Update stored data
        if result['latitude'] and result['longitude']:
            self.position = (result['latitude'], result['longitude'], None)
            
            # Process new position in real-time
            self._process_new_position(result)
            
        if result['time']:
            self.time_info = result['time']
        if result['speed_knots'] is not None:
            self.velocity = {
                'speed_knots': result['speed_knots'],
                'speed_kmh': result['speed_knots'] * 1.852,
                'course': result['course']
            }
            
        return result
    
    def parse_gsa(self, parts: List[str]) -> Dict:
        """Parse GSA sentence - GPS DOP and active satellites"""
        if len(parts) < 18:
            return {}
            
        satellites_used = [int(s) for s in parts[3:15] if s]
        
        result = {
            'type': 'GSA',
            'mode': parts[1],  # A=automatic, M=manual
            'fix_type': self.get_fix_type(parts[2]) if parts[2] else None,
            'satellites_used': satellites_used,
            'pdop': float(parts[15]) if parts[15] else None,
            'hdop': float(parts[16]) if parts[16] else None,
            'vdop': float(parts[17]) if parts[17] else None,
        }
        
        return result
    
    def parse_gsv(self, parts: List[str]) -> Dict:
        """Parse GSV sentence - GPS Satellites in view"""
        if len(parts) < 8:
            return {}
            
        total_messages = int(parts[1]) if parts[1] else 0
        message_num = int(parts[2]) if parts[2] else 0
        total_satellites = int(parts[3]) if parts[3] else 0
        
        satellites = []
        # Each satellite takes 4 fields: PRN, elevation, azimuth, SNR
        for i in range(4, len(parts), 4):
            if i + 3 < len(parts):
                if parts[i]:  # PRN number exists
                    sat = {
                        'prn': int(parts[i]),
                        'elevation': float(parts[i+1]) if parts[i+1] else None,
                        'azimuth': float(parts[i+2]) if parts[i+2] else None,
                        'snr': float(parts[i+3]) if parts[i+3] else None,
                    }
                    satellites.append(sat)
        
        result = {
            'type': 'GSV',
            'total_messages': total_messages,
            'message_num': message_num,
            'total_satellites': total_satellites,
            'satellites': satellites,
        }
        
        # Update stored satellite data
        constellation = self.get_constellation(parts[0])
        if constellation not in self.satellites:
            self.satellites[constellation] = []
        
        for sat in satellites:
            # Update or add satellite info
            existing = next((s for s in self.satellites[constellation] if s['prn'] == sat['prn']), None)
            if existing:
                existing.update(sat)
            else:
                self.satellites[constellation].append(sat)
        
        return result
    
    def parse_vtg(self, parts: List[str]) -> Dict:
        """Parse VTG sentence - Track made good and Ground speed"""
        if len(parts) < 10:
            return {}
            
        result = {
            'type': 'VTG',
            'course_true': float(parts[1]) if parts[1] else None,
            'course_magnetic': float(parts[3]) if parts[3] else None,
            'speed_knots': float(parts[5]) if parts[5] else None,
            'speed_kmh': float(parts[7]) if parts[7] else None,
        }
        
        if result['speed_knots'] is not None:
            self.velocity = {
                'speed_knots': result['speed_knots'],
                'speed_kmh': result['speed_kmh'] or result['speed_knots'] * 1.852,
                'course': result['course_true']
            }
        
        return result
    
    def parse_gns(self, parts: List[str]) -> Dict:
        """Parse GNS sentence - GNSS fix data"""
        if len(parts) < 13:
            return {}
            
        result = {
            'type': 'GNS',
            'time': self.parse_time(parts[1]) if parts[1] else None,
            'latitude': self.parse_coordinate(parts[2], parts[3]) if parts[2] and parts[3] else None,
            'longitude': self.parse_coordinate(parts[4], parts[5]) if parts[4] and parts[5] else None,
            'mode_indicator': parts[6],
            'num_satellites': int(parts[7]) if parts[7] else 0,
            'hdop': float(parts[8]) if parts[8] else None,
            'altitude': float(parts[9]) if parts[9] else None,
            'geoid_height': float(parts[10]) if parts[10] else None,
        }
        
        return result
    
    def parse_pqxfi(self, parts: List[str]) -> Dict:
        """Parse PQXFI sentence - Proprietary sentence"""
        if len(parts) < 9:
            return {}
            
        result = {
            'type': 'PQXFI',
            'time': self.parse_time(parts[1]) if parts[1] else None,
            'latitude': self.parse_coordinate(parts[2], parts[3]) if parts[2] and parts[3] else None,
            'longitude': self.parse_coordinate(parts[4], parts[5]) if parts[4] and parts[5] else None,
            'altitude': float(parts[6]) if parts[6] else None,
            'value1': float(parts[7]) if parts[7] else None,
            'value2': float(parts[8]) if parts[8] else None,
            'value3': float(parts[9]) if len(parts) > 9 and parts[9] else None,
        }
        
        return result
    
    def parse_time(self, time_str: str) -> Optional[str]:
        """Parse HHMMSS.ss format to readable time"""
        if not time_str or len(time_str) < 6:
            return None
            
        try:
            hours = int(time_str[:2])
            minutes = int(time_str[2:4])
            seconds = float(time_str[4:])
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        except (ValueError, IndexError):
            return None
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse DDMMYY format to readable date"""
        if not date_str or len(date_str) != 6:
            return None
            
        try:
            day = int(date_str[:2])
            month = int(date_str[2:4])
            year = 2000 + int(date_str[4:6])  # Assume 20xx
            return f"{year}-{month:02d}-{day:02d}"
        except (ValueError, IndexError):
            return None
    
    def parse_coordinate(self, coord_str: str, direction: str) -> Optional[float]:
        """Parse coordinate in DDMM.MMMM format to decimal degrees"""
        if not coord_str or not direction:
            return None
            
        try:
            # Find decimal point
            if '.' not in coord_str:
                return None
                
            # Split into degrees and minutes
            decimal_pos = coord_str.find('.')
            if decimal_pos < 3:
                return None
                
            degrees = int(coord_str[:decimal_pos-2])
            minutes = float(coord_str[decimal_pos-2:])
            
            decimal_degrees = degrees + minutes / 60.0
            
            # Apply direction
            if direction in ['S', 'W']:
                decimal_degrees = -decimal_degrees
                
            return decimal_degrees
        except (ValueError, IndexError):
            return None
    
    def get_fix_quality(self, quality_str: str) -> str:
        """Convert fix quality number to description"""
        quality_map = {
            '0': 'Invalid',
            '1': 'GPS fix (SPS)',
            '2': 'DGPS fix',
            '3': 'PPS fix',
            '4': 'Real Time Kinematic',
            '5': 'Float RTK',
            '6': 'Estimated (dead reckoning)',
            '7': 'Manual input mode',
            '8': 'Simulation mode'
        }
        return quality_map.get(quality_str, f'Unknown ({quality_str})')
    
    def get_fix_type(self, fix_str: str) -> str:
        """Convert fix type number to description"""
        fix_map = {
            '1': 'No fix',
            '2': '2D fix',
            '3': '3D fix'
        }
        return fix_map.get(fix_str, f'Unknown ({fix_str})')
    
    def get_constellation(self, sentence_type: str) -> str:
        """Get constellation name from sentence type"""
        if sentence_type.startswith('GP'):
            return 'GPS'
        elif sentence_type.startswith('GL'):
            return 'GLONASS'
        elif sentence_type.startswith('GA'):
            return 'Galileo'
        elif sentence_type.startswith('GB'):
            return 'BeiDou'
        elif sentence_type.startswith('GN'):
            return 'GNSS (Multi-constellation)'
        else:
            return 'Unknown'
    
    def colorize(self, text: str, color_type: str) -> str:
        """Apply color to text based on color type"""
        if not COLOR_AVAILABLE:
            return text
        return f"{self.colors.get(color_type, '')}{text}{self.colors['reset']}"
    
    def get_signal_color(self, snr: Optional[int]) -> str:
        """Get color based on signal strength"""
        if not snr:
            return 'error'
        elif snr >= 35:
            return 'success'
        elif snr >= 25:
            return 'data'
        elif snr >= 15:
            return 'warning'
        else:
            return 'error'
    
    def get_fix_quality_color(self, quality: str) -> str:
        """Get color based on fix quality"""
        if 'Invalid' in quality or 'No fix' in quality:
            return 'error'
        elif 'RTK' in quality or '3D fix' in quality:
            return 'success'
        elif 'GPS fix' in quality or '2D fix' in quality:
            return 'data'
        else:
            return 'warning'
    
    def format_position(self) -> str:
        """Format position information in human-readable form"""
        if not self.position:
            return f"{self.colorize('Position:', 'label')} {self.colorize('Not available', 'error')}"
            
        lat, lon, alt = self.position
        
        # Convert to degrees, minutes, seconds for display
        def dd_to_dms(dd):
            degrees = int(abs(dd))
            minutes = int((abs(dd) - degrees) * 60)
            seconds = ((abs(dd) - degrees) * 60 - minutes) * 60
            return degrees, minutes, seconds
        
        lat_d, lat_m, lat_s = dd_to_dms(lat)
        lon_d, lon_m, lon_s = dd_to_dms(lon)
        
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        
        result = f"{self.colorize('Position:', 'header')}\n"
        lat_coords = f"{lat_d:02d}°{lat_m:02d}'{lat_s:05.2f}\" {lat_dir}"
        lon_coords = f"{lon_d:03d}°{lon_m:02d}'{lon_s:05.2f}\" {lon_dir}"
        result += f"  {self.colorize('Latitude:', 'label')}  {self.colorize(lat_coords, 'data')} {self.colorize(f'({lat:.6f}°)', 'info')}\n"
        result += f"  {self.colorize('Longitude:', 'label')} {self.colorize(lon_coords, 'data')} {self.colorize(f'({lon:.6f}°)', 'info')}\n"
        
        if alt is not None:
            result += f"  {self.colorize('Altitude:', 'label')}  {self.colorize(f'{alt:.1f} m', 'data')}\n"
        
        return result
    
    def format_time(self) -> str:
        """Format time information"""
        if not self.time_info:
            return f"{self.colorize('Time:', 'label')} {self.colorize('Not available', 'error')}"
        return f"{self.colorize('Time:', 'label')} {self.colorize(self.time_info, 'data')} {self.colorize('UTC', 'info')}"
    
    def format_satellites(self) -> str:
        """Format satellite information"""
        if not self.satellites:
            return f"{self.colorize('Satellites:', 'label')} {self.colorize('No data available', 'error')}"
        
        result = f"{self.colorize('Satellites:', 'header')}\n"
        total_visible = 0
        total_used = 0
        
        for constellation, sats in self.satellites.items():
            if not sats:
                continue
                
            result += f"  {self.colorize(constellation + ':', 'subheader')}\n"
            visible = len(sats)
            used = len([s for s in sats if s.get('snr') and s['snr'] > 0])
            
            result += f"    {self.colorize('Visible:', 'label')} {self.colorize(str(visible), 'data')}, "
            result += f"{self.colorize('Used:', 'label')} {self.colorize(str(used), 'data')}\n"
            
            # Show details for satellites with good signal
            good_sats = [s for s in sats if s.get('snr') and s['snr'] > 20]
            if good_sats:
                result += f"    {self.colorize('Strong signals:', 'label')}\n"
                for sat in good_sats[:5]:  # Show top 5
                    snr_color = self.get_signal_color(sat['snr'])
                    prn_text = f"{sat['prn']:2d}"
                    snr_text = f"{sat['snr']:4.1f}dB"
                    result += f"      {self.colorize('PRN', 'label')} {self.colorize(prn_text, 'info')}: "
                    result += f"{self.colorize('SNR', 'label')} {self.colorize(snr_text, snr_color)}"
                    if sat.get('elevation') is not None:
                        el_text = f"{sat['elevation']:4.1f}°"
                        result += f", {self.colorize('El', 'label')} {self.colorize(el_text, 'info')}"
                    if sat.get('azimuth') is not None:
                        az_text = f"{sat['azimuth']:5.1f}°"
                        result += f", {self.colorize('Az', 'label')} {self.colorize(az_text, 'info')}"
                    result += "\n"
            
            total_visible += visible
            total_used += used
        
        result += f"  {self.colorize('Total:', 'label')} {self.colorize(str(total_visible), 'data')} visible, "
        result += f"{self.colorize(str(total_used), 'data')} with signal\n"
        
        if self.fix_info:
            quality = self.fix_info.get('quality', 'Unknown')
            quality_color = self.get_fix_quality_color(quality)
            result += f"  {self.colorize('Fix quality:', 'label')} {self.colorize(quality, quality_color)}\n"
            result += f"  {self.colorize('Satellites in fix:', 'label')} {self.colorize(str(self.fix_info.get('satellites', 0)), 'data')}\n"
            if self.fix_info.get('hdop'):
                hdop_val = self.fix_info['hdop']
                hdop_color = 'success' if hdop_val < 2.0 else 'warning' if hdop_val < 5.0 else 'error'
                result += f"  {self.colorize('HDOP:', 'label')} {self.colorize(f'{hdop_val:.1f}', hdop_color)}\n"
        
        return result
    
    def format_velocity(self) -> str:
        """Format velocity information"""
        if not self.velocity:
            return f"{self.colorize('Velocity:', 'label')} {self.colorize('Not available', 'error')}"
        
        result = f"{self.colorize('Velocity:', 'header')}\n"
        
        speed_knots = self.velocity['speed_knots']
        speed_kmh = self.velocity['speed_kmh']
        
        # Color code speed based on typical vessel speeds
        if speed_knots < 1:
            speed_color = 'warning'  # Very slow/stationary
        elif speed_knots < 10:
            speed_color = 'data'     # Normal speed
        else:
            speed_color = 'success'  # Fast speed
            
        result += f"  {self.colorize('Speed:', 'label')} {self.colorize(f'{speed_knots:.1f} knots', speed_color)} "
        result += f"{self.colorize(f'({speed_kmh:.1f} km/h)', 'info')}\n"
        
        if self.velocity.get('course') is not None:
            course = self.velocity['course']
            # Convert course to compass direction
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                         'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            direction_idx = int((course + 11.25) / 22.5) % 16
            result += f"  {self.colorize('Course:', 'label')} {self.colorize(f'{course:.1f}°', 'data')} "
            result += f"{self.colorize(f'({directions[direction_idx]})', 'info')}\n"
        
        return result
    
    def format_summary(self) -> str:
        """Format a complete summary of all parsed data"""
        separator = self.colorize("=" * 50, 'separator')
        title = self.colorize("NMEA DATA SUMMARY", 'header')
        
        result = f"{separator}\n"
        result += f"{title}\n"
        result += f"{separator}\n\n"
        
        result += self.format_time() + "\n\n"
        result += self.format_position() + "\n"
        result += self.format_velocity() + "\n"
        result += self.format_satellites() + "\n"
        
        return result
    
    def to_json(self) -> str:
        """Convert all parsed data to JSON format for Splunk ingestion"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'position': None,
            'time_info': self.time_info,
            'satellites': {},
            'fix_info': self.fix_info,
            'velocity': self.velocity
        }
        
        # Add position data if available
        if self.position:
            lat, lon, alt = self.position
            data['position'] = {
                'latitude': lat,
                'longitude': lon,
                'altitude': alt,
                'coordinates': [lon, lat]  # GeoJSON format [lng, lat]
            }
        
        # Process satellite data
        if self.satellites:
            for constellation, sats in self.satellites.items():
                data['satellites'][constellation] = {
                    'visible_count': len(sats),
                    'used_count': len([s for s in sats if s.get('snr') and s['snr'] > 0]),
                    'satellites': sats
                }
        
        return json.dumps(data, indent=2)
    
    def get_summary_dict(self) -> Dict:
        """Get summary data as a dictionary for Splunk logging"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'has_position': bool(self.position),
            'has_time': bool(self.time_info),
            'has_velocity': bool(self.velocity),
            'satellite_constellations': list(self.satellites.keys()) if self.satellites else [],
            'total_satellites_visible': 0,
            'total_satellites_used': 0
        }
        
        # Add position summary
        if self.position:
            lat, lon, alt = self.position
            summary['position_summary'] = {
                'latitude': lat,
                'longitude': lon,
                'altitude': alt,
                'coordinates': [lon, lat]  # GeoJSON format
            }
        
        # Add satellite summary
        if self.satellites:
            for constellation, sats in self.satellites.items():
                visible = len(sats)
                used = len([s for s in sats if s.get('snr') and s['snr'] > 0])
                summary['total_satellites_visible'] += visible
                summary['total_satellites_used'] += used
                
                # Add constellation-specific data
                summary[f'{constellation.lower()}_satellites'] = {
                    'visible': visible,
                    'used': used,
                    'strong_signals': len([s for s in sats if s.get('snr') and s['snr'] > 20])
                }
        
        # Add fix quality summary
        if self.fix_info:
            summary['fix_summary'] = {
                'quality': self.fix_info.get('quality'),
                'satellites_in_fix': self.fix_info.get('satellites', 0),
                'hdop': self.fix_info.get('hdop')
            }
        
        # Add velocity summary
        if self.velocity:
            summary['velocity_summary'] = {
                'speed_knots': self.velocity.get('speed_knots'),
                'speed_kmh': self.velocity.get('speed_kmh'),
                'course': self.velocity.get('course')
            }
        
        return summary
    
    def add_position_callback(self, callback: Callable[[Dict], None]):
        """Add a callback function to be called when a new position is received"""
        self.position_callbacks.append(callback)
    
    def remove_position_callback(self, callback: Callable[[Dict], None]):
        """Remove a position callback"""
        if callback in self.position_callbacks:
            self.position_callbacks.remove(callback)
    
    def _process_new_position(self, position_data: Dict):
        """Process a new position and call all registered callbacks"""
        # Create position info dictionary
        position_info = {
            'timestamp': datetime.now().isoformat(),
            'latitude': position_data.get('latitude'),
            'longitude': position_data.get('longitude'),
            'altitude': position_data.get('altitude'),
            'time': position_data.get('time'),
            'fix_quality': position_data.get('fix_quality'),
            'num_satellites': position_data.get('num_satellites'),
            'hdop': position_data.get('hdop'),
            'source': position_data.get('type', 'Unknown')
        }
        
        # Calculate movement if we have a previous position
        if self.last_position:
            movement_info = self._calculate_movement(self.last_position, position_info)
            position_info.update(movement_info)
        
        # Store position in history (keep last 100 positions)
        self.position_history.append(position_info)
        if len(self.position_history) > 100:
            self.position_history.pop(0)
        
        # Update last position
        self.last_position = position_info
        
        # Call all registered callbacks
        for callback in self.position_callbacks:
            try:
                callback(position_info)
            except Exception as e:
                # Don't let callback errors break the parser
                print(f"Error in position callback: {e}")
    
    def _calculate_movement(self, last_pos: Dict, current_pos: Dict) -> Dict:
        """Calculate movement between two positions"""
        if not all([last_pos.get('latitude'), last_pos.get('longitude'),
                   current_pos.get('latitude'), current_pos.get('longitude')]):
            return {}
        
        # Calculate distance using Haversine formula
        distance_m = self._haversine_distance(
            last_pos['latitude'], last_pos['longitude'],
            current_pos['latitude'], current_pos['longitude']
        )
        
        # Calculate bearing
        bearing = self._calculate_bearing(
            last_pos['latitude'], last_pos['longitude'],
            current_pos['latitude'], current_pos['longitude']
        )
        
        # Calculate time difference and speed
        time_diff = 0
        speed_ms = 0
        speed_knots = 0
        speed_kmh = 0
        
        try:
            last_time = datetime.fromisoformat(last_pos['timestamp'])
            current_time = datetime.fromisoformat(current_pos['timestamp'])
            time_diff = (current_time - last_time).total_seconds()
            
            if time_diff > 0:
                speed_ms = distance_m / time_diff
                speed_knots = speed_ms * 1.94384  # m/s to knots
                speed_kmh = speed_ms * 3.6       # m/s to km/h
        except:
            pass
        
        return {
            'movement': {
                'distance_m': distance_m,
                'bearing_deg': bearing,
                'time_diff_s': time_diff,
                'speed_ms': speed_ms,
                'speed_knots': speed_knots,
                'speed_kmh': speed_kmh,
                'is_moving': distance_m > getattr(self, 'movement_threshold', 1.0)  # Configurable threshold
            }
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth's radius in meters
        r = 6371000
        
        return c * r
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the bearing from point 1 to point 2 in degrees"""
        from math import radians, degrees, cos, sin, atan2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        y = sin(dlon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        
        bearing = atan2(y, x)
        bearing = degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360
        
        return bearing

class UDPReceiver:
    """
    UDP receiver for continuous NMEA data streaming
    Handles real-time data from GPS devices, AIS receivers, etc.
    """
    
    def __init__(self, port: int, host: str = '0.0.0.0', buffer_size: int = 4096):
        """Initialize UDP receiver"""
        self.port = port
        self.host = host
        self.buffer_size = buffer_size
        self.socket = None
        self.running = False
        self.thread = None
        self.data_callback = None
        self.error_callback = None
        
        # Statistics
        self.stats = {
            'packets_received': 0,
            'bytes_received': 0,
            'sentences_parsed': 0,
            'parse_errors': 0,
            'last_packet_time': None,
            'start_time': None,
            'connection_errors': 0
        }
        
        # Buffer for incomplete sentences
        self.sentence_buffer = ""
    
    def set_data_callback(self, callback: Callable[[str], None]):
        """Set callback function for received NMEA sentences"""
        self.data_callback = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback function for error messages"""
        self.error_callback = callback
    
    def start(self) -> bool:
        """Start the UDP receiver"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for clean shutdown
            
            # Start receiving thread
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            self.stats['start_time'] = time.time()
            return True
            
        except Exception as e:
            error_msg = f"Failed to start UDP receiver on {self.host}:{self.port}: {e}"
            if self.error_callback:
                self.error_callback(error_msg)
            self.stats['connection_errors'] += 1
            return False
    
    def stop(self):
        """Stop the UDP receiver"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
    
    def _receive_loop(self):
        """Main receiving loop (runs in separate thread)"""
        while self.running:
            try:
                # Receive data with timeout
                try:
                    data, addr = self.socket.recvfrom(self.buffer_size)
                except socket.timeout:
                    continue  # Check if still running
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        error_msg = f"Socket receive error: {e}"
                        if self.error_callback:
                            self.error_callback(error_msg)
                        self.stats['connection_errors'] += 1
                    continue
                
                # Update statistics
                self.stats['packets_received'] += 1
                self.stats['bytes_received'] += len(data)
                self.stats['last_packet_time'] = time.time()
                
                # Decode data
                try:
                    text_data = data.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    # Try latin-1 as fallback (common in marine equipment)
                    text_data = data.decode('latin-1', errors='ignore')
                
                # Process NMEA sentences
                self._process_data(text_data)
                
            except Exception as e:
                if self.running:
                    error_msg = f"Error in UDP receive loop: {e}"
                    if self.error_callback:
                        self.error_callback(error_msg)
                    self.stats['connection_errors'] += 1
                    time.sleep(1)  # Brief pause before retrying
    
    def _process_data(self, data: str):
        """Process received data and extract NMEA sentences"""
        # Add to buffer
        self.sentence_buffer += data
        
        # Split by line endings and process complete sentences
        lines = self.sentence_buffer.split('\n')
        
        # Keep the last incomplete line in buffer
        self.sentence_buffer = lines[-1]
        
        # Process complete lines
        for line in lines[:-1]:
            line = line.strip()
            if line and line.startswith('$'):
                # Valid NMEA sentence
                if self.data_callback:
                    self.data_callback(line)
                self.stats['sentences_parsed'] += 1
            elif line:
                # Non-NMEA data received
                self.stats['parse_errors'] += 1
    
    def get_stats(self) -> Dict:
        """Get receiver statistics"""
        stats = self.stats.copy()
        
        # Calculate runtime
        if stats['start_time']:
            stats['runtime_seconds'] = time.time() - stats['start_time']
            
            # Calculate rates
            if stats['runtime_seconds'] > 0:
                stats['packets_per_second'] = stats['packets_received'] / stats['runtime_seconds']
                stats['bytes_per_second'] = stats['bytes_received'] / stats['runtime_seconds']
                stats['sentences_per_second'] = stats['sentences_parsed'] / stats['runtime_seconds']
        
        return stats
    
    def is_running(self) -> bool:
        """Check if receiver is running"""
        return self.running and self.thread and self.thread.is_alive()

def create_argument_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description='Parse NMEA sentences and display GPS/GNSS data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 nmea_parser.py data.nmea                    # Parse file and display
  python3 nmea_parser.py data.nmea --verbose          # Show detailed parsing
  python3 nmea_parser.py data.nmea --json             # Output as JSON
  python3 nmea_parser.py data.nmea --splunk           # Send to Splunk
  python3 nmea_parser.py --interactive                # Interactive mode
  python3 nmea_parser.py --udp 4001                   # Receive UDP stream on port 4001
  python3 nmea_parser.py --udp 4001 --splunk          # UDP stream to Splunk
  python3 nmea_parser.py --udp 4001 --json            # UDP stream as JSON
  
Splunk Configuration (via environment variables):
  export SPLUNK_HOST=splunk.company.com
  export SPLUNK_USERNAME=nmea_user
  export SPLUNK_PASSWORD=secure_password
  export SPLUNK_INDEX=maritime_data
        """
    )
    
    # Input options
    parser.add_argument('filename', nargs='?', help='NMEA data file to parse')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode - enter sentences manually')
    
    # UDP streaming options
    parser.add_argument('--udp', '-u', type=int, metavar='PORT',
                        help='Receive NMEA data via UDP on specified port')
    parser.add_argument('--udp-host', default='0.0.0.0',
                        help='UDP host to bind to (default: 0.0.0.0 - all interfaces)')
    parser.add_argument('--udp-buffer', type=int, default=4096,
                        help='UDP receive buffer size in bytes (default: 4096)')
    parser.add_argument('--continuous', '-c', action='store_true',
                        help='Continuous output mode (for UDP streaming)')
    parser.add_argument('--track-position', action='store_true',
                        help='Enable real-time position tracking and movement analysis')
    parser.add_argument('--geofence', action='append', nargs=4, metavar=('LAT', 'LON', 'RADIUS', 'NAME'),
                        help='Add geofence: --geofence 50.612 5.587 100 "Home Base"')
    parser.add_argument('--min-movement', type=float, default=1.0, metavar='METERS',
                        help='Minimum movement threshold in meters (default: 1.0)')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed parsing of each sentence')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output data in JSON format')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output')
    
    # Splunk options
    parser.add_argument('--splunk', '-s', action='store_true',
                        help='Send parsed data to Splunk')
    parser.add_argument('--splunk-config', action='store_true',
                        help='Show Splunk configuration help')
    parser.add_argument('--splunk-test', action='store_true',
                        help='Test Splunk connection and exit')
    
    return parser

def handle_udp_stream(args, nmea_parser: NMEAParser, splunk_logger):
    """Handle UDP streaming mode"""
    # Set up signal handler for clean shutdown
    shutdown_event = threading.Event()
    
    def signal_handler(sig, frame):
        print(f"\n{nmea_parser.colorize('Shutting down...', 'warning')}")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create UDP receiver
    udp_receiver = UDPReceiver(args.udp, args.udp_host, args.udp_buffer)
    
    # Statistics tracking
    sentence_count = 0
    last_stats_time = time.time()
    last_sentence_count = 0
    
    # Continuous output handling
    def process_sentence(sentence: str):
        nonlocal sentence_count
        sentence_count += 1
        
        # Parse the sentence
        result = nmea_parser.parse_sentence(sentence)
        if not result:
            return
        
        # Send to Splunk if enabled
        if splunk_logger:
            splunk_logger.log_nmea_data(result, sentence)
        
        # Handle output based on mode
        if args.json:
            # JSON mode - output each sentence as JSON
            sentence_data = {
                'timestamp': datetime.now().isoformat(),
                'sentence': sentence,
                'parsed': result
            }
            print(json.dumps(sentence_data))
        elif args.continuous or args.verbose:
            # Continuous mode - show real-time updates
            print(f"{nmea_parser.colorize('📡', 'info')} {sentence}")
            if args.verbose:
                print(f"   → {result}")
        
        # Show periodic stats in continuous mode
        nonlocal last_stats_time, last_sentence_count
        current_time = time.time()
        if not args.json and (current_time - last_stats_time) >= 10:  # Every 10 seconds
            show_realtime_stats(nmea_parser, udp_receiver, sentence_count, current_time)
            last_stats_time = current_time
            last_sentence_count = sentence_count
    
    def error_handler(error_msg: str):
        if not args.json:
            print(f"{nmea_parser.colorize('Error:', 'error')} {error_msg}")
    
    # Set up callbacks
    udp_receiver.set_data_callback(process_sentence)
    udp_receiver.set_error_callback(error_handler)
    
    # Start UDP receiver
    if not udp_receiver.start():
        print(f"{nmea_parser.colorize('Failed to start UDP receiver', 'error')}")
        return
    
    if not args.json:
        print(f"{nmea_parser.colorize('✅ UDP receiver started', 'success')}")
        print(f"Listening for NMEA data on {args.udp_host}:{args.udp}")
        if not args.continuous:
            print(f"Use {nmea_parser.colorize('--continuous', 'info')} flag to see real-time data")
    
    # Main loop - wait for shutdown
    try:
        while not shutdown_event.is_set() and udp_receiver.is_running():
            shutdown_event.wait(1)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        # Stop UDP receiver
        udp_receiver.stop()
        
        if not args.json:
            # Show final statistics
            print(f"\n{nmea_parser.colorize('Final Statistics:', 'header')}")
            show_final_stats(nmea_parser, udp_receiver, sentence_count, splunk_logger)
        
        # Send summary to Splunk if enabled
        if splunk_logger:
            summary_data = nmea_parser.get_summary_dict()
            summary_data['udp_stats'] = udp_receiver.get_stats()
            summary_data['total_sentences'] = sentence_count
            splunk_logger.log_summary_data(summary_data)

def show_realtime_stats(nmea_parser: NMEAParser, udp_receiver: UDPReceiver, sentence_count: int, current_time: float):
    """Show real-time statistics during UDP streaming"""
    udp_stats = udp_receiver.get_stats()
    
    print(f"\n{nmea_parser.colorize('📊 Real-time Stats:', 'subheader')}")
    packets_rate = f"{udp_stats.get('packets_per_second', 0):.1f}/s"
    sentences_rate = f"{udp_stats.get('sentences_per_second', 0):.1f}/s"
    
    print(f"  Packets: {nmea_parser.colorize(str(udp_stats['packets_received']), 'data')} "
          f"({nmea_parser.colorize(packets_rate, 'info')})")
    print(f"  Sentences: {nmea_parser.colorize(str(sentence_count), 'data')} "
          f"({nmea_parser.colorize(sentences_rate, 'info')})")
    
    if nmea_parser.position:
        lat, lon, alt = nmea_parser.position
        print(f"  Position: {nmea_parser.colorize(f'{lat:.6f}°, {lon:.6f}°', 'success')}")
    
    if nmea_parser.velocity and nmea_parser.velocity.get('speed_knots'):
        speed = nmea_parser.velocity['speed_knots']
        print(f"  Speed: {nmea_parser.colorize(f'{speed:.1f} knots', 'data')}")
    
    if udp_stats['parse_errors'] > 0:
        print(f"  Errors: {nmea_parser.colorize(str(udp_stats['parse_errors']), 'error')}")
    
    print()

def show_final_stats(nmea_parser: NMEAParser, udp_receiver: UDPReceiver, sentence_count: int, splunk_logger):
    """Show final statistics after UDP streaming ends"""
    udp_stats = udp_receiver.get_stats()
    
    runtime_str = f"{udp_stats.get('runtime_seconds', 0):.1f}s"
    avg_rate_str = f"{udp_stats['sentences_per_second']:.1f} sentences/s"
    
    print(f"  Runtime: {nmea_parser.colorize(runtime_str, 'data')}")
    print(f"  Packets received: {nmea_parser.colorize(str(udp_stats['packets_received']), 'data')}")
    print(f"  Bytes received: {nmea_parser.colorize(str(udp_stats['bytes_received']), 'data')}")
    print(f"  NMEA sentences: {nmea_parser.colorize(str(sentence_count), 'data')}")
    print(f"  Parse errors: {nmea_parser.colorize(str(udp_stats['parse_errors']), 'error' if udp_stats['parse_errors'] > 0 else 'data')}")
    
    if udp_stats.get('sentences_per_second', 0) > 0:
        print(f"  Average rate: {nmea_parser.colorize(avg_rate_str, 'info')}")
    
    # Show final position summary
    if nmea_parser.position or nmea_parser.satellites:
        print(f"\n{nmea_parser.format_summary()}")
    
    # Show Splunk statistics
    if splunk_logger:
        stats = splunk_logger.get_stats()
        print(f"\n{nmea_parser.colorize('Splunk Statistics:', 'subheader')}")
        print(f"  Events sent: {nmea_parser.colorize(str(stats['events_sent']), 'success')}")
        print(f"  Batches sent: {nmea_parser.colorize(str(stats['batches_sent']), 'data')}")
        if stats['events_failed'] > 0:
            print(f"  Events failed: {nmea_parser.colorize(str(stats['events_failed']), 'error')}")

def create_position_tracker(args, nmea_parser):
    """Create position tracking callbacks based on command line arguments"""
    if not args.track_position:
        return None
    
    def position_callback(position_info):
        """Position processing callback"""
        if not position_info.get('latitude') or not position_info.get('longitude'):
            return
        
        lat = position_info['latitude']
        lon = position_info['longitude']
        alt = position_info.get('altitude')
        
        # Basic position display
        coords_text = f"{lat:.6f}°, {lon:.6f}°"
        if alt is not None:
            coords_text += f", {alt:.1f}m"
        
        print(f"📍 {nmea_parser.colorize('Position:', 'label')} {nmea_parser.colorize(coords_text, 'data')}")
        
        # Movement analysis
        if 'movement' in position_info:
            movement = position_info['movement']
            
            if movement['is_moving']:
                distance_text = f"{movement['distance_m']:.1f}m"
                bearing_text = f"{movement['bearing_deg']:.1f}°"
                speed_text = f"{movement['speed_knots']:.1f} knots"
                
                print(f"   {nmea_parser.colorize('Movement:', 'label')} {nmea_parser.colorize(distance_text, 'data')} "
                      f"at {nmea_parser.colorize(bearing_text, 'data')}, {nmea_parser.colorize(speed_text, 'success')}")
                
                # Speed alerts
                if movement['speed_knots'] > 10:
                    print(f"   ⚠️  {nmea_parser.colorize('High speed detected!', 'warning')}")
                
                # Large movement alerts
                if movement['distance_m'] > 100:
                    print(f"   🚨 {nmea_parser.colorize('Large position jump detected!', 'error')}")
            else:
                print(f"   {nmea_parser.colorize('Status:', 'label')} {nmea_parser.colorize('STATIONARY', 'warning')}")
        
        # Geofence checking
        if args.geofence:
            for geofence_args in args.geofence:
                fence_lat, fence_lon, radius, name = float(geofence_args[0]), float(geofence_args[1]), float(geofence_args[2]), geofence_args[3]
                
                # Calculate distance to geofence center
                distance = nmea_parser._haversine_distance(lat, lon, fence_lat, fence_lon)
                
                if distance <= radius:
                    print(f"   🏠 {nmea_parser.colorize('Inside geofence:', 'success')} {name} ({distance:.1f}m from center)")
                elif distance <= radius * 1.2:  # Near geofence
                    print(f"   🔶 {nmea_parser.colorize('Near geofence:', 'warning')} {name} ({distance:.1f}m away)")
        
        print()
    
    return position_callback

def main():
    """Main function to handle input and display results"""
    # Parse command line arguments
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()
    
    # Validate input options
    input_sources = sum([
        bool(args.filename),
        bool(args.interactive),
        bool(args.udp)
    ])
    
    if input_sources > 1:
        print("Error: Please specify only one input source (file, interactive, or UDP)")
        return
    
    if input_sources == 0:
        # Default to interactive mode
        args.interactive = True
    
    # Handle special cases first
    if args.splunk_config:
        if SPLUNK_AVAILABLE:
            from splunk_config import print_config_help
            print_config_help()
        else:
            print("Splunk integration not available. Install with: pip install splunk-sdk")
        return
    
    # Create NMEA parser
    nmea_parser = NMEAParser()
    
    # Disable colors if requested
    if args.no_color:
        for key in nmea_parser.colors:
            nmea_parser.colors[key] = ''
    
    # Set up position tracking if requested
    position_callback = create_position_tracker(args, nmea_parser)
    if position_callback:
        nmea_parser.add_position_callback(position_callback)
        
        # Update movement threshold if specified
        if hasattr(args, 'min_movement') and args.min_movement != 1.0:
            nmea_parser.movement_threshold = args.min_movement
    
    # Initialize Splunk logger if requested
    splunk_logger = None
    if args.splunk or args.splunk_test:
        if not SPLUNK_AVAILABLE:
            print(f"{nmea_parser.colorize('Error:', 'error')} Splunk SDK not available. Install with: pip install splunk-sdk")
            return
        
        print(f"{nmea_parser.colorize('Initializing Splunk connection...', 'info')}")
        splunk_config = SplunkConfig()
        splunk_logger = create_splunk_logger(splunk_config)
        
        if not splunk_logger:
            print(f"{nmea_parser.colorize('Error:', 'error')} Failed to connect to Splunk")
            print("Check your configuration and network connectivity")
            return
        
        # Test connection if requested
        if args.splunk_test:
            is_connected, message = splunk_logger.test_connection()
            status_color = 'success' if is_connected else 'error'
            status_icon = '✅' if is_connected else '❌'
            print(f"{status_icon} {nmea_parser.colorize('Splunk connection:', status_color)} {message}")
            splunk_logger.disconnect()
            return
        
        print(f"{nmea_parser.colorize('✅ Connected to Splunk', 'success')}")
    
    # Show header (unless JSON mode)
    if not args.json:
        if args.udp:
            print(f"{nmea_parser.colorize('NMEA Parser', 'header')} - UDP Stream Mode")
            print(f"Listening on {nmea_parser.colorize(f'{args.udp_host}:{args.udp}', 'info')}")
        else:
            print(f"{nmea_parser.colorize('NMEA Parser', 'header')} - Enter NMEA sentences (one per line)")
        
        if splunk_logger:
            print(f"{nmea_parser.colorize('📡 Splunk logging enabled', 'success')}")
        
        if args.udp:
            print(f"Press {nmea_parser.colorize('Ctrl+C', 'warning')} to stop UDP receiver")
        else:
            print(f"Press {nmea_parser.colorize('Ctrl+C', 'warning')} to exit and show summary")
        print(nmea_parser.colorize("-" * 50, 'separator'))
    
    try:
        if args.udp:
            # UDP streaming mode
            return handle_udp_stream(args, nmea_parser, splunk_logger)
        else:
            # File or interactive mode
            lines = []
            if args.filename:
                # Read from file
                try:
                    with open(args.filename, 'r') as f:
                        lines = f.readlines()
                except FileNotFoundError:
                    print(f"{nmea_parser.colorize('Error:', 'error')} File '{nmea_parser.colorize(args.filename, 'info')}' not found")
                    return
            elif args.interactive:
                # Interactive mode
                if not args.json:
                    print("Enter NMEA sentences (press Ctrl+D when done):")
                try:
                    while True:
                        line = input()
                        if line.strip():
                            lines.append(line.strip())
                except EOFError:
                    pass
                except KeyboardInterrupt:
                    pass
        
        # Parse all sentences
        parsed_sentences = []
        for line in lines:
            line = line.strip()
            if line and line.startswith('$'):
                result = nmea_parser.parse_sentence(line)
                if result:
                    parsed_sentences.append(result)
                    
                    # Send to Splunk if enabled
                    if splunk_logger:
                        splunk_logger.log_nmea_data(result, line)
        
        if not parsed_sentences:
            print(f"{nmea_parser.colorize('Warning:', 'warning')} No valid NMEA sentences found.")
            return
        
        # Handle different output formats
        if args.json:
            # JSON output
            print(nmea_parser.to_json())
        else:
            # Display individual sentence details if requested
            if args.verbose:
                print(f"\n{nmea_parser.colorize('Parsed Sentences:', 'subheader')}")
                print(nmea_parser.colorize("-" * 30, 'separator'))
                for i, sentence in enumerate(parsed_sentences, 1):
                    print(f"{i}. {sentence.get('type', 'Unknown')}: {sentence}")
                print()
            
            # Display summary
            print(nmea_parser.format_summary())
        
        # Send summary to Splunk if enabled
        if splunk_logger:
            summary_data = nmea_parser.get_summary_dict()
            splunk_logger.log_summary_data(summary_data)
            
            # Show Splunk statistics
            if not args.json:
                stats = splunk_logger.get_stats()
                print(f"\n{nmea_parser.colorize('Splunk Statistics:', 'subheader')}")
                print(f"  Events sent: {nmea_parser.colorize(str(stats['events_sent']), 'success')}")
                print(f"  Batches sent: {nmea_parser.colorize(str(stats['batches_sent']), 'data')}")
                if stats['events_failed'] > 0:
                    print(f"  Events failed: {nmea_parser.colorize(str(stats['events_failed']), 'error')}")
        
    except KeyboardInterrupt:
        if not args.json:
            print(f"\n\n{nmea_parser.colorize('Interrupted by user.', 'warning')}")
            if nmea_parser.position or nmea_parser.time_info or nmea_parser.satellites:
                print(nmea_parser.format_summary())
    
    finally:
        # Clean up Splunk connection
        if splunk_logger:
            splunk_logger.disconnect()

if __name__ == "__main__":
    main()

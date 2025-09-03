#!/usr/bin/env python3
"""
NMEA Parser - Converts NMEA sentences to human-readable format
Supports GPS position, time, satellite information, and more.
"""

import sys
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
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
                        'elevation': int(parts[i+1]) if parts[i+1] else None,
                        'azimuth': int(parts[i+2]) if parts[i+2] else None,
                        'snr': int(parts[i+3]) if parts[i+3] else None,
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
                    snr_text = f"{sat['snr']:2d}dB"
                    result += f"      {self.colorize('PRN', 'label')} {self.colorize(prn_text, 'info')}: "
                    result += f"{self.colorize('SNR', 'label')} {self.colorize(snr_text, snr_color)}"
                    if sat.get('elevation'):
                        el_text = f"{sat['elevation']:2d}°"
                        result += f", {self.colorize('El', 'label')} {self.colorize(el_text, 'info')}"
                    if sat.get('azimuth'):
                        az_text = f"{sat['azimuth']:3d}°"
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

def main():
    """Main function to handle input and display results"""
    parser = NMEAParser()
    
    print(f"{parser.colorize('NMEA Parser', 'header')} - Enter NMEA sentences (one per line)")
    print(f"Press {parser.colorize('Ctrl+C', 'warning')} to exit and show summary")
    print(parser.colorize("-" * 50, 'separator'))
    
    try:
        if len(sys.argv) > 1:
            # Read from file if provided
            filename = sys.argv[1]
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
            except FileNotFoundError:
                print(f"{parser.colorize('Error:', 'error')} File '{parser.colorize(filename, 'info')}' not found")
                return
        else:
            # Read from stdin
            lines = []
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
                result = parser.parse_sentence(line)
                if result:
                    parsed_sentences.append(result)
        
        if not parsed_sentences:
            print(f"{parser.colorize('Warning:', 'warning')} No valid NMEA sentences found.")
            return
        
        # Display individual sentence details if requested
        if '--verbose' in sys.argv or '-v' in sys.argv:
            print(f"\n{parser.colorize('Parsed Sentences:', 'subheader')}")
            print(parser.colorize("-" * 30, 'separator'))
            for i, sentence in enumerate(parsed_sentences, 1):
                print(f"{i}. {sentence.get('type', 'Unknown')}: {sentence}")
            print()
        
        # Display summary
        print(parser.format_summary())
        
    except KeyboardInterrupt:
        print(f"\n\n{parser.colorize('Interrupted by user.', 'warning')}")
        if parser.position or parser.time_info or parser.satellites:
            print(parser.format_summary())

if __name__ == "__main__":
    main()

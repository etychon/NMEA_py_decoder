#!/usr/bin/env python3
"""
Color Demo for NMEA Parser
This script demonstrates the colorized output capabilities of the NMEA parser.
"""

import sys
import os

# Add current directory to path to import nmea_parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nmea_parser import NMEAParser

def demo_colors():
    """Demonstrate the color capabilities of the NMEA parser"""
    parser = NMEAParser()
    
    print(f"{parser.colorize('NMEA Parser Color Demo', 'header')}")
    print(parser.colorize("=" * 50, 'separator'))
    print()
    
    # Demo color types
    print(f"{parser.colorize('Color Types:', 'subheader')}")
    print(f"  {parser.colorize('Header text', 'header')} - Main section headers")
    print(f"  {parser.colorize('Subheader text', 'subheader')} - Subsection headers")  
    print(f"  {parser.colorize('Label:', 'label')} {parser.colorize('Data value', 'data')} - Field labels and values")
    print(f"  {parser.colorize('Additional info', 'info')} - Supplementary information")
    print(f"  {parser.colorize('Success message', 'success')} - Good status/high quality")
    print(f"  {parser.colorize('Warning message', 'warning')} - Moderate status/cautions")
    print(f"  {parser.colorize('Error message', 'error')} - Poor status/problems")
    print()
    
    # Demo signal strength colors
    print(f"{parser.colorize('Signal Strength Colors:', 'subheader')}")
    test_signals = [45, 30, 20, 10, 0]
    for snr in test_signals:
        color = parser.get_signal_color(snr) if snr > 0 else 'error'
        status = "Excellent" if snr >= 35 else "Good" if snr >= 25 else "Fair" if snr >= 15 else "Poor" if snr > 0 else "No signal"
        print(f"  SNR {parser.colorize(f'{snr:2d}dB', color)} - {status}")
    print()
    
    # Demo fix quality colors  
    print(f"{parser.colorize('Fix Quality Colors:', 'subheader')}")
    qualities = ["Real Time Kinematic", "3D fix", "GPS fix (SPS)", "2D fix", "Invalid", "No fix"]
    for quality in qualities:
        color = parser.get_fix_quality_color(quality)
        print(f"  {parser.colorize(quality, color)}")
    print()
    
    # Demo HDOP colors
    print(f"{parser.colorize('HDOP (Accuracy) Colors:', 'subheader')}")
    hdop_values = [1.5, 3.0, 8.0]
    for hdop in hdop_values:
        color = 'success' if hdop < 2.0 else 'warning' if hdop < 5.0 else 'error'
        status = "Excellent" if hdop < 2.0 else "Good" if hdop < 5.0 else "Poor"
        print(f"  HDOP {parser.colorize(f'{hdop:.1f}', color)} - {status} accuracy")
    print()
    
    print(f"{parser.colorize('Install colorama for full color support:', 'info')}")
    print(f"  {parser.colorize('pip install colorama', 'data')}")

if __name__ == "__main__":
    demo_colors()

#!/usr/bin/env python3
"""
Test script to demonstrate block-based position processing
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nmea_parser import NMEAParser

def test_block_processing():
    """Test the new block-based position processing"""
    print("🧪 Testing Block-Based Position Processing")
    print("=" * 50)
    print()
    
    # Create parser with position tracking
    parser = NMEAParser()
    
    # Create a simple callback to show when positions are processed
    position_count = 0
    
    def position_callback(position_info):
        nonlocal position_count
        position_count += 1
        
        print(f"\n🎯 Position Update #{position_count}")
        print(f"   Coordinates: {position_info['latitude']:.6f}, {position_info['longitude']:.6f}")
        
        if 'block_info' in position_info:
            block = position_info['block_info']
            print(f"   📦 Block: {block['sentence_count']} sentences, types: {block['data_types']}")
        
        if 'movement' in position_info:
            movement = position_info['movement']
            if movement['is_moving']:
                print(f"   🚀 Movement: {movement['distance_m']:.1f}m at {movement['bearing_deg']:.1f}°")
            else:
                print("   ⚓ Stationary")
    
    parser.add_position_callback(position_callback)
    
    # Test data: NMEA blocks with different sentence combinations
    test_blocks = [
        # Block 1: Complete block with GGA + GSV + GSA + RMC
        [
            "$GPGGA,123519.0,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47",
            "$GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45*75",
            "$GPGSV,2,2,08,18,09,113,45,19,13,052,44,24,02,349,36,25,05,196,30*73",
            "$GPGSA,A,3,01,02,12,14,18,19,24,25,,,,,1.5,0.9,1.2*39",
            "$GPRMC,123519.0,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        ],
        # Block 2: Position change with velocity
        [
            "$GPGGA,123520.0,4807.040,N,01131.002,E,1,08,0.9,545.5,M,46.9,M,,*43",
            "$GPRMC,123520.0,A,4807.040,N,01131.002,E,025.2,087.1,230394,003.1,W*62"
        ],
        # Block 3: Just GGA (minimal block)
        [
            "$GPGGA,123521.0,4807.042,N,01131.004,E,1,08,0.9,545.6,M,46.9,M,,*44"
        ],
        # Block 4: Multiple position updates in sequence
        [
            "$GPGGA,123522.0,4807.044,N,01131.006,E,1,08,0.9,545.7,M,46.9,M,,*41",
            "$GPGSV,1,1,04,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45*7F",
            "$GPRMC,123522.0,A,4807.044,N,01131.006,E,028.1,089.5,230394,003.1,W*6D"
        ]
    ]
    
    print("Processing NMEA blocks to demonstrate block-based position processing:")
    print("- Position callbacks should trigger AFTER each complete block")
    print("- NOT after individual sentences")
    print()
    
    for block_num, sentences in enumerate(test_blocks, 1):
        print(f"📥 Processing Block {block_num} ({len(sentences)} sentences):")
        
        for sentence in sentences:
            print(f"   Parsing: {sentence}")
            result = parser.parse_sentence(sentence)
            time.sleep(0.1)  # Small delay to simulate real-time processing
        
        # Wait a bit to allow block timeout processing
        print("   ⏳ Waiting for block completion...")
        time.sleep(2.5)  # Longer than block timeout (2.0s)
        
        print()
    
    # Force any remaining block processing
    print("🔄 Forcing final block processing...")
    parser.force_block_processing()
    
    print(f"\n✅ Test completed. Total position updates: {position_count}")
    print()
    print("Expected behavior:")
    print("- Block 1: Position update after all 5 sentences processed")
    print("- Block 2: Position update with movement data")
    print("- Block 3: Position update after timeout (minimal block)")
    print("- Block 4: Position update with complete block info")
    print(f"- Total: 4 position updates (got {position_count})")

def demo_live_udp_processing():
    """Demo for live UDP processing"""
    print("\n" + "=" * 50)
    print("🌐 Live UDP Block Processing Demo")
    print("=" * 50)
    print()
    
    print("To test with live UDP stream:")
    print()
    print("1. Start the block-based position processor:")
    print("   python3 nmea_parser.py --udp 4000 --track-position --continuous")
    print()
    print("2. Send NMEA data to port 4000 from another terminal:")
    print("   echo '$GPGGA,123519.0,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47' | nc -u localhost 4000")
    print("   echo '$GPRMC,123519.0,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A' | nc -u localhost 4000")
    print()
    print("3. Watch for block processing messages:")
    print("   📦 NMEA Block Processed: Block: 2 sentences, types: position, velocity")
    print("   📍 Position: 48.117300°, 1.516667°")
    print()
    print("Key improvements:")
    print("✅ Position processing happens AFTER complete blocks")
    print("✅ Block information shows sentence count and types")
    print("✅ Movement calculations use complete block data")
    print("✅ Velocity data from RMC sentences included in position updates")
    print("✅ Timeout-based block completion (2 second default)")

if __name__ == "__main__":
    test_block_processing()
    demo_live_udp_processing()

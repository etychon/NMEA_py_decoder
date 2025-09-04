#!/usr/bin/env python3
"""
UDP Test Sender for NMEA Parser
Sends sample NMEA data via UDP to test the parser's UDP streaming functionality.
"""

import socket
import time
import sys
import argparse
from typing import List

# Sample NMEA sentences for testing
SAMPLE_NMEA_DATA = [
    "$GPGGA,183730.0,4733.508324,N,05245.174442,W,1,03,500.0,62.9,M,12.0,M,,*75",
    "$GPRMC,183730.0,A,4733.508324,N,05245.174442,W,12.5,285.0,270417,0.0,E,A*13",
    "$GPGSV,2,1,07,07,37,305,22,09,24,262,18,21,23,049,20,30,02,314,24*74",
    "$GPGSV,2,2,07,4,,,,8,52,223,,11,05,198,*75",
    "$GLGSV,3,1,11,77,16,314,17,76,73,343,13,87,11,202,20,67,07,302,16*67",
    "$GLGSV,3,2,11,68,08,351,19,74,,,,66,,,,86,66,180,*6B",
    "$GLGSV,3,3,11,75,45,119,,84,,,,85,48,040,*6A",
    "$GNGSA,A,3,07,09,21,,,,,,,,,,500.0,500.0,500.0*24",
    "$GPVTG,285.0,T,,M,12.5,N,23.2,K,A*0F",
]

# Moving vessel data (simulates movement)
MOVING_VESSEL_DATA = [
    "$GPRMC,120500.0,A,4012.3562,N,07412.1198,W,15.3,225.0,150124,0.0,E,A*1F",
    "$GPGGA,120500.0,4012.3562,N,07412.1198,W,1,08,1.2,16.4,M,-33.9,M,,*65",
    "$GPRMC,120501.0,A,4012.3559,N,07412.1201,W,15.4,225.1,150124,0.0,E,A*1E",
    "$GPGGA,120501.0,4012.3559,N,07412.1201,W,1,08,1.2,16.5,M,-33.9,M,,*64",
    "$GPRMC,120502.0,A,4012.3556,N,07412.1204,W,15.5,225.2,150124,0.0,E,A*1D",
    "$GPGGA,120502.0,4012.3556,N,07412.1204,W,1,08,1.2,16.6,M,-33.9,M,,*63",
    "$GPRMC,120503.0,A,4012.3553,N,07412.1207,W,15.6,225.3,150124,0.0,E,A*1C",
    "$GPGGA,120503.0,4012.3553,N,07412.1207,W,1,08,1.2,16.7,M,-33.9,M,,*62",
]

def send_nmea_data(host: str, port: int, data: List[str], interval: float = 1.0, repeat: int = 1):
    """Send NMEA data via UDP"""
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        print(f"Sending NMEA data to {host}:{port}")
        print(f"Interval: {interval}s, Repeat: {repeat} times")
        print(f"Total sentences: {len(data) * repeat}")
        print("-" * 50)
        
        sentences_sent = 0
        
        for cycle in range(repeat):
            if repeat > 1:
                print(f"\nCycle {cycle + 1}/{repeat}")
            
            for i, sentence in enumerate(data):
                # Send the sentence
                sock.sendto(sentence.encode('utf-8') + b'\n', (host, port))
                sentences_sent += 1
                
                print(f"Sent: {sentence}")
                
                # Wait before sending next sentence (except for the last one)
                if i < len(data) - 1 or cycle < repeat - 1:
                    time.sleep(interval)
        
        print(f"\n✅ Successfully sent {sentences_sent} NMEA sentences")
        
    except Exception as e:
        print(f"❌ Error sending data: {e}")
        
    finally:
        sock.close()

def send_continuous_data(host: str, port: int, interval: float = 1.0):
    """Send continuous NMEA data (runs until interrupted)"""
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        print(f"Sending continuous NMEA data to {host}:{port}")
        print(f"Interval: {interval}s")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        sentences_sent = 0
        data_index = 0
        
        while True:
            # Cycle through the sample data
            sentence = SAMPLE_NMEA_DATA[data_index % len(SAMPLE_NMEA_DATA)]
            
            # Send the sentence
            sock.sendto(sentence.encode('utf-8') + b'\n', (host, port))
            sentences_sent += 1
            
            print(f"Sent ({sentences_sent}): {sentence}")
            
            data_index += 1
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Stopped. Sent {sentences_sent} NMEA sentences")
        
    except Exception as e:
        print(f"❌ Error sending data: {e}")
        
    finally:
        sock.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Send NMEA test data via UDP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 udp_test_sender.py                          # Send to localhost:4001
  python3 udp_test_sender.py -p 5000                  # Send to localhost:5000
  python3 udp_test_sender.py --host 192.168.1.100 -p 4001 # Send to remote host
  python3 udp_test_sender.py --continuous             # Send continuously
  python3 udp_test_sender.py --moving                 # Send moving vessel data
  python3 udp_test_sender.py --interval 0.5 --repeat 5 # Fast, multiple cycles
        """
    )
    
    parser.add_argument('--host', default='localhost',
                        help='Target host (default: localhost)')
    parser.add_argument('--port', '-p', type=int, default=4001,
                        help='Target port (default: 4001)')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                        help='Interval between sentences in seconds (default: 1.0)')
    parser.add_argument('--repeat', '-r', type=int, default=1,
                        help='Number of times to repeat the data set (default: 1)')
    parser.add_argument('--continuous', '-c', action='store_true',
                        help='Send data continuously until interrupted')
    parser.add_argument('--moving', '-m', action='store_true',
                        help='Send moving vessel data instead of static data')
    
    args = parser.parse_args()
    
    # Select data set
    if args.moving:
        data = MOVING_VESSEL_DATA
        print("Using moving vessel data set")
    else:
        data = SAMPLE_NMEA_DATA
        print("Using static GPS data set")
    
    # Send data
    if args.continuous:
        send_continuous_data(args.host, args.port, args.interval)
    else:
        send_nmea_data(args.host, args.port, data, args.interval, args.repeat)

if __name__ == "__main__":
    main()

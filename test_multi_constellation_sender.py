#!/usr/bin/env python3
"""
Send the multi-constellation test data via UDP
"""
import socket
import time
import sys

# Multi-constellation NMEA data
nmea_data = [
    "$PSTIS,*61",
    "$GLGSV,3,1,10,78,6.3,8.4,22.0,,,,28.9,70,71.0,341.7,23.1,86,44.3,296.7,23.7*62",
    "$GLGSV,3,2,10,80,24.6,116.7,41.5,79,31.6,54.8,31.8,69,21.1,68.9,29.9,87,16.2,337.5,20.7*60",
    "$GLGSV,3,3,10,85,33.0,215.2,42.0,71,33.8,275.6,30.8*68",
    "$GPGSV,4,1,15,03,8.4,113.9,31.3,04,34.5,63.3,32.0,06,52.7,218.0,46.3,07,42.9,164.5,42.0*79",
    "$GPGSV,4,2,15,09,76.6,59.1,39.0,11,47.8,285.5,23.5,16,9.8,67.5,31.5,29,3.5,341.7,28.7*73",
    "$GPGSV,4,3,15,30,16.9,188.4,49.4,40,15.5,122.3,42.9,49,31.6,180.0,40.6,05,,,*5A",
    "$GPGSV,4,4,15,19,,,,20,31.6,299.5,,21,30.9,293.9,*7C",
    "$GAGSV,3,1,12,04,40.8,61.9,35.6,05,32.3,240.5,34.1,09,88.6,180.0,32.9,11,22.5,168.8,41.4*50",
    "$GAGSV,3,2,12,23,9.8,70.3,37.9,34,35.9,309.4,28.1,36,59.8,218.0,43.2,06,67.5,66.1,*4C",
    "$GAGSV,3,3,12,19,,,,21,7.7,25.3,,27,,,,31,,,*53",
    "$GPGGA,113612.0,5036.742652,N,00535.205463,E,1,07,0.6,78.5,M,47.0,M,,*67",
    "$GNGNS,113612.0,5036.742652,N,00535.205463,E,AAA,18,0.6,78.5,47.0,,*1C",
    "$GPVTG,0.0,T,1.4,M,0.0,N,0.0,K,A*26",
    "$GPRMC,113612.0,A,5036.742652,N,00535.205463,E,0.0,0.0,040925,1.4,W,A*1B",
]

def send_data():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        print("Sending multi-constellation NMEA data to localhost:4001")
        print(f"Total sentences: {len(nmea_data)}")
        print("-" * 50)
        
        for i, sentence in enumerate(nmea_data):
            sock.sendto(sentence.encode('utf-8') + b'\n', ('localhost', 4001))
            print(f"Sent ({i+1}/{len(nmea_data)}): {sentence}")
            time.sleep(0.3)
        
        print("\n✅ All data sent successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    send_data()

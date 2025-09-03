# NMEA Parser Examples

This directory contains example NMEA data files and usage demonstrations.

## Sample Files

### `basic_gps.nmea`
Basic GPS data with position, time, and satellite information.

### `multi_constellation.nmea` 
Data from multiple satellite constellations (GPS, GLONASS, Galileo).

### `moving_vessel.nmea`
NMEA data from a moving vessel showing speed and course changes.

## Usage Examples

### Parse a single file
```bash
cd ..
python3 nmea_parser.py examples/basic_gps.nmea
```

### Parse with verbose output
```bash
python3 nmea_parser.py examples/multi_constellation.nmea --verbose
```

### Compare different data sets
```bash
python3 nmea_parser.py examples/basic_gps.nmea > output1.txt
python3 nmea_parser.py examples/moving_vessel.nmea > output2.txt
diff output1.txt output2.txt
```

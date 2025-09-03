# NMEA Parser

A comprehensive Python script that parses NMEA (National Marine Electronics Association) sentences and displays GPS/GNSS data in human-readable format.

## Features

- **Multi-constellation support**: GPS, GLONASS, Galileo, and BeiDou
- **Multiple NMEA sentence types**: GGA, RMC, GSA, GSV, VTG, GNS, and proprietary sentences
- **Colorized output**: Beautiful, color-coded terminal output for better readability
- **Human-readable output**: Position, time, satellite information, and navigation data
- **Flexible input**: Read from files, stdin, or interactive mode
- **Detailed satellite information**: Signal strength, elevation, azimuth, and constellation data
- **Smart color coding**: Signal strength, fix quality, and data importance indicated by colors

## Supported NMEA Sentences

| Sentence | Description | Data Extracted |
|----------|-------------|----------------|
| **GGA** | Global Positioning System Fix Data | Time, position, altitude, fix quality, satellites used |
| **RMC** | Recommended Minimum Navigation Information | Time, date, position, speed, course, status |
| **GSA** | GPS DOP and Active Satellites | Fix type, satellites used, dilution of precision |
| **GSV** | GPS Satellites in View | Satellite details, signal strength, elevation, azimuth |
| **VTG** | Track Made Good and Ground Speed | Course and speed information |
| **GNS** | GNSS Fix Data | Multi-constellation fix information |
| **PQXFI** | Proprietary Sentence | Custom data (varies by manufacturer) |

## Installation

### Quick Start (with colors)
```bash
# Install the colorama dependency for colored output
pip install colorama

# Run the parser
python3 nmea_parser.py your_nmea_file.txt
```

### Alternative (no colors)
If you prefer to run without colors or don't want to install dependencies, the script will automatically fall back to plain text output when `colorama` is not available.

**Requirements:**
- Python 3.6 or higher
- `colorama` package (optional, for colored output)

## Usage

### From Command Line

```bash
# Make the script executable
chmod +x nmea_parser.py

# Parse NMEA data from a file
python3 nmea_parser.py sample_data.txt

# Parse with verbose output (shows individual sentence parsing)
python3 nmea_parser.py sample_data.txt --verbose

# Interactive mode - paste NMEA sentences
python3 nmea_parser.py
```

### Interactive Mode

When run without arguments, the script enters interactive mode:

```bash
python3 nmea_parser.py
```

Then paste your NMEA sentences one per line and press Ctrl+D (EOF) when done.

### Input Formats

The script accepts NMEA sentences in standard format:
```
$GPGGA,183730.0,4733.508324,N,05245.174442,W,1,03,500.0,62.9,M,12.0,M,,*75
$GPRMC,183730.0,A,4733.508324,N,05245.174442,W,,,270417,0.0,E,A*13
$GPGSV,2,1,07,07,37,305,22,09,24,262,18,21,23,049,20,30,02,314,24*74
```

## Output Format

The script provides a comprehensive summary with color-coded information for better readability:

### Color Coding System

- **Headers**: Bright cyan for main sections (Position, Satellites, etc.)
- **Labels**: Magenta for field names (Latitude, Speed, etc.)
- **Data values**: Green for primary data
- **Additional info**: White for supplementary information (coordinate formats)
- **Signal strength**: 
  - Green: Strong signals (SNR ≥ 35dB)
  - Yellow: Moderate signals (15-34dB)
  - Red: Weak signals (< 15dB)
- **Fix quality**:
  - Green: High-quality fixes (RTK, 3D)
  - Yellow: Standard fixes (GPS, 2D)
  - Red: Poor or no fix
- **Warnings/Errors**: Yellow for warnings, Red for errors

The script provides a comprehensive summary including:

### Time Information
```
Time: 18:37:30.000 UTC
```

### Position Data
```
Position:
  Latitude:  47°33'30.50" N (47.558472°)
  Longitude: 052°45'10.47" W (-52.752907°)
  Altitude:  62.9 m
```

### Satellite Information
```
Satellites:
  GPS:
    Visible: 7, Used: 4
    Strong signals:
      PRN  7: SNR 22dB, El 37°, Az 305°
      PRN 30: SNR 24dB, El  2°, Az 314°
  GLONASS:
    Visible: 11, Used: 5
  Total: 18 visible, 9 with signal
  Fix quality: GPS fix (SPS)
  Satellites in fix: 3
  HDOP: 500.0
```

### Velocity Information (when available)
```
Velocity:
  Speed: 12.5 knots (23.2 km/h)
  Course: 285.0° (WNW)
```

## Example Usage

### Sample NMEA Data File

Create a file called `sample_nmea.txt`:
```
$GNGSA,A,3,07,09,21,,,,,,,,,,500.0,500.0,500.0*24
$GPGSV,2,1,07,07,37,305,22,09,24,262,18,21,23,049,20,30,02,314,24*74
$GPGGA,183730.0,4733.508324,N,05245.174442,W,1,03,500.0,62.9,M,12.0,M,,*75
$GPRMC,183730.0,A,4733.508324,N,05245.174442,W,,,270417,0.0,E,A*13
```

### Parse the Data

```bash
python3 nmea_parser.py sample_nmea.txt
```

### Expected Output

```
==================================================
NMEA DATA SUMMARY
==================================================

Time: 18:37:30.000 UTC

Position:
  Latitude:  47°33'30.50" N (47.558472°)
  Longitude: 052°45'10.47" W (-52.752907°)
  Altitude:  62.9 m

Velocity: Not available

Satellites:
  GPS:
    Visible: 7, Used: 4
    Strong signals:
      PRN  7: SNR 22dB, El 37°, Az 305°
      PRN 30: SNR 24dB, El  2°, Az 314°
  Total: 7 visible, 4 with signal
  Fix quality: GPS fix (SPS)
  Satellites in fix: 3
  HDOP: 500.0
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `filename` | Parse NMEA data from specified file |
| `--verbose` or `-v` | Show detailed parsing of each sentence |
| No arguments | Interactive mode - enter sentences manually |

## Technical Details

### Coordinate Conversion

The script converts NMEA coordinate format (DDMM.MMMM) to both:
- **Decimal degrees**: For precise calculations (47.558472°)
- **Degrees/Minutes/Seconds**: For traditional navigation (47°33'30.50")

### Satellite Constellations

Automatically detects constellation types based on sentence prefixes:
- **GP**: GPS (Global Positioning System)
- **GL**: GLONASS (Russian)
- **GA**: Galileo (European)
- **GB**: BeiDou (Chinese)
- **GN**: Multi-constellation GNSS

### Fix Quality Indicators

| Code | Description |
|------|-------------|
| 0 | Invalid |
| 1 | GPS fix (SPS) |
| 2 | DGPS fix |
| 3 | PPS fix |
| 4 | Real Time Kinematic |
| 5 | Float RTK |
| 6 | Estimated (dead reckoning) |
| 7 | Manual input mode |
| 8 | Simulation mode |

## Error Handling

The script gracefully handles:
- **Malformed sentences**: Skips invalid data without crashing
- **Missing data fields**: Shows "Not available" for incomplete information
- **Checksum errors**: Continues processing other sentences
- **File not found**: Clear error message with usage instructions

## Use Cases

- **Marine navigation**: Analyze GPS logs from boats and ships
- **Aviation**: Parse aircraft navigation data
- **Surveying**: Process high-precision GNSS measurements
- **IoT devices**: Debug GPS modules and trackers
- **Research**: Analyze satellite visibility and signal quality
- **Education**: Learn NMEA protocol and GPS technology

## Contributing

This is a single-file script designed for simplicity and portability. To extend functionality:

1. Add new sentence parsers to the `parsers` dictionary
2. Implement parsing methods following the existing pattern
3. Update the display formatting methods as needed

## License

This script is provided as-is for educational and practical use. Feel free to modify and distribute.

## Troubleshooting

### Common Issues

**"No valid NMEA sentences found"**
- Ensure sentences start with `$` and contain comma-separated fields
- Check that the file contains actual NMEA data, not binary or encoded data

**"Permission denied"**
- Make the script executable: `chmod +x nmea_parser.py`
- Or run with Python explicitly: `python3 nmea_parser.py`

**Incomplete satellite data**
- Some NMEA sources don't provide complete satellite information
- The script shows available data and indicates missing fields

### Getting Help

Run the script without arguments to see usage information:
```bash
python3 nmea_parser.py
```

For verbose output showing detailed sentence parsing:
```bash
python3 nmea_parser.py your_file.txt --verbose
```

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
- **Splunk integration**: Send parsed data to Splunk for analysis and long-term storage
- **JSON output**: Machine-readable format for integration with other systems
- **Flexible deployment**: Works standalone or integrated into larger monitoring systems
- **UDP streaming**: Real-time processing of continuous NMEA data streams
- **Network integration**: Receive data from GPS devices, AIS receivers, and marine equipment

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
- `splunk-sdk` package (optional, for Splunk integration)

## Usage

### From Command Line

```bash
# Make the script executable
chmod +x nmea_parser.py

# Parse NMEA data from a file
python3 nmea_parser.py sample_data.txt

# Parse with verbose output (shows individual sentence parsing)
python3 nmea_parser.py sample_data.txt --verbose

# Output as JSON for integration with other systems
python3 nmea_parser.py sample_data.txt --json

# Send data to Splunk for analysis
python3 nmea_parser.py sample_data.txt --splunk

# Receive UDP stream from GPS device on port 4001
python3 nmea_parser.py --udp 4001

# UDP stream with continuous display
python3 nmea_parser.py --udp 4001 --continuous

# UDP stream to Splunk in real-time
python3 nmea_parser.py --udp 4001 --splunk

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
| `--json` or `-j` | Output data in JSON format |
| `--splunk` or `-s` | Send parsed data to Splunk |
| `--splunk-config` | Show Splunk configuration help |
| `--splunk-test` | Test Splunk connection and exit |
| `--no-color` | Disable colored output |
| `--interactive` or `-i` | Interactive mode - enter sentences manually |
| `--udp PORT` or `-u PORT` | Receive NMEA data via UDP on specified port |
| `--udp-host HOST` | UDP host to bind to (default: 0.0.0.0) |
| `--continuous` or `-c` | Continuous output mode for real-time data |

## Splunk Integration

The NMEA parser can send parsed data directly to Splunk for analysis, alerting, and long-term storage. This is ideal for maritime operations, fleet management, and IoT device monitoring.

### Quick Start with Splunk

1. **Install Splunk SDK**:
   ```bash
   pip install splunk-sdk
   ```

2. **Configure connection** (via environment variables):
   ```bash
   export SPLUNK_HOST=splunk.company.com
   export SPLUNK_USERNAME=nmea_user
   export SPLUNK_PASSWORD=secure_password
   export SPLUNK_INDEX=maritime_data
   ```

3. **Test connection**:
   ```bash
   python3 nmea_parser.py --splunk-test
   ```

4. **Send data to Splunk**:
   ```bash
   python3 nmea_parser.py vessel_data.nmea --splunk
   ```

### Splunk Configuration

The parser uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `SPLUNK_HOST` | Splunk server hostname/IP | localhost |
| `SPLUNK_PORT` | Splunk management port | 8089 |
| `SPLUNK_USERNAME` | Splunk username | admin |
| `SPLUNK_PASSWORD` | Splunk password | changeme |
| `SPLUNK_SCHEME` | Connection scheme (http/https) | https |
| `SPLUNK_INDEX` | Target index name | nmea_data |
| `SPLUNK_SOURCE` | Source field value | nmea_parser |
| `SPLUNK_SOURCETYPE` | Sourcetype field value | nmea:json |
| `SPLUNK_VERIFY_SSL` | Verify SSL certificates | false |
| `SPLUNK_TIMEOUT` | Connection timeout (seconds) | 30 |
| `SPLUNK_BATCH_SIZE` | Events per batch | 100 |
| `SPLUNK_BATCH_TIMEOUT` | Batch timeout (seconds) | 10 |

### Splunk Data Structure

The parser sends structured JSON data to Splunk with the following format:

```json
{
  "timestamp": "2024-01-15T14:30:45.123456",
  "event_type": "nmea_sentence",
  "sentence_type": "GPGGA",
  "parsed_data": {
    "type": "GGA",
    "time": "14:30:45.000",
    "latitude": 47.558472,
    "longitude": -52.752907,
    "fix_quality": "GPS fix (SPS)",
    "num_satellites": 8,
    "altitude": 62.9
  },
  "location": {
    "lat": 47.558472,
    "lon": -52.752907,
    "alt": 62.9
  },
  "raw_sentence": "$GPGGA,143045.0,4733.508,N,05245.175,W,1,08,1.0,62.9,M,46.9,M,,*47"
}
```

### Splunk Searches and Dashboards

Once data is in Splunk, you can create powerful searches and dashboards:

**Track vessel movement**:
```spl
index=nmea_data event_type=nmea_sentence location.lat=* location.lon=*
| eval _time=strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
| timechart span=1m avg(location.lat) as latitude avg(location.lon) as longitude
```

**Monitor satellite signal quality**:
```spl
index=nmea_data parsed_data.satellites{}
| eval satellites=mvjoin('parsed_data.satellites{}.snr', ",")
| rex field=satellites "(?<snr>\d+)"
| stats avg(snr) as avg_snr count as satellite_count by _time
```

**Alert on GPS signal loss**:
```spl
index=nmea_data parsed_data.fix_quality="Invalid" OR parsed_data.fix_quality="No fix"
| stats count by host, parsed_data.fix_quality
```

### Production Deployment

For production environments:

1. **Create dedicated Splunk user**:
   ```bash
   # In Splunk Web: Settings > Access Controls > Users
   # Create user with 'can_edit' capability for target index
   ```

2. **Set up index with appropriate retention**:
   ```bash
   # In Splunk Web: Settings > Indexes
   # Create index with maritime-specific settings
   ```

3. **Use secure environment variables**:
   ```bash
   # Store in secure configuration management system
   export SPLUNK_HOST=splunk-prod.company.com
   export SPLUNK_USERNAME=nmea_service_account
   export SPLUNK_PASSWORD=$(vault kv get -field=password secret/splunk/nmea)
   export SPLUNK_INDEX=maritime_production
   export SPLUNK_VERIFY_SSL=true
   ```

4. **Run as service**:
   ```bash
   # Example systemd service
   python3 nmea_parser.py /var/log/vessel/nmea.log --splunk
   ```

## UDP Streaming

The NMEA parser can receive continuous data streams via UDP, making it perfect for real-time integration with GPS devices, AIS receivers, chart plotters, and marine navigation systems.

### Quick Start with UDP

1. **Start UDP receiver**:
   ```bash
   python3 nmea_parser.py --udp 4001
   ```

2. **Configure your GPS device** to send NMEA data to your computer's IP address on port 4001

3. **View real-time data**:
   ```bash
   python3 nmea_parser.py --udp 4001 --continuous
   ```

### UDP Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--udp PORT` | UDP port to listen on | Required |
| `--udp-host HOST` | Host interface to bind to | 0.0.0.0 (all interfaces) |
| `--udp-buffer SIZE` | UDP receive buffer size | 4096 bytes |
| `--continuous` | Show real-time sentence processing | Off |

### Real-time Output Modes

**Standard Mode** (summary only):
```bash
python3 nmea_parser.py --udp 4001
# Shows connection status and periodic statistics
# Final summary when stopped with Ctrl+C
```

**Continuous Mode** (real-time):
```bash
python3 nmea_parser.py --udp 4001 --continuous
# Shows each NMEA sentence as received
# Real-time statistics every 10 seconds
```

**JSON Stream Mode**:
```bash
python3 nmea_parser.py --udp 4001 --json
# Outputs each sentence as structured JSON
# Perfect for piping to other applications
```

**Splunk Integration**:
```bash
python3 nmea_parser.py --udp 4001 --splunk
# Real-time streaming to Splunk
# Includes connection statistics and error handling
```

### Common GPS Device Configurations

**Garmin GPS** (NMEA 0183 output):
- Port: Typically 4001 or 2000
- Format: Standard NMEA sentences
- Rate: 1-10 Hz depending on model

**AIS Receivers**:
- Port: Commonly 4002 or 10110
- Format: AIS messages in NMEA format
- Rate: Variable based on traffic

**Chart Plotters** (Raymarine, Furuno, etc.):
- Port: Configurable, often 4001
- Format: Multi-constellation NMEA
- Rate: 1-5 Hz typical

### Network Setup Examples

**Local GPS Device**:
```bash
# GPS device configured to send to 127.0.0.1:4001
python3 nmea_parser.py --udp 4001 --udp-host 127.0.0.1
```

**Network GPS Server**:
```bash
# Listen on all network interfaces
python3 nmea_parser.py --udp 4001 --udp-host 0.0.0.0
```

**High-frequency Data**:
```bash
# Larger buffer for high-rate GPS (10Hz+)
python3 nmea_parser.py --udp 4001 --udp-buffer 8192
```

### UDP Data Flow

```
GPS Device → UDP Network → NMEA Parser → [Display|JSON|Splunk]
    ↓              ↓             ↓              ↓
  4001/udp    Real-time      Parse &        Output
             Streaming      Process        Format
```

### Testing UDP Functionality

The repository includes a UDP test sender for development and testing:

```bash
# Send test data to localhost:4001
python3 udp_test_sender.py

# Send to different port with faster rate
python3 udp_test_sender.py --port 5000 --interval 0.1

# Send moving vessel simulation
python3 udp_test_sender.py --moving --continuous

# Send to remote host
python3 udp_test_sender.py --host 192.168.1.100 --port 4001
```

### Production Deployment

For production maritime systems:

1. **Firewall Configuration**:
   ```bash
   # Allow UDP traffic on NMEA port
   sudo ufw allow 4001/udp
   ```

2. **System Service** (systemd example):
   ```ini
   [Unit]
   Description=NMEA UDP Parser
   After=network.target

   [Service]
   Type=simple
   User=nmea
   WorkingDirectory=/opt/nmea_parser
   ExecStart=/usr/bin/python3 nmea_parser.py --udp 4001 --splunk
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Log Rotation**:
   ```bash
   # Configure logrotate for output logs
   /var/log/nmea/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

### Error Handling and Monitoring

The UDP receiver includes comprehensive error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Parse errors**: Invalid sentences logged but don't stop processing
- **Buffer overruns**: Configurable buffer sizes for high-rate data
- **Connection monitoring**: Real-time statistics and health checks

**Monitoring Commands**:
```bash
# Check if parser is receiving data
netstat -an | grep :4001

# Monitor real-time statistics
python3 nmea_parser.py --udp 4001 --continuous | grep "Real-time Stats"

# Test connectivity
python3 udp_test_sender.py --host YOUR_HOST --port 4001
```

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

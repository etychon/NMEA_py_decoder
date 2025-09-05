# NMEA Parser

A comprehensive, production-ready Python application that parses NMEA (National Marine Electronics Association) sentences and provides advanced GPS/GNSS data processing capabilities. Designed for maritime navigation, fleet tracking, survey work, and IoT applications, it supports real-time data streams, enterprise integration, and intelligent position processing.

## Features

### 🌟 **Core Parsing Capabilities**
- **Multi-constellation support**: GPS, GLONASS, Galileo, and BeiDou with full precision
- **Comprehensive sentence types**: GGA, RMC, GSA, GSV, VTG, GNS, and proprietary sentences
- **High-precision coordinates**: Supports decimal values for satellite data (elevation, azimuth, SNR)
- **Real-world data compatibility**: Handles complex multi-constellation GNSS receiver output
- **Robust error handling**: Graceful handling of malformed or incomplete NMEA sentences

### 🎨 **Advanced Display & Output**
- **Colorized terminal output**: Beautiful, color-coded display with smart signal strength indicators
- **Block-based processing**: Processes complete NMEA blocks rather than individual sentences
- **Multiple output formats**: Human-readable, JSON, and structured data for integration
- **Real-time statistics**: Live packet rates, sentence counts, and processing metrics
- **Interactive mode**: Paste NMEA sentences directly for immediate analysis

### 📍 **Intelligent Position Processing**
- **Block-based coordinate processing**: Triggers position updates after complete NMEA data blocks
- **Movement detection & analysis**: Automatic calculation of distance, bearing, and speed between positions
- **Geofencing capabilities**: Define custom zones with entry/exit alerts and proximity monitoring
- **Position history tracking**: Maintains rolling buffer of recent positions for trend analysis
- **Configurable movement thresholds**: Adjustable sensitivity for stationary vs. moving detection

### 🌐 **Real-time Streaming & Network Integration**
- **UDP streaming support**: Receive continuous NMEA data from GPS devices, AIS receivers, and marine equipment
- **Live data processing**: Real-time parsing with configurable update intervals and statistics
- **Network device compatibility**: Works with professional maritime and survey equipment
- **Concurrent processing**: Handle multiple data types simultaneously (position, satellites, velocity)
- **Production-ready reliability**: Robust UDP handling with error recovery and connection monitoring

### 📊 **Enterprise Integration & Analytics**
- **Splunk integration**: Complete enterprise logging with human-readable output for every data transmission
- **Structured data export**: JSON format with precise coordinate data and metadata
- **Batch processing**: Efficient handling of large NMEA datasets with progress indicators
- **Configuration management**: Environment variable-based setup for production deployments
- **Monitoring & observability**: Comprehensive statistics, error tracking, and performance metrics

### 🛰️ **Advanced Satellite Analysis**
- **Multi-constellation tracking**: Separate analysis for GPS, GLONASS, Galileo, and other systems
- **Signal quality assessment**: Color-coded SNR indicators with strong/moderate/weak classifications
- **Satellite geometry analysis**: Elevation, azimuth, and HDOP calculations for accuracy assessment
- **Fix quality monitoring**: Real-time tracking of 2D/3D fixes and satellite usage
- **Constellation performance**: Compare signal strength and availability across different GNSS systems

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

# Send data to Splunk for analysis (with human-readable logging)
python3 nmea_parser.py sample_data.txt --splunk

# Receive UDP stream from GPS device on port 4001
python3 nmea_parser.py --udp 4001

# UDP stream with continuous display
python3 nmea_parser.py --udp 4001 --continuous

# UDP stream to Splunk in real-time
python3 nmea_parser.py --udp 4001 --splunk

# Real-time position processing with movement analysis
python3 nmea_parser.py --udp 4001 --track-position

# Position tracking with geofencing
python3 nmea_parser.py --udp 4001 --track-position \
    --geofence 50.612 5.587 100 "Home Base" \
    --geofence 50.613 5.588 50 "Waypoint Alpha"

# Complete maritime monitoring setup
python3 nmea_parser.py --udp 4001 --track-position --splunk \
    --geofence 40.689 -74.044 500 "NY Harbor" \
    --min-movement 0.5

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

## Block-Based Position Processing

The NMEA parser features intelligent **block-based position processing** that processes GPS coordinates after receiving complete NMEA data blocks rather than individual sentences. This provides more accurate and contextual position updates.

### How It Works

Instead of triggering position callbacks after each individual sentence, the parser:

1. **Collects related sentences** into logical blocks (GGA + GSV + GSA + RMC + VTG)
2. **Waits for block completion** based on data types received or timeout
3. **Processes complete blocks** with full context (position + satellites + velocity)
4. **Triggers position callbacks** with comprehensive data

### Example Output

```bash
📦 NMEA Block Processed: Block: 15 sentences, types: fix_data, position, satellites
📍 Position: 50.612336°, 5.586746°, 68.4m
   Movement: 4.5m at 33.7°, 5.1 knots
   Block Velocity: 22.4 knots @ 84.4°
   🏠 Inside geofence: Harbor Zone (104.2m from center)
```

### Benefits

- **More accurate movement calculations** using complete block data
- **Contextual position updates** with satellite and velocity information
- **Reduced noise** from incomplete or partial data
- **Better real-time performance** for continuous streams
- **Enhanced geofencing** with complete position context

### Configuration

```bash
# Enable position tracking with block processing
python3 nmea_parser.py --udp 4001 --track-position

# Add geofences for zone monitoring
python3 nmea_parser.py --udp 4001 --track-position \
    --geofence 50.612 5.587 100 "Home Base"

# Adjust movement sensitivity
python3 nmea_parser.py --udp 4001 --track-position --min-movement 0.5
```

## Command Line Options

### Basic Options
| Option | Description |
|--------|-------------|
| `filename` | Parse NMEA data from specified file |
| `--verbose` or `-v` | Show detailed parsing of each sentence |
| `--json` or `-j` | Output data in JSON format |
| `--no-color` | Disable colored output |
| `--interactive` or `-i` | Interactive mode - enter sentences manually |

### Network & Streaming Options
| Option | Description |
|--------|-------------|
| `--udp PORT` or `-u PORT` | Receive NMEA data via UDP on specified port |
| `--udp-host HOST` | UDP host to bind to (default: 0.0.0.0 - all interfaces) |
| `--udp-buffer SIZE` | UDP receive buffer size in bytes (default: 4096) |
| `--continuous` or `-c` | Continuous output mode for real-time UDP streaming |

### Position Processing Options
| Option | Description |
|--------|-------------|
| `--track-position` | Enable real-time position tracking and movement analysis |
| `--geofence LAT LON RADIUS NAME` | Add geofence zone (can be used multiple times) |
| `--min-movement METERS` | Minimum movement threshold in meters (default: 1.0) |

### Splunk Integration Options
| Option | Description |
|--------|-------------|
| `--splunk` or `-s` | Send parsed data to Splunk with human-readable logging |
| `--splunk-config` | Show Splunk configuration help and examples |
| `--splunk-test` | Test Splunk connection and exit |

## Splunk Integration

The NMEA parser provides comprehensive Splunk integration with **human-readable logging** for every data transmission. This is ideal for maritime operations, fleet management, and IoT device monitoring, providing both enterprise data storage and immediate operational visibility.

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

### Human-Readable Splunk Logging

Every time data is sent to Splunk, you'll see immediate human-readable feedback:

```bash
📤 Splunk: GGA Position 47.558472°, -52.752907°, 62.9m at 18:37:30.000
📤 Splunk: GSV Satellites - 7 total, 4 with signal
📤 Splunk: GSA Fix - 3D fix, 3 satellites, HDOP 500.0
📤 Splunk: RMC Position 47.558472°, -52.752907° at 18:37:30.000
📤 Splunk: VTG Velocity - 22.4 knots @ 84.4°
📤 Splunk: Summary data sent to index 'main'
```

**Benefits:**
- **Immediate feedback** - See exactly what's being sent to Splunk
- **Data verification** - Confirm parsing accuracy before storage
- **Troubleshooting** - Quickly identify connection or data issues
- **Operational visibility** - Monitor data flow in real-time

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

### 🚢 **Maritime & Marine Operations**
- **Real-time vessel tracking** with block-based position processing and movement analysis
- **Harbor management** with geofencing for port entry/exit monitoring
- **Fleet coordination** using UDP streaming from multiple vessels
- **Navigation safety** with continuous GNSS monitoring and Splunk alerting
- **AIS integration** for comprehensive maritime situational awareness

### 📊 **Enterprise & Analytics**
- **Maritime data analytics** with Splunk integration and human-readable logging
- **Performance monitoring** of GNSS equipment and signal quality
- **Compliance reporting** with structured data export and long-term storage
- **Operational dashboards** using JSON output for real-time visualization
- **Alert systems** based on geofence violations and movement patterns

### 🛰️ **Survey & High-Precision Applications**
- **Survey data processing** with multi-constellation support and decimal precision
- **RTK/PPK workflows** with comprehensive satellite analysis
- **Quality assessment** using HDOP, signal strength, and constellation performance
- **Data validation** with block-based processing and movement verification
- **Research applications** for GNSS signal analysis and atmospheric studies

### 🌐 **IoT & Device Integration**
- **GPS module testing** with real-time UDP streaming and diagnostics
- **Device debugging** using verbose output and detailed sentence parsing
- **Network integration** with professional marine and survey equipment
- **Production monitoring** with continuous data streams and error handling
- **System integration** via JSON API and structured data export

### 🎓 **Education & Development**
- **NMEA protocol learning** with color-coded output and detailed explanations
- **GNSS technology education** showing multi-constellation operations
- **Development testing** with interactive mode and comprehensive error handling
- **Protocol analysis** using verbose parsing and block-based processing
- **System prototyping** with flexible input/output options and real-time capabilities

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

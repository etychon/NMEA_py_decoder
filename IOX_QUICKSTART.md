# IOx Quick Start Guide for NMEA Parser

This guide will get you up and running with the NMEA Parser on a Cisco IOx-enabled router in under 10 minutes.

## Prerequisites ✅

- Cisco router with IOx capability (ISR 4K, ASR 1K, IR 1K, etc.)
- IOx enabled on the router
- Docker installed on your build machine
- Network access to the router
- NMEA data source (GPS device, AIS receiver, etc.)

## Step 1: Build the IOx Package 🔨

```bash
# Clone or navigate to the NMEA parser directory
cd NMEA_py_decoder

# Build the complete IOx package
./build_iox.sh

# This creates: nmea-parser-1.0.0.tar
```

## Step 2: Deploy to Router 🚀

### Option A: Using ioxclient (Recommended)

```bash
# Install ioxclient if not already installed
pip install ioxclient

# Configure connection to your router
ioxclient configure local
# Enter router IP, username, password when prompted

# Install the application
ioxclient app install nmea-parser-1.0.0.tar --name nmea-parser

# Activate and start
ioxclient app activate nmea-parser
ioxclient app start nmea-parser
```

### Option B: Using Local Manager Web Interface

1. Open browser to `https://your-router-ip:8443`
2. Login with your router credentials
3. Navigate to **Apps** → **Install App**
4. Browse and select `nmea-parser-1.0.0.tar`
5. Click **Install**
6. After installation, **Activate** and **Start** the app

## Step 3: Configure NMEA Data Source 📡

Configure your GPS device or NMEA source to send UDP packets to:
- **IP Address**: Your router's IP address
- **Port**: 4001
- **Protocol**: UDP

### Example GPS Device Configurations:

**Garmin GPS:**
- Output: NMEA 0183
- Interface: Network/UDP
- Target: router-ip:4001

**Chart Plotter:**
- NMEA Output: Enabled
- Network: UDP Broadcast
- Port: 4001

**AIS Receiver:**
- Output Format: NMEA
- Network: UDP
- Destination: router-ip:4001

## Step 4: Verify Operation ✓

```bash
# Check application status
ioxclient app status nmea-parser

# View real-time logs
ioxclient app logs nmea-parser --follow

# Test health endpoint
curl http://router-ip:8080/health
```

Expected output in logs:
```
[INFO] Starting IOx NMEA Parser Service
[INFO] UDP receiver started successfully
[INFO] Position update: 50.612336°, 5.586746°, 68.4m
[INFO] Movement: 4.5m at 33.7°, 5.1 knots
```

## Step 5: Test with Sample Data 🧪

If you don't have a GPS device ready, test with sample data:

```bash
# Send test NMEA data to the router
echo '$GPGGA,183730.0,4733.508324,N,05245.174442,W,1,03,500.0,62.9,M,12.0,M,,*75' | nc -u router-ip 4001

# Check logs for processing
ioxclient app logs nmea-parser
```

## Configuration Options ⚙️

### Basic Configuration (Environment Variables)

```bash
# Configure via ioxclient
ioxclient app configure nmea-parser --env NMEA_TRACK_POSITION=true
ioxclient app configure nmea-parser --env NMEA_MIN_MOVEMENT=2.0

# Restart to apply changes
ioxclient app stop nmea-parser
ioxclient app start nmea-parser
```

### Advanced Configuration

Create a configuration file and apply it:

```bash
# Create env.json
{
  "NMEA_MODE": "udp",
  "NMEA_UDP_PORT": "4001",
  "NMEA_TRACK_POSITION": "true",
  "NMEA_CONTINUOUS": "true",
  "NMEA_GEOFENCES": "[{\"lat\": 50.612, \"lon\": 5.587, \"radius\": 100, \"name\": \"Harbor\"}]",
  "NMEA_STATS_INTERVAL": "300"
}

# Apply configuration
ioxclient app configure nmea-parser --env-file env.json
```

## Monitoring & Maintenance 📊

### Health Checks
```bash
# Application health
curl http://router-ip:8080/health

# Detailed status
ioxclient app status nmea-parser --detail

# Resource usage
ioxclient app resource nmea-parser
```

### Log Monitoring
```bash
# Follow live logs
ioxclient app logs nmea-parser --follow

# Get last 100 lines
ioxclient app logs nmea-parser --tail 100

# Search for errors
ioxclient app logs nmea-parser | grep ERROR
```

### Performance Tuning
```bash
# For high-frequency data (10Hz+ GPS)
ioxclient app configure nmea-parser --env NMEA_UDP_BUFFER_SIZE=8192

# Reduce logging for production
ioxclient app configure nmea-parser --env NMEA_VERBOSE_LOGGING=false
ioxclient app configure nmea-parser --env NMEA_LOG_LEVEL=WARN
```

## Troubleshooting 🔧

### Common Issues

**App won't start:**
```bash
# Check router resources
ioxclient platform resource

# Check app logs
ioxclient app logs nmea-parser
```

**No NMEA data:**
```bash
# Test UDP connectivity
nc -u router-ip 4001 < sample_nmea.txt

# Check GPS device configuration
# Verify network routing
```

**High CPU/Memory usage:**
```bash
# Check resource consumption
ioxclient app resource nmea-parser

# Reduce processing frequency
ioxclient app configure nmea-parser --env NMEA_STATS_INTERVAL=600
```

### Debug Mode

```bash
# Enable debug logging
ioxclient app configure nmea-parser --env NMEA_LOG_LEVEL=DEBUG
ioxclient app stop nmea-parser
ioxclient app start nmea-parser

# Watch debug output
ioxclient app logs nmea-parser --follow
```

## Production Deployment 🏭

### Security Considerations
- Change default ports if needed
- Configure firewall rules appropriately
- Use secure credentials for Splunk integration
- Enable log rotation

### Scaling
- Monitor resource usage under load
- Adjust buffer sizes for high-frequency data
- Consider multiple instances for redundancy

### Integration
- Configure Splunk for enterprise logging
- Set up geofencing for operational alerts
- Integrate with network management systems

## Next Steps 🎯

1. **Configure Geofencing**: Set up location-based alerts
2. **Enable Splunk Integration**: For enterprise data analytics
3. **Set up Monitoring**: Integrate with your network monitoring system
4. **Optimize Performance**: Tune for your specific data rates and requirements

## Support 💬

- Check application logs: `ioxclient app logs nmea-parser`
- Review health status: `curl http://router-ip:8080/health`
- Consult the full README.md for detailed configuration options
- Verify GPS device NMEA output format and network settings

---

**Success!** 🎉 Your NMEA Parser is now running on IOx and processing GPS data at the network edge!

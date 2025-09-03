# Changelog

All notable changes to the NMEA Python Decoder project will be documented in this file.

## [1.0.0] - 2024-09-03

### Added
- Initial release of NMEA Python Decoder
- Support for multiple NMEA sentence types:
  - GGA (Global Positioning System Fix Data)
  - RMC (Recommended Minimum Navigation Information)
  - GSA (GPS DOP and Active Satellites)
  - GSV (GPS Satellites in View)
  - VTG (Track Made Good and Ground Speed)
  - GNS (GNSS Fix Data)
  - PQXFI (Proprietary sentences)
- Multi-constellation support (GPS, GLONASS, Galileo, BeiDou)
- Human-readable output formatting
- Command-line interface with file input and interactive modes
- Verbose mode for detailed sentence parsing
- Comprehensive error handling
- Complete documentation and examples
- Project structure with examples directory
- MIT License
- Requirements file (no external dependencies)
- Git ignore file for Python projects

### Features
- Coordinate conversion (DDMM.MMMM to decimal degrees and DMS format)
- Satellite information with signal strength, elevation, and azimuth
- Time parsing and formatting
- Speed and course calculation with compass directions
- Fix quality interpretation
- Dilution of Precision (DOP) values

### Examples
- Basic GPS data parsing
- Multi-constellation satellite data
- Moving vessel with speed and course changes

### Documentation
- Comprehensive README with usage examples
- Technical details and troubleshooting guide
- Examples directory with sample NMEA files
- Inline code documentation and type hints

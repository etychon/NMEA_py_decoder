#!/bin/bash

# Build script for NMEA Parser IOx Application
# This script builds and packages the application for Cisco IOx deployment

set -e  # Exit on any error

# Configuration
APP_NAME="nmea-parser"
VERSION="1.0.0"
DOCKER_IMAGE="${APP_NAME}:${VERSION}"
IOX_PACKAGE="${APP_NAME}-${VERSION}.tar"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker."
        exit 1
    fi
    
    # Check if ioxclient is available (optional)
    if command -v ioxclient &> /dev/null; then
        IOX_CLIENT_AVAILABLE=true
        log_info "ioxclient found - can build IOx packages"
    else
        IOX_CLIENT_AVAILABLE=false
        log_warning "ioxclient not found - will create manual package"
    fi
    
    log_success "Dependencies check completed"
}

# Clean previous builds
clean_build() {
    log_info "Cleaning previous builds..."
    
    # Remove old Docker images
    if docker images | grep -q "${APP_NAME}"; then
        log_info "Removing old Docker images..."
        docker rmi "${DOCKER_IMAGE}" 2>/dev/null || true
        docker rmi "${APP_NAME}:latest" 2>/dev/null || true
    fi
    
    # Remove old package files
    rm -f "${IOX_PACKAGE}"
    rm -rf "package"
    
    log_success "Clean completed"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image: ${DOCKER_IMAGE}"
    
    # Build the image
    docker build -t "${DOCKER_IMAGE}" -t "${APP_NAME}:latest" .
    
    # Verify the image was built successfully
    if docker images | grep -q "${APP_NAME}"; then
        log_success "Docker image built successfully"
        
        # Show image info
        docker images | grep "${APP_NAME}"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Test Docker image
test_docker_image() {
    log_info "Testing Docker image..."
    
    # Run basic health check
    log_info "Running container health check..."
    if docker run --rm "${DOCKER_IMAGE}" python3 health_check.py; then
        log_success "Container health check passed"
    else
        log_error "Container health check failed"
        exit 1
    fi
    
    # Test configuration loading
    log_info "Testing configuration loading..."
    if docker run --rm "${DOCKER_IMAGE}" python3 iox_config.py; then
        log_success "Configuration test passed"
    else
        log_error "Configuration test failed"
        exit 1
    fi
    
    log_success "Docker image tests completed"
}

# Create IOx package structure
create_package_structure() {
    log_info "Creating IOx package structure..."
    
    mkdir -p package
    
    # Copy package descriptor
    cp package.yaml package/
    
    # Export Docker image
    log_info "Exporting Docker image..."
    docker save "${DOCKER_IMAGE}" -o package/rootfs.tar
    
    log_success "Package structure created"
}

# Build IOx package with ioxclient
build_iox_package() {
    if [ "$IOX_CLIENT_AVAILABLE" = true ]; then
        log_info "Building IOx package with ioxclient..."
        
        cd package
        ioxclient package .
        cd ..
        
        # Move the package to the main directory
        if [ -f "package/package.tar" ]; then
            mv "package/package.tar" "${IOX_PACKAGE}"
            log_success "IOx package built: ${IOX_PACKAGE}"
        else
            log_error "ioxclient failed to create package"
            exit 1
        fi
    else
        log_info "Creating manual IOx package..."
        
        # Create tar package manually
        cd package
        tar -cf "../${IOX_PACKAGE}" *
        cd ..
        
        log_success "Manual IOx package created: ${IOX_PACKAGE}"
    fi
}

# Validate IOx package
validate_package() {
    log_info "Validating IOx package..."
    
    if [ ! -f "${IOX_PACKAGE}" ]; then
        log_error "Package file not found: ${IOX_PACKAGE}"
        exit 1
    fi
    
    # Check package size
    PACKAGE_SIZE=$(du -h "${IOX_PACKAGE}" | cut -f1)
    log_info "Package size: ${PACKAGE_SIZE}"
    
    # List package contents
    log_info "Package contents:"
    tar -tf "${IOX_PACKAGE}" | head -20
    
    if [ "$IOX_CLIENT_AVAILABLE" = true ]; then
        # Validate with ioxclient
        log_info "Validating with ioxclient..."
        if ioxclient package verify "${IOX_PACKAGE}"; then
            log_success "Package validation passed"
        else
            log_error "Package validation failed"
            exit 1
        fi
    fi
    
    log_success "Package validation completed"
}

# Generate deployment documentation
generate_docs() {
    log_info "Generating deployment documentation..."
    
    cat > "IOX_DEPLOYMENT.md" << EOF
# IOx Deployment Guide for NMEA Parser

## Package Information
- **Application Name**: ${APP_NAME}
- **Version**: ${VERSION}
- **Package File**: ${IOX_PACKAGE}
- **Build Date**: $(date)

## Prerequisites
1. Cisco router with IOx capability
2. IOx enabled on the router
3. Network connectivity for NMEA data input

## Deployment Steps

### 1. Upload Package
\`\`\`bash
# Using ioxclient
ioxclient app install ${IOX_PACKAGE} --name ${APP_NAME}

# Or via Local Manager web interface
# Navigate to: https://router-ip:8443
# Go to Apps -> Install App -> Browse and select ${IOX_PACKAGE}
\`\`\`

### 2. Configure Application
\`\`\`bash
# Activate the application
ioxclient app activate ${APP_NAME}

# Start the application
ioxclient app start ${APP_NAME}
\`\`\`

### 3. Environment Configuration
Create an environment configuration file with your specific settings:

\`\`\`bash
# Example configuration
NMEA_MODE=udp
NMEA_UDP_PORT=4001
NMEA_TRACK_POSITION=true
NMEA_CONTINUOUS=true
\`\`\`

### 4. Verification
\`\`\`bash
# Check application status
ioxclient app status ${APP_NAME}

# View application logs
ioxclient app logs ${APP_NAME}

# Check health status
curl http://router-ip:8080/health
\`\`\`

## Network Configuration
- **UDP Port 4001**: NMEA data input
- **TCP Port 8080**: Health check endpoint

## Monitoring
- Health checks run every 30 seconds
- Logs are available via ioxclient or Local Manager
- Application statistics are logged every 5 minutes

## Troubleshooting
1. Check application logs for errors
2. Verify network connectivity to NMEA data source
3. Ensure UDP port 4001 is accessible
4. Check router resource utilization

## Configuration Options
See the sample.env file in the package for all available configuration options.
EOF

    log_success "Deployment documentation generated: IOX_DEPLOYMENT.md"
}

# Main build process
main() {
    log_info "Starting IOx build process for ${APP_NAME} v${VERSION}"
    
    # Check if we're in the right directory
    if [ ! -f "nmea_parser.py" ]; then
        log_error "Please run this script from the NMEA parser directory"
        exit 1
    fi
    
    # Run build steps
    check_dependencies
    clean_build
    build_docker_image
    test_docker_image
    create_package_structure
    build_iox_package
    validate_package
    generate_docs
    
    # Clean up temporary files
    rm -rf package
    
    log_success "IOx build completed successfully!"
    log_info "Package: ${IOX_PACKAGE}"
    log_info "Size: $(du -h "${IOX_PACKAGE}" | cut -f1)"
    log_info "Documentation: IOX_DEPLOYMENT.md"
    
    echo ""
    echo "Next steps:"
    echo "1. Copy ${IOX_PACKAGE} to your IOx-enabled router"
    echo "2. Follow the deployment guide in IOX_DEPLOYMENT.md"
    echo "3. Configure NMEA data source to send to router IP:4001"
}

# Handle script arguments
case "${1:-}" in
    "clean")
        clean_build
        ;;
    "docker")
        build_docker_image
        ;;
    "test")
        test_docker_image
        ;;
    "package")
        create_package_structure
        build_iox_package
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|docker|test|package]"
        echo "  clean   - Clean previous builds"
        echo "  docker  - Build Docker image only"
        echo "  test    - Test Docker image only"
        echo "  package - Create IOx package only"
        echo "  (no args) - Full build process"
        exit 1
        ;;
esac

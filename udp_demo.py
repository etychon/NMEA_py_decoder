#!/usr/bin/env python3
"""
UDP Streaming Demo for NMEA Parser
Demonstrates the UDP streaming capabilities with examples and tests.
"""

import subprocess
import time
import sys
import threading
import os

def run_command(cmd, timeout=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def demo_udp_help():
    """Show UDP-related help"""
    print("=" * 60)
    print("UDP STREAMING HELP")
    print("=" * 60)
    print()
    
    # Show UDP options in help
    code, stdout, stderr = run_command("python3 nmea_parser.py --help | grep -A 20 'UDP'")
    if code == 0:
        print("UDP Options in Help:")
        print("-" * 30)
        print(stdout)
    else:
        print("Could not retrieve help information")
    
    print()

def demo_udp_sender_options():
    """Show UDP test sender options"""
    print("=" * 60)
    print("UDP TEST SENDER OPTIONS")
    print("=" * 60)
    print()
    
    code, stdout, stderr = run_command("python3 udp_test_sender.py --help")
    if code == 0:
        print(stdout)
    else:
        print("UDP test sender not available")
        print("Error:", stderr)

def demo_basic_udp_test():
    """Demonstrate basic UDP functionality"""
    print("=" * 60)
    print("BASIC UDP STREAMING TEST")
    print("=" * 60)
    print()
    
    print("Starting UDP receiver in JSON mode...")
    print("Command: python3 nmea_parser.py --udp 4001 --json")
    print()
    
    # Start receiver in background
    receiver_process = subprocess.Popen(
        ["python3", "nmea_parser.py", "--udp", "4001", "--json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(1)
    
    print("Sending test NMEA data...")
    print("Command: python3 udp_test_sender.py --repeat 2 --interval 0.3")
    print()
    
    # Send test data
    code, stdout, stderr = run_command("python3 udp_test_sender.py --repeat 2 --interval 0.3")
    
    # Give receiver time to process
    time.sleep(1)
    
    # Stop receiver
    receiver_process.terminate()
    
    # Get receiver output
    try:
        receiver_stdout, receiver_stderr = receiver_process.communicate(timeout=2)
        
        print("UDP Receiver Output:")
        print("-" * 30)
        if receiver_stdout:
            # Show first few JSON lines
            lines = receiver_stdout.strip().split('\n')
            for i, line in enumerate(lines[:3]):
                if line.strip():
                    print(f"Line {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
            if len(lines) > 3:
                print(f"... and {len(lines) - 3} more lines")
        else:
            print("No output received")
            
        if receiver_stderr:
            print("Errors:", receiver_stderr)
            
    except subprocess.TimeoutExpired:
        receiver_process.kill()
        print("Receiver process had to be killed")
    
    print()
    print("Sender Output:")
    print("-" * 30)
    if stdout:
        print(stdout)
    if stderr:
        print("Errors:", stderr)

def demo_udp_modes():
    """Show different UDP output modes"""
    print("=" * 60)
    print("UDP OUTPUT MODES DEMONSTRATION")
    print("=" * 60)
    print()
    
    modes = [
        ("Standard Mode", "--udp 4002"),
        ("Continuous Mode", "--udp 4003 --continuous"),
        ("JSON Mode", "--udp 4004 --json"),
        ("Verbose Mode", "--udp 4005 --continuous --verbose")
    ]
    
    for mode_name, mode_args in modes:
        print(f"{mode_name}:")
        print(f"  Command: python3 nmea_parser.py {mode_args}")
        print(f"  Use case: {get_mode_description(mode_name)}")
        print()

def get_mode_description(mode_name):
    """Get description for each mode"""
    descriptions = {
        "Standard Mode": "Basic UDP reception with summary on exit",
        "Continuous Mode": "Real-time display of received sentences",
        "JSON Mode": "Structured JSON output for integration",
        "Verbose Mode": "Detailed parsing information for debugging"
    }
    return descriptions.get(mode_name, "Unknown mode")

def demo_network_configurations():
    """Show network configuration examples"""
    print("=" * 60)
    print("NETWORK CONFIGURATION EXAMPLES")
    print("=" * 60)
    print()
    
    configs = [
        ("Local GPS Device", "--udp 4001 --udp-host 127.0.0.1", "GPS connected via USB/serial to UDP bridge"),
        ("Network GPS Server", "--udp 4001 --udp-host 0.0.0.0", "Listen on all network interfaces"),
        ("High-Rate Data", "--udp 4001 --udp-buffer 8192", "Large buffer for 10Hz+ GPS data"),
        ("AIS Receiver", "--udp 10110", "Standard AIS port for marine traffic"),
        ("Chart Plotter", "--udp 2000 --continuous", "Real-time navigation display")
    ]
    
    for name, command, description in configs:
        print(f"{name}:")
        print(f"  Command: python3 nmea_parser.py {command}")
        print(f"  Description: {description}")
        print()

def demo_production_examples():
    """Show production deployment examples"""
    print("=" * 60)
    print("PRODUCTION DEPLOYMENT EXAMPLES")
    print("=" * 60)
    print()
    
    examples = [
        ("Maritime Vessel Monitoring", 
         "python3 nmea_parser.py --udp 4001 --splunk --continuous",
         "Real-time vessel tracking with Splunk logging"),
        
        ("Fleet Management Hub",
         "python3 nmea_parser.py --udp 4001 --json | fleet_processor.py",
         "JSON stream processing for fleet management"),
        
        ("Research Data Collection",
         "python3 nmea_parser.py --udp 4001 --json >> /data/nmea_$(date +%Y%m%d).log",
         "Continuous data logging for research"),
        
        ("Maritime Safety System",
         "python3 nmea_parser.py --udp 10110 --splunk --verbose",
         "AIS monitoring with detailed logging")
    ]
    
    for name, command, description in examples:
        print(f"{name}:")
        print(f"  Command: {command}")
        print(f"  Use case: {description}")
        print()

def demo_troubleshooting():
    """Show troubleshooting commands"""
    print("=" * 60)
    print("TROUBLESHOOTING GUIDE")
    print("=" * 60)
    print()
    
    print("Common Issues and Solutions:")
    print()
    
    issues = [
        ("Port already in use", 
         "netstat -an | grep :4001",
         "Check if another process is using the port"),
        
        ("No data received",
         "python3 udp_test_sender.py --host YOUR_IP --port 4001",
         "Test connectivity with the included sender"),
        
        ("High packet loss",
         "python3 nmea_parser.py --udp 4001 --udp-buffer 16384",
         "Increase buffer size for high-rate data"),
        
        ("Parse errors",
         "python3 nmea_parser.py --udp 4001 --verbose",
         "Enable verbose mode to see parsing details"),
        
        ("Network connectivity",
         "sudo ufw allow 4001/udp",
         "Ensure firewall allows UDP traffic")
    ]
    
    for issue, command, solution in issues:
        print(f"Issue: {issue}")
        print(f"  Test: {command}")
        print(f"  Solution: {solution}")
        print()

def main():
    """Run all demonstrations"""
    print("NMEA Parser - UDP Streaming Demonstration")
    print("=" * 60)
    print()
    print("This demo shows the UDP streaming capabilities of the NMEA parser.")
    print("Perfect for real-time GPS, AIS, and marine navigation data processing.")
    print()
    
    demos = [
        ("UDP Help Information", demo_udp_help),
        ("UDP Test Sender Options", demo_udp_sender_options),
        ("Basic UDP Streaming Test", demo_basic_udp_test),
        ("UDP Output Modes", demo_udp_modes),
        ("Network Configurations", demo_network_configurations),
        ("Production Examples", demo_production_examples),
        ("Troubleshooting Guide", demo_troubleshooting)
    ]
    
    for title, demo_func in demos:
        try:
            demo_func()
            print("\n" + "=" * 60 + "\n")
        except Exception as e:
            print(f"Error in {title}: {e}")
            print("\n" + "=" * 60 + "\n")
    
    print("UDP STREAMING SUMMARY")
    print("=" * 60)
    print()
    print("Key Features:")
    print("✅ Real-time UDP data reception")
    print("✅ Multiple output formats (display, JSON, Splunk)")
    print("✅ Configurable network settings")
    print("✅ Production-ready error handling")
    print("✅ Built-in testing tools")
    print("✅ Comprehensive monitoring")
    print()
    print("Ready for:")
    print("🚢 Maritime vessel tracking")
    print("📡 AIS message processing") 
    print("🗺️  Chart plotter integration")
    print("📊 Fleet management systems")
    print("🔬 Research data collection")
    print("⚠️  Maritime safety systems")
    print()
    print("Next Steps:")
    print("1. Configure your GPS device to send UDP data")
    print("2. Start the parser: python3 nmea_parser.py --udp YOUR_PORT")
    print("3. Add --splunk for logging or --json for integration")
    print("4. Use --continuous for real-time monitoring")

if __name__ == "__main__":
    main()

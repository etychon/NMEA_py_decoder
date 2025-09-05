#!/usr/bin/env python3
"""
Health Check Script for NMEA Parser IOx Application
Used by IOx monitoring system to check application health
"""

import sys
import os
import json
import time
import socket
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add current directory to Python path
sys.path.insert(0, '/app')

def check_process_running():
    """Check if the main NMEA parser process is running"""
    try:
        # Check for the main process by looking for the PID file or process name
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'iox_entrypoint.py' in ' '.join(proc.info['cmdline'] or []):
                    return True, f"Process running with PID {proc.info['pid']}"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return False, "Main process not found"
        
    except ImportError:
        # Fallback method without psutil
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'iox_entrypoint.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                return True, f"Process running with PID(s): {', '.join(pids)}"
            else:
                return False, "Main process not found (pgrep)"
        except Exception as e:
            return False, f"Unable to check process: {e}"

def check_udp_port():
    """Check if UDP port is open and listening"""
    try:
        udp_port = int(os.getenv('NMEA_UDP_PORT', '4001'))
        
        # Try to bind to the port (if it fails, something is already using it)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('127.0.0.1', udp_port))
            sock.close()
            return False, f"UDP port {udp_port} is not in use"
        except OSError:
            # Port is in use (which is what we want)
            return True, f"UDP port {udp_port} is active"
            
    except Exception as e:
        return False, f"Error checking UDP port: {e}"

def check_log_files():
    """Check log files for recent activity"""
    try:
        log_file = Path('/app/logs/nmea_parser.log')
        
        if not log_file.exists():
            return False, "Log file not found"
            
        # Check if log file was modified recently (within last 5 minutes)
        mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        time_diff = datetime.now() - mod_time
        
        if time_diff > timedelta(minutes=5):
            return False, f"Log file not updated for {time_diff}"
            
        # Check log file size (should not be empty)
        file_size = log_file.stat().st_size
        if file_size == 0:
            return False, "Log file is empty"
            
        return True, f"Log file active, size: {file_size} bytes, last modified: {mod_time}"
        
    except Exception as e:
        return False, f"Error checking log files: {e}"

def check_data_activity():
    """Check for recent NMEA data activity"""
    try:
        stats_file = Path('/app/logs/stats.json')
        
        if not stats_file.exists():
            return True, "Stats file not found (may be normal for new deployment)"
            
        # Read stats file
        with open(stats_file, 'r') as f:
            stats = json.load(f)
            
        # Check if sentences are being processed
        sentences_processed = stats.get('sentences_processed', 0)
        last_position_time = stats.get('last_position', {}).get('timestamp')
        
        if sentences_processed == 0:
            return False, "No NMEA sentences processed"
            
        # Check if position data is recent (within last 10 minutes)
        if last_position_time:
            try:
                last_pos_dt = datetime.fromisoformat(last_position_time.replace('Z', '+00:00'))
                time_diff = datetime.now() - last_pos_dt.replace(tzinfo=None)
                
                if time_diff > timedelta(minutes=10):
                    return False, f"No position data for {time_diff}"
                    
            except Exception:
                pass  # Ignore datetime parsing errors
                
        return True, f"Data activity normal: {sentences_processed} sentences processed"
        
    except Exception as e:
        return False, f"Error checking data activity: {e}"

def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        
        # Check disk space for logs directory
        total, used, free = shutil.disk_usage('/app/logs')
        
        # Convert to MB
        free_mb = free / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        used_percent = (used / total) * 100
        
        # Alert if less than 10MB free or more than 90% used
        if free_mb < 10:
            return False, f"Low disk space: {free_mb:.1f}MB free"
        elif used_percent > 90:
            return False, f"Disk usage high: {used_percent:.1f}% used"
        else:
            return True, f"Disk space OK: {free_mb:.1f}MB free ({used_percent:.1f}% used)"
            
    except Exception as e:
        return False, f"Error checking disk space: {e}"

def check_memory_usage():
    """Check memory usage"""
    try:
        import psutil
        
        # Get system memory info
        memory = psutil.virtual_memory()
        
        # Check if memory usage is too high
        if memory.percent > 90:
            return False, f"High memory usage: {memory.percent:.1f}%"
        else:
            return True, f"Memory usage OK: {memory.percent:.1f}%"
            
    except ImportError:
        return True, "Memory check skipped (psutil not available)"
    except Exception as e:
        return False, f"Error checking memory: {e}"

def perform_health_check():
    """Perform comprehensive health check"""
    checks = [
        ("Process Status", check_process_running),
        ("UDP Port", check_udp_port),
        ("Log Files", check_log_files),
        ("Data Activity", check_data_activity),
        ("Disk Space", check_disk_space),
        ("Memory Usage", check_memory_usage),
    ]
    
    results = {}
    overall_healthy = True
    
    for check_name, check_func in checks:
        try:
            is_healthy, message = check_func()
            results[check_name] = {
                'healthy': is_healthy,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            if not is_healthy:
                overall_healthy = False
                
        except Exception as e:
            results[check_name] = {
                'healthy': False,
                'message': f"Check failed: {e}",
                'timestamp': datetime.now().isoformat()
            }
            overall_healthy = False
    
    return overall_healthy, results

def save_health_status(results):
    """Save health check results to file"""
    try:
        health_file = Path('/app/logs/health.json')
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': all(r['healthy'] for r in results.values()),
            'checks': results
        }
        
        with open(health_file, 'w') as f:
            json.dump(health_data, f, indent=2)
            
    except Exception as e:
        print(f"Failed to save health status: {e}")

def main():
    """Main health check function"""
    try:
        # Perform health check
        overall_healthy, results = perform_health_check()
        
        # Save results
        save_health_status(results)
        
        # Print summary for IOx monitoring
        if overall_healthy:
            print("HEALTHY: All checks passed")
            for check_name, result in results.items():
                if result['healthy']:
                    print(f"  ✓ {check_name}: {result['message']}")
            sys.exit(0)
        else:
            print("UNHEALTHY: One or more checks failed")
            for check_name, result in results.items():
                status = "✓" if result['healthy'] else "✗"
                print(f"  {status} {check_name}: {result['message']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"UNHEALTHY: Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

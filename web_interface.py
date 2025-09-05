#!/usr/bin/env python3
"""
Simple Web Interface for NMEA Parser IOx Application
Provides health monitoring and basic status information
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Add current directory to Python path
sys.path.insert(0, '/app')

class NMEAWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for NMEA parser web interface"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/':
                self._serve_main_page()
            elif path == '/health':
                self._serve_health_check()
            elif path == '/status':
                self._serve_status_json()
            elif path == '/logs':
                self._serve_logs()
            elif path == '/config':
                self._serve_config()
            elif path.startswith('/static/'):
                self._serve_static_file(path)
            else:
                self._serve_404()
                
        except Exception as e:
            self.logger.error(f"Error handling request {path}: {e}")
            self._serve_error(str(e))
    
    def _serve_main_page(self):
        """Serve the main dashboard page"""
        html = self._generate_dashboard_html()
        self._send_response(200, html, 'text/html')
    
    def _serve_health_check(self):
        """Serve health check endpoint"""
        try:
            # Read health status
            health_file = Path('/app/logs/health.json')
            if health_file.exists():
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
                    
                is_healthy = health_data.get('overall_healthy', False)
                status_code = 200 if is_healthy else 503
                
                response = {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'checks': health_data.get('checks', {})
                }
            else:
                response = {
                    'status': 'unknown',
                    'message': 'Health check data not available',
                    'timestamp': datetime.now().isoformat()
                }
                status_code = 503
                
            self._send_json_response(status_code, response)
            
        except Exception as e:
            self._send_json_response(500, {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _serve_status_json(self):
        """Serve application status as JSON"""
        try:
            status = self._get_application_status()
            self._send_json_response(200, status)
        except Exception as e:
            self._send_json_response(500, {'error': str(e)})
    
    def _serve_logs(self):
        """Serve recent log entries"""
        try:
            log_file = Path('/app/logs/nmea_parser.log')
            if log_file.exists():
                # Get last 100 lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                logs = {
                    'timestamp': datetime.now().isoformat(),
                    'total_lines': len(lines),
                    'recent_lines': [line.strip() for line in recent_lines],
                    'file_size': log_file.stat().st_size
                }
            else:
                logs = {
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Log file not found',
                    'recent_lines': []
                }
                
            self._send_json_response(200, logs)
            
        except Exception as e:
            self._send_json_response(500, {'error': str(e)})
    
    def _serve_config(self):
        """Serve current configuration"""
        try:
            config = {
                'timestamp': datetime.now().isoformat(),
                'environment_variables': {
                    k: v for k, v in os.environ.items() 
                    if k.startswith(('NMEA_', 'SPLUNK_', 'PYTHON'))
                },
                'application_info': {
                    'name': 'NMEA Parser IOx',
                    'version': '1.0.0',
                    'mode': os.getenv('NMEA_MODE', 'udp'),
                    'udp_port': os.getenv('NMEA_UDP_PORT', '4001'),
                    'track_position': os.getenv('NMEA_TRACK_POSITION', 'true')
                }
            }
            self._send_json_response(200, config)
            
        except Exception as e:
            self._send_json_response(500, {'error': str(e)})
    
    def _serve_404(self):
        """Serve 404 page"""
        html = """
        <html>
        <head><title>404 Not Found</title></head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The requested page was not found.</p>
            <a href="/">Return to Dashboard</a>
        </body>
        </html>
        """
        self._send_response(404, html, 'text/html')
    
    def _serve_error(self, error_msg):
        """Serve error page"""
        html = f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>An error occurred: {error_msg}</p>
            <a href="/">Return to Dashboard</a>
        </body>
        </html>
        """
        self._send_response(500, html, 'text/html')
    
    def _get_application_status(self):
        """Get comprehensive application status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'application': {
                'name': 'NMEA Parser IOx',
                'version': '1.0.0',
                'uptime': self._get_uptime(),
                'mode': os.getenv('NMEA_MODE', 'udp')
            },
            'configuration': {
                'udp_port': os.getenv('NMEA_UDP_PORT', '4001'),
                'udp_host': os.getenv('NMEA_UDP_HOST', '0.0.0.0'),
                'track_position': os.getenv('NMEA_TRACK_POSITION', 'true'),
                'continuous': os.getenv('NMEA_CONTINUOUS', 'true'),
                'log_level': os.getenv('NMEA_LOG_LEVEL', 'INFO')
            },
            'health': self._get_health_summary(),
            'statistics': self._get_statistics(),
            'recent_activity': self._get_recent_activity()
        }
        
        return status
    
    def _get_uptime(self):
        """Calculate application uptime"""
        try:
            stats_file = Path('/app/logs/stats.json')
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    start_time = stats.get('start_time')
                    if start_time:
                        uptime_seconds = time.time() - start_time
                        return f"{uptime_seconds:.0f} seconds"
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_health_summary(self):
        """Get health check summary"""
        try:
            health_file = Path('/app/logs/health.json')
            if health_file.exists():
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
                    return {
                        'overall_healthy': health_data.get('overall_healthy', False),
                        'last_check': health_data.get('timestamp'),
                        'failed_checks': [
                            name for name, check in health_data.get('checks', {}).items()
                            if not check.get('healthy', True)
                        ]
                    }
            return {'status': 'No health data available'}
        except:
            return {'status': 'Error reading health data'}
    
    def _get_statistics(self):
        """Get application statistics"""
        try:
            stats_file = Path('/app/logs/stats.json')
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    return json.load(f)
            return {'message': 'No statistics available'}
        except:
            return {'error': 'Error reading statistics'}
    
    def _get_recent_activity(self):
        """Get recent activity summary"""
        try:
            log_file = Path('/app/logs/nmea_parser.log')
            if log_file.exists():
                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                file_size = log_file.stat().st_size
                
                return {
                    'last_log_update': mod_time.isoformat(),
                    'log_file_size': file_size,
                    'minutes_since_update': (datetime.now() - mod_time).total_seconds() / 60
                }
            return {'message': 'No log file found'}
        except:
            return {'error': 'Error reading log file'}
    
    def _generate_dashboard_html(self):
        """Generate the main dashboard HTML"""
        status = self._get_application_status()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NMEA Parser IOx Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    background: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .card {{
                    background: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .status-good {{ color: #27ae60; }}
                .status-bad {{ color: #e74c3c; }}
                .status-warning {{ color: #f39c12; }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .refresh-btn {{
                    background: #3498db;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 10px 0;
                }}
                .refresh-btn:hover {{
                    background: #2980b9;
                }}
                pre {{
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 3px;
                    overflow-x: auto;
                    font-size: 12px;
                }}
                .api-links {{
                    margin-top: 20px;
                }}
                .api-links a {{
                    display: inline-block;
                    margin-right: 10px;
                    padding: 5px 10px;
                    background: #95a5a6;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                    font-size: 12px;
                }}
            </style>
            <script>
                function refreshPage() {{
                    window.location.reload();
                }}
                
                function autoRefresh() {{
                    setTimeout(refreshPage, 30000); // Refresh every 30 seconds
                }}
                
                window.onload = autoRefresh;
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛰️ NMEA Parser IOx Dashboard</h1>
                    <p>Real-time GPS/GNSS Data Processing on Cisco IOx</p>
                    <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh</button>
                    <span style="float: right; font-size: 14px;">
                        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </span>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>📊 Application Status</h3>
                        <p><strong>Name:</strong> {status['application']['name']}</p>
                        <p><strong>Version:</strong> {status['application']['version']}</p>
                        <p><strong>Mode:</strong> {status['application']['mode']}</p>
                        <p><strong>Uptime:</strong> {status['application']['uptime']}</p>
                        <p><strong>Health:</strong> 
                            <span class="{'status-good' if status['health'].get('overall_healthy') else 'status-bad'}">
                                {'✅ Healthy' if status['health'].get('overall_healthy') else '❌ Unhealthy'}
                            </span>
                        </p>
                    </div>
                    
                    <div class="card">
                        <h3>⚙️ Configuration</h3>
                        <p><strong>UDP Port:</strong> {status['configuration']['udp_port']}</p>
                        <p><strong>UDP Host:</strong> {status['configuration']['udp_host']}</p>
                        <p><strong>Position Tracking:</strong> {status['configuration']['track_position']}</p>
                        <p><strong>Continuous Mode:</strong> {status['configuration']['continuous']}</p>
                        <p><strong>Log Level:</strong> {status['configuration']['log_level']}</p>
                    </div>
                    
                    <div class="card">
                        <h3>📈 Statistics</h3>
                        <pre>{json.dumps(status.get('statistics', {}), indent=2)}</pre>
                    </div>
                    
                    <div class="card">
                        <h3>🏥 Health Checks</h3>
                        <pre>{json.dumps(status.get('health', {}), indent=2)}</pre>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🔗 API Endpoints</h3>
                    <div class="api-links">
                        <a href="/health" target="_blank">Health Check</a>
                        <a href="/status" target="_blank">Status JSON</a>
                        <a href="/logs" target="_blank">Recent Logs</a>
                        <a href="/config" target="_blank">Configuration</a>
                    </div>
                    <p><small>Auto-refresh enabled (30 seconds)</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_response(self, status_code, content, content_type):
        """Send HTTP response"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length', str(len(content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        content = json.dumps(data, indent=2)
        self._send_response(status_code, content, 'application/json')
    
    def log_message(self, format, *args):
        """Override to use proper logging"""
        logging.info(f"{self.address_string()} - {format % args}")

class NMEAWebServer:
    """Web server for NMEA parser monitoring"""
    
    def __init__(self, port=8080, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.server = None
        self.thread = None
        self.running = False
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the web server"""
        try:
            self.server = HTTPServer((self.host, self.port), NMEAWebHandler)
            self.running = True
            
            self.logger.info(f"Starting web server on {self.host}:{self.port}")
            
            # Start server in a separate thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            self.logger.info(f"Web dashboard available at http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            return False
    
    def stop(self):
        """Stop the web server"""
        if self.server:
            self.logger.info("Stopping web server...")
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            self.logger.info("Web server stopped")

def main():
    """Main function for standalone web server"""
    port = int(os.getenv('NMEA_HEALTH_PORT', '8080'))
    host = os.getenv('NMEA_WEB_HOST', '0.0.0.0')
    
    web_server = NMEAWebServer(port, host)
    
    try:
        if web_server.start():
            print(f"NMEA Parser Web Dashboard running on http://{host}:{port}")
            print("Press Ctrl+C to stop")
            
            # Keep the server running
            while web_server.running:
                time.sleep(1)
        else:
            print("Failed to start web server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutting down web server...")
    finally:
        web_server.stop()

if __name__ == "__main__":
    main()

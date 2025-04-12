import os
import sys
import platform
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if platform.system() == 'Windows':
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    
    if getattr(sys, 'frozen', False):
        os.environ['EVENTLET_THREADPOOL_SIZE'] = '30'

using_fallback_mode = False

try:
    import eventlet
    if platform.system() == 'Windows':
        eventlet.monkey_patch(os=False, thread=False, time=False)
    else:
        eventlet.monkey_patch()
except ImportError as e:
    logging.warning(f"Cannot import eventlet: {e}")
    logging.info("Falling back to pure threading mode")
    using_fallback_mode = True
except Exception as e:
    logging.warning(f"Error initializing eventlet: {e}")
    if platform.system() == 'Windows' and getattr(sys, 'frozen', False):
        logging.info("This is likely due to PyInstaller packaging issues with eventlet.")
        logging.info("Falling back to pure threading mode")
    using_fallback_mode = True

import time
import threading
from flask import Flask, send_from_directory, current_app

if not using_fallback_mode:
    try:
        from flask_socketio import SocketIO, Namespace
    except ImportError:
        logging.warning("Cannot import flask_socketio with eventlet support")
        using_fallback_mode = True

if using_fallback_mode:
    try:
        from flask_socketio import SocketIO, Namespace
    except ImportError as e:
        logging.critical(f"Cannot import flask_socketio: {e}")
        logging.critical("Application cannot run without SocketIO support")
        sys.exit(1)

from data_provider import DataProvider
from interface import interface_bp
from overlays import overlays_bp

def resource_path(relative_path):
    """Get absolute path to resource, working for both development and PyInstaller environments.
    
    Args:
        relative_path: The relative path to the resource
        
    Returns:
        str: The absolute path to the resource
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class TelemetryNamespace(Namespace):
    """Socket.IO namespace for telemetry-related communications."""
    
    def on_connect(self):
        """Handle client connection event."""
        logging.info("Client connected to telemetry namespace")

    def on_disconnect(self):
        """Handle client disconnection event."""
        logging.info("Client disconnected from telemetry namespace")

class LapPaceNamespace(Namespace):
    """Socket.IO namespace for lap pace-related communications."""
    
    def on_connect(self):
        """Handle client connection event."""
        logging.info("Client connected to lap pace namespace")

    def on_disconnect(self):
        """Handle client disconnection event."""
        logging.info("Client disconnected from lap pace namespace")

class WebInterface:
    """Manages the web interface for displaying telemetry overlays.
    
    This class handles web server initialization, socket.io communications,
    and real-time data transmission to overlays.
    """

    def __init__(self, selected_overlays=None):
        """Initialize the web interface with selected overlays.
        
        Args:
            selected_overlays: List of overlay identifiers to activate
        """
        self.selected_overlays = selected_overlays or []
        self.app = Flask(__name__)
        self.app.register_blueprint(interface_bp, url_prefix='/')
        self.app.register_blueprint(overlays_bp, url_prefix='/overlay')
        
        socketio_kwargs = self._configure_socketio()
        self.socketio = SocketIO(self.app, **socketio_kwargs)
        self.data_provider = DataProvider()
        
        # Store app context for thread access
        self.app_context = self.app.app_context()
        
        self._setup_routes()
        self.telemetry_thread = None
        self.shutdown_flag = False
        self._register_namespaces()
        self._start_telemetry_thread()

    def _configure_socketio(self):
        """Configure SocketIO settings based on environment.
        
        Returns:
            dict: Configuration parameters for SocketIO
        """
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            logging.info("Using threading mode for SocketIO")
            return {
                'async_mode': 'threading',
                'ping_timeout': 60,
                'ping_interval': 25,
                'logger': True,
                'engineio_logger': True,
                'cors_allowed_origins': '*'  # Allow all origins for easier testing
            }
        else:
            logging.info("Using eventlet mode for SocketIO")
            return {
                'async_mode': 'eventlet',
                'cors_allowed_origins': '*'  # Allow all origins for easier testing
            }

    def _register_namespaces(self):
        """Register SocketIO namespaces for all selected overlays."""
        for overlay in self.selected_overlays:
            namespace_class = LapPaceNamespace if overlay == 'lap_pace' else TelemetryNamespace
            self.socketio.on_namespace(namespace_class(f'/{overlay}'))

    def _setup_routes(self):
        """Set up additional routes for serving common static files."""
        @self.app.route('/common/js/<path:filename>')
        def serve_common_js(filename):
            common_js_folder = resource_path(os.path.join('common', 'js'))
            return send_from_directory(common_js_folder, filename)

    def _start_telemetry_thread(self):
        """Start a background thread to emit telemetry data."""
        def telemetry_thread():
            # Push an application context for the thread
            with self.app_context:
                while not self.shutdown_flag:
                    try:
                        if self.data_provider.is_connected:
                            self._process_telemetry_data()
                    except Exception as e:
                        logging.error(f"Unexpected error in telemetry thread: {e}")
                    
                    # Use a small sleep time to reduce CPU usage
                    time.sleep(0.01)

        self.telemetry_thread = threading.Thread(target=telemetry_thread)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()
    
    def _process_telemetry_data(self):
        """Process and emit telemetry data to connected clients."""
        try:
            data = self.data_provider.get_telemetry_data()
            if data:
                self._sanitize_and_emit_telemetry(data)
            
            self._process_lap_times()
        except Exception as e:
            logging.error(f"Error in telemetry processing: {e}")
    
    def _sanitize_and_emit_telemetry(self, data):
        """Sanitize telemetry data and emit to clients.
        
        Args:
            data: Raw telemetry data dictionary
        """
        for key, value in data.items():
            if key == 'gear':
                data[key] = int(value) if value is not None else 0
            elif value is None:
                data[key] = 0.0
            else:
                try:
                    data[key] = float(value)
                except (TypeError, ValueError):
                    data[key] = 0.0
        
        self.socketio.emit('telemetry_update', data, namespace='/input_telemetry')
    
    def _process_lap_times(self):
        """Process and emit lap time data."""
        try:
            lap_times = self.data_provider.get_lap_times()
            if lap_times and lap_times:
                self.socketio.emit('lap_time_update', {'lap_time': lap_times[-1]}, namespace='/lap_pace')
        except Exception as e:
            logging.error(f"Error getting lap times: {e}")

    def run(self, host='127.0.0.1', port=8081):
        """Run the Flask web server application.
        
        Args:
            host: Host address to bind the server to
            port: Port number to listen on
        """
        self.data_provider.connect()
        
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            self._run_in_threading_mode(host, port)
        else:
            self._run_in_eventlet_mode(host, port)
    
    def _run_in_threading_mode(self, host, port):
        """Run server using threading mode.
        
        Args:
            host: Host address
            port: Port number
        """
        try:
            logging.info("Starting SocketIO server with threading mode...")
            self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        except TypeError as e:
            logging.error(f"Error with SocketIO run parameters: {e}")
            try:
                self.socketio.run(self.app, host=host, port=port, allow_unsafe_werkzeug=True)
            except Exception as e:
                logging.critical(f"Critical error starting SocketIO server: {e}")
                sys.exit(1)
        except Exception as e:
            logging.critical(f"Error starting SocketIO server: {e}")
            sys.exit(1)
    
    def _run_in_eventlet_mode(self, host, port):
        """Run server using eventlet mode.
        
        Args:
            host: Host address
            port: Port number
        """
        try:
            self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)
        except Exception as e:
            logging.warning(f"Error in eventlet mode, falling back to threading: {e}")
            self.socketio = SocketIO(self.app, async_mode='threading', cors_allowed_origins='*')
            self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        
    def shutdown(self):
        """Shutdown the web interface properly, closing all connections and threads."""
        logging.info("Shutting down web interface...")
        
        self.shutdown_flag = True
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            try:
                self.telemetry_thread.join(timeout=2)
            except Exception as e:
                logging.error(f"Error joining telemetry thread: {e}")
            
        if self.data_provider:
            self.data_provider.disconnect()
            
        try:
            self.socketio.stop()
        except Exception as e:
            logging.error(f"Error stopping SocketIO: {e}")
        
        logging.info("Web interface shutdown complete") 
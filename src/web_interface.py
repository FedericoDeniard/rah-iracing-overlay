import os
import sys
import platform

# Flag to track if we're using the fallback threading mode
using_fallback_mode = False

# Windows-specific configuration for eventlet
if platform.system() == 'Windows':
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    # Remove specific hub selection to let eventlet auto-detect the best available hub
    # os.environ['EVENTLET_HUB'] = 'poll'  
    
    # For PyInstaller builds
    if getattr(sys, 'frozen', False):
        # Force threading mode when inside PyInstaller bundle
        os.environ['EVENTLET_THREADPOOL_SIZE'] = '30'

# Import eventlet with more error handling
try:
    import eventlet
    # Use a more cautious monkey patching approach
    if platform.system() == 'Windows':
        # On Windows, be more selective with monkey patching
        eventlet.monkey_patch(os=False, thread=False, time=False)
    else:
        eventlet.monkey_patch()
except ImportError as e:
    print(f"WARNING: Cannot import eventlet: {e}")
    print("Falling back to pure threading mode")
    using_fallback_mode = True
except Exception as e:
    print(f"WARNING: Error initializing eventlet: {e}")
    if platform.system() == 'Windows' and getattr(sys, 'frozen', False):
        print("This is likely due to PyInstaller packaging issues with eventlet.")
        print("Falling back to pure threading mode")
    using_fallback_mode = True

# Standard library imports
from flask import Flask, send_from_directory
import time
import threading
import multiprocessing

# Conditional Flask-SocketIO imports
if not using_fallback_mode:
    try:
        from flask_socketio import SocketIO, Namespace
    except ImportError:
        print("WARNING: Cannot import flask_socketio with eventlet support")
        using_fallback_mode = True

# If we're using fallback mode, import with threading mode explicitly
if using_fallback_mode:
    try:
        from flask_socketio import SocketIO, Namespace
    except ImportError as e:
        print(f"CRITICAL ERROR: Cannot import flask_socketio: {e}")
        print("Application cannot run without SocketIO support")
        sys.exit(1)

# Application-specific imports
from data_provider import DataProvider
from interface import interface_bp
from overlays import overlays_bp

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class TelemetryNamespace(Namespace):
    def on_connect(self):
        print("Client connected to telemetry namespace")

    def on_disconnect(self):
        print("Client disconnected from telemetry namespace")

class LapPaceNamespace(Namespace):
    def on_connect(self):
        print("Client connected to lap pace namespace")

    def on_disconnect(self):
        print("Client disconnected from lap pace namespace")

class WebInterface:
    """
    Manages the web interface for displaying telemetry overlays.
    """

    def __init__(self, selected_overlays=None):
        self.selected_overlays = selected_overlays or []
        self.app = Flask(__name__)
        self.app.register_blueprint(interface_bp, url_prefix='/')
        self.app.register_blueprint(overlays_bp, url_prefix='/overlay')
        
        # SocketIO configuration
        socketio_kwargs = {}
        
        # Always use threading mode if we're in fallback mode or on Windows executable
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            socketio_kwargs = {
                'async_mode': 'threading',
                'ping_timeout': 60,
                'ping_interval': 25,
                'logger': True,
                'engineio_logger': True
            }
            print("Using threading mode for SocketIO")
        else:
            socketio_kwargs = {'async_mode': 'eventlet'}
            print(f"Using eventlet mode for SocketIO")
            
        self.socketio = SocketIO(self.app, **socketio_kwargs)
        self.data_provider = DataProvider()
        self._setup_routes()
        self.telemetry_thread = None
        self.shutdown_flag = False
        self._start_telemetry_thread()
        for overlay in self.selected_overlays:
            if overlay == 'lap_pace':
                self.socketio.on_namespace(LapPaceNamespace(f'/{overlay}'))
            else:
                self.socketio.on_namespace(TelemetryNamespace(f'/{overlay}'))

    def _setup_routes(self):
        """
        Set up additional routes for serving common static files.
        """
        @self.app.route('/common/js/<path:filename>')
        def serve_common_js(filename):
            common_js_folder = resource_path(os.path.join('common', 'js'))
            return send_from_directory(common_js_folder, filename)

    def _start_telemetry_thread(self):
        """
        Start a background thread to emit telemetry data.
        """
        def telemetry_thread():
            while not self.shutdown_flag:
                if self.data_provider.is_connected:
                    data = self.data_provider.get_telemetry_data()
                    if data:
                        self.socketio.emit('telemetry_update', data, namespace='/input_telemetry')
                    lap_times = self.data_provider.get_lap_times()
                    if lap_times:
                        self.socketio.emit('lap_time_update', {'lap_time': lap_times[-1]}, namespace='/lap_pace')
                time.sleep(0.016)

        self.telemetry_thread = threading.Thread(target=telemetry_thread)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()

    def run(self, host='127.0.0.1', port=8081):
        """
        Run the Flask application.
        """
        self.data_provider.connect()
        
        # Always use basic parameters for threading mode
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            try:
                print("Starting SocketIO server with threading mode...")
                self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)
            except TypeError as e:
                print(f"Error with SocketIO run parameters: {e}")
                # Fall back if the above fails
                try:
                    self.socketio.run(self.app, host=host, port=port)
                except Exception as e:
                    print(f"Critical error starting SocketIO server: {e}")
                    sys.exit(1)
            except Exception as e:
                print(f"Error starting SocketIO server: {e}")
                sys.exit(1)
        else:
            # For development with eventlet
            try:
                self.socketio.run(self.app, host=host, port=port)
            except Exception as e:
                print(f"Error in eventlet mode, falling back to threading: {e}")
                # Fall back to threading mode
                self.socketio = SocketIO(self.app, async_mode='threading')
                self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)
        
    def shutdown(self):
        """
        Shutdown the web interface properly.
        """
        print("Shutting down web interface...")
        
        # Stop the telemetry thread
        self.shutdown_flag = True
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            try:
                self.telemetry_thread.join(timeout=2)
            except:
                pass
            
        # Disconnect from iRacing
        if self.data_provider:
            self.data_provider.disconnect()
            
        # Stop the Socket.IO server
        try:
            self.socketio.stop()
        except Exception as e:
            print(f"Error stopping SocketIO: {e}")
        
        print("Web interface shutdown complete") 
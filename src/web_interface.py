import os
import sys
import platform
import time
import threading
import logging
from typing import List, Dict, Optional, Any, Union

using_fallback_mode = False

if platform.system() == 'Windows':
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    
    if getattr(sys, 'frozen', False):
        os.environ['EVENTLET_THREADPOOL_SIZE'] = '30'

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

from flask import Flask, send_from_directory

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


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    Args:
        relative_path: The relative path to the resource
        
    Returns:
        The absolute path to the resource
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


class TelemetryNamespace(Namespace):
    """Socket.IO namespace for telemetry data."""
    
    def on_connect(self) -> None:
        """Handle client connection to telemetry namespace."""
        logging.info("Client connected to telemetry namespace")

    def on_disconnect(self) -> None:
        """Handle client disconnection from telemetry namespace."""
        logging.info("Client disconnected from telemetry namespace")


class LapPaceNamespace(Namespace):
    """Socket.IO namespace for lap pace data."""
    
    def on_connect(self) -> None:
        """Handle client connection to lap pace namespace."""
        logging.info("Client connected to lap pace namespace")

    def on_disconnect(self) -> None:
        """Handle client disconnection from lap pace namespace."""
        logging.info("Client disconnected from lap pace namespace")


class WebInterface:
    """
    Manages the web interface for displaying iRacing telemetry overlays.
    
    This class handles the web server, WebSocket connections, and data 
    transmission between the iRacing sim and the overlay interface.
    """

    def __init__(self, selected_overlays: Optional[List[str]] = None) -> None:
        """
        Initialize the web interface.
        
        Args:
            selected_overlays: List of overlay names to enable
        """
        self.selected_overlays = selected_overlays or []
        self.app = Flask(__name__)
        self.app.register_blueprint(interface_bp, url_prefix='/')
        self.app.register_blueprint(overlays_bp, url_prefix='/overlay')
        
        self._configure_socketio()
        self.data_provider = DataProvider()
        self._setup_routes()
        self.telemetry_thread = None
        self.shutdown_flag = False
        self._start_telemetry_thread()
        self._setup_namespaces()

    def _configure_socketio(self) -> None:
        """Configure the Socket.IO server with appropriate settings."""
        socketio_kwargs = {}
        
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            socketio_kwargs = {
                'async_mode': 'threading',
                'ping_timeout': 60,
                'ping_interval': 25,
                'logger': True,
                'engineio_logger': True
            }
            logging.info("Using threading mode for SocketIO")
        else:
            socketio_kwargs = {'async_mode': 'eventlet'}
            logging.info("Using eventlet mode for SocketIO")
            
        self.socketio = SocketIO(self.app, **socketio_kwargs)

    def _setup_namespaces(self) -> None:
        """Register Socket.IO namespaces for each enabled overlay."""
        for overlay in self.selected_overlays:
            if overlay == 'lap_pace':
                self.socketio.on_namespace(LapPaceNamespace(f'/{overlay}'))
            else:
                self.socketio.on_namespace(TelemetryNamespace(f'/{overlay}'))

    def _setup_routes(self) -> None:
        """
        Set up additional routes for serving common static files.
        """
        @self.app.route('/common/js/<path:filename>')
        def serve_common_js(filename: str):
            common_js_folder = resource_path(os.path.join('common', 'js'))
            return send_from_directory(common_js_folder, filename)

    def _start_telemetry_thread(self) -> None:
        """
        Start a background thread to emit telemetry data.
        """
        def telemetry_thread() -> None:
            """
            Thread function that processes and emits telemetry data.
            """
            while not self.shutdown_flag:
                try:
                    if self.data_provider.is_connected:
                        self._process_telemetry_data()
                except Exception as e:
                    logging.error(f"Unexpected error in telemetry thread: {e}")
                    
                time.sleep(0.016)  # 60 FPS target

        self.telemetry_thread = threading.Thread(target=telemetry_thread)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()
        
    def _process_telemetry_data(self) -> None:
        """Process and emit telemetry and lap time data."""
        try:
            data = self.data_provider.get_telemetry_data()
            if data:
                self._normalize_and_emit_telemetry(data)
                
            self._process_lap_times()
        except Exception as e:
            logging.error(f"Error in telemetry processing: {e}")
            
    def _normalize_and_emit_telemetry(self, data: Dict[str, Any]) -> None:
        """
        Ensure all telemetry values are of correct type and emit the data.
        
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
        
    def _process_lap_times(self) -> None:
        """Process and emit lap time data."""
        try:
            lap_times = self.data_provider.get_lap_times()
            if lap_times and lap_times:
                self.socketio.emit('lap_time_update', {'lap_time': lap_times[-1]}, namespace='/lap_pace')
        except Exception as e:
            logging.error(f"Error getting lap times: {e}")

    def run(self, host: str = '127.0.0.1', port: int = 8081) -> None:
        """
        Run the Flask application.
        
        Args:
            host: The hostname to listen on
            port: The port of the webserver
        """
        self.data_provider.connect()
        
        if using_fallback_mode or (platform.system() == 'Windows' and getattr(sys, 'frozen', False)):
            self._run_with_threading(host, port)
        else:
            self._run_with_eventlet(host, port)
            
    def _run_with_threading(self, host: str, port: int) -> None:
        """
        Run the server using threading mode.
        
        Args:
            host: The hostname to listen on
            port: The port of the webserver
        """
        try:
            logging.info("Starting SocketIO server with threading mode...")
            self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)
        except TypeError as e:
            logging.error(f"Error with SocketIO run parameters: {e}")
            try:
                self.socketio.run(self.app, host=host, port=port)
            except Exception as e:
                logging.critical(f"Critical error starting SocketIO server: {e}")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Error starting SocketIO server: {e}")
            sys.exit(1)
            
    def _run_with_eventlet(self, host: str, port: int) -> None:
        """
        Run the server using eventlet mode.
        
        Args:
            host: The hostname to listen on
            port: The port of the webserver
        """
        try:
            self.socketio.run(self.app, host=host, port=port)
        except Exception as e:
            logging.warning(f"Error in eventlet mode, falling back to threading: {e}")
            self.socketio = SocketIO(self.app, async_mode='threading')
            self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False)
        
    def shutdown(self) -> None:
        """
        Shutdown the web interface properly.
        """
        logging.info("Shutting down web interface...")
        
        self.shutdown_flag = True
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            try:
                self.telemetry_thread.join(timeout=2)
            except Exception:
                pass
            
        if self.data_provider:
            self.data_provider.disconnect()
            
        try:
            self.socketio.stop()
        except Exception as e:
            logging.error(f"Error stopping SocketIO: {e}")
        
        logging.info("Web interface shutdown complete") 
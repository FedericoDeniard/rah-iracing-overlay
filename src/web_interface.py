import eventlet
eventlet.monkey_patch()

from flask import Flask, send_from_directory
from flask_socketio import SocketIO, Namespace
from data_provider import DataProvider
from interface import interface_bp
from overlays import overlays_bp
import os
import time
from threading import Thread

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
        self.socketio = SocketIO(self.app, async_mode='eventlet')
        self.data_provider = DataProvider()
        self._setup_routes()
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
            common_js_folder = os.path.join(os.path.dirname(__file__), 'common', 'js')
            return send_from_directory(common_js_folder, filename)

    def _start_telemetry_thread(self):
        """
        Start a background thread to emit telemetry data.
        """
        def telemetry_thread():
            while True:
                if self.data_provider.is_connected:
                    data = self.data_provider.get_telemetry_data()
                    if data:
                        self.socketio.emit('telemetry_update', data, namespace='/input_telemetry')
                    lap_times = self.data_provider.get_lap_times()
                    if lap_times:
                        self.socketio.emit('lap_time_update', {'lap_time': lap_times[-1]}, namespace='/lap_pace')
                time.sleep(0.016)

        thread = Thread(target=telemetry_thread)
        thread.daemon = True
        thread.start()

    def run(self, host='127.0.0.1', port=8081):
        """
        Run the Flask application.
        """
        self.data_provider.connect()
        self.socketio.run(self.app, host=host, port=port) 
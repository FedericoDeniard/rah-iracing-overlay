import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, Namespace
from telemetry.data_provider import TelemetryDataProvider
import os
import sys
import time
from threading import Thread


def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TelemetryNamespace(Namespace):
    def on_connect(self):
        print("Client connected to telemetry namespace")

    def on_disconnect(self):
        print("Client disconnected from telemetry namespace")

class TelemetryWebInterface:
    """
    Manages the web interface for displaying telemetry overlays.
    """

    def __init__(self):
        template_folder = resource_path('overlays')
        self.app = Flask(__name__, template_folder=template_folder)
        self.socketio = SocketIO(self.app, async_mode='eventlet')
        self.data_provider = TelemetryDataProvider()
        self._setup_routes()
        self._start_telemetry_thread()
        self.socketio.on_namespace(TelemetryNamespace('/input_telemetry'))

    def _setup_routes(self):
        """
        Set up Flask routes for serving overlays.
        """
        @self.app.route('/overlay/<overlay_name>')
        def serve_overlay(overlay_name):
            overlay_path = os.path.join(self.app.template_folder, overlay_name)
            html_file_path = os.path.join(overlay_path, f'{overlay_name}.html')
            print(f"Looking for overlay at: {html_file_path}")  # Debug statement
            if os.path.exists(html_file_path):
                return render_template(f'{overlay_name}/{overlay_name}.html')
            else:
                return "Overlay not found", 404

        @self.app.route('/overlay/<overlay_name>/static/<path:filename>')
        def serve_static(overlay_name, filename):
            static_folder = os.path.join(self.app.template_folder, overlay_name, 'static')
            return send_from_directory(static_folder, filename)

        @self.app.route('/common/js/<path:filename>')
        def serve_common_js(filename):
            common_js_folder = resource_path('common/js')
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
                time.sleep(0.016)

        thread = Thread(target=telemetry_thread)
        thread.daemon = True
        thread.start()

    def run(self, host='127.0.0.1', port=8080):
        """
        Run the Flask application.
        """
        self.data_provider.connect()
        self.socketio.run(self.app, host=host, port=port) 
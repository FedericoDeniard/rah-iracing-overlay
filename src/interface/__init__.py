from flask import Blueprint, render_template, send_from_directory, jsonify, request
import os
import multiprocessing
from overlay_window import OverlayWindow
import json

interface_bp = Blueprint(
    'interface', __name__,
    template_folder='.',
    static_folder=None
)

opened_overlays = {}

@interface_bp.route('/')
def index():
    return render_template('index.html')

@interface_bp.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(interface_bp.root_path, 'static'), filename)

@interface_bp.route('/images/<filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(interface_bp.root_path, 'static', 'images'), filename)

@interface_bp.route('/get_overlays')
def get_overlays():
    overlays_dir = os.path.join(os.path.dirname(__file__), '..', 'overlays')
    overlays = []
    for name in os.listdir(overlays_dir):
        overlay_path = os.path.join(overlays_dir, name)
        properties_path = os.path.join(overlay_path, 'properties.json')
        if os.path.isdir(overlay_path) and os.path.exists(properties_path):
            with open(properties_path, 'r') as properties_file:
                properties = json.load(properties_file)
                display_name = properties.get('display_name', name)
                overlays.append({
                    'display_name': display_name,
                    'url': f"http://127.0.0.1:8081/overlay/{name}"
                })
    return jsonify(overlays)

@interface_bp.route('/launch', methods=['POST'])
def launch_overlay():
    data = request.get_json()
    overlay_name = data.get('overlay')
    if overlay_name:
        if overlay_name in opened_overlays and opened_overlays[overlay_name].is_alive():
            return jsonify({'status': 'success', 'message': f'Overlay {overlay_name} is already running.'}), 200

        overlay_url = f"http://127.0.0.1:8081/overlay/{overlay_name}"
        properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', overlay_name, 'properties.json')
        
        if os.path.exists(properties_path):
            with open(properties_path, 'r') as properties_file:
                properties = json.load(properties_file)
                resolution = properties.get('resolution', {'width': 800, 'height': 600})
        else:
            resolution = {'width': 800, 'height': 600} 

        process = multiprocessing.Process(target=launch_overlay_window, args=(overlay_url, resolution))
        process.start()
        opened_overlays[overlay_name] = process
        return jsonify({'status': 'success', 'message': f'Overlay {overlay_name} launched.'}), 200
    return jsonify({'status': 'error', 'message': 'Overlay name not provided.'}), 400

def launch_overlay_window(url, resolution):
    """
    Launch the overlay window in a separate process with the specified resolution.
    """
    overlay_window = OverlayWindow(url, width=resolution['width'], height=resolution['height'])
    overlay_window.create_overlay_window()
from flask import Blueprint, render_template, send_from_directory, jsonify, request
import os
import multiprocessing
from overlay_window import OverlayWindow
import json
import logging
import sys

interface_bp = Blueprint(
    'interface', __name__,
    template_folder='.',
    static_folder=None
)

# Shared dictionary to track opened overlays across processes
opened_overlays = {}

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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
                description = properties.get('description', 'No description available.')
                overlays.append({
                    'display_name': display_name,
                    'folder_name': name,
                    'description': description,
                    'url': f"http://127.0.0.1:8081/overlay/{name}"
                })
    return jsonify(overlays)

@interface_bp.route('/launch', methods=['POST'])
def launch_overlay():
    data = request.get_json()
    overlay_name = data.get('overlay')
    folder_name = next((overlay['folder_name'] for overlay in get_overlays().json if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        logging.debug(f"Attempting to launch overlay: {folder_name}")
        
        # Clean up any terminated processes
        for name in list(opened_overlays.keys()):
            if not opened_overlays[name].is_alive():
                del opened_overlays[name]
                
        if folder_name in opened_overlays and opened_overlays[folder_name].is_alive():
            return jsonify({'status': 'success', 'message': f'Overlay {folder_name} is already running.'}), 200

        overlay_url = f"http://127.0.0.1:8081/overlay/{folder_name}"
        properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
        
        logging.debug(f"Properties path: {properties_path}")
        
        if os.path.exists(properties_path):
            with open(properties_path, 'r') as properties_file:
                properties = json.load(properties_file)
                resolution = properties.get('resolution', {'width': 800, 'height': 600})
                logging.debug(f"Overlay properties: {properties}")
        else:
            logging.error(f"Overlay properties file not found for {folder_name}")
            return jsonify({'status': 'error', 'message': f'Overlay {folder_name} not found.'}), 404
        
        # Create a shared flag for this overlay
        exit_flag = multiprocessing.Value('i', 0)
        
        # Launch the overlay in a separate process
        process = multiprocessing.Process(
            target=launch_overlay_window, 
            args=(overlay_url, resolution, exit_flag)
        )
        process.daemon = True  # Set as daemon so it exits when main process exits
        process.start()
        opened_overlays[folder_name] = process
        
        return jsonify({'status': 'success', 'message': f'Overlay {folder_name} launched.'}), 200
    return jsonify({'status': 'error', 'message': 'Overlay name not provided.'}), 400

def launch_overlay_window(url, resolution, exit_flag=None):
    """
    Launch the overlay window in a separate process with the specified resolution.
    """
    try:
        # Create the overlay window
        overlay_window = OverlayWindow(url, width=resolution['width'], height=resolution['height'])
        
        # Set a callback for when the window is closed
        def on_closed():
            sys.exit(0)
            
        overlay_window.set_on_closed(on_closed)
        
        # Launch the window
        overlay_window.create_overlay_window()
    except Exception as e:
        logging.error(f"Error launching overlay window: {e}")
        sys.exit(1)
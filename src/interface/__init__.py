from flask import Blueprint, render_template, send_from_directory, jsonify, request
import os
import multiprocessing
from overlay_window import OverlayWindow
import json
import logging
import sys
import threading
import time

interface_bp = Blueprint(
    'interface', __name__,
    template_folder='.',
    static_folder=None
)

# Shared dictionary to track opened overlays across processes
opened_overlays = {}
# Dictionary to track overlay windows across the app
overlay_windows = {}

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
                position = properties.get('position', None)
                dpi_info = properties.get('dpi_info', {'scale': 1.0})
                
                # Look for preview GIFs in the overlay's static/images folder
                preview_gif = properties.get('preview_gif', None)
                if not preview_gif:
                    # Check static/images folder for preview.gif (correct path)
                    images_folder = os.path.join(overlay_path, 'static', 'images')
                    if os.path.exists(images_folder):
                        preview_file = os.path.join(images_folder, 'preview.gif')
                        if os.path.exists(preview_file):
                            # Use relative URL for the frontend
                            preview_gif = f"/overlay/{name}/static/images/preview.gif"
                    
                    # Fallback to static folder if not found
                    if not preview_gif:
                        static_folder = os.path.join(overlay_path, 'static')
                        if os.path.exists(static_folder):
                            preview_file = os.path.join(static_folder, 'preview.gif')
                            if os.path.exists(preview_file):
                                preview_gif = f"/overlay/{name}/static/preview.gif"
                
                overlays.append({
                    'display_name': display_name,
                    'folder_name': name,
                    'description': description,
                    'url': f"http://127.0.0.1:8081/overlay/{name}",
                    'position': position,
                    'dpi_info': dpi_info,
                    'preview_gif': preview_gif
                })
    return jsonify(overlays)

@interface_bp.route('/launch', methods=['POST'])
def launch_overlay():
    data = request.get_json()
    overlay_name = data.get('overlay')
    is_transparent = data.get('transparent', True)  # Default to transparent mode
    
    folder_name = next((overlay['folder_name'] for overlay in get_overlays().json if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        logging.debug(f"Attempting to launch overlay: {folder_name}")
        
        # Close existing overlay if it's open
        if folder_name in opened_overlays and opened_overlays[folder_name] is not None and opened_overlays[folder_name].is_alive():
            logging.debug(f"Closing existing overlay: {folder_name}")
            opened_overlays[folder_name].terminate()
            opened_overlays[folder_name].join(timeout=1)
            # Remove from opened_overlays
            del opened_overlays[folder_name]
            # Wait a moment to ensure the window is closed
            time.sleep(0.5)
        
        overlay_url = f"http://127.0.0.1:8081/overlay/{folder_name}"
        properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
        
        logging.debug(f"Properties path: {properties_path}")
        
        if os.path.exists(properties_path):
            with open(properties_path, 'r') as properties_file:
                properties = json.load(properties_file)
                resolution = properties.get('resolution', {'width': 800, 'height': 600})
                position = properties.get('position', None)
                logging.debug(f"Overlay properties: {properties}")
        else:
            logging.error(f"Overlay properties file not found for {folder_name}")
            return jsonify({'status': 'error', 'message': f'Overlay {folder_name} not found.'}), 404
        
        # Create a shared flag for this overlay
        exit_flag = multiprocessing.Value('i', 0)
        
        # Launch the overlay in a separate process
        process = multiprocessing.Process(
            target=launch_overlay_window, 
            args=(overlay_url, resolution, exit_flag, is_transparent, position, folder_name)
        )
        process.daemon = True  # Set as daemon so it exits when main process exits
        process.start()
        
        # Store process reference
        opened_overlays[folder_name] = process
        
        return jsonify({
            'status': 'success', 
            'message': f'Overlay {folder_name} launched.',
            'transparent': is_transparent
        }), 200
    return jsonify({'status': 'error', 'message': 'Overlay name not provided.'}), 400

@interface_bp.route('/toggle_transparency', methods=['POST'])
def toggle_transparency():
    data = request.get_json()
    overlay_name = data.get('overlay')
    
    folder_name = next((overlay['folder_name'] for overlay in get_overlays().json if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        # Get current saved position from properties.json
        properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
        position = None
        
        if os.path.exists(properties_path):
            with open(properties_path, 'r') as properties_file:
                properties = json.load(properties_file)
                position = properties.get('position', None)
        
        # Close existing overlay if it's open
        if folder_name in opened_overlays and opened_overlays[folder_name] is not None and opened_overlays[folder_name].is_alive():
            # Close the existing overlay
            opened_overlays[folder_name].terminate()
            opened_overlays[folder_name].join(timeout=1)
            # Small delay to ensure window closes
            time.sleep(0.5)
        
        # Launch with non-transparent mode
        return launch_overlay_with_transparency(folder_name, False)
    
    return jsonify({'status': 'error', 'message': 'Overlay not found.'}), 404

@interface_bp.route('/toggle_to_transparent', methods=['POST'])
def toggle_to_transparent():
    data = request.get_json()
    overlay_name = data.get('overlay')
    position = data.get('position')
    
    folder_name = next((overlay['folder_name'] for overlay in get_overlays().json if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        # Save position first
        if position:
            save_overlay_position(folder_name, position['x'], position['y'])
        
        # Close existing overlay and launch transparent one
        if folder_name in opened_overlays and opened_overlays[folder_name] is not None and opened_overlays[folder_name].is_alive():
            # Close the existing overlay
            opened_overlays[folder_name].terminate()
            opened_overlays[folder_name].join(timeout=1)
            # Small delay to ensure window closes
            time.sleep(0.5)
        
        # Launch with transparent=True
        return launch_overlay_with_transparency(folder_name, True)
    
    return jsonify({'status': 'error', 'message': 'Overlay not found.'}), 404

@interface_bp.route('/report_window_position', methods=['POST'])
def report_window_position():
    """
    Endpoint for pywebview windows to report their position directly from the window process
    """
    data = request.get_json()
    folder_name = data.get('folder_name')
    position = data.get('position')
    dpi_scale = data.get('dpi_scale', 1.0)  # Get DPI scaling factor from client
    
    if not folder_name or not position:
        return jsonify({'status': 'error', 'message': 'Missing required data'}), 400
    
    # Make sure position values are integers
    position['x'] = int(position['x'])
    position['y'] = int(position['y'])
    
    # Ensure position is on screen (prevent negative values)
    if position['x'] < 0:
        position['x'] = 0
    if position['y'] < 0:
        position['y'] = 0
    
    # Log the exact position and DPI scale being used
    logging.info(f"Saving position for {folder_name}: x={position['x']}, y={position['y']} with DPI scale: {dpi_scale}")
    
    # Save the dpi_scale along with the position
    properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
    
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as properties_file:
            properties = json.load(properties_file)
            
        # Save DPI info with position
        properties['position'] = {'x': position['x'], 'y': position['y']}
        properties['dpi_info'] = {'scale': dpi_scale}
            
        # Write back to file
        with open(properties_path, 'w') as properties_file:
            json.dump(properties, properties_file, indent=4)
    
    # Save the position
    if save_overlay_position(folder_name, position['x'], position['y']):
        # Close the existing overlay
        if folder_name in opened_overlays and opened_overlays[folder_name] is not None and opened_overlays[folder_name].is_alive():
            try:
                # Close the non-transparent overlay 
                opened_overlays[folder_name].terminate()
                opened_overlays[folder_name].join(timeout=1)
                # Small delay to ensure window closes
                time.sleep(0.5)
                
                # Launch transparent overlay at saved position
                return launch_overlay_with_transparency(folder_name, True)
            except Exception as e:
                logging.error(f"Error toggling overlay: {e}")
                return jsonify({'status': 'error', 'message': 'Error toggling overlay', 'error': str(e)}), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Position for {folder_name} saved',
            'position': position,
            'dpi_scale': dpi_scale
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'Failed to save position'}), 500

def launch_overlay_with_transparency(folder_name, is_transparent):
    """Helper function to launch overlay with specified transparency"""
    overlay_url = f"http://127.0.0.1:8081/overlay/{folder_name}"
    properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
    
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as properties_file:
            properties = json.load(properties_file)
            resolution = properties.get('resolution', {'width': 800, 'height': 600})
            position = properties.get('position', None)
    else:
        return jsonify({'status': 'error', 'message': f'Overlay {folder_name} properties not found.'}), 404
    
    # Create a shared flag for this overlay
    exit_flag = multiprocessing.Value('i', 0)
    
    # Launch the overlay in a separate process
    process = multiprocessing.Process(
        target=launch_overlay_window, 
        args=(overlay_url, resolution, exit_flag, is_transparent, position, folder_name)
    )
    process.daemon = True
    process.start()
    
    # Store process reference
    opened_overlays[folder_name] = process
    
    return jsonify({
        'status': 'success', 
        'message': f'Overlay {folder_name} launched with transparency={is_transparent}.',
        'transparent': is_transparent
    }), 200

@interface_bp.route('/save_position', methods=['POST'])
def save_position():
    data = request.get_json()
    overlay_name = data.get('overlay')
    
    folder_name = next((overlay['folder_name'] for overlay in get_overlays().json if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        # Get latest window position from client side
        position = data.get('position')
        
        if position:
            # Save position to properties.json
            save_overlay_position(folder_name, position['x'], position['y'])
            
            return jsonify({
                'status': 'success', 
                'message': f'Position saved for {folder_name}.', 
                'position': position
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'No position data provided.'}), 400
    
    return jsonify({'status': 'error', 'message': 'Overlay not found.'}), 404

def save_overlay_position(folder_name, x, y):
    """
    Save the overlay position to its properties.json file
    """
    properties_path = os.path.join(os.path.dirname(__file__), '..', 'overlays', folder_name, 'properties.json')
    
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as properties_file:
            properties = json.load(properties_file)
        
        # Update position
        properties['position'] = {'x': x, 'y': y}
        
        # Write back to file
        with open(properties_path, 'w') as properties_file:
            json.dump(properties, properties_file, indent=4)
        
        logging.debug(f"Saved position for {folder_name}: {x}, {y}")
        return True
    
    logging.error(f"Could not find properties file for {folder_name}")
    return False

@interface_bp.route('/close_overlay', methods=['POST'])
def close_overlay():
    """
    Close a specific overlay
    """
    data = request.get_json()
    overlay_name = data.get('overlay')
    folder_name = data.get('folder_name')
    
    if not folder_name:
        # If folder_name not provided directly, try to get it from display_name
        folder_name = next((overlay['folder_name'] for overlay in get_overlays().json 
                            if overlay['display_name'] == overlay_name), None)
    
    if folder_name:
        logging.debug(f"Attempting to close overlay: {folder_name}")
        
        if folder_name in opened_overlays and opened_overlays[folder_name] is not None and opened_overlays[folder_name].is_alive():
            try:
                logging.debug(f"Terminating overlay process: {folder_name}")
                opened_overlays[folder_name].terminate()
                opened_overlays[folder_name].join(timeout=1)
                # Remove from opened_overlays completely instead of setting to None
                del opened_overlays[folder_name]
                return jsonify({'status': 'success', 'message': f'Overlay {overlay_name} closed successfully'}), 200
            except Exception as e:
                logging.error(f"Error closing overlay: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            # If process is not found or not alive, consider it already closed
            logging.debug(f"Overlay {folder_name} is not running or already closed")
            return jsonify({'status': 'success', 'message': f'Overlay {overlay_name} is already closed'}), 200
    
    return jsonify({'status': 'error', 'message': 'Invalid overlay name provided'}), 400

@interface_bp.route('/get_active_overlays', methods=['GET'])
def get_active_overlays():
    """
    Return a list of currently active overlays
    """
    active = {}
    
    for folder_name, process in opened_overlays.items():
        if process is not None and process.is_alive():
            # Find the display name for this folder
            display_name = None
            for overlay in get_overlays().json:
                if overlay['folder_name'] == folder_name:
                    display_name = overlay['display_name']
                    break
            
            active[folder_name] = {
                'display_name': display_name,
                'folder_name': folder_name,
                'active': True
            }
    
    return jsonify({
        'status': 'success',
        'active_overlays': active
    }), 200

def launch_overlay_window(url, resolution, exit_flag=None, transparent=True, position=None, folder_name=None):
    """
    Launch the overlay window in a separate process with the specified resolution.
    """
    try:
        # Create the overlay window object
        overlay_window = OverlayWindow(
            url, 
            width=resolution['width'], 
            height=resolution['height'], 
            transparent=transparent,
            on_top=True
        )
        
        # Set folder name for position reporting first (needed for DPI info)
        if folder_name:
            overlay_window.set_folder_name(folder_name)
            
        # Now set position if available (will be properly adjusted for DPI)
        if position:
            logging.info(f"Setting position for {folder_name}: {position}")
            overlay_window.position = position
        
        def on_closed():
            logging.debug(f"Window for {folder_name} closed")
            if folder_name and folder_name in opened_overlays:
                del opened_overlays[folder_name]
            sys.exit(0)
            
        overlay_window.set_on_closed(on_closed)
        
        overlay_window.create_overlay_window()
    except Exception as e:
        logging.error(f"Error launching overlay window: {e}")
        sys.exit(1)
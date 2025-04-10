from flask import request, jsonify

@app.route('/close_overlay', methods=['POST'])
def close_overlay():
    data = request.json
    overlay_name = data.get('overlay')
    folder_name = data.get('folder_name')
    
    if not overlay_name or not folder_name:
        return jsonify({'status': 'error', 'message': 'Missing overlay information'})
    
    try:
        # Find and close the overlay window
        for window in overlay_windows:
            if window['display_name'] == overlay_name and window['folder_name'] == folder_name:
                if window['window'] and window['window'].is_alive():
                    window['window'].close()
                overlay_windows.remove(window)
                return jsonify({'status': 'success', 'message': f'Overlay {overlay_name} closed'})
        
        return jsonify({'status': 'error', 'message': 'Overlay not found or already closed'})
    except Exception as e:
        print(f"Error closing overlay: {e}")
        return jsonify({'status': 'error', 'message': str(e)}) 
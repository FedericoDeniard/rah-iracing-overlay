from flask import Blueprint, render_template, send_from_directory, Response
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)

overlays_bp = Blueprint(
    'overlays', __name__,
    template_folder='.',
    static_folder=None 
)

@overlays_bp.route('/<overlay_name>')
def serve_overlay(overlay_name):
    html_file_path = os.path.join(resource_path('overlays'), overlay_name, f'{overlay_name}.html')
    if os.path.exists(html_file_path):
        # Render the template with transparency support
        rendered_html = render_template(f'{overlay_name}/{overlay_name}.html')
        
        # Return with appropriate headers
        response = Response(rendered_html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    else:
        return "Overlay not found", 404

@overlays_bp.route('/<overlay_name>/static/<path:filename>')
def serve_static(overlay_name, filename):
    static_folder = os.path.join(resource_path('overlays'), overlay_name, 'static')
    return send_from_directory(static_folder, filename)
from flask import Blueprint, render_template, send_from_directory
import os

overlays_bp = Blueprint(
    'overlays', __name__,
    template_folder='.',
    static_folder=None 
)

@overlays_bp.route('/<overlay_name>')
def serve_overlay(overlay_name):
    html_file_path = os.path.join(overlays_bp.root_path, overlay_name, f'{overlay_name}.html')
    if os.path.exists(html_file_path):
        return render_template(f'{overlay_name}/{overlay_name}.html')
    else:
        return "Overlay not found", 404

@overlays_bp.route('/<overlay_name>/static/<path:filename>')
def serve_static(overlay_name, filename):
    static_folder = os.path.join(overlays_bp.root_path, overlay_name, 'static')
    return send_from_directory(static_folder, filename)
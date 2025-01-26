from flask import Blueprint, render_template, send_from_directory
import os

interface_bp = Blueprint(
    'interface', __name__,
    template_folder='.',
    static_folder=None
)

@interface_bp.route('/')
def index():
    return render_template('index.html')

@interface_bp.route('/static/<filename>')
def serve_static(filename):
    print(f"Serving static file: {filename}")
    print(f"Root path: {interface_bp.root_path}")
    return send_from_directory(os.path.join(interface_bp.root_path, 'static'), filename)
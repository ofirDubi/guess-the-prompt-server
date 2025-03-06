# app/images/routes.py
from flask import Blueprint,  send_from_directory, jsonify, request, url_for
import os
data_bp = Blueprint('data', __name__)

@data_bp.route('/<path:filename>')
def serve_image(filename):
    print("************************")
    root_dir = os.getcwd()
    target_path = os.path.join(root_dir, 'static', 'data', 'selected_images') 
    print(target_path)
    print("************************")
    print(os.path.exists(target_path))

    return send_from_directory(os.path.join(root_dir, 'static', 'data', 'selected_images'), path=filename)
from flask import Blueprint, request, jsonify
from utils.file_utils import list_files_in_path, rename_files
from utils.folder_utils import list_subfolders

api_bp = Blueprint('api', __name__)

@api_bp.route('/list_files')
def list_files():
    path = request.args.get('path')
    return jsonify(list_files_in_path(path))

@api_bp.route('/list_folders')
def list_folders():
    path = request.args.get('path')
    return jsonify(list_subfolders(path))

@api_bp.route('/process_files', methods=['POST'])
def process_files():
    data = request.get_json()
    result = rename_files(data)
    return jsonify(result)

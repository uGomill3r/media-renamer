import os

def list_subfolders(path):
    try:
        return sorted([
            f for f in os.listdir(path)
            if os.path.isdir(os.path.join(path, f)) and not f.startswith('.')
        ])
    except Exception as e:
        print(f"Error al listar subcarpetas: {e}")
        return []


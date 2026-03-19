import os
from config import VIDEO_EXTENSIONS, SUBTITLE_EXTENSIONS

def list_files_in_path(path):
    video_files = []
    sub_files = []

    if not os.path.isdir(path):
        return {"video_files": [], "sub_files": []}

    for f in sorted(os.listdir(path)):
        if f.startswith('.'):
            continue  # Ignorar archivos ocultos

        ext = os.path.splitext(f)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            video_files.append(f)
        elif ext in SUBTITLE_EXTENSIONS:
            sub_files.append(f)

    return {"video_files": video_files, "sub_files": sub_files}


def rename_files(data):
    action = data.get('action')
    path = data.get('path')
    videos = data.get('video_files', [])
    subs = data.get('sub_files', [])

    if len(videos) != len(subs):
        return {"message": "Cantidad desigual de archivos", "success": False}

    try:
        for i in range(len(videos)):
            video_name = os.path.splitext(videos[i])[0]
            sub_ext = os.path.splitext(subs[i])[1]
            new_name = f"{video_name}.es{sub_ext}"

            if action == 'rename_subtitles':
                os.rename(os.path.join(path, subs[i]), os.path.join(path, new_name))
            elif action == 'rename_videos':
                video_ext = os.path.splitext(videos[i])[1]
                sub_name = os.path.splitext(subs[i])[0]
                new_name = f"{sub_name}{video_ext}"
                os.rename(os.path.join(path, videos[i]), os.path.join(path, new_name))

        return {"message": "Renombrado exitoso", "success": True}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "success": False}

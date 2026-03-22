# MediaRenamer

App web Flask para renombrar masivamente archivos de video y subtítulos en una carpeta. Permite sincronizar los nombres entre ambos tipos de archivo — copiando el nombre del video al subtítulo o viceversa — de forma visual y con soporte para reordenar archivos con drag & drop.

---

## Funcionalidad

La app resuelve el problema de tener videos y subtítulos con nombres distintos que los reproductores no asocian automáticamente. Por ejemplo:

```
Película.2024.1080p.BluRay.mp4   →   Película.2024.1080p.BluRay.es.srt
sub_descargado.srt               →   (renombrado al nombre del video)
```

### Modos de renombrado

**Renombrar subtítulos** (botón morado):
Copia el nombre base del video a cada subtítulo, agregando el sufijo `.es` antes de la extensión.
```
Video:     Pelicula.2024.1080p.mp4
Subtítulo: sub.srt  →  Pelicula.2024.1080p.es.srt
```

**Renombrar videos** (botón gris):
Copia el nombre base del subtítulo a cada video, conservando la extensión del video.
```
Subtítulo: Pelicula.2024.1080p.es.srt
Video:     video.mp4  →  Pelicula.2024.1080p.es.mp4
```

En ambos casos el emparejamiento es por posición — el video 1 se empareja con el subtítulo 1, el video 2 con el subtítulo 2, etc. El orden se puede ajustar con drag & drop antes de ejecutar el renombrado.

---

## Stack técnico

- **Flask 3.1** — framework web
- **Tailwind CSS** (CDN) — estilos
- **SortableJS** (CDN) — drag & drop para reordenar archivos
- **Vanilla JS** — lógica del cliente (sin frameworks)

---

## Estructura del proyecto

```
MediaRenamer/
├── app.py                  ← arranque Flask
├── config.py               ← configuración: ruta base, extensiones
├── requirements.txt
├── routes/
│   ├── __init__.py         ← registro de blueprints
│   ├── home.py             ← ruta principal GET /
│   └── api.py              ← API JSON: listar archivos, listar carpetas, renombrar
├── utils/
│   ├── file_utils.py       ← listar y renombrar archivos
│   └── folder_utils.py     ← listar subcarpetas
├── static/
│   ├── js/
│   │   └── main.js         ← lógica del cliente
│   ├── mr-apple-touch-icon.png
│   └── mr-favicon.ico
└── templates/
    └── home.html           ← vista principal
```

---

## Configuración

Editá `config.py` antes de arrancar:

```python
MEDIA_PATH = '/ruta/a/tu/carpeta'   # carpeta raíz del explorador de archivos

VIDEO_EXTENSIONS    = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.vtt', '.sub']

SECRET_KEY = 'cambiame-por-una-clave-segura'
```

---

## Instalación

```bash
git clone https://github.com/tu-usuario/MediaRenamer.git
cd MediaRenamer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Accedé en `http://localhost:8000`

---

## API

### `GET /list_folders?path=<ruta>`
Retorna las subcarpetas de la ruta indicada.
```json
["Carpeta A", "Carpeta B"]
```

### `GET /list_files?path=<ruta>`
Retorna los archivos de video y subtítulos en la ruta.
```json
{
  "video_files": ["pelicula.mp4"],
  "sub_files": ["pelicula.srt"]
}
```

### `POST /process_files`
Ejecuta el renombrado. Body JSON:
```json
{
  "action": "rename_subtitles",
  "path": "/ruta/carpeta",
  "video_files": ["video1.mp4", "video2.mp4"],
  "sub_files":   ["sub1.srt",   "sub2.srt"]
}
```
`action` puede ser `rename_subtitles` o `rename_videos`.

Respuesta:
```json
{"message": "Renombrado exitoso", "success": true}
```

---

## Uso

1. Navegá el árbol de carpetas en la pestaña **Seleccionar Carpeta**
2. Una vez seleccionada la carpeta, los videos y subtítulos aparecen en las pestañas **Videos** y **Subtítulos**
3. Si el orden no coincide, reordenás los archivos con drag & drop
4. Elegís el modo:
   - **Renombrar subtítulos** → los subtítulos toman el nombre de los videos
   - **Renombrar videos** → los videos toman el nombre de los subtítulos
5. Confirmás la operación — el resultado se muestra en pantalla

---

## Notas

- Los archivos ocultos (que empiezan con `.`) se ignoran automáticamente
- La cantidad de videos y subtítulos debe ser igual para poder renombrar
- El renombrado es irreversible — recomendable hacer backup antes
- Los subtítulos renombrados desde videos reciben el sufijo `.es` antes de la extensión (ej: `pelicula.es.srt`)

---

## Licencia

MIT License — Copyright (c) 2025 uGomill3r. Ver `LICENSE.md` para el texto completo.
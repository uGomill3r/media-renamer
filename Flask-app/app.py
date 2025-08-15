import os
import shutil
import json
from pathlib import Path
from zipfile import ZipFile
from flask import Flask, render_template_string, request, flash, send_from_directory, redirect, url_for, jsonify
from werkzeug.exceptions import HTTPException

# --- Configuración de la aplicación Flask ---
app = Flask(__name__)
# ¡IMPORTANTE! Usa una clave secreta fuerte y aleatoria para producción.
app.secret_key = "6efdd6116ae6569e5d0fdca0be9a8644"

# Directorio para archivos temporales y zip (ya no se usa para renombrar in-place)
app.config['UPLOAD_PATH'] = 'uploads/'
project_dir = Path(__file__).parent

# Extensiones de archivo que el script buscará
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.vtt', '.sub']


# --- Rutas de la aplicación ---
@app.errorhandler(HTTPException)
def handle_exception(e):
    """Maneja las excepciones HTTP y las convierte en una respuesta JSON."""
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.route('/', methods=['GET'])
def home():
    """
    Ruta principal que muestra la interfaz de selección de carpetas
    y maneja el procesamiento de archivos.
    """
    temp_upload_path = project_dir / app.config['UPLOAD_PATH']
    if temp_upload_path.exists():
        shutil.rmtree(temp_upload_path)
    temp_upload_path.mkdir(exist_ok=True)

    # Si es un método GET, mostrar la plantilla con el árbol de carpetas
    return render_template_string("""
        <!doctype html>
        <html lang="es">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Renombrar Subtítulos</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
            <style>
              .arrow {
                transition: transform 0.2s;
              }
              .expanded .arrow {
                transform: rotate(90deg);
              }
              .folder-name {
                  cursor: pointer;
              }
              .selected-folder .folder-name {
                background-color: #e0f2fe; /* blue-100 */
                font-weight: 600;
              }
              .sortable-ghost {
                opacity: 0.4;
                background-color: #f3f4f6; /* gray-100 */
              }
              .drag-handle {
                cursor: grab;
              }
              .tab-button.active {
                  border-color: #4f46e5;
                  color: #4f46e5;
              }
              .tab-content.hidden {
                  display: none;
              }
            </style>
          </head>
          <body class="bg-gray-100 flex items-center justify-center min-h-screen font-sans">
            <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-2xl">
              <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">Renombrar Subtítulos</h1>
              {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                  <ul class="mb-4 space-y-2">
                  {% for category, message in messages %}
                    <li class="p-3 rounded-md text-sm {% if category == 'danger' %}bg-red-100 text-red-700{% elif category == 'warning' %}bg-yellow-100 text-yellow-700{% else %}bg-green-100 text-green-700{% endif %}">{{ message }}</li>
                  {% endfor %}
                  </ul>
                {% endif %}
              {% endwith %}

              <!-- Formulario y vista de árbol -->
              <form id="folder-form" class="space-y-6">
                <div>
                  <label for="selected_path" class="block text-sm font-medium text-gray-700 mb-2">Ruta seleccionada:</label>
                  <div class="flex items-center space-x-2">
                      <input type="text" name="selected_path" id="selected_path" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 focus:outline-none" readonly>
                      <button type="button" id="refresh-button" class="p-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors" aria-label="Refrescar">
                          <span class="h-5 w-5 flex items-center justify-center text-gray-500">🔄</span>
                      </button>
                  </div>
                </div>

                <!-- Contenedor para las pestañas -->
                <div class="flex border-b border-gray-200 mb-4" id="tabs-container">
                    <button type="button" data-tab="folder" class="tab-button active flex-1 py-2 px-4 text-center text-sm font-medium border-b-2 border-indigo-600 text-indigo-600 hover:bg-gray-100">Seleccionar Carpeta</button>
                    <button type="button" data-tab="videos" class="tab-button flex-1 py-2 px-4 text-center text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300">Videos</button>
                    <button type="button" data-tab="subtitles" class="tab-button flex-1 py-2 px-4 text-center text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300">Subtítulos</button>
                </div>

                <!-- Mensaje de estado -->
                <div id="status-message" class="hidden p-3 rounded-md text-sm"></div>

                <!-- Contenido de las pestañas -->
                <div class="tab-content border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-80 overflow-y-auto" id="folder-tab-content">
                    <h2 class="text-lg font-semibold text-gray-700 mb-2">Selecciona la carpeta:</h2>
                    <!-- Se cambió a <ul> para corregir el error de la viñeta de punto -->
                    <ul id="tree-container" class="list-none space-y-1">
                        <!-- El árbol se generará aquí con JavaScript -->
                        <li class="flex items-center text-gray-500 italic">
                            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            Cargando...
                        </li>
                    </ul>
                </div>

                <div class="tab-content border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-80 overflow-y-auto hidden" id="videos-tab-content">
                    <div id="video-files-list"></div>
                </div>

                <div class="tab-content border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-80 overflow-y-auto hidden" id="subtitles-tab-content">
                    <div id="subtitle-files-list"></div>
                    <div id="no-files-message" class="text-gray-500 italic text-sm mt-4 hidden">No se encontraron archivos en esta carpeta.</div>
                </div>

                <div class="flex space-x-4">
                  <button type="button" id="rename-subs-button" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-lg text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                    Renombrar subtítulos
                  </button>
                  <button type="button" id="rename-videos-button" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-lg text-lg font-medium text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors">
                    Renombrar videos
                  </button>
                </div>
              </form>
            </div>

            <script>
                // Se cambió el contenedor principal del árbol de un div a un ul
                const treeContainer = document.getElementById('tree-container');
                const selectedPathInput = document.getElementById('selected_path');
                const videoListDiv = document.getElementById('video-files-list');
                const subtitleListDiv = document.getElementById('subtitle-files-list');
                const form = document.getElementById('folder-form');
                const noFilesMessage = document.getElementById('no-files-message');
                const statusMessageDiv = document.getElementById('status-message');
                const refreshButton = document.getElementById('refresh-button');

                const renameSubsButton = document.getElementById('rename-subs-button');
                const renameVideosButton = document.getElementById('rename-videos-button');

                // Polyfill simple para Path.join
                class Path {
                    static separator = '/';
                    static join(...parts) {
                        return parts.filter(p => p).join(Path.separator).replace(new RegExp(Path.separator + '+', 'g'), Path.separator);
                    }
                }

                function showStatusMessage(message, isError = false) {
                    statusMessageDiv.textContent = message;
                    statusMessageDiv.classList.remove('hidden', 'bg-red-100', 'text-red-700', 'bg-green-100', 'text-green-700');
                    if (isError) {
                        statusMessageDiv.classList.add('bg-red-100', 'text-red-700');
                    } else {
                        statusMessageDiv.classList.add('bg-green-100', 'text-green-700');
                    }
                }

                function clearStatusMessage() {
                    statusMessageDiv.classList.add('hidden');
                }

                // Función para actualizar la numeración de una lista
                function updateListNumbers(listElement) {
                    const listItems = listElement.children;
                    for (let i = 0; i < listItems.length; i++) {
                        // El número está en el segundo hijo (el primero es el handle)
                        const numberSpan = listItems[i].querySelector('span:nth-child(2)');
                        if (numberSpan) {
                            numberSpan.textContent = `${i + 1}.`;
                        }
                    }
                }

                // Función para mostrar los archivos en la UI y hacerlos arrastrables
                function displayFiles(filesData) {
                    // Limpiar las listas antes de rellenarlas
                    videoListDiv.innerHTML = '';
                    subtitleListDiv.innerHTML = '';
                    noFilesMessage.classList.add('hidden');

                    const { video_files, sub_files } = filesData;

                    const createList = (title, files, type, parentDiv) => {
                        const titleEl = document.createElement('h2');
                        titleEl.classList.add('text-lg', 'font-semibold', 'text-gray-700', 'mb-2');
                        titleEl.textContent = `${title} (${files.length})`;
                        parentDiv.appendChild(titleEl);

                        if (files.length > 0) {
                            const ul = document.createElement('ul');
                            ul.id = `${type}-sortable`;
                            ul.classList.add('list-none', 'text-sm', 'text-gray-600', 'mt-1', 'space-y-1');

                            files.forEach((file, index) => {
                                const li = document.createElement('li');
                                li.classList.add('flex', 'items-center', 'p-2', 'bg-white', 'border', 'border-gray-200', 'rounded', 'shadow-sm', 'hover:bg-gray-50');

                                const dragHandle = document.createElement('span');
                                dragHandle.classList.add('drag-handle', 'mr-2', 'text-gray-400');
                                dragHandle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" /></svg>';

                                const numberSpan = document.createElement('span');
                                numberSpan.textContent = `${index + 1}.`;
                                numberSpan.classList.add('font-medium', 'text-gray-500', 'w-6', 'flex-shrink-0');

                                const fileNameSpan = document.createElement('span');
                                fileNameSpan.textContent = file;
                                fileNameSpan.classList.add('flex-grow');

                                li.appendChild(dragHandle);
                                li.appendChild(numberSpan);
                                li.appendChild(fileNameSpan);
                                ul.appendChild(li);
                            });
                            parentDiv.appendChild(ul);
                            new Sortable(ul, {
                                animation: 150,
                                ghostClass: 'sortable-ghost',
                                handle: '.drag-handle',
                                onUpdate: function (evt) {
                                  // Llamar a la función para actualizar la numeración
                                  updateListNumbers(ul);
                                }
                            });
                        } else {
                            const emptyMsg = document.createElement('p');
                            emptyMsg.classList.add('text-gray-500', 'italic', 'text-sm');
                            emptyMsg.textContent = `No se encontraron archivos de ${title.toLowerCase()}.`;
                            parentDiv.appendChild(emptyMsg);
                        }
                    };

                    if (video_files.length > 0 || sub_files.length > 0) {
                        createList('Videos', video_files, 'video', videoListDiv);
                        createList('Subtítulos', sub_files, 'subtitle', subtitleListDiv);

                        if (video_files.length !== sub_files.length) {
                            showStatusMessage('El número de archivos de video y subtítulos no coincide. El proceso de renombrado podría fallar.', true);
                        }
                    } else {
                        noFilesMessage.classList.remove('hidden');
                    }
                }

                // Función para obtener y mostrar los archivos de la carpeta seleccionada
                async function fetchAndDisplayFiles(path) {
                    clearStatusMessage();
                    // Mostrar los mensajes de carga
                    videoListDiv.innerHTML = '<div class="flex items-center text-gray-500 italic"><svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Cargando archivos...</div>';
                    subtitleListDiv.innerHTML = '<div class="flex items-center text-gray-500 italic"><svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Cargando archivos...</div>';
                    noFilesMessage.classList.add('hidden');

                    try {
                        const response = await fetch(`list_files?path=${encodeURIComponent(path)}`);
                        if (!response.ok) {
                             throw new Error('La respuesta del servidor no fue exitosa.');
                        }
                        const filesData = await response.json();
                        // Asegurarse de que los datos son un objeto válido
                        if (!filesData || !Array.isArray(filesData.video_files) || !Array.isArray(filesData.sub_files)) {
                           throw new Error('El formato de los datos del servidor no es el esperado.');
                        }
                        displayFiles(filesData);
                    } catch (error) {
                        console.error('Error fetching or parsing files:', error);
                        // Mensaje de error más detallado en la interfaz
                        showStatusMessage('Error al cargar los archivos. Revisa la consola del navegador para más detalles.', true);
                        videoListDiv.innerHTML = '<div class="text-gray-500 p-2 italic">Error al cargar archivos.</div>';
                        subtitleListDiv.innerHTML = '<div class="text-gray-500 p-2 italic">Error al cargar archivos.</div>';
                    }
                }

                function createFolderElement(folder, path, depth) {
                    const li = document.createElement('li');
                    li.classList.add('space-y-1');

                    const container = document.createElement('div');
                    container.classList.add('flex', 'items-center', 'space-x-1', 'py-1', `pl-${depth * 4}`);

                    const toggle = document.createElement('span');
                    toggle.innerHTML = '<svg class="h-4 w-4 text-gray-400 arrow transition-transform" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path></svg>';
                    toggle.classList.add('cursor-pointer');

                    const folderIcon = '<svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path></svg>';

                    const folderName = document.createElement('span');
                    folderName.innerHTML = `${folderIcon} <span class="ml-2">${folder}</span>`;
                    folderName.classList.add('flex', 'items-center', 'text-gray-800', 'hover:bg-gray-200', 'p-1', 'rounded', 'flex-grow', 'folder-name');

                    const fullPath = Path.join(path, folder);
                    folderName.onclick = () => {
                        selectedPathInput.value = fullPath;
                        document.querySelectorAll('.selected-folder').forEach(el => el.classList.remove('selected-folder'));
                        container.classList.add('selected-folder');
                        fetchAndDisplayFiles(fullPath); // Llama a la nueva función aquí
                    };

                    container.appendChild(toggle);
                    container.appendChild(folderName);
                    li.appendChild(container);

                    const subList = document.createElement('ul');
                    // Se añadió la clase 'list-none' a la lista de subcarpetas
                    subList.classList.add('hidden', 'space-y-1', 'list-none');

                    toggle.onclick = async () => {
                        const isExpanded = li.classList.toggle('expanded');
                        subList.classList.toggle('hidden', !isExpanded);

                        if (isExpanded && subList.children.length === 0) {
                            toggle.innerHTML = '<svg class="animate-spin h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
                            try {
                                const response = await fetch(`list_folders?path=${encodeURIComponent(fullPath)}`);
                                if (!response.ok) {
                                    throw new Error('No se pudo cargar la carpeta.');
                                }
                                const data = await response.json();

                                data.forEach(item => {
                                    subList.appendChild(createFolderElement(item, fullPath, depth + 1));
                                });
                                if (data.length === 0) {
                                  const emptyLi = document.createElement('li');
                                  emptyLi.textContent = "Carpeta vacía";
                                  emptyLi.classList.add('text-gray-500', 'italic', 'text-sm', 'pl-4');
                                  subList.appendChild(emptyLi);
                                }
                            } catch (error) {
                                console.error('Error fetching folders:', error);
                                const errorLi = document.createElement('li');
                                errorLi.textContent = "Error al cargar. Revisa la consola del navegador.";
                                errorLi.classList.add('text-red-500', 'italic', 'text-sm', 'pl-4');
                                subList.appendChild(errorLi);
                            } finally {
                                toggle.innerHTML = '<svg class="h-4 w-4 text-gray-400 arrow transition-transform" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path></svg>';
                            }
                        }
                    };

                    li.appendChild(subList);
                    return li;
                }

                async function loadInitialTree() {
                    const initialPath = '{{ initial_path }}';
                    selectedPathInput.value = initialPath;

                    try {
                        const response = await fetch(`list_folders?path=${encodeURIComponent(initialPath)}`);
                        if (!response.ok) {
                             throw new Error('La respuesta del servidor no fue exitosa.');
                        }
                        const data = await response.json();
                        treeContainer.innerHTML = '';
                        if (data.length === 0) {
                            // Si la carpeta inicial está vacía, no se renderizan elementos de lista
                            treeContainer.innerHTML = '<li class="text-gray-500 italic">Carpeta inicial vacía.</li>';
                        } else {
                            data.forEach(item => {
                                treeContainer.appendChild(createFolderElement(item, initialPath, 0));
                            });
                        }
                        // También cargar los archivos de la ruta inicial
                        fetchAndDisplayFiles(initialPath);
                    } catch (error) {
                        console.error('Error loading initial path:', error);
                        treeContainer.innerHTML = '<li class="text-red-500 p-2 border-l-4 border-red-500 bg-red-100">Error al cargar la ruta inicial. Asegúrate de que Flask está ejecutándose y tiene acceso a la carpeta.</li>';
                    }
                }

                // Manejar el cambio de pestañas
                document.querySelectorAll('.tab-button').forEach(button => {
                    button.addEventListener('click', () => {
                        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active', 'border-indigo-600', 'text-indigo-600'));
                        document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));

                        button.classList.add('active', 'border-indigo-600', 'text-indigo-600');
                        button.classList.remove('border-transparent', 'text-gray-500');

                        const tabName = button.getAttribute('data-tab');
                        document.getElementById(`${tabName}-tab-content`).classList.remove('hidden');
                    });
                });


                // Iniciar la carga al cargar la página
                window.onload = function() {
                  loadInitialTree();
                };

                // Función central para manejar el proceso de renombrado
                async function handleRename(action) {
                    const videoList = document.getElementById('video-sortable');
                    const subtitleList = document.getElementById('subtitle-sortable');
                    const submitButton = form.querySelector('button[type="submit"]');

                    clearStatusMessage();

                    if (!videoList || !subtitleList) {
                        showStatusMessage('No se encontraron archivos de video o subtítulos en la página para procesar.', true);
                        return;
                    }

                    const videoFiles = Array.from(videoList.children).map(li => li.querySelector('span:last-child').textContent);
                    const subtitleFiles = Array.from(subtitleList.children).map(li => li.querySelector('span:last-child').textContent);
                    const selectedPath = selectedPathInput.value;

                    if (videoFiles.length !== subtitleFiles.length) {
                        showStatusMessage('El número de archivos de video y subtítulos no coincide. Por favor, revisa las listas.', true);
                        return;
                    }

                    if (videoFiles.length === 0) {
                        showStatusMessage('No hay archivos para renombrar.', true);
                        return;
                    }

                    // Deshabilitar los botones mientras se procesa
                    renameSubsButton.disabled = true;
                    renameVideosButton.disabled = true;

                    if (action === 'rename_subtitles') {
                        renameSubsButton.textContent = 'Procesando...';
                    } else {
                        renameVideosButton.textContent = 'Procesando...';
                    }

                    try {
                        const response = await fetch('/process_files', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                action: action,
                                path: selectedPath,
                                video_files: videoFiles,
                                sub_files: subtitleFiles
                            })
                        });

                        const result = await response.json();

                        if (response.ok) {
                            showStatusMessage(result.message || 'Archivos renombrados exitosamente.');
                            // Recargar los archivos para reflejar los cambios
                            fetchAndDisplayFiles(selectedPath);
                        } else {
                            showStatusMessage(`Error: ${result.message || 'Ocurrió un error en el servidor.'}`, true);
                        }
                    } catch (error) {
                        console.error('Error en el proceso de renombrado:', error);
                        showStatusMessage('Ocurrió un error inesperado. Revisa la consola del navegador.', true);
                    } finally {
                        renameSubsButton.disabled = false;
                        renameVideosButton.disabled = false;
                        renameSubsButton.textContent = 'Renombrar subtítulos';
                        renameVideosButton.textContent = 'Renombrar videos';
                    }
                }

                // Manejar los clics de los nuevos botones
                renameSubsButton.addEventListener('click', () => handleRename('rename_subtitles'));
                renameVideosButton.addEventListener('click', () => handleRename('rename_videos'));

                // Manejar el clic en el botón de refrescar
                refreshButton.addEventListener('click', () => {
                    const selectedPath = selectedPathInput.value;
                    if (selectedPath) {
                        fetchAndDisplayFiles(selectedPath);
                    } else {
                        showStatusMessage('No hay una ruta seleccionada para refrescar.', true);
                    }
                });

            </script>
          </body>
        </html>
    """, initial_path=str('/mnt/HDD/Library'))


@app.route('/list_files')
def list_files():
    """
    Nuevo endpoint para listar archivos de video y subtítulos en una carpeta específica,
    excluyendo los archivos de metadatos ocultos de macOS.
    """
    base_path_str = request.args.get('path', '/')
    base_path = Path(base_path_str)

    if not base_path.is_dir():
        return jsonify({"error": "La ruta no existe o no es un directorio"}), 404

    try:
        all_files = [f for f in base_path.iterdir() if f.is_file() and not f.name.startswith('._')]
        video_files = sorted([f.name for f in all_files if f.suffix.lower() in VIDEO_EXTENSIONS])
        sub_files = sorted([f.name for f in all_files if f.suffix.lower() in SUBTITLE_EXTENSIONS])

        return jsonify({
            "video_files": video_files,
            "sub_files": sub_files
        })
    except Exception as e:
        # Registro detallado del error en la consola del servidor
        print(f"Error en /list_files para la ruta '{base_path_str}': {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/list_folders')
def list_folders():
    # Obtener la ruta del sistema de archivos desde el parámetro de la URL
    base_path_str = request.args.get('path', '/')
    base_path = Path(base_path_str)

    # Verificar si la ruta es válida y es un directorio
    if not base_path.is_dir():
        return jsonify({"error": "La ruta no existe o no es un directorio"}), 404

    try:
        folders = [f.name for f in base_path.iterdir() if f.is_dir()]
        return jsonify(folders)
    except Exception as e:
        # Registro detallado del error en la consola del servidor
        print(f"Error en /list_folders para la ruta '{base_path_str}': {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/process_files', methods=['POST'])
def process_files():
    """
    Ruta para renombrar archivos. La acción (renombrar subtítulos o videos)
    se determina por el parámetro 'action'.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Datos de entrada no válidos."}), 400

        # Obtener los datos del cuerpo de la solicitud
        action = data.get('action')
        selected_path = data.get('path')
        video_filenames = data.get('video_files', [])
        sub_filenames = data.get('sub_files', [])

        if not selected_path or not action:
            return jsonify({"message": "La ruta y la acción de renombrado son requeridas."}), 400

        if len(video_filenames) != len(sub_filenames):
            return jsonify({"message": "El número de archivos de video y subtítulos no coincide."}), 400

        if not video_filenames:
            return jsonify({"message": "No hay archivos para procesar."}), 400

        folder_path = Path(selected_path)

        # Bucle principal para renombrar, con lógica condicional
        for i in range(len(video_filenames)):
            video_file_name = video_filenames[i]
            sub_file_name = sub_filenames[i]

            if action == 'rename_subtitles':
                # Renombrar subtítulos con nombres de videos
                old_path = folder_path / sub_file_name
                new_stem = Path(video_file_name).stem
                new_path = old_path.with_name(f"{new_stem}{old_path.suffix}")

            elif action == 'rename_videos':
                # Renombrar videos con nombres de subtítulos
                old_path = folder_path / video_file_name
                new_stem = Path(sub_file_name).stem
                new_path = old_path.with_name(f"{new_stem}{old_path.suffix}")

            else:
                return jsonify({"message": "Acción de renombrado no válida."}), 400

            # Realizar el renombrado, manejando posibles errores
            try:
                if not old_path.exists():
                    return jsonify({
                                       "message": f"Error: El archivo '{old_path.name}' no se encontró en la carpeta. Verifica que el archivo exista y que el orden en las listas sea correcto."}), 404

                old_path.rename(new_path)

            except FileNotFoundError:
                return jsonify({"message": f"Error: El archivo '{old_path.name}' no se encontró en la carpeta."}), 404
            except OSError as e:
                return jsonify({"message": f"Error del sistema al renombrar '{old_path.name}': {str(e)}."}), 500
            except Exception as e:
                print(f"Error inesperado al renombrar '{old_path.name}': {e}")
                return jsonify(
                    {"message": f"Ocurrió un error inesperado al procesar el archivo '{old_path.name}': {str(e)}"}), 500

        return jsonify({"message": "Archivos renombrados exitosamente."}), 200

    except Exception as e:
        print(f"Error en /process_files: {e}")
        return jsonify({"message": f"Ocurrió un error en el servidor: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)

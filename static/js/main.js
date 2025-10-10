
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

// File Browser Functions
let currentBrowserPath = '~';
let selectedFilePath = null;

async function openFileBrowser() {
    const modal = document.getElementById('file-browser-modal');
    modal.style.display = 'block';
    currentBrowserPath = '~';
    selectedFilePath = null;
    await browseDirectory('~');
}

function closeFileBrowser() {
    const modal = document.getElementById('file-browser-modal');
    modal.style.display = 'none';
}

async function browseDirectory(path) {
    const fileList = document.getElementById('file-list');
    const currentPathSpan = document.getElementById('current-path');

    fileList.innerHTML = '<p>Loading...</p>';

    try {
        const response = await fetch('/api/files/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path })
        });

        const data = await response.json();

        if (response.ok) {
            currentBrowserPath = data.path;
            currentPathSpan.textContent = data.path;
            displayFileList(data.entries);
        } else {
            fileList.innerHTML = `<p class="error">Error: ${data.detail || 'Failed to list directory'}</p>`;
        }
    } catch (error) {
        fileList.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }
}

function displayFileList(entries) {
    const fileList = document.getElementById('file-list');

    if (!entries || entries.length === 0) {
        fileList.innerHTML = '<p>Empty directory</p>';
        return;
    }

    let html = '';

    entries.forEach(entry => {
        const icon = entry.type === 'directory' ? '📁' : '📄';
        const entryClass = entry.type === 'directory' ? 'directory' : 'file';
        const executable = entry.executable ? '<span class="executable-badge">exec</span>' : '';

        html += `
            <div class="file-entry ${entryClass}" onclick="handleFileClick('${entry.path}', '${entry.type}', '${entry.name}')">
                <span class="icon">${icon}</span>
                <span class="name">${entry.name}</span>
                <span class="size">${entry.size}</span>
                ${executable}
            </div>
        `;
    });

    fileList.innerHTML = html;
}

async function handleFileClick(path, type, name) {
    if (type === 'directory') {
        // Navigate to directory
        await browseDirectory(path);
    } else {
        // Select file
        selectedFilePath = path;
        document.getElementById('selected-file').textContent = path;

        // Highlight selected file
        document.querySelectorAll('.file-entry').forEach(el => {
            el.classList.remove('selected');
        });
        event.target.closest('.file-entry').classList.add('selected');
    }
}

async function navigateToParent() {
    const parentPath = currentBrowserPath.substring(0, currentBrowserPath.lastIndexOf('/')) || '/';
    await browseDirectory(parentPath);
}

async function navigateToHome() {
    await browseDirectory('~');
}

function selectFile() {
    if (selectedFilePath) {
        document.getElementById('xhpl-path').value = selectedFilePath;
        closeFileBrowser();

        // Auto-verify the selected file
        verifyHPLPath();
    } else {
        alert('Please select a file first');
    }
}

// Find HPL binaries automatically
async function findHPLBinaries() {
    const statusDiv = document.getElementById('xhpl-verify-status');
    statusDiv.innerHTML = '<span class="info">Searching for HPL binaries...</span>';

    try {
        const response = await fetch('/api/files/find-hpl');
        const data = await response.json();

        if (response.ok) {
            if (data.found_count === 0) {
                statusDiv.innerHTML = '<span class="error">No xhpl binaries found in common locations.</span>';
            } else if (data.found_count === 1) {
                // Auto-select if only one found
                document.getElementById('xhpl-path').value = data.paths[0];
                statusDiv.innerHTML = `<span class="success">✓ Found and selected: ${data.paths[0]}</span>`;
                verifyHPLPath();
            } else {
                // Show list to choose from
                let html = '<div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-top: 5px;">';
                html += `<strong>Found ${data.found_count} HPL binaries:</strong><br>`;
                data.paths.forEach((path, index) => {
                    html += `<div style="margin-top: 5px;">
                        <button onclick="document.getElementById('xhpl-path').value='${path}'; verifyHPLPath();" class="btn-secondary btn-small">
                            Select: ${path}
                        </button>
                    </div>`;
                });
                html += '</div>';
                statusDiv.innerHTML = html;
            }
        } else {
            statusDiv.innerHTML = `<span class="error">Error: ${data.detail || 'Search failed'}</span>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<span class="error">Error: ${error.message}</span>`;
    }
}

// Verify HPL path
async function verifyHPLPath() {
    const path = document.getElementById('xhpl-path').value;
    const statusDiv = document.getElementById('xhpl-verify-status');

    if (!path || path === 'xhpl') {
        statusDiv.innerHTML = '<span class="info">ℹ Using default "xhpl" from $PATH</span>';
        return;
    }

    statusDiv.innerHTML = '<span class="info">Verifying...</span>';

    try {
        const response = await fetch('/api/files/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path })
        });

        const data = await response.json();

        if (response.ok) {
            const file = data.file;
            if (file.executable) {
                statusDiv.innerHTML = `<span class="success">✓ Valid executable: ${file.name} (${file.size})</span>`;
            } else {
                statusDiv.innerHTML = `<span class="error">⚠ File exists but is not executable!</span>`;
            }
        } else {
            statusDiv.innerHTML = `<span class="error">✗ ${data.detail || 'File not found'}</span>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<span class="error">Error: ${error.message}</span>`;
    }
}

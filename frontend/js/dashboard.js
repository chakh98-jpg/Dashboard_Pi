/**
 * Dashboard Pi - Enhanced JavaScript v2.0
 * Full system control with WebSocket real-time updates
 */

// Configuration
const CONFIG = {
    wsUrl: `ws://${window.location.host}/ws`,
    apiUrl: `http://${window.location.host}/api`,
    reconnectInterval: 3000,
    chartDataPoints: 30,
    statsRefreshInterval: 60000,
};

// State
let ws = null;
let reconnectAttempts = 0;
let charts = {};
let currentPath = '/';
let editingFile = null;
let pendingAction = null;

let chartData = {
    cpu: [],
    ram: [],
    temp: [],
    labels: []
};

// ========================================
// DOM Ready
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCharts();
    fetchSystemInfo();
    fetchStats();
    connectWebSocket();

    setInterval(fetchStats, CONFIG.statsRefreshInterval);
});

// ========================================
// Navigation
// ========================================
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(sectionName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionName);
    });

    // Update sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.toggle('active', section.id === `section-${sectionName}`);
    });

    // Update title
    const titles = {
        monitoring: 'Monitoring',
        processes: 'Processus',
        docker: 'Docker',
        files: 'Gestionnaire de fichiers',
        system: 'Contrôles Système'
    };
    document.getElementById('sectionTitle').textContent = titles[sectionName] || sectionName;

    // Load section data
    switch (sectionName) {
        case 'processes':
            loadProcesses();
            break;
        case 'docker':
            loadDockerContainers();
            loadDockerImages();
            break;
        case 'files':
            loadFiles();
            break;
        case 'system':
            loadServices();
            break;
    }
}

// ========================================
// WebSocket & Metrics
// ========================================
function connectWebSocket() {
    setConnectionStatus('connecting');

    ws = new WebSocket(CONFIG.wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            if (message.type === 'metrics') {
                updateMetrics(message.data);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('error');

        const delay = Math.min(30000, CONFIG.reconnectInterval * Math.pow(2, reconnectAttempts));
        reconnectAttempts++;
        setTimeout(connectWebSocket, delay);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
    };
}

function setConnectionStatus(status) {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');

    dot.classList.remove('connected');

    switch (status) {
        case 'connected':
            dot.classList.add('connected');
            text.textContent = 'Connecté';
            break;
        case 'error':
            text.textContent = 'Déconnecté';
            break;
        default:
            text.textContent = 'Connexion...';
    }
}

function updateMetrics(metrics) {
    // CPU
    document.getElementById('cpuValue').textContent = metrics.cpu_percent.toFixed(1);
    updateGauge('cpuGauge', metrics.cpu_percent);

    // RAM
    document.getElementById('ramValue').textContent = metrics.ram_percent.toFixed(1);
    document.getElementById('ramUsed').textContent = metrics.ram_used_gb.toFixed(1);
    document.getElementById('ramTotal').textContent = metrics.ram_total_gb.toFixed(1);
    updateGauge('ramGauge', metrics.ram_percent);

    // Disk
    document.getElementById('diskValue').textContent = metrics.disk_percent.toFixed(1);
    document.getElementById('diskUsed').textContent = metrics.disk_used_gb.toFixed(1);
    document.getElementById('diskTotal').textContent = metrics.disk_total_gb.toFixed(1);
    updateGauge('diskGauge', metrics.disk_percent);

    // Temperature
    if (metrics.cpu_temp !== null) {
        document.getElementById('tempValue').textContent = metrics.cpu_temp.toFixed(1);
        const tempPercent = Math.min(100, Math.max(0, ((metrics.cpu_temp - 30) / 55) * 100));
        document.getElementById('tempMarker').style.left = `${tempPercent}%`;
    }

    // Uptime
    document.getElementById('uptime').textContent = `⏱️ ${metrics.uptime_formatted}`;

    // Alerts
    const alertsBanner = document.getElementById('alertsBanner');
    if (metrics.alerts && metrics.alerts.length > 0) {
        alertsBanner.style.display = 'block';
        document.getElementById('alertsContent').innerHTML =
            metrics.alerts.map(a => `<span class="alert-item">${a}</span>`).join('');
    } else {
        alertsBanner.style.display = 'none';
    }

    // Last update
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

    // Charts
    updateCharts(metrics);
}

function updateGauge(id, value) {
    const gauge = document.getElementById(id);
    gauge.style.width = `${value}%`;
    gauge.className = 'gauge-fill';
    if (value >= 90) gauge.classList.add('danger');
    else if (value >= 70) gauge.classList.add('warning');
}

// ========================================
// Charts
// ========================================
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: { display: false, min: 0, max: 100 }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4, borderWidth: 2 }
        },
        animation: { duration: 300 }
    };

    charts.cpu = new Chart(document.getElementById('cpuChart'), {
        type: 'line',
        data: { labels: [], datasets: [{ data: [], borderColor: '#00d4ff', backgroundColor: 'rgba(0, 212, 255, 0.1)', fill: true }] },
        options: chartOptions
    });

    charts.ram = new Chart(document.getElementById('ramChart'), {
        type: 'line',
        data: { labels: [], datasets: [{ data: [], borderColor: '#7c3aed', backgroundColor: 'rgba(124, 58, 237, 0.1)', fill: true }] },
        options: chartOptions
    });

    charts.temp = new Chart(document.getElementById('tempChart'), {
        type: 'line',
        data: { labels: [], datasets: [{ data: [], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true }] },
        options: { ...chartOptions, scales: { ...chartOptions.scales, y: { display: false, min: 30, max: 85 } } }
    });
}

function updateCharts(metrics) {
    const now = new Date().toLocaleTimeString();

    chartData.labels.push(now);
    chartData.cpu.push(metrics.cpu_percent);
    chartData.ram.push(metrics.ram_percent);
    chartData.temp.push(metrics.cpu_temp || 0);

    if (chartData.labels.length > CONFIG.chartDataPoints) {
        chartData.labels.shift();
        chartData.cpu.shift();
        chartData.ram.shift();
        chartData.temp.shift();
    }

    charts.cpu.data.labels = chartData.labels;
    charts.cpu.data.datasets[0].data = chartData.cpu;
    charts.cpu.update('none');

    charts.ram.data.labels = chartData.labels;
    charts.ram.data.datasets[0].data = chartData.ram;
    charts.ram.update('none');

    charts.temp.data.labels = chartData.labels;
    charts.temp.data.datasets[0].data = chartData.temp;
    charts.temp.update('none');
}

// ========================================
// API Functions
// ========================================
async function fetchSystemInfo() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/system/hostname`);
        const data = await response.json();
        document.getElementById('hostname').textContent = `🖥️ ${data.user}@${data.hostname}`;
    } catch (error) {
        console.error('Error fetching system info:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/metrics/stats?hours=1`);
        const data = await response.json();

        document.getElementById('statCpuAvg').textContent = `${data.cpu.avg}%`;
        document.getElementById('statCpuMax').textContent = `${data.cpu.max}%`;
        document.getElementById('statRamAvg').textContent = `${data.ram.avg}%`;
        document.getElementById('statTempMax').textContent = data.temperature.max ? `${data.temperature.max}°C` : '-';
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// ========================================
// Processes
// ========================================
async function loadProcesses() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/processes/list?limit=30`);
        const processes = await response.json();

        const tbody = document.getElementById('processesBody');
        tbody.innerHTML = processes.map(p => `
            <tr>
                <td>${p.pid}</td>
                <td>${p.name}</td>
                <td>${p.username}</td>
                <td>${p.cpu_percent.toFixed(1)}%</td>
                <td>${p.memory_percent.toFixed(1)}%</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="killProcess(${p.pid}, '${p.name}')">
                        ⛔ Kill
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading processes:', error);
    }
}

async function killProcess(pid, name) {
    if (!confirm(`Tuer le processus "${name}" (PID: ${pid}) ?`)) return;

    try {
        const response = await fetch(`${CONFIG.apiUrl}/processes/kill/${pid}`, { method: 'POST' });
        if (response.ok) {
            alert('Processus terminé');
            loadProcesses();
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

// ========================================
// Docker
// ========================================
function getHostIP() {
    // Get base URL host (without port)
    return window.location.hostname;
}

function parsePortMappings(portsString) {
    if (!portsString) return [];
    const ports = [];
    const matches = portsString.matchAll(/(\d+\.\d+\.\d+\.\d+:)?(\d+)->(\d+)\/(tcp|udp)/g);
    for (const match of matches) {
        ports.push({
            hostPort: match[2],
            containerPort: match[3],
            protocol: match[4]
        });
    }
    return ports;
}

async function loadDockerContainers() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/docker/containers`);
        const containers = await response.json();
        const hostIP = getHostIP();

        const tbody = document.getElementById('dockerBody');
        tbody.innerHTML = containers.map(c => {
            const ports = parsePortMappings(c.ports);
            const portLinks = ports.length > 0
                ? ports.map(p => `<a href="http://${hostIP}:${p.hostPort}" target="_blank" class="port-link">:${p.hostPort} 🔗</a>`).join(' ')
                : '<span style="color: var(--text-muted)">-</span>';

            return `
            <tr>
                <td><code>${c.id}</code></td>
                <td><strong>${c.name}</strong></td>
                <td>${c.image}</td>
                <td>
                    <span class="status-badge ${c.state === 'running' ? 'status-running' : 'status-stopped'}">
                        ${c.state}
                    </span>
                </td>
                <td>${portLinks}</td>
                <td>
                    <div class="docker-actions">
                        ${c.state === 'running'
                    ? `<button class="btn btn-warning btn-sm" onclick="dockerAction('${c.id}', 'stop')" title="Arrêter">⏹️</button>
                               <button class="btn btn-secondary btn-sm" onclick="dockerAction('${c.id}', 'restart')" title="Redémarrer">🔄</button>`
                    : `<button class="btn btn-success btn-sm" onclick="dockerAction('${c.id}', 'start')" title="Démarrer">▶️</button>`
                }
                        <button class="btn btn-danger btn-sm" onclick="deleteContainer('${c.id}', '${c.name}', ${c.state === 'running'})" title="Supprimer">🗑️</button>
                    </div>
                </td>
            </tr>
        `}).join('');
    } catch (error) {
        console.error('Error loading containers:', error);
    }
}

async function loadDockerImages() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/docker/images`);
        const data = await response.json();

        document.getElementById('dockerImages').innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Image</th>
                        <th>Tag</th>
                        <th>Taille</th>
                        <th>Créé</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.images.map(i => `
                        <tr>
                            <td><strong>${i.repository}</strong></td>
                            <td><code>${i.tag}</code></td>
                            <td>${i.size}</td>
                            <td>${i.created}</td>
                            <td>
                                <button class="btn btn-danger btn-sm" onclick="deleteImage('${i.id}', '${i.repository}:${i.tag}')" title="Supprimer">🗑️</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Error loading images:', error);
    }
}

async function dockerAction(containerId, action) {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/docker/container/${containerId}/${action}`, { method: 'POST' });
        if (response.ok) {
            loadDockerContainers();
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

async function deleteContainer(containerId, name, isRunning) {
    const forceMsg = isRunning ? '\n⚠️ Ce conteneur est en cours d\'exécution. Il sera arrêté de force.' : '';
    if (!confirm(`Supprimer le conteneur "${name}" ?${forceMsg}`)) return;

    try {
        const url = isRunning
            ? `${CONFIG.apiUrl}/docker/container/${containerId}?force=true`
            : `${CONFIG.apiUrl}/docker/container/${containerId}`;
        const response = await fetch(url, { method: 'DELETE' });

        if (response.ok) {
            loadDockerContainers();
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

async function deleteImage(imageId, name) {
    if (!confirm(`Supprimer l'image "${name}" ?`)) return;

    try {
        const response = await fetch(`${CONFIG.apiUrl}/docker/image/${imageId}`, { method: 'DELETE' });

        if (response.ok) {
            loadDockerImages();
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

// ========================================
// File Manager
// ========================================
async function loadFiles(path = currentPath) {
    currentPath = path;
    document.getElementById('currentPath').value = path;

    try {
        const response = await fetch(`${CONFIG.apiUrl}/files/list?path=${encodeURIComponent(path)}`);
        const files = await response.json();

        const fileList = document.getElementById('fileList');
        fileList.innerHTML = files.map(f => `
            <div class="file-item ${f.is_dir ? 'directory' : ''}" 
                 onclick="${f.is_dir ? `loadFiles('${f.path}')` : `openFile('${f.path}')`}">
                <span class="file-icon">${f.is_dir ? '📁' : '📄'}</span>
                <span class="file-name">${f.name}</span>
                <span class="file-size">${f.is_dir ? '' : formatSize(f.size)}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function navigateUp() {
    const parts = currentPath.split('/').filter(Boolean);
    parts.pop();
    loadFiles('/' + parts.join('/'));
}

async function openFile(path) {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/files/read?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        editingFile = path;
        document.getElementById('editorFileName').textContent = path;
        document.getElementById('editorContent').value = data.content;
        document.getElementById('fileEditor').style.display = 'flex';
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

async function saveFile() {
    if (!editingFile) return;

    try {
        const content = document.getElementById('editorContent').value;
        const response = await fetch(`${CONFIG.apiUrl}/files/write?path=${encodeURIComponent(editingFile)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            alert('Fichier sauvegardé !');
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }
}

function closeEditor() {
    document.getElementById('fileEditor').style.display = 'none';
    editingFile = null;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

// ========================================
// System Controls
// ========================================
function confirmAction(action) {
    pendingAction = action;

    const modal = document.getElementById('confirmModal');
    const messages = {
        reboot: 'Voulez-vous vraiment REDÉMARRER le Raspberry Pi ?',
        shutdown: 'Voulez-vous vraiment ARRÊTER le Raspberry Pi ?'
    };

    document.getElementById('modalMessage').textContent = messages[action];
    document.getElementById('modalConfirm').onclick = executeAction;
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('confirmModal').classList.remove('active');
    pendingAction = null;
}

async function executeAction() {
    if (!pendingAction) return;

    try {
        const response = await fetch(`${CONFIG.apiUrl}/system/${pendingAction}`, { method: 'POST' });
        if (response.ok) {
            alert(`Action "${pendingAction}" exécutée !`);
        } else {
            const error = await response.json();
            alert(`Erreur: ${error.detail}`);
        }
    } catch (error) {
        alert(`Erreur: ${error.message}`);
    }

    closeModal();
}

async function loadServices() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/system/services`);
        const data = await response.json();

        document.getElementById('servicesList').innerHTML = data.services.slice(0, 10).map(s => `
            <div class="stat-item">
                <span class="stat-label">${s.name}</span>
                <span class="status-badge status-running">${s.active}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

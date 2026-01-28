/**
 * Dashboard Monitoring - JavaScript
 * Real-time metrics display with WebSocket
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
let chartData = {
    cpu: [],
    ram: [],
    temp: [],
    labels: []
};

// DOM Elements
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    statusDot: document.querySelector('.status-dot'),
    statusText: document.querySelector('.status-text'),
    hostname: document.getElementById('hostname'),
    uptime: document.getElementById('uptime'),
    alertsBanner: document.getElementById('alertsBanner'),
    alertsContent: document.getElementById('alertsContent'),
    cpuValue: document.getElementById('cpuValue'),
    cpuGauge: document.getElementById('cpuGauge'),
    ramValue: document.getElementById('ramValue'),
    ramGauge: document.getElementById('ramGauge'),
    ramUsed: document.getElementById('ramUsed'),
    ramTotal: document.getElementById('ramTotal'),
    diskValue: document.getElementById('diskValue'),
    diskGauge: document.getElementById('diskGauge'),
    diskUsed: document.getElementById('diskUsed'),
    diskTotal: document.getElementById('diskTotal'),
    tempValue: document.getElementById('tempValue'),
    tempBar: document.getElementById('tempBar'),
    lastUpdate: document.getElementById('lastUpdate'),
    statCpuAvg: document.getElementById('statCpuAvg'),
    statCpuMax: document.getElementById('statCpuMax'),
    statRamAvg: document.getElementById('statRamAvg'),
    statTempMax: document.getElementById('statTempMax'),
};

// Initialize Charts
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { display: false },
            y: {
                display: false,
                min: 0,
                max: 100
            }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4, borderWidth: 2 }
        },
        animation: { duration: 300 }
    };

    // CPU Chart
    charts.cpu = new Chart(document.getElementById('cpuChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                fill: true
            }]
        },
        options: chartOptions
    });

    // RAM Chart
    charts.ram = new Chart(document.getElementById('ramChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#7b68ee',
                backgroundColor: 'rgba(123, 104, 238, 0.1)',
                fill: true
            }]
        },
        options: chartOptions
    });

    // Temperature Chart
    charts.temp = new Chart(document.getElementById('tempChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#ff6b81',
                backgroundColor: 'rgba(255, 107, 129, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: { display: false, min: 30, max: 85 }
            }
        }
    });
}

// Update chart data
function updateCharts(metrics) {
    const now = new Date().toLocaleTimeString();

    // Add new data
    chartData.labels.push(now);
    chartData.cpu.push(metrics.cpu_percent);
    chartData.ram.push(metrics.ram_percent);
    chartData.temp.push(metrics.cpu_temp || 0);

    // Limit data points
    if (chartData.labels.length > CONFIG.chartDataPoints) {
        chartData.labels.shift();
        chartData.cpu.shift();
        chartData.ram.shift();
        chartData.temp.shift();
    }

    // Update charts
    charts.cpu.data.labels = chartData.labels;
    charts.cpu.data.datasets[0].data = chartData.cpu;
    charts.cpu.update('none');

    charts.ram.data.labels = chartData.labels;
    charts.ram.data.datasets[0].data = chartData.ram;
    charts.ram.update('none');

    if (metrics.cpu_temp) {
        charts.temp.data.labels = chartData.labels;
        charts.temp.data.datasets[0].data = chartData.temp;
        charts.temp.update('none');
    }
}

// Update gauge classes based on value
function getGaugeClass(value) {
    if (value >= 90) return 'danger';
    if (value >= 70) return 'warning';
    return '';
}

// Update metrics display
function updateMetrics(metrics) {
    // CPU
    elements.cpuValue.textContent = metrics.cpu_percent.toFixed(1);
    elements.cpuGauge.style.width = `${metrics.cpu_percent}%`;
    elements.cpuGauge.className = `gauge-fill ${getGaugeClass(metrics.cpu_percent)}`;

    // RAM
    elements.ramValue.textContent = metrics.ram_percent.toFixed(1);
    elements.ramGauge.style.width = `${metrics.ram_percent}%`;
    elements.ramGauge.className = `gauge-fill ${getGaugeClass(metrics.ram_percent)}`;
    elements.ramUsed.textContent = metrics.ram_used_gb.toFixed(1);
    elements.ramTotal.textContent = metrics.ram_total_gb.toFixed(1);

    // Disk
    elements.diskValue.textContent = metrics.disk_percent.toFixed(1);
    elements.diskGauge.style.width = `${metrics.disk_percent}%`;
    elements.diskGauge.className = `gauge-fill ${getGaugeClass(metrics.disk_percent)}`;
    elements.diskUsed.textContent = metrics.disk_used_gb.toFixed(1);
    elements.diskTotal.textContent = metrics.disk_total_gb.toFixed(1);

    // Temperature
    if (metrics.cpu_temp !== null) {
        elements.tempValue.textContent = metrics.cpu_temp.toFixed(1);
        // Map temperature (30-85°C) to percentage (0-100%)
        const tempPercent = Math.min(100, Math.max(0, ((metrics.cpu_temp - 30) / 55) * 100));
        elements.tempBar.style.left = `${tempPercent}%`;
    } else {
        elements.tempValue.textContent = '-';
    }

    // Uptime
    elements.uptime.textContent = `Uptime: ${metrics.uptime_formatted}`;

    // Alerts
    if (metrics.alerts && metrics.alerts.length > 0) {
        elements.alertsBanner.style.display = 'block';
        elements.alertsContent.innerHTML = metrics.alerts
            .map(alert => `<span class="alert-item">${alert}</span>`)
            .join('');
    } else {
        elements.alertsBanner.style.display = 'none';
    }

    // Last update
    elements.lastUpdate.textContent = new Date().toLocaleTimeString();

    // Update charts
    updateCharts(metrics);
}

// Set connection status
function setConnectionStatus(status) {
    elements.statusDot.classList.remove('connected', 'error');

    switch (status) {
        case 'connected':
            elements.statusDot.classList.add('connected');
            elements.statusText.textContent = 'Connecté';
            break;
        case 'error':
            elements.statusDot.classList.add('error');
            elements.statusText.textContent = 'Déconnecté';
            break;
        default:
            elements.statusText.textContent = 'Connexion...';
    }
}

// WebSocket connection
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

        // Reconnect with exponential backoff
        const delay = Math.min(30000, CONFIG.reconnectInterval * Math.pow(2, reconnectAttempts));
        reconnectAttempts++;

        console.log(`Reconnecting in ${delay}ms...`);
        setTimeout(connectWebSocket, delay);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
    };
}

// Fetch system info
async function fetchSystemInfo() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/system`);
        const data = await response.json();
        elements.hostname.textContent = data.hostname;
    } catch (error) {
        console.error('Error fetching system info:', error);
    }
}

// Fetch statistics
async function fetchStats() {
    try {
        const response = await fetch(`${CONFIG.apiUrl}/metrics/stats?hours=1`);
        const data = await response.json();

        elements.statCpuAvg.textContent = `${data.cpu.avg}%`;
        elements.statCpuMax.textContent = `${data.cpu.max}%`;
        elements.statRamAvg.textContent = `${data.ram.avg}%`;
        elements.statTempMax.textContent = data.temperature.max ? `${data.temperature.max}°C` : '-';
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchSystemInfo();
    fetchStats();
    connectWebSocket();

    // Refresh stats periodically
    setInterval(fetchStats, CONFIG.statsRefreshInterval);
});

let isOfflineMode = false;
let heartbeatInterval = null;

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js')
        .then(() => console.log('Service Worker Registered'));
}

async function login() {
    const pin = document.getElementById('pin').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const statusDiv = document.getElementById('login-status');

    if (!pin || !username || !password) {
        statusDiv.innerText = "Lengkapi semua field!";
        return;
    }

    statusDiv.innerText = "Menghubungkan...";
    const result = await ApiService.login(pin, username, password);

    if (result.success) {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('monitoring-container').style.display = 'block';
        
        startMonitoring();
    } else {
        statusDiv.innerText = result.msg;
    }
}

function handleLog(tipeAnomali, deskripsi) {
    if (isOfflineMode) {
        const timeStr = new Date().toLocaleTimeString();
        const logHtml = `<li><span style="color:#e74c3c">[${timeStr}]</span> <b>${tipeAnomali}</b>: ${deskripsi}</li>`;
        document.getElementById('log-list').innerHTML += logHtml;
    } else {
        ApiService.sendLog(tipeAnomali, deskripsi);
    }
}

function startMonitoring() {
    SensorManager.startSensors(handleLog);
    
    heartbeatInterval = setInterval(() => {
        if (!isOfflineMode) ApiService.sendHeartbeat();
    }, 10000); // 10 seconds
}

function startOfflineTest() {
    isOfflineMode = true;
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('monitoring-container').style.display = 'block';
    
    document.getElementById('mode-text').innerText = "Mode Uji Coba Offline berjalan. Log akan tampil di bawah.";
    document.getElementById('monitor-status-text').innerText = "Status: OFFLINE TESTING";
    document.getElementById('offline-logs').style.display = 'block';
    
    startMonitoring();
}

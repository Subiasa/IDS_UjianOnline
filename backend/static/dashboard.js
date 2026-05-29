// Konfigurasi
const API_BASE = '/api/v1';
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/dashboard`;

// State
let participants = {}; 
let globalAnomalies = [];
let currentSelectedPeserta = null;
let ws = null;

// =======================
// INIT & WEBSOCKET
// =======================
async function initDashboard() {
    await refreshData();
    connectWebSocket();
    setupEventListeners();
}

function connectWebSocket() {
    if (ws) ws.close();
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => console.log('Tersambung ke WebSocket Peladen');
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'anomali') {
                handleNewAnomaly(data);
            } else if (data.type === 'heartbeat') {
                handleHeartbeat(data);
            } else if (data.type === 'screenshot') {
                handleScreenshot(data);
            }
        } catch (e) {
            console.error("Gagal memproses pesan WS:", e);
        }
    };
    
    ws.onclose = () => {
        console.log('Koneksi terputus. Mencoba ulang dalam 3 detik...');
        setTimeout(connectWebSocket, 3000);
    };
}

// =======================
// DATA FETCHING
// =======================
async function refreshData() {
    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    const originalContent = refreshBtn ? refreshBtn.innerHTML : null;
    
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Loading...';
    }

    try {
        console.log("Membersihkan dan mengambil data terbaru...");
        participants = {};
        globalAnomalies = [];
        renderTable();
        renderGlobalLog();

        const [partRes, histRes] = await Promise.all([
            fetch(`${API_BASE}/telemetry/participants`),
            fetch(`${API_BASE}/telemetry/history?limit=100`)
        ]);
        
        if (!partRes.ok || !histRes.ok) throw new Error("Gagal mengambil data dari server");

        const partData = await partRes.json();
        const histData = await histRes.json();
        
        if (Array.isArray(partData)) {
            partData.forEach(p => {
                participants[String(p.id)] = { ...p, history: [] };
            });
        }
        
        if (Array.isArray(histData)) {
            [...histData].reverse().forEach(log => {
                const pid = String(log.peserta_id);
                globalAnomalies.unshift(log); 
                if (participants[pid]) {
                    participants[pid].history.unshift(log);
                }
            });
        }
        
        const activeCount = Object.values(participants).filter(p => p.agent_status === 'active').length;
        document.getElementById('total-peserta').textContent = activeCount;
        document.getElementById('total-anomali').textContent = Array.isArray(histData) ? histData.length : 0;
        document.getElementById('selesai-peserta').textContent = Array.isArray(partData) ? partData.length : 0;
        
        renderTable();
        renderGlobalLog();
        
        if (currentSelectedPeserta && participants[currentSelectedPeserta]) {
            openParticipantDetail(currentSelectedPeserta);
        } else if (currentSelectedPeserta) {
            closeModal('modal-participant-detail');
        }

        console.log("Data berhasil disinkronkan.");
    } catch (err) {
        console.error("Gagal refresh:", err);
        customAlert("Gagal sinkronisasi data. Silakan periksa koneksi backend.");
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = originalContent;
        }
    }
}

// =======================
// RENDERING
// =======================
function renderTable() {
    const tbody = document.getElementById('participants-body');
    const searchInput = document.getElementById('search-input');
    const search = searchInput ? searchInput.value.toLowerCase() : '';
    
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const sortedParticipants = Object.values(participants).sort((a, b) => b.id - a.id);

    sortedParticipants.forEach(p => {
        const displayName = p.username || `Peserta ${p.id}`;
        if (search && !displayName.toLowerCase().includes(search)) return;
        
        const statusClass = p.agent_status === 'active' ? 'active' : 'inactive';
        const curangCount = p.history ? p.history.length : 0;
        
        const tr = document.createElement('tr');
        tr.onclick = () => openParticipantDetail(String(p.id));
        tr.style.cursor = 'pointer';
        
        tr.innerHTML = `
            <td><strong>${displayName}</strong></td>
            <td><span class="status-badge ${statusClass}"><i class="ri-checkbox-blank-circle-fill"></i> ${p.agent_status.toUpperCase()}</span></td>
            <td><strong class="text-red">${curangCount}</strong></td>
            <td><span style="color:var(--success)">${p.agent_status === 'active' ? 'Stabil' : '-'}</span></td>
            <td class="actions-cell">
                <button class="btn btn-icon btn-outline-primary" onclick="event.stopPropagation(); requestScreenshot('${p.id}')" title="Intip Layar">
                    <i class="ri-eye-line"></i>
                </button>
                <button class="btn btn-icon btn-outline-warning" onclick="event.stopPropagation(); sendWarning('${p.id}')" title="Beri Peringatan">
                    <i class="ri-error-warning-line"></i>
                </button>
                <button class="btn btn-icon btn-outline-danger" onclick="event.stopPropagation(); deleteParticipant('${p.id}')" title="Hapus Peserta">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderGlobalLog() {
    const ul = document.getElementById('anomaly-list');
    ul.innerHTML = '';
    
    if (globalAnomalies.length === 0) {
        ul.innerHTML = '<li class="empty-state">Belum ada aktivitas.</li>';
        return;
    }
    
    globalAnomalies.slice(0, 20).forEach(log => {
        const li = document.createElement('li');
        li.className = `log-item ${log.tipe_anomali !== 'HEARTBEAT' ? 'severe' : ''}`;
        
        const date = new Date(log.timestamp ? log.timestamp * 1000 : log.created_at);
        const timeStr = date.toLocaleTimeString();
        const desc = log.metadata_log ? log.metadata_log.deskripsi : '';
        
        li.innerHTML = `
            <strong>${log.tipe_anomali}</strong> - Peserta ${log.peserta_id}
            <div class="log-meta">${timeStr}</div>
            <div style="margin-top:4px; font-size:12px;">${desc.substring(0,60)}${desc.length>60?'...':''}</div>
        `;
        ul.appendChild(li);
    });
}

// =======================
// EVENT HANDLERS
// =======================
function handleNewAnomaly(data) {
    const pid = String(data.peserta_id);
    globalAnomalies.unshift(data);
    
    if (participants[pid]) {
        participants[pid].history.unshift(data);
    }
    
    const el = document.getElementById('total-anomali');
    el.textContent = parseInt(el.textContent) + 1;
    
    renderTable();
    renderGlobalLog();
    
    if (currentSelectedPeserta == pid) {
        renderParticipantHistory(pid);
        document.getElementById('pd-total-curang').textContent = participants[pid].history.length;
    }
}

function handleHeartbeat(data) {
    const pid = String(data.peserta_id);
    if (participants[pid]) {
        const wasInactive = participants[pid].agent_status !== 'active';
        participants[pid].agent_status = 'active';
        participants[pid].last_heartbeat = data.timestamp;
        if (wasInactive) {
            renderTable();
            document.getElementById('total-peserta').textContent = Object.values(participants).filter(p => p.agent_status === 'active').length;
        }
    }
}

function handleScreenshot(data) {
    const pid = String(data.peserta_id);
    
    if (data.is_anomaly) {
        if (participants[pid] && participants[pid].history.length > 0) {
            participants[pid].history[0].image_base64 = data.image;
            if (currentSelectedPeserta == pid) renderParticipantHistory(pid);
        }
    } else {
        const onDemandLog = {
            peserta_id: pid,
            tipe_anomali: "TANGKAPAN_LAYAR_MANUAL",
            timestamp: data.timestamp,
            metadata_log: { deskripsi: "Tangkapan layar diminta oleh pengawas." },
            image_base64: data.image
        };
        if (participants[pid]) participants[pid].history.unshift(onDemandLog);
        if (currentSelectedPeserta == pid) {
            renderParticipantHistory(pid);
        } else {
            openImageViewer(`data:image/webp;base64,${data.image}`);
        }
    }
}

function requestScreenshot(pesertaId) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'peek_screen',
            peserta_id: String(pesertaId)
        }));
        console.log(`Requested screenshot for ${pesertaId}`);
    } else {
        customAlert("WebSocket tidak terhubung!");
    }
}

// =======================
// UI & MODALS
// =======================
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('onclick').includes(tabName));
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.dataset.tab === tabName);
    });
}

function setupEventListeners() {
    document.getElementById('search-input').addEventListener('keyup', renderTable);
    
    // Single Account Create
    document.getElementById('form-create-account').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        btn.textContent = "Menyimpan...";
        btn.disabled = true;
        
        try {
            const res = await fetch(`${API_BASE}/auth/create-credential`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pin_sesi: document.getElementById('ca-pin').value,
                    username: document.getElementById('ca-username').value,
                    password: document.getElementById('ca-password').value
                })
            });
            const data = await res.json();
            if (res.ok) {
                customAlert("Akun berhasil dibuat!");
                closeModal('modal-create-account');
                refreshData();
                e.target.reset();
            } else {
                customAlert("Gagal: " + (data.detail || "Error tak dikenal"));
            }
        } catch (err) {
            customAlert("Terjadi kesalahan jaringan.");
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });

    // Bulk Account Create
    document.getElementById('form-bulk-create-account').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        btn.textContent = "Memproses...";
        btn.disabled = true;
        
        try {
            const res = await fetch(`${API_BASE}/auth/bulk-create-credential`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pin_sesi: document.getElementById('ba-pin').value,
                    count: parseInt(document.getElementById('ba-count').value),
                    password_default: document.getElementById('ba-password').value
                })
            });
            const data = await res.json();
            if (res.ok) {
                customAlert(data.message + "\n\nUser: " + data.users.join(", "));
                closeModal('modal-create-account');
                refreshData();
                e.target.reset();
            } else {
                customAlert("Gagal: " + (data.detail || "Error tak dikenal"));
            }
        } catch (err) {
            customAlert("Terjadi kesalahan jaringan.");
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });
    
    document.getElementById('btn-intip-layar').addEventListener('click', () => {
        if(currentSelectedPeserta) requestScreenshot(currentSelectedPeserta);
    });
    
    document.getElementById('btn-beri-peringatan').addEventListener('click', () => {
        if(currentSelectedPeserta) sendWarning(currentSelectedPeserta);
    });
}

function openCreateAccountModal() {
    document.getElementById('modal-create-account').classList.add('active');
}

function openParticipantDetail(pesertaId) {
    const pid = String(pesertaId);
    currentSelectedPeserta = pid;
    const p = participants[pid];
    if(!p) return;
    
    document.getElementById('pd-name').textContent = p.username || `Peserta ${p.id}`;
    document.getElementById('pd-status').textContent = p.agent_status.toUpperCase();
    document.getElementById('pd-total-curang').textContent = p.history.length;
    
    renderParticipantHistory(pid);
    
    document.getElementById('modal-participant-detail').classList.add('active');
}

function renderParticipantHistory(pesertaId) {
    const pid = String(pesertaId);
    const listEl = document.getElementById('pd-history-list');
    listEl.innerHTML = '';
    
    const history = participants[pid] ? participants[pid].history : [];
    if (history.length === 0) {
        listEl.innerHTML = '<div class="empty-state">Belum ada kecurangan tercatat.</div>';
        return;
    }
    
    history.forEach(log => {
        const div = document.createElement('div');
        div.className = 'anomaly-card';
        
        const date = new Date(log.timestamp ? log.timestamp * 1000 : log.created_at || Date.now());
        const timeStr = date.toLocaleString();
        const desc = log.metadata_log ? log.metadata_log.deskripsi : '';
        
        let imgHtml = '';
        if (log.image_base64) {
            imgHtml = `
            <div class="anomaly-image-container" onclick="openImageViewer('data:image/webp;base64,${log.image_base64}')">
                <img src="data:image/webp;base64,${log.image_base64}" alt="Bukti Pelanggaran" loading="lazy">
            </div>`;
        }
        
        div.innerHTML = `
            <div class="anomaly-card-header">
                <span class="anomaly-type"><i class="ri-error-warning-fill"></i> ${log.tipe_anomali}</span>
                <span class="anomaly-time">${timeStr}</span>
            </div>
            <div class="anomaly-desc">${desc}</div>
            ${imgHtml}
        `;
        listEl.appendChild(div);
    });
}

function openImageViewer(src) {
    document.getElementById('viewer-image').src = src;
    document.getElementById('modal-image-viewer').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    if (modalId === 'modal-participant-detail') {
        currentSelectedPeserta = null;
    }
}

// Kickoff
initDashboard();

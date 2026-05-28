const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
let ws;

// State
let participants = new Map();
let totalAnomalies = 0;

function connectWebSocket() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Connected to HIDS WebSocket');
        // Clear empty state if reconnecting
        const list = document.getElementById('anomaly-list');
        if (list.innerHTML.includes('empty-state')) {
            list.innerHTML = '';
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        ws.close();
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'anomali') {
        addAnomalyToFeed(data);
        incrementAnomalyCount();
        updateParticipantStatus(data.peserta_id, 'active', null, true); // true = is anomaly
    } else if (data.type === 'heartbeat') {
        updateParticipantStatus(data.peserta_id, 'active', data.timestamp);
    }
}

function addAnomalyToFeed(anomaly) {
    const list = document.getElementById('anomaly-list');
    
    // Remove empty state if present
    const emptyState = list.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const li = document.createElement('li');
    const date = new Date(anomaly.timestamp * 1000);
    const timeString = date.toLocaleTimeString('id-ID');
    const dateString = date.toLocaleDateString('id-ID');

    // Determine description based on metadata
    let desc = anomaly.metadata_log.description || JSON.stringify(anomaly.metadata_log);
    
    li.innerHTML = `
        <div class="log-icon"><div class="log-icon-dot"></div></div>
        <div class="log-details">
            <div class="log-text"><strong>${anomaly.tipe_anomali}</strong> - Peserta ${anomaly.peserta_id} ${desc ? ': ' + desc : ''}</div>
            <div class="log-date">${dateString} ${timeString}</div>
        </div>
    `;

    // Add to top of list
    list.prepend(li);

    // Keep list manageable
    if (list.children.length > 50) {
        list.removeChild(list.lastChild);
    }
}

function incrementAnomalyCount() {
    totalAnomalies++;
    document.getElementById('total-anomali').innerText = totalAnomalies;
}

function generateMockData() {
    return {
        jawaban: Math.floor(Math.random() * 40) + 10,
        latency: Math.floor(Math.random() * 40) + 5
    };
}

function updateParticipantStatus(id, status, timestamp, isAnomaly = false) {
    if (!participants.has(id)) {
        const mock = generateMockData();
        participants.set(id, { 
            status: status, 
            anomalies: isAnomaly ? 1 : 0,
            jawaban: mock.jawaban,
            latency: mock.latency
        });
        document.getElementById('total-peserta').innerText = participants.size;
    } else {
        const p = participants.get(id);
        p.status = status;
        if (isAnomaly) p.anomalies++;
        // Update latency randomly to simulate ping
        if (timestamp) {
             p.latency = Math.floor(Math.random() * 40) + 5;
        }
        participants.set(id, p);
    }
    renderParticipants();
}

function renderParticipants() {
    const tbody = document.getElementById('participants-body');
    tbody.innerHTML = '';
    
    participants.forEach((data, id) => {
        const tr = document.createElement('tr');
        const curangClass = data.anomalies > 0 ? 'curang-red' : '';
        const statusText = data.status === 'active' ? 'Mengerjakan' : 'Offline';
        
        tr.innerHTML = `
            <td>1 DPS TKJ ${id}</td>
            <td>${data.jawaban}/50</td>
            <td class="${curangClass}">${data.anomalies}</td>
            <td>
                <span class="status-pill">
                    <span class="status-dot"></span> ${statusText}
                </span>
            </td>
            <td class="latency-green">${data.latency}ms</td>
            <td>-</td>
        `;
        tbody.appendChild(tr);
    });
}

async function fetchInitialData() {
    try {
        const [participantsRes, historyRes] = await Promise.all([
            fetch('/api/v1/telemetry/participants'),
            fetch('/api/v1/telemetry/history?limit=50')
        ]);
        
        if (participantsRes.ok) {
            const pData = await participantsRes.json();
            pData.forEach(p => {
                let timestamp = null;
                if (p.last_heartbeat) {
                    timestamp = new Date(p.last_heartbeat).getTime() / 1000;
                }
                updateParticipantStatus(p.id, p.agent_status, timestamp);
            });
        }
        
        if (historyRes.ok) {
            const hData = await historyRes.json();
            hData.reverse().forEach(a => {
                a.timestamp = new Date(a.created_at).getTime() / 1000;
                if (!a.metadata_log) a.metadata_log = {};
                addAnomalyToFeed(a);
                incrementAnomalyCount();
                
                // Track anomaly per user in state
                if (participants.has(a.peserta_id)) {
                    const p = participants.get(a.peserta_id);
                    p.anomalies++;
                    participants.set(a.peserta_id, p);
                }
            });
            renderParticipants(); // Re-render to show updated anomaly counts
        }
    } catch (e) {
        console.error("Gagal mengambil data awal:", e);
    }
}

// Search functionality
document.getElementById('search-input')?.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#participants-body tr');
    
    rows.forEach(row => {
        const name = row.cells[0].textContent.toLowerCase();
        if (name.includes(term)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await fetchInitialData();
    connectWebSocket();
});

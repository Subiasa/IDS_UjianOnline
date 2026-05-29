// =======================
// CUSTOM ALERTS
// =======================
let alertCallback = null;

function customAlert(message, title = "Info") {
    document.getElementById('alert-title').textContent = title;
    document.getElementById('alert-message').textContent = message;
    document.getElementById('alert-btn-cancel').style.display = 'none';
    document.getElementById('alert-btn-confirm').textContent = 'OK';
    document.getElementById('alert-btn-confirm').onclick = () => closeModal('modal-alert');
    document.getElementById('modal-alert').classList.add('active');
}

function customConfirm(message, confirmCallback, title = "Konfirmasi") {
    document.getElementById('alert-title').textContent = title;
    document.getElementById('alert-message').textContent = message;
    document.getElementById('alert-btn-cancel').style.display = 'inline-flex';
    document.getElementById('alert-btn-confirm').textContent = 'Ya';
    alertCallback = confirmCallback;
    document.getElementById('modal-alert').classList.add('active');
}

function handleAlertConfirm() {
    if (alertCallback) alertCallback();
    closeModal('modal-alert');
    alertCallback = null;
}

// =======================
// RE-IMPLEMENTED ACTIONS
// =======================
function sendWarning(pesertaId) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const msg = prompt("Masukkan pesan peringatan untuk peserta:");
        if (msg) {
            ws.send(JSON.stringify({
                action: 'send_warning',
                peserta_id: String(pesertaId),
                message: msg
            }));
            customAlert("Peringatan terkirim.");
        }
    } else {
        customAlert("WebSocket tidak terhubung!");
    }
}

function deleteParticipant(pesertaId) {
    deleteParticipantConfirm(pesertaId);
}

function deleteParticipantConfirm(pesertaId) {
    customConfirm(`Apakah Anda yakin ingin menghapus Peserta ${pesertaId} dan semua datanya?`, async () => {
        try {
            const res = await fetch(`${API_BASE}/telemetry/participants/${pesertaId}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (res.ok) {
                customAlert(data.message);
                refreshData();
            } else {
                customAlert("Gagal menghapus: " + (data.detail || "Error tak dikenal"));
            }
        } catch (err) {
            customAlert("Kesalahan jaringan saat menghapus peserta.");
        }
    });
}

function resetAllData() {
    resetAllDataConfirm();
}

function resetAllDataConfirm() {
    customConfirm("PERINGATAN! Tindakan ini akan menghapus SEMUA log kecurangan peserta secara permanen. Data peserta akan tetap ada. Lanjutkan?", async () => {
        const reason = prompt("Ketik 'RESET' untuk mengonfirmasi:");
        if (reason !== 'RESET') return;

        try {
            const res = await fetch(`${API_BASE}/telemetry/reset-all`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                customAlert(data.message);
                refreshData();
            } else {
                customAlert("Gagal reset: " + (data.detail || "Error tak dikenal"));
            }
        } catch (err) {
            customAlert("Kesalahan jaringan saat meriset data.");
        }
    });
}

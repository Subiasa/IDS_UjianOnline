const API_URL = '/api/v1'; // Served from the same backend
const AGENT_SECRET = 'kunci_rahasia_hmac_untuk_agen_desktop_dan_mobile';

const ApiService = {
    sessionToken: null,
    pesertaId: null,

    async generateSignature(payloadStr) {
        const encoder = new TextEncoder();
        const keyData = encoder.encode(AGENT_SECRET);
        const cryptoKey = await crypto.subtle.importKey(
            'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
        );
        const signatureBuffer = await crypto.subtle.sign('HMAC', cryptoKey, encoder.encode(payloadStr));
        const signatureArray = Array.from(new Uint8Array(signatureBuffer));
        return signatureArray.map(b => b.toString(16).padStart(2, '0')).join('');
    },

    async login(pin, username, password) {
        try {
            const response = await fetch(`${API_URL}/auth/agent-login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin_sesi: pin, username: username, password: password })
            });

            if (response.ok) {
                const data = await response.json();
                this.sessionToken = data.access_token;
                this.pesertaId = data.peserta_id;
                return { success: true };
            } else {
                const err = await response.json();
                return { success: false, msg: err.detail || "Kesalahan server" };
            }
        } catch (e) {
            return { success: false, msg: "Koneksi ke server gagal." };
        }
    },

    async sendLog(tipeAnomali, deskripsi) {
        if (!this.pesertaId) return;

        const payload = {
            peserta_id: this.pesertaId,
            tipe_anomali: tipeAnomali,
            metadata_log: { deskripsi: deskripsi },
            timestamp: Date.now() / 1000
        };

        const rawPayload = JSON.stringify(payload);
        const signature = await this.generateSignature(rawPayload);

        try {
            const res = await fetch(`${API_URL}/telemetry/log`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Signature': signature
                },
                body: rawPayload
            });
            if (!res.ok) throw new Error("Server error");
        } catch (e) {
            console.error("Gagal mengirim log, menyimpan ke antrean offline:", e);
            // Simpan ke localStorage untuk offline queue
            this.saveOfflineLog(payload);
        }
    },

    async sendHeartbeat() {
        if (!this.pesertaId) return;
        const payload = { peserta_id: this.pesertaId, timestamp: Date.now() / 1000 };
        const rawPayload = JSON.stringify(payload);
        const signature = await this.generateSignature(rawPayload);

        fetch(`${API_URL}/telemetry/heartbeat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Signature': signature
            },
            body: rawPayload
        }).catch(e => console.error("Heartbeat gagal:", e));
    },

    saveOfflineLog(payload) {
        let logs = JSON.parse(localStorage.getItem('offline_logs') || '[]');
        logs.push(payload);
        localStorage.setItem('offline_logs', JSON.stringify(logs));
    },

    async syncOfflineLogs() {
        let logs = JSON.parse(localStorage.getItem('offline_logs') || '[]');
        if (logs.length === 0) return;

        console.log(`Mensinkronisasi ${logs.length} log offline...`);
        let failedLogs = [];

        for (const payload of logs) {
            const rawPayload = JSON.stringify(payload);
            const signature = await this.generateSignature(rawPayload);
            try {
                const res = await fetch(`${API_URL}/telemetry/log`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Signature': signature
                    },
                    body: rawPayload
                });
                if (!res.ok) failedLogs.push(payload);
            } catch (e) {
                failedLogs.push(payload);
            }
        }
        
        localStorage.setItem('offline_logs', JSON.stringify(failedLogs));
    }
};

// Check for network connection and sync logs automatically
window.addEventListener('online', () => {
    ApiService.syncOfflineLogs();
});

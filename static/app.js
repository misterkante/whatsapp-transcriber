// Tout le texte venant des fichiers ou de l'historique est inséré via textContent,
// jamais via innerHTML : un nom de fichier ne peut pas injecter de HTML.

const $ = (id) => document.getElementById(id);
const dropzone = $('dropzone');
const fileInput = $('fileInput');
const queueEl = $('queue');
const transcribeBtn = $('transcribeBtn');
const resultsList = $('resultsList');
const emptyState = $('emptyState');
const searchInput = $('searchInput');
const template = $('itemTemplate');

const AUDIO_EXT = /\.(ogg|opus|wav|mp3|m4a|aac)$/i;

let queue = [];      // [{ file, status, el }]
let historyData = [];
let busy = false;

// --- Sélection des fichiers ---------------------------------------------

fileInput.addEventListener('change', () => addFiles(fileInput.files));

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('over');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('over'));
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('over');
    addFiles(e.dataTransfer.files);
});

function addFiles(fileList) {
    if (busy) return;
    const files = Array.from(fileList).filter(f => f.type.startsWith('audio/') || AUDIO_EXT.test(f.name));
    queue = queue.filter(q => q.status === 'pending');
    for (const file of files) queue.push({ file, status: 'pending' });
    fileInput.value = '';
    renderQueue();
}

function renderQueue() {
    queueEl.replaceChildren(...queue.map(q => {
        const li = document.createElement('li');
        const name = document.createElement('span');
        name.className = 'name';
        name.textContent = q.file.name;
        const status = document.createElement('span');
        status.className = 'status';
        li.append(name, status);
        q.el = status;
        setStatus(q, q.status, q.message);
        return li;
    }));
    transcribeBtn.disabled = busy || !queue.some(q => q.status === 'pending');
}

function setStatus(q, status, message) {
    q.status = status;
    q.message = message;
    const labels = {
        pending: `${(q.file.size / 1024).toFixed(0)} Ko`,
        running: 'transcription…',
        done: 'terminé',
        error: message || 'erreur',
    };
    q.el.textContent = labels[status];
    q.el.className = 'status' + (status === 'done' ? ' ok' : status === 'error' ? ' error' : '');
    q.el.title = status === 'error' ? message || '' : '';
}

// --- Transcription : un fichier par requête, pour suivre l'avancement ----

transcribeBtn.addEventListener('click', async () => {
    busy = true;
    transcribeBtn.disabled = true;
    const model = $('modelSelect').value;
    const language = $('languageSelect').value;
    let ok = 0;

    for (const q of queue.filter(q => q.status === 'pending')) {
        setStatus(q, 'running');
        const form = new FormData();
        form.append('files', q.file);
        form.append('model_name', model);
        form.append('language', language);
        try {
            const res = await fetch('/api/transcribe', { method: 'POST', body: form });
            const body = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
            setStatus(q, 'done');
            ok++;
            await fetchHistory();
        } catch (err) {
            setStatus(q, 'error', err.message);
        }
    }

    busy = false;
    renderQueue();
    if (ok) showToast(ok > 1 ? `${ok} notes transcrites` : 'Note transcrite');
});

// --- Historique ----------------------------------------------------------

async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        historyData = await res.json();
    } catch (err) {
        console.error(err);
        historyData = [];
    }
    renderResults();
}

function formatTime(seconds) {
    const s = Math.floor(seconds);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function renderResults() {
    const query = searchInput.value.trim().toLowerCase();
    const items = historyData.filter(i =>
        !query || i.filename.toLowerCase().includes(query) || i.text.toLowerCase().includes(query)
    );

    emptyState.hidden = items.length > 0;
    emptyState.textContent = historyData.length ? 'Aucun résultat.' : "Aucune transcription pour l'instant.";

    resultsList.replaceChildren(...items.map(item => {
        const node = template.content.firstElementChild.cloneNode(true);
        const id = encodeURIComponent(item.id);
        node.dataset.id = item.id;
        node.querySelector('.filename').textContent = item.filename;
        node.querySelector('.meta').textContent =
            `${item.timestamp} · ${item.model} · ${item.language || '?'} · ${item.duration_proc} s`;
        node.querySelector('audio').src = `/api/audio/${id}`;
        node.querySelector('.text').textContent = item.text || '(aucune parole détectée)';
        for (const a of node.querySelectorAll('a[data-export]')) {
            a.href = `/api/export/${id}?format=${a.dataset.export}`;
            a.setAttribute('download', '');
        }

        const segments = item.segments || [];
        const details = node.querySelector('details');
        if (segments.length) {
            details.querySelector('.segments').replaceChildren(...segments.map(s => {
                const li = document.createElement('li');
                const time = document.createElement('time');
                time.textContent = formatTime(s.start);
                const text = document.createElement('span');
                text.textContent = s.text;
                li.append(time, text);
                return li;
            }));
        } else {
            details.remove();
        }
        return node;
    }));
}

resultsList.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const id = btn.closest('.item').dataset.id;
    const item = historyData.find(i => i.id === id);
    if (!item) return;

    if (btn.dataset.action === 'copy') {
        await navigator.clipboard.writeText(item.text);
        showToast('Texte copié');
    } else if (btn.dataset.action === 'delete') {
        if (!confirm(`Supprimer « ${item.filename} » ?`)) return;
        await fetch(`/api/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
        fetchHistory();
    }
});

searchInput.addEventListener('input', renderResults);

let toastTimer;
function showToast(message) {
    const toast = $('toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

fetchHistory();

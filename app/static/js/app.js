/* MoM AI — no build step, no CDN. */

const TERMINAL = new Set(['completed', 'failed', 'cancelled']);

function csrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

/* ── Toasts ─────────────────────────────────────────────── */

const TOAST_ICON = {
  success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  error: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
};

function showToast(message, category = 'info', duration = 5000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const type = category === 'danger' ? 'error' : (TOAST_ICON[category] ? category : 'info');

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <svg class="toast-icon toast-icon-${type}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${TOAST_ICON[type]}"/>
    </svg>
    <p class="toast-message"></p>
    <button class="toast-close" aria-label="Dismiss">
      <svg style="width:1rem;height:1rem" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>`;
  toast.querySelector('.toast-message').textContent = message;

  const dismiss = () => {
    clearTimeout(toast._timer);
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 200);
  };
  toast.querySelector('.toast-close').addEventListener('click', dismiss);
  container.appendChild(toast);
  toast._timer = setTimeout(dismiss, duration);
}

document.addEventListener('DOMContentLoaded', () => {
  const flash = document.getElementById('flash-data');
  if (!flash) return;
  for (const [category, message] of JSON.parse(flash.textContent)) showToast(message, category);
});

/* ── Upload ─────────────────────────────────────────────── */

function uploadForm() {
  return {
    allowed: [],
    maxMb: 0,
    file: null,
    dragging: false,
    uploading: false,
    percent: 0,

    get sizeLabel() {
      return this.file ? formatBytes(this.file.size) : '';
    },

    handleDrop(event) {
      this.dragging = false;
      if (event.dataTransfer.files.length) this.setFile(event.dataTransfer.files[0]);
    },

    setFile(file) {
      if (!file) return;
      const extension = (file.name.split('.').pop() || '').toLowerCase();
      if (!this.allowed.includes(extension)) {
        showToast(`That file type is not supported. Allowed: ${this.allowed.join(', ')}.`, 'error');
        return;
      }
      if (file.size > this.maxMb * 1024 * 1024) {
        showToast(`That file is ${formatBytes(file.size)}. The limit is ${this.maxMb} MB.`, 'error');
        return;
      }
      this.file = file;

      const transfer = new DataTransfer();
      transfer.items.add(file);
      this.$refs.fileInput.files = transfer.files;

      const title = document.getElementById('title');
      if (title && !title.value) title.value = file.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ');
    },

    clear() {
      this.file = null;
      this.$refs.fileInput.value = '';
    },

    init() {
      this.allowed = (this.$el.dataset.allowed || '').split(',').filter(Boolean);
      this.maxMb = Number(this.$el.dataset.maxMb) || 0;
      this.$el.addEventListener('submit', (event) => {
        if (!this.file || this.uploading) return;
        event.preventDefault();
        this.send();
      });
    },

    send() {
      this.uploading = true;
      this.percent = 0;

      const request = new XMLHttpRequest();
      request.open('POST', this.$el.action);
      request.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) this.percent = Math.round((event.loaded / event.total) * 100);
      });
      request.addEventListener('load', () => {
        if (request.status >= 200 && request.status < 400) {
          window.location = request.responseURL || '/meetings/';
        } else {
          this.uploading = false;
          showToast(
            request.status === 413
              ? `That file is larger than the ${this.maxMb} MB limit.`
              : `Upload failed (HTTP ${request.status}).`,
            'error',
          );
        }
      });
      request.addEventListener('error', () => {
        this.uploading = false;
        showToast('Upload failed. Check that the app is still running.', 'error');
      });
      request.send(new FormData(this.$el));
    },
  };
}

function formatBytes(bytes) {
  if (!bytes) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${unit === 0 ? value : value.toFixed(1)} ${units[unit]}`;
}

/* ── Status polling ─────────────────────────────────────── */

function pollStatuses(ids, statuses) {
  const active = ids.filter((_, index) => !TERMINAL.has(statuses[index]));
  if (!active.length) return;

  const pending = new Set(active);
  const timer = setInterval(async () => {
    for (const id of [...pending]) {
      const data = await fetchStatus(id);
      if (!data) continue;

      const badge = document.querySelector(`[data-status-badge="${id}"]`);
      if (badge) {
        badge.textContent = capitalise(data.status);
        badge.className = `status-badge status-${data.status}`;
      }
      if (TERMINAL.has(data.status)) pending.delete(id);
    }
    if (!pending.size) clearInterval(timer);
  }, 4000);
}

function trackMeeting(id, status) {
  if (TERMINAL.has(status)) return;

  const timer = setInterval(async () => {
    const data = await fetchStatus(id);
    if (!data) return;

    setText('progress-pct', `${data.progress}%`);
    setText('progress-label', `${capitalise(data.status)}…`);
    setText('status-label', capitalise(data.status));

    const bar = document.getElementById('progress-bar');
    if (bar) bar.style.width = `${data.progress}%`;

    const badge = document.getElementById('status-badge');
    if (badge) badge.className = `status-badge status-${data.status} text-sm px-3 py-1.5`;

    renderEvents(data.events);

    if (TERMINAL.has(data.status)) {
      clearInterval(timer);
      setTimeout(() => window.location.reload(), 700);
    }
  }, 3000);
}

async function fetchStatus(id) {
  try {
    const response = await fetch(`/api/v1/meetings/${id}/status`);
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

function renderEvents(events) {
  const list = document.getElementById('event-list');
  if (!list || !events) return;

  list.replaceChildren(...events.map((event) => {
    const item = document.createElement('li');
    item.className = 'flex items-start gap-3 px-6 py-3';

    const dot = document.createElement('span');
    dot.className = `event-dot event-${event.level}`;

    const message = document.createElement('span');
    message.className = `text-sm flex-1 ${event.level === 'error' ? 'text-red-600' : 'text-gray-700'}`;
    message.textContent = event.message;

    const time = document.createElement('span');
    time.className = 'text-xs text-gray-400 flex-shrink-0';
    time.textContent = event.at ? new Date(event.at).toLocaleTimeString() : '';

    item.append(dot, message, time);
    return item;
  }));
}

/* ── Settings helpers ───────────────────────────────────── */

function applyPreset(select, urlField, modelField) {
  const option = select.selectedOptions[0];
  if (!option?.value) return;
  document.getElementById(urlField).value = option.value;

  const model = document.getElementById(modelField);
  if (model && !model.value) model.value = option.dataset.model || '';
}

async function testProvider(group, button) {
  const result = document.querySelector(`[data-test-result="${group}"]`);
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = 'Testing…';
  result.textContent = '';
  result.className = 'text-sm truncate';

  try {
    const response = await fetch(`/admin/settings/test/${group}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
      body: new FormData(button.closest('form')),
    });
    const data = await response.json();
    result.textContent = data.message;
    result.className = `text-sm truncate ${data.ok ? 'text-green-600' : 'text-red-600'}`;
    if (!data.ok) showToast(data.message, 'error', 9000);
  } catch (error) {
    result.textContent = 'The test could not be run.';
    result.className = 'text-sm truncate text-red-600';
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

function promptPassword(form) {
  const password = window.prompt('New password (at least 8 characters):');
  if (!password) return false;
  form.querySelector('input[name="password"]').value = password;
  return true;
}

/* ── Misc ───────────────────────────────────────────────── */

function copyElement(id) {
  const element = document.getElementById(id);
  if (!element) return;
  navigator.clipboard.writeText(element.innerText || element.textContent)
    .then(() => showToast('Copied to clipboard.', 'success', 2500))
    .catch(() => showToast('Your browser blocked the copy.', 'error'));
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function capitalise(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

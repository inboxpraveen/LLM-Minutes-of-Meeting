/* ────────────────────────────────────────────────────────────
   MoM AI — App JavaScript
──────────────────────────────────────────────────────────── */

// ── Alpine.js component for the main shell ──────────────────
function appShell() {
  return {
    sidebarOpen: false,
  };
}

// ── Alpine.js component for upload form ─────────────────────
function uploadForm() {
  return {
    selectedFile: null,
    dragging: false,
    uploading: false,

    handleDrop(event) {
      this.dragging = false;
      const files = event.dataTransfer.files;
      if (files.length > 0) this.setFile(files[0]);
    },

    handleFileSelect(event) {
      const files = event.target.files;
      if (files.length > 0) this.setFile(files[0]);
    },

    setFile(file) {
      const allowed = ['mp4','mp3','wav','m4a','webm','ogg','mkv'];
      const ext = file.name.split('.').pop().toLowerCase();
      if (!allowed.includes(ext)) {
        showToast('File type not supported. Allowed: ' + allowed.join(', '), 'error');
        return;
      }
      this.selectedFile = file;
      // Auto-fill title from filename
      const titleInput = document.getElementById('title');
      if (titleInput && !titleInput.value) {
        titleInput.value = file.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ');
      }
    },

    clearFile() {
      this.selectedFile = null;
      const fileInput = this.$refs.fileInput;
      if (fileInput) fileInput.value = '';
    },

    formatFileSize(bytes) {
      if (!bytes) return '';
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / 1048576).toFixed(1) + ' MB';
    },
  };
}

// ── Toast notification system ───────────────────────────────
const TOAST_ICONS = {
  success: `<svg class="toast-icon toast-icon-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>`,
  error: `<svg class="toast-icon toast-icon-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>`,
  info: `<svg class="toast-icon toast-icon-info" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>`,
  warning: `<svg class="toast-icon toast-icon-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
  </svg>`,
};

function showToast(message, category = 'info', duration = 4500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  // Normalise Flask category names
  const type = category === 'danger' ? 'error' : (category || 'info');

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    ${TOAST_ICONS[type] || TOAST_ICONS.info}
    <div class="toast-body">
      <p class="toast-message">${escapeHtml(message)}</p>
    </div>
    <button class="toast-close" aria-label="Close">
      <svg style="width:1rem;height:1rem" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => dismissToast(toast));

  container.appendChild(toast);

  const timer = setTimeout(() => dismissToast(toast), duration);
  toast._timer = timer;
}

function dismissToast(toast) {
  clearTimeout(toast._timer);
  toast.classList.add('toast-out');
  setTimeout(() => toast.remove(), 220);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Status polling for meetings list ────────────────────────
function startPolling(meetingIds) {
  if (!meetingIds || meetingIds.length === 0) return;

  const active = new Set(meetingIds);
  const TERMINAL = new Set(['completed', 'failed']);

  const poll = setInterval(async () => {
    for (const id of [...active]) {
      try {
        const resp = await fetch(`/api/v1/meetings/${id}/status`);
        if (!resp.ok) continue;
        const data = await resp.json();

        // Update status badge in table row
        const statusEl = document.getElementById(`status-${id}`);
        const labelEl = document.querySelector(`.label-${id}`);
        if (statusEl && labelEl) {
          labelEl.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
          statusEl.className = `status-badge status-${data.status}`;
        }

        if (TERMINAL.has(data.status)) {
          active.delete(id);
          if (data.status === 'completed') {
            showToast('Meeting processing completed!', 'success');
          }
        }
      } catch (e) { /* network error — ignore */ }
    }

    if (active.size === 0) clearInterval(poll);
  }, 4000);
}

// ── Copy to clipboard helper ────────────────────────────────
function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success', 2500);
  }).catch(() => {
    showToast('Failed to copy.', 'error');
  });
}

// ── Upload form: show spinner on submit ──────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', () => {
      const btn = document.getElementById('submit-btn');
      if (btn) {
        // Trigger Alpine uploading state
        const alpineEl = uploadForm.closest('[x-data]') || uploadForm;
        if (alpineEl._x_dataStack) {
          const data = alpineEl._x_dataStack[0];
          if (data) data.uploading = true;
        }
      }
    });
  }
});

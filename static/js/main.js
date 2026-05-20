/* ═══════════════════════════════════════════════════════════
   Gujarat Police Feedback System — Main JS
═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Sidebar Toggle ─────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      if (window.innerWidth <= 992) {
        sidebar.classList.toggle('open');
      } else {
        sidebar.classList.toggle('collapsed');
        document.querySelector('.main-content')?.classList.toggle('full');
      }
    });
    // Close on outside click (mobile)
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 992 && sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Theme Toggle ───────────────────────────────────────────
  const themeToggle = document.getElementById('themeToggle');
  const html = document.documentElement;
  const savedTheme = localStorage.getItem('gp-theme') || 'light';
  html.setAttribute('data-theme', savedTheme);
  if (themeToggle) {
    updateThemeIcon(savedTheme);
    themeToggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      html.setAttribute('data-theme', next);
      localStorage.setItem('gp-theme', next);
      updateThemeIcon(next);
    });
  }
  function updateThemeIcon(theme) {
    const icon = themeToggle?.querySelector('i');
    if (icon) icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
  }

  // ── Auto-dismiss toasts ────────────────────────────────────
  document.querySelectorAll('.toast.show').forEach(toast => {
    setTimeout(() => {
      new bootstrap.Toast(toast).hide();
    }, 4000);
  });

  // ── Intersection Observer for animate-up ──────────────────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        entry.target.style.opacity = '1';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.animate-up').forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });

  // ── Notification bell ─────────────────────────────────────
  const notifBtn = document.getElementById('notifBtn');
  if (notifBtn) {
    notifBtn.addEventListener('click', () => {
      fetch('/api/notifications/mark-read', { method: 'POST' })
        .then(() => {
          const badge = notifBtn.querySelector('.notif-badge');
          if (badge) badge.remove();
        });
    });
  }

  // ── Table search highlight ─────────────────────────────────
  const searchInput = document.querySelector('input[name="search"]');
  if (searchInput && searchInput.value) {
    const val = searchInput.value.toLowerCase();
    document.querySelectorAll('.gp-table tbody td').forEach(td => {
      const text = td.textContent.toLowerCase();
      if (text.includes(val) && !td.querySelector('button')) {
        td.innerHTML = td.innerHTML.replace(
          new RegExp(`(${val})`, 'gi'),
          '<mark style="background:#fff3cd;padding:0 2px;border-radius:2px">$1</mark>'
        );
      }
    });
  }
});

// Global toast helper
window.showToast = function(msg, type = 'success') {
  const container = document.querySelector('.toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast show align-items-center text-white bg-${type} border-0`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toast);
  setTimeout(() => { new bootstrap.Toast(toast).hide(); toast.remove(); }, 4000);
};

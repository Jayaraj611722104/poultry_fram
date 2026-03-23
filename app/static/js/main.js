// Language Management
let currentLang = localStorage.getItem('lang') || 'en';

function applyLanguage(lang) {
  document.documentElement.setAttribute('data-lang', lang);
  document.querySelectorAll('[data-ta][data-en]').forEach(el => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      if (el.hasAttribute('placeholder')) {
        el.placeholder = el.getAttribute(`data-${lang}`) || el.placeholder;
      } else if (el.type === 'button' || el.type === 'submit') {
        el.value = el.getAttribute(`data-${lang}`) || el.value;
      }
    } else {
      el.textContent = el.getAttribute(`data-${lang}`) || el.textContent;
    }
  });
  const btn = document.getElementById('langBtn');
  if (btn) btn.innerHTML = `<i class="bi bi-translate"></i> ${lang === 'en' ? 'தமிழ்' : 'English'}`;
}

function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'ta' : 'en';
  localStorage.setItem('lang', currentLang);
  applyLanguage(currentLang);
}

// Sidebar
function toggleSidebar() {
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.toggle('open');
    const bd = document.getElementById('sidebarBackdrop');
    if (bd) bd.classList.toggle('show');
  } else {
    document.body.classList.toggle('sidebar-collapsed');
  }
}

// Farm Selector
let farmTarget = '';
function selectFarm(target) {
  farmTarget = target;
  fetch('/farms/api/list')
    .then(r => r.json())
    .then(farms => {
      const list = document.getElementById('farmList');
      if (!farms.length) {
        list.innerHTML = '<p class="text-muted text-center">No farms found. Please add a farm first.</p>';
      } else {
        list.innerHTML = farms.map(f => `
          <a href="/${target}/${f.id}" class="d-block p-3 mb-2 rounded border text-decoration-none"
             style="background:#f0faf2;border-color:#b7e4c7 !important;color:#1a472a;font-weight:500;">
            🏡 ${f.name}
          </a>
        `).join('');
      }
      new bootstrap.Modal(document.getElementById('farmSelectorModal')).show();
    });
}

// Toast Auto-dismiss
document.querySelectorAll('.alert-toast').forEach(el => {
  setTimeout(() => el && el.remove(), 4000);
});

// Loading Overlay
function showLoading() {
  let ov = document.getElementById('loadingOverlay');
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'loadingOverlay';
    ov.className = 'loading-overlay';
    ov.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(ov);
  }
  ov.classList.add('show');
}

function hideLoading() {
  const ov = document.getElementById('loadingOverlay');
  if (ov) ov.classList.remove('show');
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  applyLanguage(currentLang);
});

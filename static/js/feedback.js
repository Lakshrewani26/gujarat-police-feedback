/* ═══════════════════════════════════════════════════════════
   Gujarat Police — Feedback Form JS
═══════════════════════════════════════════════════════════ */

const EMOJIS = { 1: '😞', 2: '😕', 3: '😐', 4: '😊', 5: '😄' };
const LABELS = { 1: 'Very Poor', 2: 'Poor', 3: 'Average', 4: 'Good', 5: 'Excellent' };

// ── Multi-step form ─────────────────────────────────────────
window.nextStep = function(step) {
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.getElementById(`step${step}`).classList.add('active');
  updateStepIndicators(step);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.prevStep = function(step) {
  nextStep(step);
};

function updateStepIndicators(current) {
  for (let i = 1; i <= 3; i++) {
    const ind = document.getElementById(`step${i}-ind`);
    if (!ind) continue;
    ind.classList.remove('active', 'done');
    if (i === current) ind.classList.add('active');
    else if (i < current) ind.classList.add('done');
  }
}

// ── Star Rating System ──────────────────────────────────────
document.querySelectorAll('.star-rating').forEach(group => {
  const stars = group.querySelectorAll('.star-btn');
  const field = group.dataset.field;
  const input = document.querySelector(`input[name="${field}"]`);
  const emojiEl = group.closest('.rating-item')?.querySelector('.rating-emoji');

  stars.forEach((star, idx) => {
    star.addEventListener('mouseenter', () => highlightStars(stars, idx));
    star.addEventListener('mouseleave', () => {
      const val = parseInt(input?.value || 0);
      highlightStars(stars, val - 1);
    });
    star.addEventListener('click', () => {
      const val = idx + 1;
      if (input) input.value = val;
      highlightStars(stars, idx);
      if (emojiEl) {
        emojiEl.textContent = EMOJIS[val];
        emojiEl.style.transform = 'scale(1.4)';
        setTimeout(() => emojiEl.style.transform = 'scale(1)', 200);
      }
    });
  });
});

function highlightStars(stars, upTo) {
  stars.forEach((s, i) => {
    s.classList.toggle('active', i <= upTo);
  });
}

// ── Overall Rating ──────────────────────────────────────────
const overallStars = document.querySelectorAll('.overall-star');
const overallInput = document.querySelector('input[name="overall_rating"]');
const overallLabel = document.getElementById('overallLabel');

overallStars.forEach((star, idx) => {
  star.addEventListener('mouseenter', () => highlightOverall(idx));
  star.addEventListener('mouseleave', () => {
    const val = parseInt(overallInput?.value || 0);
    highlightOverall(val - 1);
  });
  star.addEventListener('click', () => {
    const val = idx + 1;
    if (overallInput) overallInput.value = val;
    highlightOverall(idx);
    if (overallLabel) {
      overallLabel.textContent = `${EMOJIS[val]} ${LABELS[val]}`;
      overallLabel.style.color = val >= 4 ? '#2e7d32' : val >= 3 ? '#f57f17' : '#c62828';
    }
  });
});

function highlightOverall(upTo) {
  overallStars.forEach((s, i) => {
    s.classList.toggle('active', i <= upTo);
  });
}

// ── Image Upload ────────────────────────────────────────────
const uploadZone = document.getElementById('uploadZone');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');

uploadZone?.addEventListener('click', () => imageInput?.click());
uploadZone?.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.style.background = 'rgba(26,35,126,0.04)';
});
uploadZone?.addEventListener('dragleave', () => {
  uploadZone.style.background = '';
});
uploadZone?.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.style.background = '';
  const file = e.dataTransfer.files[0];
  if (file) showPreview(file);
});
imageInput?.addEventListener('change', (e) => {
  if (e.target.files[0]) showPreview(e.target.files[0]);
});

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    if (previewImg) previewImg.src = e.target.result;
    imagePreview?.classList.remove('d-none');
    uploadZone?.classList.add('d-none');
  };
  reader.readAsDataURL(file);
}

window.clearImage = function() {
  if (imageInput) imageInput.value = '';
  if (previewImg) previewImg.src = '';
  imagePreview?.classList.add('d-none');
  uploadZone?.classList.remove('d-none');
};

// ── Form Submission ─────────────────────────────────────────
document.getElementById('feedbackForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  document.querySelector('.submit-text')?.classList.add('d-none');
  document.querySelector('.submit-loading')?.classList.remove('d-none');
  btn.disabled = true;

  try {
    const formData = new FormData(e.target);
    const res = await fetch(window.location.href, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      document.getElementById('ackId').textContent = data.ack_id;
      new bootstrap.Modal(document.getElementById('successModal')).show();
    } else {
      alert('Error: ' + (data.error || 'Submission failed. Please try again.'));
      btn.disabled = false;
      document.querySelector('.submit-text')?.classList.remove('d-none');
      document.querySelector('.submit-loading')?.classList.add('d-none');
    }
  } catch (err) {
    alert('Network error. Please check your connection and try again.');
    btn.disabled = false;
    document.querySelector('.submit-text')?.classList.remove('d-none');
    document.querySelector('.submit-loading')?.classList.add('d-none');
  }
});

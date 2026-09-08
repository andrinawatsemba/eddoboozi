const fileInput = document.getElementById('fileInput');
const dropzoneLabel = document.getElementById('dropzoneLabel');
const preview = document.getElementById('preview');
const stageExtract = document.getElementById('stage-extract');
const stageVoice = document.getElementById('stage-voice');
const stageExport = document.getElementById('stage-export');
const extractedText = document.getElementById('extractedText');
const ocrStatus = document.getElementById('ocrStatus');
const ttsStatus = document.getElementById('ttsStatus');
const generateBtn = document.getElementById('generateBtn');
const player = document.getElementById('player');
const exportBtn = document.getElementById('exportBtn');
const langButtons = document.querySelectorAll('.lang-btn');

let currentLang = 'eng';

function setStage(el, state) {
  el.dataset.state = state;
}

fileInput.addEventListener('change', async () => {
  const file = fileInput.files[0];
  if (!file) return;

  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  dropzoneLabel.textContent = file.name;

  setStage(stageExtract, 'active');
  extractedText.value = '';
  extractedText.placeholder = 'Reading the page…';
  ocrStatus.textContent = '';
  ocrStatus.className = 'status';

  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await fetch('/ocr', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not read the page');

    extractedText.value = data.text;
    extractedText.disabled = false;
    setStage(stageVoice, 'active');
    generateBtn.disabled = false;
  } catch (err) {
    ocrStatus.textContent = err.message;
    ocrStatus.className = 'status error';
  }
});

langButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    langButtons.forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-checked', 'false');
    });
    btn.classList.add('active');
    btn.setAttribute('aria-checked', 'true');
    currentLang = btn.dataset.lang;
  });
});

generateBtn.addEventListener('click', async () => {
  const text = extractedText.value.trim();
  if (!text) return;

  generateBtn.disabled = true;
  generateBtn.textContent = 'Generating…';
  ttsStatus.textContent = '';
  ttsStatus.className = 'status';

  try {
    const res = await fetch('/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language: currentLang }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not generate audio');

    player.src = data.audio_url;
    player.hidden = false;
    player.play().catch(() => {});

    setStage(stageExport, 'active');
    const langLabel = currentLang === 'lug' ? 'lug' : 'eng';
    exportBtn.href = data.audio_url;
    exportBtn.download = `page_${langLabel}_${Date.now()}.mp3`;
    exportBtn.removeAttribute('aria-disabled');
  } catch (err) {
    ttsStatus.textContent = err.message;
    ttsStatus.className = 'status error';
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate audio';
  }
});

const chatEl = document.getElementById('chat');
const statusEl = document.getElementById('status');
const toggleBtn = document.getElementById('toggle-rec');
const clearBtn = document.getElementById('clear-chat');
const textInput = document.getElementById('text-input');
const autoSpeakEl = document.getElementById('auto-speak');
const continuousEl = document.getElementById('continuous');
const tokenInput = document.getElementById('token-input');
const saveTokenBtn = document.getElementById('save-token');

let bearerToken = localStorage.getItem('HYDI_ACCESS_TOKEN') || '';
if (bearerToken) tokenInput.value = bearerToken;

saveTokenBtn.addEventListener('click', () => {
  bearerToken = tokenInput.value.trim();
  if (bearerToken) localStorage.setItem('HYDI_ACCESS_TOKEN', bearerToken);
  else localStorage.removeItem('HYDI_ACCESS_TOKEN');
  toast('Token saved');
});

function appendMessage(role, text) {
  const item = document.createElement('div');
  item.className = `msg ${role}`;
  item.textContent = text;
  chatEl.appendChild(item);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setStatus(text) {
  statusEl.textContent = text;
}

async function sendToBackend(message) {
  const payload = { message, sessionId: 'local' };
  const headers = { 'Content-Type': 'application/json' };
  if (bearerToken) headers['Authorization'] = `Bearer ${bearerToken}`;

  const res = await fetch('/api/respond', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const t = await res.text();
    throw new Error(`Backend error ${res.status}: ${t}`);
  }
  const data = await res.json();
  return data.reply || '';
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.0;
  utt.pitch = 1.0;
  utt.volume = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utt);
}

// Speech Recognition (browser API)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let recognizing = false;

function initRecognizer() {
  if (!SpeechRecognition) {
    setStatus('Speech recognition not supported in this browser');
    return null;
  }
  const rec = new SpeechRecognition();
  rec.lang = 'en-US';
  rec.interimResults = true;
  rec.continuous = continuousEl.checked;

  rec.onstart = () => { recognizing = true; setStatus('Listening...'); toggleBtn.textContent = 'Stop'; };
  rec.onend = () => { recognizing = false; setStatus('Idle'); toggleBtn.textContent = 'Start Talking'; if (continuousEl.checked) rec.start(); };
  rec.onerror = (e) => { setStatus(`Error: ${e.error}`); };

  let finalBuffer = '';
  rec.onresult = async (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const res = event.results[i];
      if (res.isFinal) finalBuffer += res[0].transcript;
      else interim += res[0].transcript;
    }
    if (interim) setStatus(`Heard: ${interim}`);
    if (finalBuffer) {
      const text = finalBuffer.trim();
      finalBuffer = '';
      appendMessage('user', text);
      try {
        setStatus('Thinking...');
        const reply = await sendToBackend(text);
        appendMessage('assistant', reply);
        if (autoSpeakEl.checked) speak(reply);
        setStatus('Listening...');
      } catch (err) {
        appendMessage('system', String(err));
        setStatus('Idle');
      }
    }
  };

  return rec;
}

toggleBtn.addEventListener('click', () => {
  if (!recognizer) recognizer = initRecognizer();
  if (!recognizer) return;

  if (!recognizing) recognizer.start();
  else recognizer.stop();
});

continuousEl.addEventListener('change', () => {
  if (recognizer) recognizer.continuous = continuousEl.checked;
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden && recognizing && recognizer) recognizer.stop();
});

textInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    const text = textInput.value.trim();
    if (!text) return;
    textInput.value = '';
    appendMessage('user', text);
    try {
      setStatus('Thinking...');
      const reply = await sendToBackend(text);
      appendMessage('assistant', reply);
      if (autoSpeakEl.checked) speak(reply);
      setStatus('Idle');
    } catch (err) {
      appendMessage('system', String(err));
      setStatus('Idle');
    }
  }
});

clearBtn.addEventListener('click', () => {
  chatEl.innerHTML = '';
});

function toast(msg) {
  setStatus(msg);
  setTimeout(() => setStatus('Idle'), 1200);
}
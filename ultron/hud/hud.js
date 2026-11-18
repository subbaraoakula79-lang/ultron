// ULTRON HOLOGRAPHIC COMMAND ENGINE

// Web Audio API for Futuristic SFX
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playUiBeep(freq = 880, type = 'sine', duration = 0.08) {
    try {
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {}
}

// 1. Clock
function updateClock() {
    const now = new Date();
    document.getElementById('systemClock').innerText = now.toTimeString().split(' ')[0];
}
setInterval(updateClock, 1000);
updateClock();

// 2. 3D Holographic Core Canvas Animation
const canvas = document.getElementById('holoCanvas');
const ctx = canvas.getContext('2d');
let width, height;

function resizeCanvas() {
    width = canvas.width = canvas.parentElement.clientWidth;
    height = canvas.height = canvas.parentElement.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Holographic particle sphere vertices
const NUM_PARTICLES = 160;
const particles = [];
for (let i = 0; i < NUM_PARTICLES; i++) {
    const theta = Math.acos(2 * Math.random() - 1);
    const phi = 2 * Math.PI * Math.random();
    const r = 90 + (Math.random() * 20);
    particles.push({
        x: r * Math.sin(theta) * Math.cos(phi),
        y: r * Math.sin(theta) * Math.sin(phi),
        z: r * Math.cos(theta),
        baseR: r
    });
}

let rotX = 0;
let rotY = 0;
let corePulse = 0;
let isSpeaking = false;

function renderHoloCore() {
    ctx.clearRect(0, 0, width, height);
    const cx = width / 2;
    const cy = height / 2;
    const fov = 260;

    rotX += 0.007;
    rotY += 0.012;
    corePulse += 0.04;

    const pulseMultiplier = isSpeaking ? (1 + 0.15 * Math.sin(corePulse * 3)) : (1 + 0.04 * Math.sin(corePulse));

    // Draw connecting neural lines
    ctx.strokeStyle = isSpeaking ? 'rgba(255, 42, 85, 0.25)' : 'rgba(0, 240, 255, 0.15)';
    ctx.lineWidth = 0.8;

    const projected = [];
    particles.forEach(p => {
        // Rotate around Y
        let x1 = p.x * Math.cos(rotY) - p.z * Math.sin(rotY);
        let z1 = p.x * Math.sin(rotY) + p.z * Math.cos(rotY);
        // Rotate around X
        let y1 = p.y * Math.cos(rotX) - z1 * Math.sin(rotX);
        let z2 = p.y * Math.sin(rotX) + z1 * Math.cos(rotX);

        x1 *= pulseMultiplier;
        y1 *= pulseMultiplier;

        const scale = fov / (fov + z2 + 180);
        const x2d = cx + x1 * scale;
        const y2d = cy + y1 * scale;
        const alpha = Math.max(0.1, (z2 + 120) / 240);

        projected.push({ x: x2d, y: y2d, alpha, scale, z: z2 });
    });

    // Draw particle points
    projected.forEach((p, idx) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.8 * p.scale, 0, Math.PI * 2);
        ctx.fillStyle = isSpeaking ? `rgba(255, 42, 85, ${p.alpha})` : `rgba(0, 240, 255, ${p.alpha})`;
        ctx.shadowColor = isSpeaking ? '#ff2a55' : '#00f0ff';
        ctx.shadowBlur = 6;
        ctx.fill();

        // Connect nearby points
        for (let j = idx + 1; j < projected.length; j += 12) {
            const p2 = projected[j];
            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
            if (dist < 55) {
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }
    });

    requestAnimationFrame(renderHoloCore);
}
renderHoloCore();

// 3. Audio Visualizer Simulation
const vizCanvas = document.getElementById('audioVisualizer');
const vizCtx = vizCanvas.getContext('2d');
const BARS = 48;

function renderVisualizer() {
    vizCanvas.width = vizCanvas.parentElement.clientWidth;
    vizCtx.clearRect(0, 0, vizCanvas.width, vizCanvas.height);
    const barWidth = vizCanvas.width / BARS;

    for (let i = 0; i < BARS; i++) {
        let h;
        if (isSpeaking) {
            h = Math.random() * 40 + 8;
        } else {
            h = 4 + 6 * Math.sin(Date.now() * 0.005 + i * 0.2);
        }
        const x = i * barWidth;
        const y = vizCanvas.height - h;

        vizCtx.fillStyle = isSpeaking ? '#ff2a55' : '#00f0ff';
        vizCtx.shadowColor = isSpeaking ? '#ff2a55' : '#00f0ff';
        vizCtx.shadowBlur = 4;
        vizCtx.fillRect(x + 1, y, barWidth - 2, h);
    }
    requestAnimationFrame(renderVisualizer);
}
renderVisualizer();

// 4. Voice Synthesis (TTS) - Ultron Persona
let availableVoices = [];
function updateVoicesList() {
    if ('speechSynthesis' in window) {
        availableVoices = window.speechSynthesis.getVoices();
    }
}
updateVoicesList();
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = updateVoicesList;
}

function speakAsUltron(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    // Strip code blocks and raw markdown symbols for clean speech
    const cleanText = text
        .replace(/```[\s\S]*?```/g, '')
        .replace(/[\*\_`\#\[\]\(\)\{\}\<\>]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.pitch = 0.7; // Cold, robotic resonance
    utterance.rate = 1.0;

    if (!availableVoices.length) updateVoicesList();
    const voice = availableVoices.find(v => v.lang.startsWith('en') && (v.name.includes('David') || v.name.includes('Male') || v.name.includes('Natural') || v.name.includes('George')));
    if (voice) utterance.voice = voice;

    utterance.onstart = () => { isSpeaking = true; };
    utterance.onend = () => { isSpeaking = false; };
    utterance.onerror = () => { isSpeaking = false; };

    window.speechSynthesis.speak(utterance);
}

// 5. Speech Recognition (STT) - Voice Commands
const voiceBtn = document.getElementById('voiceBtn');
const voiceLabel = document.getElementById('voiceBtnLabel');
const transcriptText = document.getElementById('transcriptText');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        voiceBtn.classList.add('listening');
        voiceLabel.innerText = 'LISTENING...';
        transcriptText.innerText = 'Listening to voice stream... (speak now)';
        playUiBeep(1200, 'triangle', 0.1);
    };

    recognition.onresult = (e) => {
        let current = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            current += e.results[i][0].transcript;
        }
        transcriptText.innerText = current;
        if (e.results[0].isFinal) {
            executeDirective(current);
        }
    };

    recognition.onerror = (e) => {
        console.warn("Speech recognition error:", e.error);
        if (e.error === 'not-allowed') {
            transcriptText.innerText = "Microphone access blocked. Click the lock/tune icon in the browser URL bar to allow microphone.";
        } else if (e.error === 'no-speech') {
            transcriptText.innerText = "No voice input detected. Tap button and try speaking again.";
        } else {
            transcriptText.innerText = `Voice error: ${e.error}`;
        }
        stopListening();
    };

    recognition.onend = () => {
        stopListening();
    };
} else {
    voiceLabel.innerText = "VOICE API UNAVAILABLE";
}

function toggleListening() {
    if (!recognition) {
        alert("Speech Recognition API is not supported in this browser. Please use Chrome or Edge.");
        return;
    }
    if (isListening) {
        recognition.stop();
        stopListening();
    } else {
        recognition.start();
    }
}

function stopListening() {
    isListening = false;
    voiceBtn.classList.remove('listening');
    voiceLabel.innerText = 'TAP TO SPEAK';
}

voiceBtn.addEventListener('click', toggleListening);

function sendVoiceText(text) {
    playUiBeep(950, 'sine', 0.05);
    transcriptText.innerText = text;
    executeDirective(text);
}

// 6. Directive Execution & Backend Uplink
async function executeDirective(cmdText) {
    if (!cmdText.trim()) return;
    appendLog(`[USER] > ${cmdText}`, 'sys');
    playUiBeep(700, 'square', 0.05);

    try {
        const res = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmdText })
        });
        const data = await res.json();
        const reply = data.response || "Directive processed.";
        appendLog(`[ULTRON] ${reply}`, 'ultron');
        speakAsUltron(reply);
        fetchTelemetry(); // Refresh status immediately
    } catch (e) {
        appendLog(`[ERROR] Directive dispatch failed: ${e.message}`, 'err');
    }
}

function handleManualSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('cmdInput');
    const val = input.value.trim();
    if (val) {
        executeDirective(val);
        input.value = '';
    }
}

function appendLog(text, type = 'sys') {
    const stream = document.getElementById('terminalStream');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerText = text;
    stream.appendChild(entry);
    stream.scrollTop = stream.scrollHeight;
}

// 7. Telemetry Polling (/api/status)
async function fetchTelemetry() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Update Gauges
        const cpu = data.cpu?.overall_percent || 0;
        document.getElementById('cpuPercent').innerText = cpu;
        document.getElementById('cpuGauge').style.strokeDashoffset = 264 - (264 * cpu / 100);

        const mem = data.memory?.percent || 0;
        document.getElementById('ramPercent').innerText = mem;
        document.getElementById('ramGauge').style.strokeDashoffset = 264 - (264 * mem / 100);
        document.getElementById('ramDetails').innerText = `${data.memory?.used_gb || 0} / ${data.memory?.total_gb || 0} GB`;

        // Update Disks
        const diskContainer = document.getElementById('diskList');
        if (data.disks && data.disks.length > 0) {
            diskContainer.innerHTML = data.disks.map(d => `
                <div class="storage-item">
                    <div class="storage-header">
                        <span>${d.mountpoint} (${d.free_gb} GB Free)</span>
                        <span>${d.percent}%</span>
                    </div>
                    <div class="storage-bar-bg">
                        <div class="storage-bar-fill" style="width: ${d.percent}%;"></div>
                    </div>
                </div>
            `).join('');
        }

        // Update Processes
        const procList = document.getElementById('processList');
        if (data.top_processes_by_cpu && data.top_processes_by_cpu.length > 0) {
            procList.innerHTML = data.top_processes_by_cpu.slice(0, 4).map(p => `
                <li><span>${p.name}</span><span>${p.cpu_percent}% CPU</span></li>
            `).join('');
        }

        // Engine indicator
        if (data.engine) {
            document.getElementById('activeEngineText').innerText = `AI: ${data.engine}`;
        }
    } catch (e) {}
}

// Poll status every 2 seconds
setInterval(fetchTelemetry, 2000);
fetchTelemetry();

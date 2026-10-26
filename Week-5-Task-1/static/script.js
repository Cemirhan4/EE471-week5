document.addEventListener('DOMContentLoaded', () => {
  // ==========================================
  // TAB NAVIGATION
  // ==========================================
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetTab = document.getElementById(btn.dataset.tab);
      if (targetTab) targetTab.classList.add('active');
    });
  });

  // ==========================================
  // TAB 1: TEXT-TO-SPEECH
  // ==========================================
  const textInput = document.getElementById('text-input');
  const synthesizeBtn = document.getElementById('synthesize-btn');
  const synthBtnText = document.getElementById('synth-btn-text');
  const ttsClearBtn = document.getElementById('tts-clear-btn');
  const ttsStatusBadge = document.getElementById('tts-status-badge');
  const ttsStatusText = document.getElementById('tts-status-text');
  const ttsAudioSection = document.getElementById('tts-audio-section');
  const ttsAudioPlayer = document.getElementById('tts-audio-player');

  function showTtsStatus(message, isError = false) {
    ttsStatusBadge.className = `status-badge ${isError ? 'error' : ''}`;
    ttsStatusText.textContent = message;
    ttsStatusBadge.style.display = 'block';
  }

  function hideTtsStatus() {
    ttsStatusBadge.style.display = 'none';
  }

  synthesizeBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    if (!text) {
      showTtsStatus('Please enter some text to synthesize.', true);
      return;
    }

    synthesizeBtn.disabled = true;
    synthBtnText.textContent = 'Synthesizing...';
    hideTtsStatus();

    try {
      const response = await fetch('/api/text-to-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        showTtsStatus(data.message || '✓ Speech synthesized successfully!');
        ttsAudioPlayer.src = data.audio_url;
        ttsAudioSection.style.display = 'block';
        ttsAudioPlayer.load();
        ttsAudioPlayer.play().catch(() => {});
      } else {
        showTtsStatus(data.error || 'Failed to synthesize speech.', true);
      }
    } catch (err) {
      showTtsStatus('Network error while reaching server.', true);
    } finally {
      synthesizeBtn.disabled = false;
      synthBtnText.textContent = 'Synthesize Speech';
    }
  });

  ttsClearBtn.addEventListener('click', () => {
    textInput.value = '';
    hideTtsStatus();
    ttsAudioSection.style.display = 'none';
    ttsAudioPlayer.pause();
    ttsAudioPlayer.currentTime = 0;
    ttsAudioPlayer.src = '';
  });

  // ==========================================
  // TAB 2: SPEECH-TO-TEXT WITH PURE PCM WAV RECORDER
  // ==========================================
  const startRecordBtn = document.getElementById('start-record-btn');
  const stopRecordBtn = document.getElementById('stop-record-btn');
  const audioFileInput = document.getElementById('audio-file-input');
  const fileChosenName = document.getElementById('file-chosen-name');
  const recordingIndicator = document.getElementById('recording-indicator');
  const sttPreviewSection = document.getElementById('stt-preview-section');
  const sttPreviewPlayer = document.getElementById('stt-preview-player');
  const transcribeBtn = document.getElementById('transcribe-btn');
  const transcribeBtnText = document.getElementById('transcribe-btn-text');
  const sttClearBtn = document.getElementById('stt-clear-btn');
  const transcriptionOutput = document.getElementById('transcription-output');
  const copyBtn = document.getElementById('copy-btn');
  const sttStatusBadge = document.getElementById('stt-status-badge');
  const sttStatusText = document.getElementById('stt-status-text');

  let audioContext = null;
  let mediaStream = null;
  let audioInput = null;
  let scriptProcessor = null;
  let audioSamples = [];
  let recordedWavBlob = null;
  let selectedFile = null;

  function showSttStatus(message, isError = false) {
    sttStatusBadge.className = `status-badge ${isError ? 'error' : ''}`;
    sttStatusText.textContent = message;
    sttStatusBadge.style.display = 'block';
  }

  function hideSttStatus() {
    sttStatusBadge.style.display = 'none';
  }

  // --- Real-time 16-bit PCM WAV Recorder ---
  startRecordBtn.addEventListener('click', async () => {
    try {
      audioSamples = [];
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      audioContext = new AudioCtx({ sampleRate: 16000 });

      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      audioInput = audioContext.createMediaStreamSource(mediaStream);
      // Buffer size 4096, 1 input channel, 1 output channel
      scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

      scriptProcessor.onaudioprocess = (e) => {
        const channelData = e.inputBuffer.getChannelData(0);
        audioSamples.push(new Float32Array(channelData));
      };

      audioInput.connect(scriptProcessor);
      scriptProcessor.connect(audioContext.destination);

      startRecordBtn.disabled = true;
      stopRecordBtn.disabled = false;
      recordingIndicator.style.display = 'flex';
      hideSttStatus();
    } catch (err) {
      showSttStatus('Microphone access denied: ' + err.message, true);
    }
  });

  stopRecordBtn.addEventListener('click', () => {
    if (scriptProcessor && audioInput) {
      scriptProcessor.disconnect();
      audioInput.disconnect();
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
    }

    startRecordBtn.disabled = false;
    stopRecordBtn.disabled = true;
    recordingIndicator.style.display = 'none';

    // Merge audio sample chunks
    const totalLength = audioSamples.reduce((acc, chunk) => acc + chunk.length, 0);
    const mergedSamples = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of audioSamples) {
      mergedSamples.set(chunk, offset);
      offset += chunk.length;
    }

    const sampleRate = audioContext ? audioContext.sampleRate : 16000;
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close();
    }

    // Encode into a 100% genuine RIFF PCM WAV Blob
    recordedWavBlob = encodeWAV(mergedSamples, sampleRate);

    // Show preview player
    sttPreviewPlayer.src = URL.createObjectURL(recordedWavBlob);
    sttPreviewSection.style.display = 'block';
    transcribeBtn.disabled = false;
    fileChosenName.textContent = 'Voice recording (16-bit PCM WAV) ready';
  });

  // --- 16-bit Mono PCM WAV Encoder ---
  function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');

    // "fmt " sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);          // Subchunk1Size: 16 for PCM
    view.setUint16(20, 1, true);           // AudioFormat: 1 (PCM)
    view.setUint16(22, 1, true);           // NumChannels: 1 (Mono)
    view.setUint32(24, sampleRate, true);  // SampleRate (16000)
    view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * 1 * 16/8)
    view.setUint16(32, 2, true);           // BlockAlign (1 * 16/8)
    view.setUint16(34, 16, true);          // BitsPerSample: 16-bit

    // "data" sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Write PCM samples
    let index = 44;
    for (let i = 0; i < samples.length; i++) {
      let s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      index += 2;
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  // Choose File Upload
  audioFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      selectedFile = e.target.files[0];
      fileChosenName.textContent = selectedFile.name;
      sttPreviewPlayer.src = URL.createObjectURL(selectedFile);
      sttPreviewSection.style.display = 'block';
      transcribeBtn.disabled = false;
      recordedWavBlob = null;
      hideSttStatus();
    }
  });

  // Transcribe Audio
  transcribeBtn.addEventListener('click', async () => {
    const audioPayload = selectedFile || recordedWavBlob;
    if (!audioPayload) {
      showSttStatus('Please record audio or choose a file first.', true);
      return;
    }

    const formData = new FormData();
    formData.append('audio', audioPayload, 'recorded_speech.wav');

    transcribeBtn.disabled = true;
    transcribeBtnText.textContent = 'Transcribing...';
    hideSttStatus();

    try {
      const response = await fetch('/api/speech-to-text', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok && data.success) {
        transcriptionOutput.value = data.transcription;
        showSttStatus(data.message || '✓ Audio transcribed successfully!');
      } else {
        showSttStatus(data.error || 'Failed to transcribe audio.', true);
      }
    } catch (err) {
      showSttStatus('Network error while transcribing audio.', true);
    } finally {
      transcribeBtn.disabled = false;
      transcribeBtnText.textContent = 'Transcribe Audio';
    }
  });

  // Copy Text Button
  copyBtn.addEventListener('click', () => {
    if (!transcriptionOutput.value) return;
    navigator.clipboard.writeText(transcriptionOutput.value).then(() => {
      copyBtn.innerText = 'Copied!';
      setTimeout(() => copyBtn.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg> Copy Text
      `, 1500);
    });
  });

  // Clear STT
  sttClearBtn.addEventListener('click', () => {
    selectedFile = null;
    recordedWavBlob = null;
    audioFileInput.value = '';
    fileChosenName.textContent = 'No file chosen';
    sttPreviewPlayer.src = '';
    sttPreviewSection.style.display = 'none';
    transcriptionOutput.value = '';
    transcribeBtn.disabled = true;
    hideSttStatus();
    if (scriptProcessor && audioInput) {
      scriptProcessor.disconnect();
      audioInput.disconnect();
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
    }
    startRecordBtn.disabled = false;
    stopRecordBtn.disabled = true;
    recordingIndicator.style.display = 'none';
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const display = document.getElementById('display');
  const micBtn = document.getElementById('mic-btn');
  const clearBtn = document.getElementById('clear-btn');
  const voiceStatus = document.getElementById('voice-status');
  const voiceText = document.getElementById('voice-text');

  // Calculator internal state
  let num1 = null;
  let operator = null;
  let waitingForNum2 = false;
  let speechQueue = [];

  // ==========================================
  // TEXT-TO-SPEECH (MAGICAL SPEAKING FEATURE)
  // ==========================================
  function speak(text) {
    if (!('speechSynthesis' in window)) return;

    // Cancel any ongoing speech so clicks sound crisp and immediate
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
  }

  function updateDisplay(val) {
    display.textContent = val;
  }

  // ==========================================
  // BUTTON CLICKS (FEATURING VOICE OUTPUT)
  // ==========================================
  document.querySelectorAll('.keypad .btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const val = btn.dataset.val;
      const speechWord = btn.dataset.speech || val;

      if (btn.classList.contains('btn-num') && val !== '=') {
        handleNumber(val);
        // Speak number e.g. "Three"
        speak(speechWord);
      } else if (btn.classList.contains('btn-op')) {
        handleOperator(val);
        // Speak operator e.g. "plus", "times", "over", "minus"
        speak(speechWord);
      } else if (btn.classList.contains('btn-equal') || val === '=') {
        await handleEquals();
      }
    });
  });

  function handleNumber(val) {
    if (waitingForNum2) {
      updateDisplay(val);
      waitingForNum2 = false;
    } else {
      const current = display.textContent;
      if (val === '.' && current.includes('.')) return;
      updateDisplay(current === '0' ? val : current + val);
    }
  }

  function handleOperator(val) {
    num1 = parseFloat(display.textContent);
    operator = val;
    waitingForNum2 = true;
  }

  async function handleEquals() {
    if (num1 === null || operator === null) return;
    const num2 = parseFloat(display.textContent);

    try {
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num1, operator, num2 })
      });

      const data = await response.json();

      if (response.ok && data.result !== undefined) {
        updateDisplay(data.result);
        // Speak "is [result]" e.g. "is eight" or "is seven"
        speak(`is ${data.result}`);
      } else {
        updateDisplay('Error');
        speak(data.error || 'Error');
        setTimeout(() => updateDisplay('0'), 2000);
      }
    } catch (err) {
      updateDisplay('Error');
      speak('Error');
    }

    // Reset state
    num1 = null;
    operator = null;
    waitingForNum2 = true;
  }

  clearBtn.addEventListener('click', () => {
    updateDisplay('0');
    num1 = null;
    operator = null;
    waitingForNum2 = false;
    speak('Clear');
  });

  // ==========================================
  // VOICE COMMAND RECOGNITION (MIC BUTTON)
  // ==========================================
  let recognition = null;
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      micBtn.classList.add('listening');
      voiceStatus.style.display = 'flex';
      voiceText.textContent = 'Listening... Speak now!';
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      voiceText.textContent = `Heard: "${transcript}"`;

      // Send recognized text to backend parser
      try {
        const response = await fetch('/api/voice-command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: transcript })
        });

        const data = await response.json();

        if (response.ok && data.result !== undefined) {
          updateDisplay(data.result);
          voiceText.textContent = `${data.num1} ${data.operator} ${data.num2} = ${data.result}`;
          // Speak result
          speak(data.spoken_sentence || `is ${data.result}`);
        } else {
          voiceText.textContent = data.error || 'Could not understand command.';
          speak('Could not understand');
        }
      } catch (err) {
        voiceText.textContent = 'Server error processing voice.';
      }
    };

    recognition.onerror = (event) => {
      voiceText.textContent = `Voice error: ${event.error}`;
      micBtn.classList.remove('listening');
      setTimeout(() => voiceStatus.style.display = 'none', 3000);
    };

    recognition.onend = () => {
      micBtn.classList.remove('listening');
      setTimeout(() => voiceStatus.style.display = 'none', 3000);
    };
  }

  micBtn.addEventListener('click', () => {
    if (!recognition) {
      alert('Speech Recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }

    try {
      recognition.start();
    } catch (e) {
      // If already started, restart
      recognition.stop();
    }
  });
});

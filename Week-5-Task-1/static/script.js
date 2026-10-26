document.addEventListener('DOMContentLoaded', () => {
  const textInput = document.getElementById('text-input');
  const synthesizeBtn = document.getElementById('synthesize-btn');
  const btnText = document.getElementById('btn-text');
  const clearBtn = document.getElementById('clear-btn');
  const statusBadge = document.getElementById('status-badge');
  const statusText = document.getElementById('status-text');
  const audioSection = document.getElementById('audio-section');
  const audioPlayer = document.getElementById('audio-player');
  const downloadBtn = document.getElementById('download-btn');

  function showStatus(message, isError = false) {
    statusBadge.className = `status-badge ${isError ? 'error' : ''}`;
    statusText.textContent = message;
    statusBadge.style.display = 'block';
  }

  function hideStatus() {
    statusBadge.style.display = 'none';
  }

  // Synthesize Speech
  synthesizeBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();

    if (!text) {
      showStatus('Please enter some text to synthesize.', true);
      return;
    }

    // Set loading state
    synthesizeBtn.disabled = true;
    btnText.textContent = 'Synthesizing...';
    hideStatus();

    try {
      const response = await fetch('/api/text-to-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        showStatus(data.message || '✓ Speech synthesized successfully!');
        
        // Update audio player source and play
        audioPlayer.src = data.audio_url;
        audioSection.style.display = 'block';
        audioPlayer.load();
        audioPlayer.play().catch(() => {
          // Browser autoplay restrictions may prevent immediate play until user interacts
        });
      } else {
        showStatus(data.error || 'Failed to synthesize speech.', true);
      }
    } catch (err) {
      showStatus('Network error: Could not reach the server.', true);
    } finally {
      synthesizeBtn.disabled = false;
      btnText.textContent = 'Synthesizing Speech';
    }
  });

  // Clear Input & Results
  clearBtn.addEventListener('click', () => {
    textInput.value = '';
    hideStatus();
    audioSection.style.display = 'none';
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    audioPlayer.src = '';
  });
});

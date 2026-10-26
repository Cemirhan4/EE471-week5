import os
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

# Ensure audio output directory exists
AUDIO_DIR = os.path.join(app.static_folder or 'static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(AUDIO_DIR, 'synthesized_speech.wav')

SPEECH_KEY = os.getenv('SPEECH_KEY', '').strip()
SPEECH_REGION = os.getenv('SPEECH_REGION', 'eastus').strip()


def synthesize_with_azure(text, output_path):
    """Synthesizes text to speech using Azure Cognitive Services Speech SDK."""
    import azure.cognitiveservices.speech as speechsdk

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return True, "Speech synthesized successfully with Azure Speech Services!"
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        reason = cancellation.error_details or cancellation.reason
        return False, f"Azure Speech synthesis canceled: {reason}"
    return False, "Unknown Azure synthesis error."


def synthesize_fallback(text, output_path):
    """Local fallback synthesis using gTTS (Google Text-to-Speech) if Azure key is not provided."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        # Save as mp3 or wav
        temp_mp3 = output_path.replace('.wav', '.mp3')
        tts.save(temp_mp3)

        # Convert to wav if pydub is installed, else serve mp3
        try:
            from pydub import AudioSegment
            sound = AudioSegment.from_mp3(temp_mp3)
            sound.export(output_path, format="wav")
            return True, "Speech synthesized successfully! (Fallback mode: Ready for Azure key)"
        except Exception:
            # Return mp3 directly
            return True, "Speech synthesized successfully! (Fallback mode)"
    except Exception as e:
        return False, f"Synthesis error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'Please enter some text to synthesize.'}), 400

    text = data.get('text').strip()

    # If Azure credentials exist, use Azure
    if SPEECH_KEY and SPEECH_KEY != 'your_azure_speech_key_here':
        try:
            success, message = synthesize_with_azure(text, OUTPUT_FILE)
            if not success:
                # Fallback on failure
                success, message = synthesize_fallback(text, OUTPUT_FILE)
        except Exception as e:
            success, message = synthesize_fallback(text, OUTPUT_FILE)
    else:
        # Use fallback synthesizer
        success, message = synthesize_fallback(text, OUTPUT_FILE)

    if success:
        # Determine audio URL (support both wav and mp3 fallback)
        audio_url = '/static/audio/synthesized_speech.wav'
        if not os.path.exists(OUTPUT_FILE) and os.path.exists(OUTPUT_FILE.replace('.wav', '.mp3')):
            audio_url = '/static/audio/synthesized_speech.mp3'

        # Append timestamp to bypass browser audio caching
        import time
        audio_url_with_cache_buster = f"{audio_url}?t={int(time.time())}"

        return jsonify({
            'success': True,
            'message': message,
            'audio_url': audio_url_with_cache_buster
        }), 200
    else:
        return jsonify({'error': message}), 500


@app.route('/download-audio')
def download_audio():
    target = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else OUTPUT_FILE.replace('.wav', '.mp3')
    if os.path.exists(target):
        return send_file(target, as_attachment=True, download_name='speech_audio.wav')
    return jsonify({'error': 'No audio file available to download.'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)

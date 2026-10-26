import os
import tempfile
import time
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

SPEECH_KEY = os.getenv('SPEECH_KEY', '').strip()
SPEECH_REGION = os.getenv('SPEECH_REGION', 'eastus').strip()

# Directories for audio files
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
AUDIO_DIR = os.path.join(STATIC_DIR, 'audio')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'uploads')
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

SYNTH_OUTPUT_FILE = os.path.join(AUDIO_DIR, 'synthesized_speech.wav')


# ==========================================
# 1. TEXT-TO-SPEECH HELPERS
# ==========================================
def synthesize_with_azure(text, output_path):
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
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        temp_mp3 = output_path.replace('.wav', '.mp3')
        tts.save(temp_mp3)
        try:
            from pydub import AudioSegment
            sound = AudioSegment.from_mp3(temp_mp3)
            sound.export(output_path, format="wav")
            return True, "Speech synthesized successfully!"
        except Exception:
            return True, "Speech synthesized successfully! (MP3 format)"
    except Exception as e:
        return False, f"Synthesis error: {str(e)}"


# ==========================================
# 2. SPEECH-TO-TEXT HELPERS
# ==========================================
def transcribe_with_azure(audio_path):
    import azure.cognitiveservices.speech as speechsdk
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return True, result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return False, "No speech could be recognized in the audio."
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        reason = cancellation.error_details or cancellation.reason
        return False, f"Azure recognition canceled: {reason}"
    return False, "Unknown transcription error."


def transcribe_fallback(audio_path):
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    # 1. Try reading directly as WAV
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return True, text
    except Exception as direct_err:
        # 2. If direct WAV read fails, attempt pydub conversion
        try:
            from pydub import AudioSegment
            conv_path = audio_path + '_conv.wav'
            sound = AudioSegment.from_file(audio_path)
            sound = sound.set_channels(1).set_frame_rate(16000)
            sound.export(conv_path, format="wav")
            with sr.AudioFile(conv_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            if os.path.exists(conv_path):
                os.remove(conv_path)
            return True, text
        except Exception:
            # 3. Informative error message
            msg = str(direct_err)
            if "could not be read as PCM WAV" in msg:
                return False, "Audio format error: Please record using the Start Recording button (which produces 16-bit PCM WAV) or upload a standard .wav file."
            return False, f"Transcription error: {msg}"


# ==========================================
# 3. PART 4: TRANSLATION & PRONUNCIATION HELPERS
# ==========================================
def translate_speech_azure(audio_path, target_lang='es'):
    try:
        import azure.cognitiveservices.speech as speechsdk
        import azure.cognitiveservices.speech.translation as translation_sdk

        translation_config = translation_sdk.SpeechTranslationConfig(
            subscription=SPEECH_KEY, region=SPEECH_REGION
        )
        translation_config.speech_recognition_language = "en-US"
        translation_config.add_target_language(target_lang)

        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = translation_sdk.TranslationRecognizer(
            translation_config=translation_config, audio_config=audio_config
        )

        result = recognizer.recognize_once_async().get()

        if result.reason == translation_sdk.ResultReason.TranslatedSpeech:
            translated_text = result.translations.get(target_lang, "")
            return True, {
                'original': result.text,
                'translated': translated_text,
                'target_lang': target_lang
            }
        elif result.reason == translation_sdk.ResultReason.NoMatch:
            return False, "No speech recognized for translation."
        return False, "Translation canceled or failed."
    except Exception as e:
        return False, str(e)


# ==========================================
# FLASK ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'Please enter some text to synthesize.'}), 400

    text = data.get('text').strip()

    if SPEECH_KEY and SPEECH_KEY != 'your_azure_speech_key_here':
        try:
            success, message = synthesize_with_azure(text, SYNTH_OUTPUT_FILE)
            if not success:
                success, message = synthesize_fallback(text, SYNTH_OUTPUT_FILE)
        except Exception:
            success, message = synthesize_fallback(text, SYNTH_OUTPUT_FILE)
    else:
        success, message = synthesize_fallback(text, SYNTH_OUTPUT_FILE)

    if success:
        audio_url = '/static/audio/synthesized_speech.wav'
        if not os.path.exists(SYNTH_OUTPUT_FILE) and os.path.exists(SYNTH_OUTPUT_FILE.replace('.wav', '.mp3')):
            audio_url = '/static/audio/synthesized_speech.mp3'

        return jsonify({
            'success': True,
            'message': message,
            'audio_url': f"{audio_url}?t={int(time.time())}"
        }), 200
    return jsonify({'error': message}), 500


@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided in request.'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=UPLOAD_DIR)
    audio_file.save(temp_file.name)
    temp_file.close()

    try:
        if SPEECH_KEY and SPEECH_KEY != 'your_azure_speech_key_here':
            try:
                success, text = transcribe_with_azure(temp_file.name)
                if not success:
                    success, text = transcribe_fallback(temp_file.name)
            except Exception:
                success, text = transcribe_fallback(temp_file.name)
        else:
            success, text = transcribe_fallback(temp_file.name)

        if success:
            return jsonify({
                'success': True,
                'transcription': text,
                'message': '✓ Audio transcribed successfully!'
            }), 200
        return jsonify({'error': text}), 400
    finally:
        try:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
        except Exception:
            pass


@app.route('/download-audio')
def download_audio():
    target = SYNTH_OUTPUT_FILE if os.path.exists(SYNTH_OUTPUT_FILE) else SYNTH_OUTPUT_FILE.replace('.wav', '.mp3')
    if os.path.exists(target):
        return send_file(target, as_attachment=True, download_name='speech_audio.wav')
    return jsonify({'error': 'No audio file available to download.'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)

import os
import base64
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

# URL of the Cog model container HTTP API
COG_INFERENCE_URL = os.getenv("COG_INFERENCE_URL", "http://localhost:5001/predictions")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classify', methods=['POST'])
def classify_cat():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded.'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected image.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Allowed image formats: PNG, JPG, JPEG, WEBP.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Convert image to data URI base64 to send to Cog container API
    try:
        with open(filepath, "rb") as img_f:
            b64_data = base64.b64encode(img_f.read()).decode("utf-8")
        
        mime_type = "image/jpeg"
        if filename.lower().endswith(".png"):
            mime_type = "image/png"
        elif filename.lower().endswith(".webp"):
            mime_type = "image/webp"

        data_uri = f"data:{mime_type};base64,{b64_data}"

        # Send request to Cog inference endpoint
        print(f"[API] Sending inference request to Cog container at {COG_INFERENCE_URL}...")
        payload = {"input": {"image": data_uri}}
        response = requests.post(COG_INFERENCE_URL, json=payload, timeout=30)

        if response.status_code == 200:
            result_json = response.json()
            predictions = result_json.get("output", {})
            return jsonify({
                "success": True,
                "predictions": predictions,
                "image_url": f"/static/uploads/{filename}"
            }), 200
        else:
            print(f"[API ERROR] Cog returned status {response.status_code}: {response.text}")
            return jsonify({
                "error": f"Cog container returned status {response.status_code}: {response.text}"
            }), 502

    except requests.exceptions.ConnectionError:
        # Fallback if Cog container is not currently running: run local prediction if torch available
        print("[API NOTICE] Cog container not responding on port 5001. Attempting local torchvision inference...")
        try:
            from predict import Predictor
            predictor = Predictor()
            predictor.setup()
            preds = predictor.predict(filepath)
            return jsonify({
                "success": True,
                "predictions": preds,
                "image_url": f"/static/uploads/{filename}",
                "mode": "standalone_local"
            }), 200
        except Exception as local_err:
            return jsonify({
                "error": f"Could not connect to Cog container at {COG_INFERENCE_URL}. Make sure your Cog container is running (`docker run -p 5001:5000 cat-classifier`). Error: {str(local_err)}"
            }), 503

    except Exception as e:
        return jsonify({'error': f"Prediction error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)

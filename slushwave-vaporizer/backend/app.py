# app.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from audio_processor import process_audio

app = Flask(__name__)
# Note: In a real app, these would be configured properly.
# Using relative paths for simplicity in this environment.
app.config['UPLOAD_FOLDER'] = 'slushwave-vaporizer/backend/uploads'
app.config['OUTPUT_FOLDER'] = 'slushwave-vaporizer/backend/outputs'

# Create upload and output folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello, World!")

@app.route('/api/slushify', methods=['POST'])
def slushify():
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No selected file"), 400

    if file:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)

        # Define output path
        output_filename = f"{unique_id}_slushed_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # --- Call the refactored function ---
        # For now, use default options. Later, these will come from the request.
        try:
            audio_out = process_audio(input_path, output_path)

            # Clean up input file
            os.remove(input_path)

            response = {
                'message': 'Processing successful!',
                'audio_output': audio_out
            }
            return jsonify(response)

        except Exception as e:
            # Clean up input file even if processing fails
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

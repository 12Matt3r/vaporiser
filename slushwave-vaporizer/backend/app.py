# app.py
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from tasks import celery_app, slushify_task, adjust_task

# Serve the built React app
app = Flask(__name__, static_folder='build', static_url_path='/')
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Be more specific about CORS

app.config['UPLOAD_FOLDER'] = 'slushwave-vaporizer/backend/uploads'
app.config['OUTPUT_FOLDER'] = 'slushwave-vaporizer/backend/outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
# Ensure the static folder exists
if not os.path.exists(app.static_folder):
    os.makedirs(app.static_folder)


# --- API Routes ---
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello, World!")

@app.route('/api/presets', methods=['GET'])
def get_presets():
    from audio_processor import PRESETS
    preset_data = {name: details['description'] for name, details in PRESETS.items()}
    return jsonify(preset_data)

@app.route('/api/outputs/<path:filename>')
def serve_output_file(filename):
    return send_from_directory(os.path.abspath(app.config['OUTPUT_FOLDER']), filename)

@app.route('/api/slushify', methods=['POST'])
def slushify():
    # ... (logic is unchanged)
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    preset = request.form.get('preset', 'slushwave')
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if file:
        filename = secure_filename(file.filename)
        temp_input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_input_path)
        reference_path = None
        if 'reference_file' in request.files:
            reference_file = request.files['reference_file']
            if reference_file.filename != '':
                ref_filename = secure_filename(reference_file.filename)
                reference_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{ref_filename}")
                reference_file.save(reference_path)
        options = {'preset': preset}
        task = slushify_task.delay(temp_input_path, filename, options, reference_path)
        return jsonify(
            task_id=task.id,
            status_url=url_for('taskstatus', task_id=task.id, _external=True)
        ), 202

@app.route('/api/status/<task_id>')
def taskstatus(task_id):
    # ... (logic is unchanged)
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = { 'state': task.state, 'status': 'Pending...' }
    elif task.state == 'PROGRESS':
        response = { 'state': task.state, 'status': task.info.get('status', '') }
    elif task.state == 'SUCCESS':
        response = { 'state': task.state, 'status': 'Task completed!', 'result': task.info.get('result') }
    else:
        response = { 'state': task.state, 'status': str(task.info) }
    return jsonify(response)

@app.route('/api/adjust/<original_task_id>', methods=['POST'])
def adjust(original_task_id):
    # ... (logic is unchanged)
    original_file_path = None
    if os.path.isdir(app.config['OUTPUT_FOLDER']):
        for f in os.listdir(app.config['OUTPUT_FOLDER']):
            if f.startswith(original_task_id):
                original_file_path = os.path.join(app.config['OUTPUT_FOLDER'], f)
                break
    if not original_file_path or not os.path.exists(original_file_path):
        return jsonify(error="Original processed file not found."), 404
    adj_data = request.get_json()
    if not adj_data or 'effect_name' not in adj_data or 'effect_params' not in adj_data:
        return jsonify(error="Invalid adjustment data provided."), 400
    new_file_id = str(uuid.uuid4())
    task = adjust_task.delay(
        original_file_path,
        adj_data['effect_name'],
        adj_data['effect_params'],
        new_file_id
    )
    return jsonify(
        task_id=task.id,
        status_url=url_for('taskstatus', task_id=task.id, _external=True)
    ), 202

# --- Static File Serving ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

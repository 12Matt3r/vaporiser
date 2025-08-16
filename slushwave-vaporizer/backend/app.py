# app.py
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from tasks import celery_app, slushify_task, adjust_task

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'slushwave-vaporizer/backend/uploads'
app.config['OUTPUT_FOLDER'] = 'slushwave-vaporizer/backend/outputs' # Define output folder config
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True) # Ensure it exists


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
    """Serves a file from the output directory."""
    return send_from_directory(os.path.abspath(app.config['OUTPUT_FOLDER']), filename)

@app.route('/api/slushify', methods=['POST'])
def slushify():
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

        # Handle optional reference file
        reference_path = None
        if 'reference_file' in request.files:
            reference_file = request.files['reference_file']
            if reference_file.filename != '':
                ref_filename = secure_filename(reference_file.filename)
                reference_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{ref_filename}")
                reference_file.save(reference_path)

        options = {'preset': preset}
        # Pass the optional reference_path to the task
        task = slushify_task.delay(temp_input_path, filename, options, reference_path)

        return jsonify(
            task_id=task.id,
            status_url=url_for('taskstatus', task_id=task.id, _external=True)
        ), 202

@app.route('/api/status/<task_id>')
def taskstatus(task_id):
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = { 'state': task.state, 'status': 'Pending...' }
    elif task.state == 'PROGRESS':
        response = { 'state': task.state, 'status': task.info.get('status', '') }
    elif task.state == 'SUCCESS':
        response = { 'state': task.state, 'status': 'Task completed!', 'result': task.info.get('result') }
    else: # state == 'FAILURE'
        response = { 'state': task.state, 'status': str(task.info) }
    return jsonify(response)

@app.route('/api/adjust/<original_task_id>', methods=['POST'])
def adjust(original_task_id):
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

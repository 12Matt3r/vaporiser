# app.py
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from tasks import celery_app, slushify_task, adjust_task

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'slushwave-vaporizer/backend/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello, World!")

@app.route('/api/presets', methods=['GET'])
def get_presets():
    from audio_processor import PRESETS
    preset_data = {name: details['description'] for name, details in PRESETS.items()}
    return jsonify(preset_data)

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

        options = {'preset': preset}
        task = slushify_task.delay(temp_input_path, filename, options)

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
    output_dir = 'slushwave-vaporizer/backend/outputs'
    original_file_path = None
    if os.path.isdir(output_dir):
        for f in os.listdir(output_dir):
            if f.startswith(original_task_id):
                original_file_path = os.path.join(output_dir, f)
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
        # It's important to note that the new filename is NOT the task.id anymore.
        # The frontend would need to get the new filename from the result of this task.
        status_url=url_for('taskstatus', task_id=task.id, _external=True)
    ), 202

if __name__ == '__main__':
    app.run(debug=True, port=5000)

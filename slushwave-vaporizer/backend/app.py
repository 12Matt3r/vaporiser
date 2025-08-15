# app.py
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from tasks import slushify_task

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'slushwave-vaporizer/backend/uploads'
# The output folder is now managed within the task, but we still need the upload folder.
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
        # Save the uploaded file to a temporary location. The task will delete it.
        temp_input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_input_path)

        options = {'preset': preset}
        # Call the task with the temp input path and original filename
        task = slushify_task.delay(temp_input_path, filename, options)

        return jsonify(
            task_id=task.id,
            status_url=url_for('taskstatus', task_id=task.id, _external=True)
        ), 202

@app.route('/api/status/<task_id>')
def taskstatus(task_id):
    task = slushify_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = { 'state': task.state, 'status': 'Pending...' }
    elif task.state == 'PROGRESS':
        response = { 'state': task.state, 'status': task.info.get('status', '') }
    elif task.state == 'SUCCESS':
        response = { 'state': task.state, 'status': 'Task completed!', 'result': task.info.get('result') }
    else: # state == 'FAILURE'
        response = { 'state': task.state, 'status': str(task.info) }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

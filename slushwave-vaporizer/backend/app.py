# app.py
from flask import Flask, request, jsonify, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from tasks import slushify_task # Import the celery task

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
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)

        output_filename = f"{unique_id}_slushed_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # --- Dispatch the Celery task ---
        task = slushify_task.delay(input_path, output_path)

        # Return a response that includes the URL to check the task status
        return jsonify(
            task_id=task.id,
            status_url=url_for('taskstatus', task_id=task.id, _external=True)
        ), 202 # 202 Accepted

@app.route('/api/status/<task_id>')
def taskstatus(task_id):
    task = slushify_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        # Job did not start yet
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Task completed!',
            'result': task.info.get('result')
        }
    else: # state == 'FAILURE'
        # Something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # This is the exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

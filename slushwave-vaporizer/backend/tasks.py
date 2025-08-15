from celery import Celery
from audio_processor import process_audio
import os

# Assume Redis is running on the default port.
# The user will configure this in their Replit environment.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task(bind=True)
def slushify_task(self, input_path, original_filename, options=None):
    """
    Celery task to process an audio file.
    It now determines its own output path based on its task ID.
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing...'})

        # Determine output path based on task ID
        output_dir = 'slushwave-vaporizer/backend/outputs'
        file_ext = os.path.splitext(original_filename)[1]
        output_filename = f"{self.request.id}{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        self.update_state(state='PROGRESS', meta={'status': 'Processing audio...'})
        result_path = process_audio(input_path, output_path, options)

        if os.path.exists(input_path):
            os.remove(input_path)

        return {'status': 'SUCCESS', 'result': result_path}
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        raise e

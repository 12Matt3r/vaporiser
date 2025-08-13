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
def slushify_task(self, input_path, output_path, options=None):
    """
    Celery task to process an audio file.
    Wraps the process_audio function and provides status updates.
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing audio...'})
        # Note: The analysis is part of process_audio now.
        # For more granular progress, process_audio could be split further.

        result_path = process_audio(input_path, output_path, options)

        # Clean up the input file after successful processing
        if os.path.exists(input_path):
            os.remove(input_path)

        return {'status': 'SUCCESS', 'result': result_path}
    except Exception as e:
        # Clean up the input file on failure as well
        if os.path.exists(input_path):
            os.remove(input_path)
        # The state will be 'FAILURE' and task.info will contain the exception
        # No need to return a custom dict here, Celery handles it.
        raise e

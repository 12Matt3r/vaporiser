from celery import Celery
from audio_processor import process_audio
import os
import time
from datetime import timedelta
import effects

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_app.conf.beat_schedule = {
    'delete-old-files-every-hour': {
        'task': 'tasks.cleanup_old_files',
        'schedule': timedelta(hours=1),
    },
}
celery_app.conf.timezone = 'UTC'

@celery_app.task(bind=True)
def slushify_task(self, input_path, original_filename, options=None, reference_path=None):
    """
    Celery task to process an audio file.
    It determines its own output path based on its task ID.
    It now accepts an optional reference_path for style transfer.
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing...'})

        output_dir = 'slushwave-vaporizer/backend/outputs'
        file_ext = os.path.splitext(original_filename)[1]
        output_filename = f"{self.request.id}{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        self.update_state(state='PROGRESS', meta={'status': 'Processing audio...'})
        # Pass the reference_path to the audio processor
        result_path = process_audio(input_path, output_path, options, reference_path)

        # Clean up input files
        if os.path.exists(input_path):
            os.remove(input_path)
        if reference_path and os.path.exists(reference_path):
            os.remove(reference_path)

        return {'status': 'SUCCESS', 'result': result_path}
    except Exception as e:
        # Clean up input files on failure too
        if os.path.exists(input_path):
            os.remove(input_path)
        if reference_path and os.path.exists(reference_path):
            os.remove(reference_path)
        raise e

@celery_app.task
def cleanup_old_files(now=None):
    """
    Deletes files in the output directory that are older than 1 hour.
    The 'now' parameter is for testability.
    """
    print("Running cleanup task...")
    if now is None:
        now = time.time()

    output_dir = 'slushwave-vaporizer/backend/outputs'
    one_hour_ago = now - 3600

    if not os.path.isdir(output_dir):
        print(f"Cleanup task: Output directory {output_dir} not found.")
        return 0

    deleted_count = 0
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path):
            try:
                file_mod_time = os.path.getmtime(file_path)
                if file_mod_time < one_hour_ago:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")
                    deleted_count += 1
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")

    print(f"Cleanup task finished. Deleted {deleted_count} files.")
    return deleted_count

@celery_app.task
def adjust_task(base_file_path, effect_name, effect_params, new_file_id):
    """
    Applies a single adjustment to an existing audio file.
    Uses new_file_id to name the output. This is not a bound task.
    """
    try:
        output_dir = os.path.dirname(base_file_path)
        _base_name, file_ext = os.path.splitext(os.path.basename(base_file_path))
        output_filename = f"{new_file_id}{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        effect_func = getattr(effects, f"apply_{effect_name}")
        effect_func(base_file_path, output_path, **effect_params)

        return {'status': 'SUCCESS', 'result': output_path}
    except Exception as e:
        raise e

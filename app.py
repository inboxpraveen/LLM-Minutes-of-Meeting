from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from celery import Celery
from redis import Redis
import time
import uuid
import os
from dotenv import load_dotenv

from utils import convert_to_wav, crop_into_segments

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL')

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/0'

# Initialize Redis
redis = Redis(host='localhost', port=6379, db=0)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


if not os.path.exists(os.path.join(os.getcwd(),"temp")):
    os.makedirs(os.path.join(os.getcwd(),"temp"))

if not os.path.exists(os.path.join(os.getcwd(),"media_storage")):
    os.makedirs(os.path.join(os.getcwd(),"media_storage"))


@celery.task
def process_file(file_path, model_type):
    """
    Asynchronously process an audio file to generate a transcript and minutes of the meeting (MoM).
    
    Parameters:
    - file_path (str): The full path to the audio file to be processed.
    - model_type (str): The type of speech-to-text model to use for the transcription.
    
    Returns:
    str: A message indicating that the Minutes of Meeting have been prepared.
    
    Example:
    ```
    task = process_file.apply_async(('path/to/file', 'ASR_Model_Type'), time_limit=120)
    ```
    """
    output_wav_path = convert_to_wav(file_path)
    for chunk in crop_into_segments(output_wav_path):
        ## Convert each chunk into speech transcrripts
        ## and then generate a complete conversation
        print(f"processing chunk {chunk} in generator fashion")
    time.sleep(5)
    ## and then prepare minutes of meeting of whole conversation as input.

    return "Here is the MoM of this file."


@app.route('/status/<task_id>')
def task_status(task_id):
    """
    Fetches the status of a given Celery task.
    
    Parameters:
    - task_id (str): The ID of the Celery task whose status is to be checked.
    
    Returns:
    JSON: A JSON object containing the task's current status and any result if available.
    
    Example:
    ```
    GET /status/<task_id>
    ```
    """
    task = process_file.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        session['result'] = task.result
    return jsonify({"status": task.state, "result": session.get('result', None)})

@app.route('/result/<task_id>')
def show_result(task_id):
    """
    Renders the result page which will display the output of the processed audio file.
    
    Parameters:
    - task_id (str): The ID of the Celery task whose result is to be displayed.
    
    Returns:
    HTML: Rendered 'result.html' template.
    
    Example:
    ```
    GET /result/<task_id>
    ```
    """
    return render_template('result.html', task_id=task_id)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Index route that either renders the file upload form or initiates file processing.
    
    On a GET request, renders the index page with a form to upload an audio file and select a model.
    On a POST request, initiates asynchronous processing of the uploaded audio file.
    
    Returns:
    HTML or Redirect: Rendered 'index.html' template or a redirection to the result route.
    
    Example:
    ```
    GET /
    POST / (with 'file' and 'model_type' as form-data)
    ```
    """
    if request.method == 'POST':
        audio_file = request.files.get('file')
        model_type = request.form.get('model_type')
        
        unique_filename = str(uuid.uuid4()) + '_' + audio_file.filename
        file_path = os.path.join(os.getcwd(),"media_storage",unique_filename)
        audio_file.save(file_path)

        task = process_file.apply_async((file_path, model_type), time_limit=120)
        
        return redirect(url_for('show_result', task_id=task.id))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

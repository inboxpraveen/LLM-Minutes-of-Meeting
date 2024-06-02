import os

from flask import Flask, render_template, request, redirect, jsonify
from celery import Celery
from werkzeug.utils import secure_filename

from speech import SpeechRecognition
from summary import SummaryModel

from utils import convert_to_wav
from global_variables import BASE_DATA_UPLOADED_RECORDINGS_DIRECTORY

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = BASE_DATA_UPLOADED_RECORDINGS_DIRECTORY
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'wav', 'mp3'}


app.config.update(
    broker_url='redis://localhost:6379/0',  # Was CELERY_BROKER_URL
    result_backend='redis://localhost:6379/0'  # Was CELERY_RESULT_BACKEND
)


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['broker_url'], backend=app.config['result_backend'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/check_task/<task_id>')
def check_task(task_id):
    task = process_audio.AsyncResult(task_id)
    return jsonify({'status': task.status})


@app.route('/results/<task_id>')
def results(task_id):
    task = process_audio.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return render_template('results.html', minutes_of_meeting=task.result['summary'])
    return "Processing...", 200


@celery.task
def process_audio(audio_path):
    
    sr = SpeechRecognition()
    text = sr.transcribe(audio_path)
    sr.clear_memory()
    del sr
    
    mom = SummaryModel()
    minutes_of_meeting = mom.get_mom(text)
    mom.clear_memory()
    del mom
    
    return {'summary': minutes_of_meeting}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    audio_path = convert_to_wav(file_path)
    task = process_audio.delay(audio_path)
    
    return render_template('index.html', task_id=task.id)

if __name__ == '__main__':
    app.run(debug=True)

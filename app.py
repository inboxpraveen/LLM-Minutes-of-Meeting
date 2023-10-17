from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from celery import Celery
from redis import Redis
import time
import uuid
import os
from dotenv import load_dotenv

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


@celery.task
def process_file(file_path, model_type):
    time.sleep(10)
    return "Here is the MoM of this file."

@app.route('/status/<task_id>')
def task_status(task_id):
    task = process_file.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        session['result'] = task.result
    return jsonify({"status": task.state, "result": session.get('result', None)})

@app.route('/result/<task_id>')
def show_result(task_id):
    return render_template('result.html', task_id=task_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        audio_file = request.files.get('file')
        model_type = request.form.get('model_type')
        
        unique_filename = str(uuid.uuid4()) + '_' + audio_file.filename
        file_path = f"./{unique_filename}"
        audio_file.save(file_path)

        task = process_file.apply_async((file_path, model_type), time_limit=120)
        
        return redirect(url_for('show_result', task_id=task.id))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

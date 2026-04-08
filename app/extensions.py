from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery

db = SQLAlchemy()
login_manager = LoginManager()
celery = Celery()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

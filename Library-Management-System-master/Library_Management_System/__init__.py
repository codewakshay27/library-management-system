"""
The flask application package.
"""

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object("config.ProductionConfig")
db = SQLAlchemy(app)
login_manager = LoginManager(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()
from config import DevelopmentConfig
app.config.from_object(DevelopmentConfig)

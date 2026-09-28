"""Composition root — app factory wiring config, DB, error handling, blueprints.

Run with:  python app.py   (or `flask --app app run`)
"""
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService
from utils.dates import utc_now


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    CORS(app)
    logging.basicConfig(level=logging.INFO)
    db.init_app(app)
    # One NotificationService per app, used by task_controller on assignment.
    app.extensions['notification_service'] = NotificationService()

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'timestamp': str(utc_now())})

    @app.route('/')
    def index():
        return jsonify({'message': 'Task Manager API', 'version': '1.0'})

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)

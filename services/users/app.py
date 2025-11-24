"""
Users Service - Authentication and User Management.
Port: 5001
Team Member: Ahmad Yateem
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics

from configs.config import get_config
from database.connection import create_pool_from_env
from services.users.routes import users_bp
from utils.logger import setup_logger
from utils.responses import error_response

app = Flask(__name__)
config = get_config()
app.config.from_object(config)

CORS(app)
jwt = JWTManager(app)
metrics = PrometheusMetrics(app)

logger = setup_logger('users-service')

db_pool = create_pool_from_env()
app.config['DB_POOL'] = db_pool

app.register_blueprint(users_bp)

logger.info("Users Service started on port 5001")


@app.errorhandler(404)
def not_found(error):
    return error_response("Endpoint not found", status_code=404)


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return error_response("Internal server error", status_code=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=config.DEBUG)

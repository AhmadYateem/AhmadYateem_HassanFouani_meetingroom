"""
Reviews Service - Flask app using raw MySQL DAO.

Author: Hassan Fouani
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics

from configs.config import get_config
from database.connection import create_pool_from_env
from services.reviews.routes import bp
from utils.logger import setup_logger


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    CORS(app)
    jwt = JWTManager(app)
    metrics = PrometheusMetrics(app)
    
    logger = setup_logger('reviews-service')

    pool = create_pool_from_env()
    bp.pool = pool
    app.config['DB_POOL'] = pool
    app.register_blueprint(bp)
    
    logger.info("Reviews Service started")

    @app.route("/")
    def index():
        return {"service": "reviews", "status": "running"}

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("REVIEW_SERVICE_PORT", 5004))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False") == "True")

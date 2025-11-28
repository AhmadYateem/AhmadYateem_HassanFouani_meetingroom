"""
Flask application for Bookings Service.
Handles booking management with conflict detection.

Author: Ahmad Yateem
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics

from configs.config import DevelopmentConfig
from database.connection import create_pool_from_env
from services.bookings.routes import bookings_bp


def create_app(config_class=DevelopmentConfig):
    """
    Create and configure Flask application.

    Args:
        config_class: Configuration class

    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)
    
    CORS(app)
    
    jwt = JWTManager(app)
    
    metrics = PrometheusMetrics(app)
    
    db_pool = create_pool_from_env()
    app.config['DB_POOL'] = db_pool
    
    app.register_blueprint(bookings_bp)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.

        Returns:
            Health status
        """
        return jsonify({
            'status': 'healthy',
            'service': 'bookings'
        }), 200
    
    @app.errorhandler(404)
    def not_found(error):
        """
        Handle 404 errors.

        Args:
            error: Error object

        Returns:
            JSON error response
        """
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle 500 errors.

        Args:
            error: Error object

        Returns:
            JSON error response
        """
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'status_code': 500
        }), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5003,
        debug=True
    )

"""
Rooms Service - Flask app using raw MySQL DAO.
"""

import os
from flask import Flask
from flask_cors import CORS

from database import create_pool_from_env
from services.rooms.routes import bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Create MySQL pool and attach to blueprint for DAO usage
    pool = create_pool_from_env("DATABASE")
    bp.pool = pool  # type: ignore[attr-defined]
    app.register_blueprint(bp)

    @app.route("/")
    def index():
        return {"service": "rooms", "status": "running"}

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("ROOM_SERVICE_PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False") == "True")

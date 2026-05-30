from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import logging

# Explicitly load the backend/.env file to ensure environment variables
# (like OPENROUTER_API_KEY / OPENROUTER_API_URL) are available when the
# app is started from the repository root.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

mongo = PyMongo()

# Initialize Limiter at the module level; will be attached to app in create_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


class _FaviconLogFilter(logging.Filter):
    def filter(self, record):
        try:
            return '/favicon.ico' not in record.getMessage()
        except Exception:
            return True


def create_app():
    # Serve frontend static files from the workspace `frontend` folder when running the backend.
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
    app = Flask(__name__, static_folder=static_dir, static_url_path='')
    
    # Configuration
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/dietassist')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    mongo.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configure limiter storage for production if Redis URL is provided
    redis_url = os.getenv('RATELIMIT_STORAGE_URL') or os.getenv('REDIS_URL')
    global limiter
    if redis_url:
        # Re-create limiter with a Redis storage backend
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"], storage_uri=redis_url)
        except Exception:
            # If redis support isn't available, fall back to existing in-memory limiter
            pass

    # Initialize limiter with the app
    limiter.init_app(app)

    # Hide noisy favicon request logs (they are not errors).
    try:
        logging.getLogger('werkzeug').addFilter(_FaviconLogFilter())
    except Exception:
        pass

    # Initialize Sentry if DSN is provided (include release & environment tags when available)
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        SENTRY_DSN = os.getenv('SENTRY_DSN')
        if SENTRY_DSN:
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.0,
                release=os.getenv('SENTRY_RELEASE'),
                environment=os.getenv('SENTRY_ENV', os.getenv('FLASK_ENV', 'production'))
            )
    except Exception:
        # Non-fatal: allow app to run without sentry installed
        pass

    # Friendly rate-limit handler: return JSON + preserve Retry-After header from the limiter
    try:
        from flask_limiter.errors import RateLimitExceeded

        @app.errorhandler(RateLimitExceeded)
        def rate_limit_handler(e):
            # Try to extract limiter headers if available
            headers = {}
            try:
                if hasattr(e, 'get_headers'):
                    headers = dict(e.get_headers())
            except Exception:
                headers = {}

            response = {
                'error': 'Too many requests',
                'message': 'You have reached the request limit. Please try again later.'
            }
            from flask import jsonify
            return jsonify(response), 429, headers
    except Exception:
        # If limiter or errors aren't available, skip custom handler
        pass    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.patient import patient_bp
    from app.routes.caretaker import caretaker_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.feedback import feedback_bp
    from app.routes.ui import ui_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(caretaker_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(ui_bp)

    # Serve the frontend index at the root for convenience
    try:
        from flask import send_from_directory

        @app.route('/')
        def index():
            return send_from_directory(app.static_folder, 'index.html')

        @app.route('/<path:path>')
        def static_proxy(path):
            # Serve other frontend files (css, js, pages)
            return send_from_directory(app.static_folder, path)

        @app.route('/favicon.ico')
        def favicon():
            # Quiet favicon 404s when no icon file is present.
            return '', 204
    except Exception:
        # If send_from_directory is unavailable, skip adding these routes
        pass
    
    return app

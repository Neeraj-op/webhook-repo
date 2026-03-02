from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='../static')
    
    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    
    # Initialize extensions
    from app.extensions import init_db
    init_db(app)
    
    # Register blueprints/routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
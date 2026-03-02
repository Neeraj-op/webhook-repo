from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"📡 Webhook endpoint: http://{host}:{port}/webhook/receiver")
    print(f"🌐 Dashboard: http://{host}:{port}/")
    
    app.run(host=host, port=port, debug=debug)
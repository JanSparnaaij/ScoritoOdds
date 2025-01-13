from dotenv import load_dotenv
import os
from app import create_app

# Load environment variables from the .env file
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Get the PORT from the environment (Heroku sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the app with dynamic port and production-ready host
    app.run(host="0.0.0.0", port=port, debug=False)

from dotenv import load_dotenv
import os
from app import create_app

# Load environment variables from the .env file
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    from os import environ
    print(f"SECRET_KEY: {environ.get('SECRET_KEY')}")
    app.run(debug=True)



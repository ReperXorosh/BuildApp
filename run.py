import os
from app import create_app

from dotenv import load_dotenv
load_dotenv('.env')

application = create_app()

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)
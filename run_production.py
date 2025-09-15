import os
from app import create_app

from dotenv import load_dotenv
load_dotenv('.env')

application = create_app()

if __name__ == '__main__':
    # Production настройки
    application.run(
        debug=False, 
        host='0.0.0.0', 
        port=5000,
        threaded=True,
        processes=4  # Несколько процессов для production
    )

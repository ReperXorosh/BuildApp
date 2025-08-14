import os

from flask import Flask
from .extensions import db, login_manager
from .config import Config

from .routes.users import user
from .routes.main import main
from .routes.objects import objects

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config.setdefault("MAX_CONTENT_LENGTH", 2 * 1024 * 1024)  # 2 МБ
    app.config.setdefault(
        "UPLOAD_FOLDER",
        os.path.join(app.root_path, "static", "uploads", "avatars")
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


    app.register_blueprint(user)
    app.register_blueprint(main)
    app.register_blueprint(objects)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "user.sign_in"  # куда редиректить неавторизованных
    login_manager.login_message_category = "warning"

    with app.app_context():
        db.create_all()

    return app


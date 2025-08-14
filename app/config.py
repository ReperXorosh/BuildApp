import os


class Config(object):
    USER = os.environ.get('USER', 'sankficeba')
    PASSWORD = os.environ.get("PASSWORD", '12345678')
    HOST = os.environ.get("HOST", "localhost")
    PORT = os.environ.get("PORT", '5532')
    DATABASE = os.environ.get("DATABASE", 'mydb')

    SQLALCHEMY_DATABASE_URI = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
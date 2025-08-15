import os


class Config(object):
    USER = os.environ.get('POSTGRES_USER', 'sankficeba')
    PASSWORD = os.environ.get("POSTGRES_PASSWORD", '12345678')
    HOST = os.environ.get("POSTGRES_HOST", "postgres")
    PORT = os.environ.get("POSTGRES_PORT", '5432')
    DATABASE = os.environ.get("POSTGRES_DB", 'mydb')

    SQLALCHEMY_DATABASE_URI = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
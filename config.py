class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://darts_user:4493abcd@localhost/dartsguesser'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'lol123'  # Use a strong secret key for sessions

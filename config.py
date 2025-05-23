import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'flask_prod_2025!')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', (
        'mysql+pymysql://banco_superuser:admin1234%23@servidortcc.mysql.database.azure.com:3306/banco_tcc'
    ))

    SQLALCHEMY_TRACK_MODIFICATIONS = False
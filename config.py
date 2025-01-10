# config.py
class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://polc6219_admin:Bismillah123@203.175.8.151:3306/polc6219_class_gojp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CORS Settings
    CORS_SETTINGS = {
        r"/classgojp/*": {
            "origins": [
                "http://localhost:4001",
                "http://127.0.0.1:4001",
                "http://localhost:4200",
                "http://127.0.0.1:4200",
                "http://localhost:4201",
                "http://127.0.0.1:4201",
                "https://class-gojp.polaris.my.id",
                "https://nihongo.tomodachi.my.id",
            ]
        }
    }
import os

# Base directory of project
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True

    # Secret key (safe and backward compatible)
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)

    # ✅ SAFE DATABASE PATH FIX (without breaking existing database)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir, "Library_Management_System", "library.db"
    )

    # IMPORTANT FIX 1 (False karo)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IMPORTANT FIX 2 (database lock fix)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False
        }
    }


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestConfig(Config):
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

    # Test database same location
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir, "Library_Management_System", "library.db"
    )
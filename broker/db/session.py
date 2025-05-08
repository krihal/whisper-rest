from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
from sqlmodel import SQLModel
from settings import get_settings

settings = get_settings()


@lru_cache
def init():
    db_url = settings.DATABASE_URL
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    instance = init()
    return instance()


def handle_database_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = None
        try:
            session = get_session()
            kwargs["session"] = session

            return func(*args, **kwargs)
        except Exception as e:
            print(f"Database error has occurred: {e}")
            raise
        finally:
            if session:
                session.close()

    return wrapper

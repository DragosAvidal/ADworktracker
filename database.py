from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Încărcăm variabilele de mediu
load_dotenv()

# Obținem calea absolută către directorul aplicației
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurare URL bază de date
# În producție (Heroku) vom folosi DATABASE_URL din variabilele de mediu
# Local vom folosi SQLite
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "employee_tracker.db")}')

# Modifică URL-ul PostgreSQL dacă este necesar (specific Heroku)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configurare engine cu parametri specifici pentru fiecare tip de bază de date
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
        pool_recycle=3600
    )
else:
    # Pentru PostgreSQL nu avem nevoie de connect_args specifice SQLite
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

# Configurare sesiune
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager pentru gestionarea sesiunilor de bază de date"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
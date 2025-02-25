"""
Script pentru inițializarea bazei de date
Rulați acest script o singură dată pentru a crea baza de date și tabelele necesare
"""

from database import engine, Base, SessionLocal
from models import User
from werkzeug.security import generate_password_hash

def init_database():
    # Creează toate tabelele
    Base.metadata.create_all(bind=engine)
    
    # Verifică dacă există deja un utilizator admin
    db = SessionLocal()
    admin = db.query(User).filter_by(username='admin').first()
    
    # Dacă nu există, creează contul admin
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin'),
            email='admin@example.com',
            is_admin=True
        )
        db.add(admin)
        db.commit()
    
    db.close()

if __name__ == '__main__':
    print("Inițializare bază de date...")
    init_database()
    print("Baza de date a fost inițializată cu succes!")
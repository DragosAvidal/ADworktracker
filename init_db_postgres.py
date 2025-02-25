from models import Base
from database import engine

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Crearea tabelelor în baza de date...")
    init_db()
    print("Tabelele au fost create cu succes!")
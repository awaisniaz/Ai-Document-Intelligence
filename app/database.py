from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker,session


DATABASE_URL = (
    "postgresql+psycopg2://postgres:awaisniaz@localhost:5432/"
    "ai-document-intellegence"
)


engine = create_engine(DATABASE_URL, echo=True)    

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db: session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass


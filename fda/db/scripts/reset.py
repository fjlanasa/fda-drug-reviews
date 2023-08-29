from sqlmodel import Session, SQLModel

from fda.db.engine import engine

if __name__ == "__main__":
    session = Session(engine)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    session.commit()

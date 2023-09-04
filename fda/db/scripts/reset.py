from sqlmodel import Session, SQLModel

from fda.db.engine import engine
from fda.db.models import (Application, ApplicationDocument, DocumentSegment,
                           Embedding, Processing)

if __name__ == "__main__":
    with Session(engine) as session:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        session.commit()

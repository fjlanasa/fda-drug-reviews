import os

from sqlmodel import create_engine

postgres_url = os.environ.get(
    "POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432"
)
print(postgres_url)
engine = create_engine(postgres_url)

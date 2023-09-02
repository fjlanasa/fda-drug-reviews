import asyncio
import os
from sys import argv
from typing import List

import httpx
from sqlmodel import Session, select

from fda.db.engine import engine
from fda.db.models import DocumentSegment, Embedding

OPENAI_KEY = os.environ["OPENAI_KEY"]

BATCH_SIZE = 100


async def calculate_embeddings(inputs: List[str]) -> List[List[float]]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "input": inputs,
                "model": "text-embedding-ada-002",
            },
        )
        embeddings = res.json()["data"]
        return embeddings


async def create_embeddings(limit: int = None, offset: int = 0) -> None:
    with Session(engine) as session:
        rows = session.query(DocumentSegment).limit(limit).offset(offset).count()
        batches = rows // BATCH_SIZE + 1
        for i in range(batches):
            print(f"Processing batch {i}")
            statement = select(DocumentSegment).limit(BATCH_SIZE).offset(i * BATCH_SIZE)
            segments = session.exec(statement).all()
            embeddings = await calculate_embeddings([seg.content for seg in segments])
            embeddings = [
                Embedding(doc_segment=seg, embedding=emb["embedding"])
                for seg, emb in zip(segments, embeddings)
            ]
            session.add_all(embeddings)
            session.commit()


if __name__ == "__main__":
    offset = argv[1] if len(argv) > 1 else 0
    limit = argv[2] if len(argv) > 2 else None
    print(f"offset: {offset}, limit: {limit}")
    asyncio.run(create_embeddings(limit=limit, offset=offset))

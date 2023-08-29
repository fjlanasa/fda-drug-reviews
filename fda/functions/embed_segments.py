import asyncio
import os
from sys import argv
from typing import List

import httpx
from sqlmodel import Session, select

from fda.db.engine import engine
from fda.db.models import DocumentSegment, Embedding

open_ai_key = os.environ["OPENAI_KEY"]


async def calculate_embeddings(inputs: List[str]) -> List[List[float]]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {open_ai_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": inputs,
                "model": "text-embedding-ada-002",
            },
        )
        embeddings = res.json()["data"]
        return embeddings


async def create_embeddings(limit: int = None, offset: int = 0) -> List[Embedding]:
    with Session(engine) as session:
        statement = select(DocumentSegment).limit(limit).offset(offset)
        segments = session.exec(statement).all()
        embeddings = await calculate_embeddings([seg.content for seg in segments])
        embeddings = [
            Embedding(doc_segment=seg, embedding=emb["embedding"])
            for seg, emb in zip(segments, embeddings)
        ]
        session.add_all(embeddings)
        session.commit()
        return embeddings


if __name__ == "__main__":
    offset = argv[1] if len(argv) > 1 else 0
    limit = argv[2] if len(argv) > 2 else None
    print(f"offset: {offset}, limit: {limit}")
    asyncio.run(create_embeddings(limit=limit, offset=offset))

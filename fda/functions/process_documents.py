import asyncio
import os
from sys import argv
from typing import List

import httpx
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlmodel import Session, select

from fda.db.engine import engine
from fda.db.models import ApplicationDocument, DocumentSegment, Embedding
from fda.functions.pdf_to_text import pdf_to_text

open_ai_key = os.getenv("OPENAI_KEY")


async def create_segments(doc: ApplicationDocument) -> List[DocumentSegment]:
    if doc.url.endswith("pdf"):
        text = await pdf_to_text(doc.url)
    elif doc.url.endswith("cfm"):
        directory = "/".join(doc.url.split("/")[:-1])
        text = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # parsing cfm files is a bit more complicated
            res = await client.get(doc.url)
            soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all(
                lambda tag: tag.has_attr("href") and tag["href"].endswith(".pdf")
            )
            for link in links:
                pdf_url = os.path.join(directory, link["href"])
                pdf_text = await pdf_to_text(pdf_url)
                text += pdf_text
    else:
        raise Exception(f"Unknown document type: {doc.url}")
    splitter = RecursiveCharacterTextSplitter()
    segments = splitter.create_documents(text)
    return [
        DocumentSegment(
            document_id=doc.id,
            segment_number=i,
            content=segment.page_content,
        )
        for i, segment in enumerate(segments)
    ]


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


async def create_embeddings(segments: List[DocumentSegment]) -> List[Embedding]:
    embeddings = await calculate_embeddings([seg.content for seg in segments])
    return [
        Embedding(doc_segment=seg, embedding=emb["embedding"])
        for seg, emb in zip(segments, embeddings)
    ]


async def process_document(doc):
    segments = await create_segments(doc)
    embeddings = await create_embeddings(segments)
    return doc, segments, embeddings


async def process_documents(limit=None, offset=0):
    if open_ai_key:
        raise Exception("OPENAI_KEY environment variable is not set")
    with Session(engine) as session:
        statement = (
            select(ApplicationDocument)
            .offset(offset)
            .limit(limit)
        )
        docs = session.exec(statement)
        for doc in docs:
            try:
                _, _, embeddings = await process_document(doc)
            except Exception as e:
                print(f"Error processing document {doc.id}: {e}")
                continue
            session.add_all(embeddings)
        session.commit()


if __name__ == "__main__":
    offset = argv[1] if len(argv) > 1 else 0
    limit = argv[2] if len(argv) > 2 else None
    print(f"offset: {offset}, limit: {limit}")
    asyncio.run(process_documents(limit=limit, offset=offset))

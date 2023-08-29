import asyncio
import multiprocessing
import os
from sys import argv
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlmodel import Session, select

from fda.db.engine import engine
from fda.db.models import ApplicationDocument, DocumentSegment
from fda.functions.pdf_to_text import pdf_to_text


def split_document(doc: ApplicationDocument) -> List[DocumentSegment]:
    try:
        if doc.url.endswith("pdf"):
            text = asyncio.run(pdf_to_text(doc.url))
        elif doc.url.endswith("cfm") or doc.url.endswith("htm"):
            directory = "/".join(doc.url.split("/")[:-1])
            text = []
            res = httpx.get(doc.url, follow_redirects=True)
            soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all(
                lambda tag: tag.has_attr("href") and tag["href"].endswith(".pdf")
            )
            for link in links:
                pdf_url = os.path.join(directory, link["href"])
                pdf_text = asyncio.run(pdf_to_text(pdf_url))
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
    except Exception as e:
        print(f"Error splitting document {doc.id}, {doc.url}, {e}")
        return []


def split_documents(
    offset: int = 0, limit: Optional[int] = None
) -> List[DocumentSegment]:
    with Session(engine) as session:
        statement = select(ApplicationDocument).offset(offset).limit(limit)
        docs = session.exec(statement)
        with multiprocessing.Pool() as pool:
            segments = pool.map(split_document, docs)
            segments = [item for sublist in segments for item in sublist]
            session.add_all(segments)
            session.commit()
            return segments


if __name__ == "__main__":
    offset = argv[1] if len(argv) > 1 else 0
    limit = argv[2] if len(argv) > 2 else None
    print(f"offset: {offset}, limit: {limit}")
    split_documents(limit=limit, offset=offset)

import asyncio
from sys import argv

from sqlmodel import Session, select

from fda.db.engine import engine
from fda.db.models import DocumentSegment, Embedding
from fda.functions.process_documents import calculate_embeddings


async def query_documents(query: str, limit: int = 10, offset: int = 0):
    query = await calculate_embeddings([query])
    with Session(engine) as session:
        statement = (
            select(Embedding)
            .order_by(Embedding.embedding.cosine_distance(query[0]["embedding"]))
            .limit(1)
        )
        result = session.exec(statement)
        embedding = result.first()
        statement = (
            select(DocumentSegment)
            .where(DocumentSegment.document_id == embedding.doc_segment.document_id)
            .where(
                DocumentSegment.segment_number
                > embedding.doc_segment.segment_number - 1
            )
            .where(
                DocumentSegment.segment_number
                < embedding.doc_segment.segment_number + 1
            )
        )
        results = session.exec(statement)
        print("\n\n".join([seg.content for seg in results.all()]))


if __name__ == "__main__":
    query = argv[1]
    asyncio.run(query_documents(query))

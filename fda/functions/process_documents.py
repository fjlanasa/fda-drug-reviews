import asyncio
from sys import argv

from fda.functions import split_documents
from fda.functions.embed_segments import create_embeddings


async def process_documents(limit=None, offset=0):
    split_documents(limit=limit, offset=offset)
    await create_embeddings(limit=limit, offset=offset)


if __name__ == "__main__":
    offset = argv[1] if len(argv) > 1 else 0
    limit = argv[2] if len(argv) > 2 else None
    print(f"offset: {offset}, limit: {limit}")
    asyncio.run(process_documents(limit=limit, offset=offset))

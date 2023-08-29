import asyncio
from io import BytesIO
from sys import argv

import httpx
from PIL import Image
from PyPDF2 import PageObject, PdfReader
from pytesseract import image_to_string


def page_to_text(page: PageObject) -> str:
    print("Extracting text from page.")
    text = page.extract_text()
    if not text:
        print("No text found. Trying to extract text from images.")
        for image in page.images:
            img = Image.open(BytesIO(image.data))
            image_text = image_to_string(img)
            if image_text:
                text += image_text
    return text


async def pdf_to_text(url: str) -> list[str]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.get(url)
        _bytes = BytesIO(res.content)
        pdf = PdfReader(_bytes)
        text = []
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i}")
            text.append(page_to_text(page))
        return text


if __name__ == "__main__":
    url = argv[1]
    print(asyncio.run(pdf_to_text(url)))

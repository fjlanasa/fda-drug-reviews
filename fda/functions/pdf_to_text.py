from io import BytesIO
from sys import argv

import httpx
from PIL import Image
from PyPDF2 import PageObject, PdfReader
from pytesseract import image_to_string


def page_to_text(page: PageObject) -> str:
    text = page.extract_text()
    if not text:
        for image in page.images:
            img = Image.open(BytesIO(image.data))
            image_text = image_to_string(img)
            if image_text:
                text += image_text
    return text


def pdf_to_text(url: str) -> list[str]:
    print(f"Processing url {url}")
    res = httpx.get(url, follow_redirects=True)
    assert res.status_code == 200
    _bytes = BytesIO(res.content)
    pdf = PdfReader(_bytes)
    text = []
    for i, page in enumerate(pdf.pages):
        print(f"Processing page {i} of {len(pdf.pages)}")
        text.append(page_to_text(page))
    return text


if __name__ == "__main__":
    url = argv[1]
    pdf_to_text(url)

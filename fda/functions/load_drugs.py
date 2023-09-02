import json
import os
import shutil
from datetime import datetime

import httpx
from sqlmodel import Session, delete

from fda.db.engine import engine
from fda.db.models import (ActiveIngredient, Application, ApplicationDocument,
                           OpenFDA, Processing, Product, Submission)


def load_drugs(url):
    now = datetime.now().isoformat()
    downloads = httpx.get("https://api.fda.gov/download.json").json()
    drugs_url = downloads["results"]["drug"]["drugsfda"]["partitions"][0]["file"]
    res = httpx.get(drugs_url)
    with open("drugs.zip", "wb") as f:
        f.write(res.content)
    shutil.unpack_archive("drugs.zip", "drugs")
    files = os.listdir("drugs")
    with open(os.path.join("drugs", files[0])) as f:
        drugs = json.load(f)["results"]

    with Session(engine) as session:
        applications = [
            Application(
                application_number=drug["application_number"],
                sponsor_name=drug["sponsor_name"],
                openfda=OpenFDA(**drug["openfda"]) if "openfda" in drug else None,
                products=[
                    Product(
                        product_number=product["product_number"],
                        reference_drug=product["reference_drug"],
                        brand_name=product["brand_name"],
                        reference_standard=product.get("reference_standard"),
                        dosage_form=product["dosage_form"],
                        route=product.get("route"),
                        marketing_status=product["marketing_status"],
                        te_code=product.get("te_code"),
                        active_ingredients=[
                            ActiveIngredient(**active_ingredient)
                            for active_ingredient in product["active_ingredients"]
                        ],
                    )
                    for product in drug.get("products", [])
                ],
                submissions=[
                    Submission(
                        submission_type=submission["submission_type"],
                        submission_number=submission["submission_number"],
                        submission_status=submission["submission_status"],
                        submission_status_date=submission.get("submission_status_date"),
                        submission_class_code=submission.get("submission_class_code"),
                        submission_class_code_description=submission.get(
                            "submission_class_code_description"
                        ),
                        application_docs=[
                            ApplicationDocument(
                                fda_id=application_doc["id"],
                                url=application_doc["url"],
                                date=application_doc["date"],
                                type=application_doc["type"],
                            )
                            for application_doc in submission.get(
                                "application_docs", []
                            )
                        ],
                    )
                    for submission in drug.get("submissions", [])
                ],
            )
            for drug in drugs
        ]
        processing = Processing(processing_datetime=now, applications=applications)
        session.add(processing)
        delete_statement = delete(Processing).where(
            Processing.processing_datetime != now
        )
        session.execute(delete_statement)
        session.commit()


if __name__ == "__main__":
    load_drugs("https://api.fda.gov/download.json")

from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Index, Text, cast
from sqlalchemy.dialects.postgresql import JSONB, array
from sqlmodel import Field, Relationship, SQLModel


class Processing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    processing_datetime: str = ...

    applications: List["Application"] = Relationship(
        back_populates="processing",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    application_number: str = ...
    sponsor_name: str = ...
    openfda: Optional["OpenFDA"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    products: List["Product"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    submissions: List["Submission"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    processing_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("processing.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    processing: Optional["Processing"] = Relationship(
        back_populates="applications",
    )


class Embedding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # 1536 is the dimensionality of the text-embedding-ada-002 embeddings
    # See https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))

    doc_segment_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("documentsegment.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    doc_segment: Optional["DocumentSegment"] = Relationship(
        back_populates="embeddings",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )


class DocumentSegment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    segment_number: int = ...
    title: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    content: str = ...

    embeddings: Optional["Embedding"] = Relationship(
        back_populates="doc_segment",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    document_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("applicationdocument.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
        nullable=False,
    )
    document: Optional["ApplicationDocument"] = Relationship(
        back_populates="document_segments",
    )


class ApplicationDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fda_id: str = Field(...)
    url: str = Field(...)
    date: str = Field(...)
    type: str = Field(...)
    title: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )

    document_segments: List["DocumentSegment"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    submission_id: int = Field(
        sa_column=Column(
            ForeignKey("submission.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    submission: Optional["Submission"] = Relationship(
        back_populates="application_docs",
    )


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submission_type: str = ...
    submission_number: str = ...
    submission_status: str = ...
    submission_status_date: Optional[str] = None
    submission_class_code: Optional[str] = None
    submission_class_code_description: Optional[str] = None

    application_docs: List["ApplicationDocument"] = Relationship(
        back_populates="submission",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    application_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    application: Optional["Application"] = Relationship(
        back_populates="submissions",
    )


class ActiveIngredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = ...
    strength: Optional[str] = None

    product_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("product.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    product: Optional["Product"] = Relationship(
        back_populates="active_ingredients",
    )


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_number: str = ...
    reference_drug: str = ...
    brand_name: str = ...
    reference_standard: Optional[str] = None
    dosage_form: str = ...
    route: Optional[str] = None
    marketing_status: str = ...
    te_code: Optional[str] = None

    active_ingredients: List[ActiveIngredient] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    application_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    application: Optional["Application"] = Relationship(
        back_populates="products",
    )


class OpenFDA(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brand_name: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    generic_name: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    manufacturer_name: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    product_ndc: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    product_type: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    route: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    substance_name: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    rxcui: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    spl_id: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    spl_set_id: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    package_ndc: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )
    unii: Optional[List[str]] = Field(
        default=[],
        sa_column=Column(
            JSONB,
            nullable=False,
            default=cast(array([], type_=Text), JSONB),
        ),
    )

    application_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
            default=None,
        ),
    )
    application: Optional["Application"] = Relationship(
        back_populates="openfda",
    )

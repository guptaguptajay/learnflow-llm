"""PostgreSQL metadata store using SQLAlchemy 2.0."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# SQLAlchemy Models
# ============================================================================


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Document(Base):
    """Document model."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    format = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")
    file_size_bytes = Column(Integer, nullable=False, default=0)
    document_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    topics = relationship("TopicNode", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Document chunk model."""

    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    topic_mappings = relationship(
        "TopicVectorMapping", back_populates="chunk", cascade="all, delete-orphan"
    )


class TopicNode(Base):
    """Topic node model for mind map structure."""

    __tablename__ = "topic_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    title = Column(String, nullable=False)
    level = Column(Integer, nullable=False, default=0)
    parent_id = Column(String, ForeignKey("topic_nodes.id"), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="topics")
    parent = relationship("TopicNode", remote_side=[id], backref="children")
    vector_mappings = relationship(
        "TopicVectorMapping", back_populates="topic", cascade="all, delete-orphan"
    )


class TopicVectorMapping(Base):
    """Mapping between topics and vector IDs."""

    __tablename__ = "topic_vector_mappings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String, ForeignKey("topic_nodes.id"), nullable=False)
    vector_id = Column(String, nullable=False)
    chunk_id = Column(String, ForeignKey("document_chunks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    topic = relationship("TopicNode", back_populates="vector_mappings")
    chunk = relationship("DocumentChunk", back_populates="topic_mappings")


# ============================================================================
# Repository Class
# ============================================================================


class MetadataRepository:
    """Repository for metadata operations on PostgreSQL."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize metadata repository.

        Args:
            database_url: PostgreSQL connection URL. If None, uses settings.
        """
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=settings.debug, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False
        )

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped successfully")

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    # Document Operations
    def create_document(
        self, filename: str, file_path: str, format: str, file_size_bytes: int
    ) -> Document:
        """Create a new document record.

        Args:
            filename: Original filename
            file_path: Path to stored file
            format: Document format (pdf, epub, mobi)
            file_size_bytes: File size in bytes

        Returns:
            Created Document instance
        """
        with self.get_session() as session:
            document = Document(
                filename=filename,
                file_path=file_path,
                format=format,
                file_size_bytes=file_size_bytes,
                status="uploaded",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            logger.info(f"Created document: {document.id}")
            return document

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document instance or None
        """
        with self.get_session() as session:
            return session.query(Document).filter(Document.id == document_id).first()

    def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document status.

        Args:
            document_id: Document identifier
            status: New status

        Returns:
            True if updated, False otherwise
        """
        with self.get_session() as session:
            document = session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                document.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Updated document {document_id} status to {status}")
                return True
            return False

    # Chunk Operations
    def create_chunks(self, document_id: str, chunks_data: List[dict]) -> List[DocumentChunk]:
        """Create document chunks.

        Args:
            document_id: Parent document ID
            chunks_data: List of chunk dictionaries with 'text', 'chunk_index', 'metadata'

        Returns:
            List of created DocumentChunk instances
        """
        with self.get_session() as session:
            chunks = []
            for chunk_data in chunks_data:
                chunk = DocumentChunk(
                    document_id=document_id,
                    text=chunk_data["text"],
                    chunk_index=chunk_data["chunk_index"],
                    chunk_metadata=chunk_data.get("metadata", {}),
                )
                session.add(chunk)
                chunks.append(chunk)

            session.commit()
            for chunk in chunks:
                session.refresh(chunk)
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks

    def get_chunks_by_document(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of DocumentChunk instances
        """
        with self.get_session() as session:
            return (
                session.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )

    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get chunk by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            DocumentChunk instance or None
        """
        with self.get_session() as session:
            return session.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()

    # Topic Operations
    def create_topic(
        self, document_id: str, title: str, level: int, parent_id: Optional[str] = None
    ) -> TopicNode:
        """Create a topic node.

        Args:
            document_id: Parent document ID
            title: Topic title
            level: Hierarchy level
            parent_id: Parent topic ID (optional)

        Returns:
            Created TopicNode instance
        """
        with self.get_session() as session:
            topic = TopicNode(
                document_id=document_id, title=title, level=level, parent_id=parent_id
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            logger.info(f"Created topic: {topic.id} - {title}")
            return topic

    def get_topic_by_id(self, topic_id: str) -> Optional[TopicNode]:
        """Get topic by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            TopicNode instance or None
        """
        with self.get_session() as session:
            return session.query(TopicNode).filter(TopicNode.id == topic_id).first()

    def get_topics_by_document(
        self, document_id: str, level: Optional[int] = None
    ) -> List[TopicNode]:
        """Get topics for a document, optionally filtered by level.

        Args:
            document_id: Document identifier
            level: Optional hierarchy level filter

        Returns:
            List of TopicNode instances
        """
        with self.get_session() as session:
            query = session.query(TopicNode).filter(TopicNode.document_id == document_id)
            if level is not None:
                query = query.filter(TopicNode.level == level)
            return query.order_by(TopicNode.level, TopicNode.created_at).all()

    def get_subtopics_by_parent(self, parent_id: str) -> List[TopicNode]:
        """Get subtopics for a parent topic.

        Args:
            parent_id: Parent topic ID

        Returns:
            List of TopicNode instances
        """
        with self.get_session() as session:
            return (
                session.query(TopicNode)
                .filter(TopicNode.parent_id == parent_id)
                .order_by(TopicNode.created_at)
                .all()
            )

    def update_topic_summary(self, topic_id: str, summary: str) -> bool:
        """Update topic summary.

        Args:
            topic_id: Topic identifier
            summary: Summary text

        Returns:
            True if updated, False otherwise
        """
        with self.get_session() as session:
            topic = session.query(TopicNode).filter(TopicNode.id == topic_id).first()
            if topic:
                topic.summary = summary
                topic.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Updated topic {topic_id} summary")
                return True
            return False

    # Topic-Vector Mapping Operations
    def create_topic_vector_mappings(
        self, topic_id: str, vector_chunk_pairs: List[tuple[str, str]]
    ) -> List[TopicVectorMapping]:
        """Create topic-vector-chunk mappings.

        Args:
            topic_id: Topic identifier
            vector_chunk_pairs: List of (vector_id, chunk_id) tuples

        Returns:
            List of created TopicVectorMapping instances
        """
        with self.get_session() as session:
            mappings = []
            for vector_id, chunk_id in vector_chunk_pairs:
                mapping = TopicVectorMapping(
                    topic_id=topic_id, vector_id=vector_id, chunk_id=chunk_id
                )
                session.add(mapping)
                mappings.append(mapping)

            session.commit()
            for mapping in mappings:
                session.refresh(mapping)
            logger.info(f"Created {len(mappings)} vector mappings for topic {topic_id}")
            return mappings

    def get_chunks_by_topic(self, topic_id: str) -> List[DocumentChunk]:
        """Get all chunks associated with a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            List of DocumentChunk instances
        """
        with self.get_session() as session:
            return (
                session.query(DocumentChunk)
                .join(TopicVectorMapping, TopicVectorMapping.chunk_id == DocumentChunk.id)
                .filter(TopicVectorMapping.topic_id == topic_id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )

    def get_vector_ids_by_topic(self, topic_id: str) -> List[str]:
        """Get all vector IDs associated with a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            List of vector IDs
        """
        with self.get_session() as session:
            mappings = (
                session.query(TopicVectorMapping)
                .filter(TopicVectorMapping.topic_id == topic_id)
                .all()
            )
            return [mapping.vector_id for mapping in mappings]


"""Service layer tests."""

import pytest

from app.repositories.metadata_store import MetadataRepository


class TestMetadataRepository:
    """Test metadata repository."""

    @pytest.fixture
    def repo(self):
        """Create test repository with in-memory SQLite."""
        repo = MetadataRepository(database_url="sqlite:///:memory:")
        repo.create_tables()
        return repo

    def test_create_document(self, repo):
        """Test creating a document."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.status == "uploaded"

    def test_get_document(self, repo):
        """Test retrieving a document."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        retrieved = repo.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id

    def test_update_document_status(self, repo):
        """Test updating document status."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        result = repo.update_document_status(doc.id, "processed")
        assert result is True
        updated = repo.get_document(doc.id)
        assert updated.status == "processed"

    def test_create_chunks(self, repo):
        """Test creating document chunks."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        chunks_data = [
            {"text": "Chunk 1", "chunk_index": 0, "metadata": {}},
            {"text": "Chunk 2", "chunk_index": 1, "metadata": {}},
        ]
        chunks = repo.create_chunks(doc.id, chunks_data)
        assert len(chunks) == 2
        assert chunks[0].text == "Chunk 1"

    def test_create_topic(self, repo):
        """Test creating a topic."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        topic = repo.create_topic(
            document_id=doc.id,
            title="Test Topic",
            level=1,
            parent_id=None,
        )
        assert topic.id is not None
        assert topic.title == "Test Topic"
        assert topic.level == 1

    def test_get_topics_by_document(self, repo):
        """Test retrieving topics by document."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        repo.create_topic(doc.id, "Topic 1", 1, None)
        repo.create_topic(doc.id, "Topic 2", 1, None)

        topics = repo.get_topics_by_document(doc.id)
        assert len(topics) == 2

    def test_update_topic_summary(self, repo):
        """Test updating topic summary."""
        doc = repo.create_document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            format="pdf",
            file_size_bytes=1000,
        )
        topic = repo.create_topic(doc.id, "Test Topic", 1, None)
        result = repo.update_topic_summary(topic.id, "Test summary")
        assert result is True
        updated = repo.get_topic_by_id(topic.id)
        assert updated.summary == "Test summary"


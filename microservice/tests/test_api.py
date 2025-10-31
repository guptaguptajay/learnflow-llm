"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "vector_store" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestDocumentEndpoints:
    """Test document endpoints."""

    def test_upload_document_no_file(self):
        """Test upload without file."""
        response = client.post("/documents/upload")
        assert response.status_code == 422

    def test_get_document_not_found(self):
        """Test getting non-existent document."""
        response = client.get("/documents/non-existent-id")
        assert response.status_code == 404

    def test_process_document_invalid_id(self):
        """Test processing with invalid document ID."""
        response = client.post(
            "/documents/process",
            json={"document_id": "invalid-id"},
        )
        assert response.status_code in [400, 500]

    def test_vectorize_document_invalid_id(self):
        """Test vectorizing with invalid document ID."""
        response = client.post(
            "/documents/vectorize",
            json={"document_id": "invalid-id"},
        )
        assert response.status_code in [400, 500]


class TestTopicEndpoints:
    """Test topic endpoints."""

    def test_generate_topics_invalid_document(self):
        """Test generating topics with invalid document."""
        response = client.post(
            "/topics/generate",
            json={"document_id": "invalid-id", "num_topics": 5},
        )
        assert response.status_code in [400, 500]

    def test_generate_subtopics_invalid_topic(self):
        """Test generating subtopics with invalid topic."""
        response = client.post(
            "/topics/subtopics/generate",
            json={"topic_id": "invalid-id", "num_subtopics": 3},
        )
        assert response.status_code in [400, 500]

    def test_generate_summary_invalid_topic(self):
        """Test generating summary with invalid topic."""
        response = client.post(
            "/topics/summary/generate",
            json={"topic_id": "invalid-id"},
        )
        assert response.status_code in [400, 500]

    def test_get_content_invalid_topic(self):
        """Test getting content with invalid topic."""
        response = client.post(
            "/topics/content",
            json={"topic_id": "invalid-id"},
        )
        assert response.status_code in [400, 404, 500]

    def test_get_document_topics_not_found(self):
        """Test getting topics for non-existent document."""
        response = client.get("/topics/non-existent-id")
        assert response.status_code == 404


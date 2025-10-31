"""Vectorization service using LangChain embeddings."""

from typing import List, Optional

from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.metadata_store import MetadataRepository
from app.repositories.vector_store import VectorStoreRepository

logger = get_logger(__name__)


class VectorizerService:
    """Service for vectorizing document chunks."""

    def __init__(
        self,
        metadata_repo: MetadataRepository,
        vector_repo: VectorStoreRepository,
    ):
        """Initialize vectorizer service.

        Args:
            metadata_repo: Metadata repository instance
            vector_repo: Vector store repository instance
        """
        self.metadata_repo = metadata_repo
        self.vector_repo = vector_repo
        self.settings = get_settings()
        self.embeddings = self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize embedding model based on configuration.

        Returns:
            LangChain embeddings instance
        """
        if self.settings.llm_provider == "openai":
            logger.info(f"Initializing OpenAI embeddings: {self.settings.openai_embedding_model}")
            return OpenAIEmbeddings(
                model=self.settings.openai_embedding_model,
                openai_api_key=self.settings.openai_api_key,
                dimensions=self.settings.openai_embedding_dimensions,
            )
        elif self.settings.llm_provider == "anthropic":
            logger.info("Initializing Anthropic embeddings")
            # Note: Anthropic doesn't provide embeddings directly
            # Fall back to OpenAI or use a different provider
            logger.warning("Anthropic embeddings not available, falling back to OpenAI")
            return OpenAIEmbeddings(
                model=self.settings.openai_embedding_model,
                openai_api_key=self.settings.openai_api_key,
                dimensions=self.settings.openai_embedding_dimensions,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        logger.debug(f"Embedding {len(texts)} texts")
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding texts: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.

        Args:
            text: Query text

        Returns:
            Embedding vector
        """
        logger.debug(f"Embedding query: {text[:100]}...")
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise

    def vectorize_document(self, document_id: str) -> int:
        """Vectorize all chunks of a document.

        Args:
            document_id: Document ID to vectorize

        Returns:
            Number of vectors created

        Raises:
            ValueError: If document not found or not processed
        """
        # Get document
        document = self.metadata_repo.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.status != "processed":
            raise ValueError(
                f"Document must be processed before vectorization. Current status: {document.status}"
            )

        # Update status
        self.metadata_repo.update_document_status(document_id, "vectorizing")

        try:
            # Get all chunks
            chunks = self.metadata_repo.get_chunks_by_document(document_id)
            if not chunks:
                raise ValueError(f"No chunks found for document: {document_id}")

            logger.info(f"Vectorizing {len(chunks)} chunks for document {document_id}")

            # Extract texts and chunk IDs
            texts = [chunk.text for chunk in chunks]
            chunk_ids = [chunk.id for chunk in chunks]

            # Create embeddings
            embeddings = self.embed_texts(texts)

            # Prepare metadata for vector store
            metadata = [
                {
                    "document_id": document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

            # Ensure collection exists (pgvector: ensures table and indexes)
            collection_name = f"documents_{document_id}"
            vector_size = len(embeddings[0])
            self.vector_repo.create_collection(collection_name, vector_size)

            # Store vectors in pgvector
            vector_ids = self.vector_repo.insert_vectors(
                collection_name=collection_name,
                vectors=embeddings,
                metadata=metadata,
                ids=chunk_ids,  # Use chunk IDs as vector IDs
            )

            # Update document status
            self.metadata_repo.update_document_status(document_id, "vectorized")

            logger.info(f"Successfully vectorized document {document_id}: {len(vector_ids)} vectors")
            return len(vector_ids)

        except Exception as e:
            logger.error(f"Error vectorizing document {document_id}: {str(e)}")
            self.metadata_repo.update_document_status(document_id, "failed")
            raise

    def search_similar_chunks(
        self,
        document_id: str,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> List[dict]:
        """Search for similar chunks using semantic search.

        Args:
            document_id: Document ID to search within
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of dictionaries with chunk info and scores
        """
        logger.info(f"Searching for similar chunks in document {document_id}")

        try:
            # Embed query
            query_embedding = self.embed_query(query)

            # Search in pgvector
            collection_name = f"documents_{document_id}"
            results = self.vector_repo.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Format results
            formatted_results = []
            for result in results:
                chunk_id = result.id
                chunk = self.metadata_repo.get_chunk_by_id(chunk_id)
                if chunk:
                    formatted_results.append(
                        {
                            "chunk_id": chunk_id,
                            "text": chunk.text,
                            "score": result.score,
                            "chunk_index": chunk.chunk_index,
                            "metadata": chunk.metadata,
                        }
                    )

            logger.info(f"Found {len(formatted_results)} similar chunks")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            raise

    def get_collection_name(self, document_id: str) -> str:
        """Get collection name for document.

        Args:
            document_id: Document identifier

        Returns:
            Collection name
        """
        return f"documents_{document_id}"


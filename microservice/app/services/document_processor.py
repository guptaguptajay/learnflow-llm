"""Document processing service with LangChain integration."""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredEPubLoader

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.metadata_store import DocumentChunk, MetadataRepository
from app.services.storage import StorageService

logger = get_logger(__name__)


class DocumentProcessorService:
    """Service for processing documents with LangChain."""

    def __init__(self, metadata_repo: MetadataRepository, storage: StorageService):
        """Initialize document processor.

        Args:
            metadata_repo: Metadata repository instance
            storage: Storage service instance
        """
        self.metadata_repo = metadata_repo
        self.storage = storage
        self.settings = get_settings()

    def load_document(self, file_path: str, format: str) -> List[dict]:
        """Load document using appropriate LangChain loader.

        Supports both S3 URIs (s3://bucket/key) and local file paths.
        For S3 files, downloads to temp location before processing.

        Args:
            file_path: Path to document file or S3 URI
            format: Document format (pdf, epub, mobi)

        Returns:
            List of loaded documents with page_content and metadata

        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If file doesn't exist
        """
        local_file_path = file_path
        temp_file = None

        try:
            # Check if this is an S3 URI
            if file_path.startswith("s3://"):
                logger.info(f"Downloading from S3: {file_path}")
                
                # Extract S3 key from URI
                s3_key = self.storage.extract_key_from_uri(file_path)
                
                # Create temp file with proper extension
                suffix = f".{format.lower()}"
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix, dir=self.settings.temp_dir
                )
                local_file_path = temp_file.name
                temp_file.close()
                
                # Download from S3
                self.storage.download_to_path(s3_key, local_file_path)
                logger.info(f"Downloaded to temp file: {local_file_path}")
            
            elif not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            logger.info(f"Loading document: {local_file_path} (format: {format})")

            # Load document with appropriate loader
            if format.lower() == "pdf":
                loader = PyPDFLoader(local_file_path)
            elif format.lower() == "epub":
                loader = UnstructuredEPubLoader(local_file_path)
            elif format.lower() == "mobi":
                # MOBI can be handled by UnstructuredFileLoader
                from langchain_community.document_loaders import UnstructuredFileLoader

                loader = UnstructuredFileLoader(local_file_path)
            else:
                raise ValueError(f"Unsupported document format: {format}")

            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages/sections from document")

            # Convert to dict format
            result = []
            for doc in documents:
                result.append({"page_content": doc.page_content, "metadata": doc.metadata})

            return result

        except Exception as e:
            logger.error(f"Error loading document: {str(e)}")
            raise
        
        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(local_file_path):
                try:
                    os.unlink(local_file_path)
                    logger.info(f"Cleaned up temp file: {local_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {local_file_path}: {str(e)}")

    def chunk_document(
        self, documents: List[dict], chunk_size: int, chunk_overlap: int
    ) -> List[Tuple[str, dict]]:
        """Chunk documents using RecursiveCharacterTextSplitter.

        Args:
            documents: List of document dictionaries
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of (text, metadata) tuples
        """
        logger.info(
            f"Chunking documents: chunk_size={chunk_size}, overlap={chunk_overlap}"
        )

        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = []
        for doc in documents:
            # Split text
            texts = text_splitter.split_text(doc["page_content"])

            # Preserve original metadata and add chunk info
            for text in texts:
                metadata = doc["metadata"].copy() if doc.get("metadata") else {}
                chunks.append((text, metadata))

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def process_document(
        self, document_id: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Process document: load and chunk.

        Args:
            document_id: Document ID to process
            chunk_size: Optional chunk size override
            chunk_overlap: Optional chunk overlap override

        Returns:
            List of created DocumentChunk instances

        Raises:
            ValueError: If document not found or already processed
        """
        # Get document from database
        document = self.metadata_repo.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.status not in ["uploaded", "failed"]:
            raise ValueError(f"Document already processed: {document.status}")

        # Update status to processing
        self.metadata_repo.update_document_status(document_id, "processing")

        try:
            # Load document
            loaded_docs = self.load_document(document.file_path, document.format)

            # Chunk document
            chunk_size = chunk_size or self.settings.chunk_size
            chunk_overlap = chunk_overlap or self.settings.chunk_overlap
            chunks = self.chunk_document(loaded_docs, chunk_size, chunk_overlap)

            # Store chunks in database
            chunks_data = []
            for idx, (text, chunk_meta) in enumerate(chunks):
                chunk_meta["chunk_size"] = chunk_size
                chunk_meta["chunk_overlap"] = chunk_overlap
                chunks_data.append(
                    {"text": text, "chunk_index": idx, "metadata": chunk_meta}
                )

            db_chunks = self.metadata_repo.create_chunks(document_id, chunks_data)

            # Update document status
            self.metadata_repo.update_document_status(document_id, "processed")

            logger.info(f"Successfully processed document {document_id}: {len(db_chunks)} chunks")
            return db_chunks

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            self.metadata_repo.update_document_status(document_id, "failed")
            raise

    def get_document_text(self, document_id: str) -> str:
        """Get full text of document from all chunks.

        Args:
            document_id: Document identifier

        Returns:
            Complete document text
        """
        chunks = self.metadata_repo.get_chunks_by_document(document_id)
        return "\n\n".join([chunk.text for chunk in chunks])


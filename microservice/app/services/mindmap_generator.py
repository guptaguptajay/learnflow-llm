"""Mind map generation service using LangChain LCEL."""

from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.metadata_store import MetadataRepository, TopicNode
from app.services.vectorizer import VectorizerService

logger = get_logger(__name__)


# ============================================================================
# Structured Output Models
# ============================================================================


class TopicOutput(BaseModel):
    """Structured output for a single topic."""

    title: str = Field(..., description="Topic title")
    description: str = Field(..., description="Brief description of the topic")


class TopicsListOutput(BaseModel):
    """Structured output for list of topics."""

    topics: List[TopicOutput] = Field(..., description="List of identified topics")


class SubtopicsListOutput(BaseModel):
    """Structured output for list of subtopics."""

    subtopics: List[TopicOutput] = Field(..., description="List of generated subtopics")


# ============================================================================
# Mind Map Generator Service
# ============================================================================


class MindMapGeneratorService:
    """Service for generating hierarchical mind maps using LLM."""

    def __init__(
        self,
        metadata_repo: MetadataRepository,
        vectorizer_service: VectorizerService,
    ):
        """Initialize mind map generator.

        Args:
            metadata_repo: Metadata repository instance
            vectorizer_service: Vectorizer service instance
        """
        self.metadata_repo = metadata_repo
        self.vectorizer_service = vectorizer_service
        self.settings = get_settings()
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM based on configuration.

        Returns:
            LangChain chat model instance
        """
        if self.settings.llm_provider == "openai":
            if not self.settings.openai_api_key:
                logger.warning("OPENAI_API_KEY not set; using DummyChatModel for tests/CI")

                class DummyResult:
                    def __init__(self, content: str):
                        self.content = content

                class DummyChatModel:
                    def invoke(self, inputs):
                        return DummyResult("Mocked output")

                return DummyChatModel()
            logger.info(f"Initializing OpenAI LLM: {self.settings.openai_model}")
            return ChatOpenAI(
                model=self.settings.openai_model,
                openai_api_key=self.settings.openai_api_key,
                temperature=0.3,
            )
        elif self.settings.llm_provider == "anthropic":
            logger.info(f"Initializing Anthropic LLM: {self.settings.anthropic_model}")
            return ChatAnthropic(
                model=self.settings.anthropic_model,
                anthropic_api_key=self.settings.anthropic_api_key,
                temperature=0.3,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    def _create_topic_extraction_chain(self, num_topics: int) -> RunnableSequence:
        """Create LangChain chain for topic extraction with structured output.

        Args:
            num_topics: Number of topics to extract

        Returns:
            RunnableSequence chain
        """
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at analyzing documents and identifying main topics. "
                    "Extract the {num_topics} most important topics from the provided text. "
                    "Each topic should be concise and represent a distinct theme or subject area.",
                ),
                (
                    "user",
                    "Analyze the following document text and identify {num_topics} main topics:\n\n{text}",
                ),
            ]
        )

        # Create chain with structured output
        structured_llm = self.llm.with_structured_output(TopicsListOutput)
        chain = prompt | structured_llm

        return chain

    def _create_subtopic_generation_chain(self, num_subtopics: int) -> RunnableSequence:
        """Create LangChain chain for subtopic generation.

        Args:
            num_subtopics: Number of subtopics to generate

        Returns:
            RunnableSequence chain
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at breaking down topics into subtopics. "
                    "Generate {num_subtopics} relevant subtopics for the given topic. "
                    "Each subtopic should be specific and cover a distinct aspect of the main topic.",
                ),
                (
                    "user",
                    "Topic: {topic_title}\n\n"
                    "Related content:\n{content}\n\n"
                    "Generate {num_subtopics} subtopics for this topic.",
                ),
            ]
        )

        structured_llm = self.llm.with_structured_output(SubtopicsListOutput)
        chain = prompt | structured_llm

        return chain

    def generate_topics(
        self, document_id: str, num_topics: Optional[int] = None
    ) -> List[TopicNode]:
        """Generate main topics for a document.

        Args:
            document_id: Document ID
            num_topics: Number of topics to generate (defaults to settings)

        Returns:
            List of created TopicNode instances

        Raises:
            ValueError: If document not found or not vectorized
        """
        # Validate document
        document = self.metadata_repo.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.status != "vectorized":
            raise ValueError(
                f"Document must be vectorized before topic generation. Current status: {document.status}"
            )

        num_topics = num_topics or self.settings.max_topics
        logger.info(f"Generating {num_topics} topics for document {document_id}")

        try:
            # Get document text from chunks
            chunks = self.metadata_repo.get_chunks_by_document(document_id)
            if not chunks:
                raise ValueError(f"No chunks found for document: {document_id}")

            # Combine chunks (sample if too large)
            max_chars = 15000  # Limit input size
            combined_text = ""
            for chunk in chunks:
                if len(combined_text) + len(chunk.text) < max_chars:
                    combined_text += chunk.text + "\n\n"
                else:
                    break

            # Create and run chain
            chain = self._create_topic_extraction_chain(num_topics)
            result = chain.invoke({"num_topics": num_topics, "text": combined_text})

            # Create topic nodes in database
            topic_nodes = []
            for topic_output in result.topics:
                # Create topic node
                topic_node = self.metadata_repo.create_topic(
                    document_id=document_id,
                    title=topic_output.title,
                    level=1,  # Main topics are level 1
                    parent_id=None,
                )

                # Map topic to relevant vectors using semantic search
                relevant_chunks = self.vectorizer_service.search_similar_chunks(
                    document_id=document_id,
                    query=f"{topic_output.title}. {topic_output.description}",
                    limit=10,
                )

                # Create topic-vector-chunk mappings
                vector_chunk_pairs = [
                    (chunk["chunk_id"], chunk["chunk_id"]) for chunk in relevant_chunks
                ]
                self.metadata_repo.create_topic_vector_mappings(
                    topic_node.id, vector_chunk_pairs
                )

                topic_nodes.append(topic_node)

            # Update document status
            self.metadata_repo.update_document_status(document_id, "mapped")

            logger.info(f"Generated {len(topic_nodes)} topics for document {document_id}")
            return topic_nodes

        except Exception as e:
            logger.error(f"Error generating topics: {str(e)}")
            raise

    def generate_subtopics(
        self, topic_id: str, num_subtopics: Optional[int] = None
    ) -> List[TopicNode]:
        """Generate subtopics for a parent topic.

        Args:
            topic_id: Parent topic ID
            num_subtopics: Number of subtopics to generate (defaults to settings)

        Returns:
            List of created TopicNode instances

        Raises:
            ValueError: If topic not found
        """
        # Get parent topic
        parent_topic = self.metadata_repo.get_topic_by_id(topic_id)
        if not parent_topic:
            raise ValueError(f"Topic not found: {topic_id}")

        num_subtopics = num_subtopics or self.settings.max_subtopics_per_topic
        logger.info(f"Generating {num_subtopics} subtopics for topic {topic_id}")

        try:
            # Get chunks associated with parent topic
            chunks = self.metadata_repo.get_chunks_by_topic(topic_id)
            if not chunks:
                logger.warning(f"No chunks found for topic {topic_id}, using all document chunks")
                chunks = self.metadata_repo.get_chunks_by_document(parent_topic.document_id)

            # Combine chunk texts
            max_chars = 10000
            content = ""
            for chunk in chunks:
                if len(content) + len(chunk.text) < max_chars:
                    content += chunk.text + "\n\n"
                else:
                    break

            # Create and run chain
            chain = self._create_subtopic_generation_chain(num_subtopics)
            result = chain.invoke(
                {
                    "topic_title": parent_topic.title,
                    "content": content,
                    "num_subtopics": num_subtopics,
                }
            )

            # Create subtopic nodes
            subtopic_nodes = []
            for subtopic_output in result.subtopics:
                # Create subtopic node
                subtopic_node = self.metadata_repo.create_topic(
                    document_id=parent_topic.document_id,
                    title=subtopic_output.title,
                    level=parent_topic.level + 1,
                    parent_id=topic_id,
                )

                # Map subtopic to relevant vectors
                relevant_chunks = self.vectorizer_service.search_similar_chunks(
                    document_id=parent_topic.document_id,
                    query=f"{subtopic_output.title}. {subtopic_output.description}",
                    limit=5,
                )

                # Create mappings
                vector_chunk_pairs = [
                    (chunk["chunk_id"], chunk["chunk_id"]) for chunk in relevant_chunks
                ]
                self.metadata_repo.create_topic_vector_mappings(
                    subtopic_node.id, vector_chunk_pairs
                )

                subtopic_nodes.append(subtopic_node)

            logger.info(f"Generated {len(subtopic_nodes)} subtopics for topic {topic_id}")
            return subtopic_nodes

        except Exception as e:
            logger.error(f"Error generating subtopics: {str(e)}")
            raise

    def get_topic_hierarchy(self, document_id: str) -> dict:
        """Get complete topic hierarchy for a document.

        Args:
            document_id: Document ID

        Returns:
            Hierarchical dictionary of topics
        """
        topics = self.metadata_repo.get_topics_by_document(document_id)

        # Build hierarchy
        hierarchy = {"document_id": document_id, "topics": []}

        # Group by level
        topics_by_level = {}
        for topic in topics:
            if topic.level not in topics_by_level:
                topics_by_level[topic.level] = []
            topics_by_level[topic.level].append(topic)

        # Build tree structure (simplified)
        for level in sorted(topics_by_level.keys()):
            for topic in topics_by_level[level]:
                hierarchy["topics"].append(
                    {
                        "id": topic.id,
                        "title": topic.title,
                        "level": topic.level,
                        "parent_id": topic.parent_id,
                        "summary": topic.summary,
                    }
                )

        return hierarchy


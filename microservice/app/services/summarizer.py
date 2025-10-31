"""Summarization service using LangChain LCEL."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.metadata_store import MetadataRepository

logger = get_logger(__name__)


class SummarizerService:
    """Service for generating summaries using LLM."""

    def __init__(self, metadata_repo: MetadataRepository):
        """Initialize summarizer service.

        Args:
            metadata_repo: Metadata repository instance
        """
        self.metadata_repo = metadata_repo
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
                        title = inputs.get("topic_title", "Topic")
                        content = inputs.get("content", "")
                        snippet = content[:200] + ("..." if len(content) > 200 else "")
                        return DummyResult(f"Summary for {title}: {snippet}")

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

    def _create_summary_chain(self) -> RunnableSequence:
        """Create LangChain chain for summarization.

        Returns:
            RunnableSequence chain
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at creating concise, informative summaries. "
                    "Create a clear summary that captures the key points and main ideas "
                    "of the provided content. The summary should be well-structured and "
                    "easy to understand.",
                ),
                (
                    "user",
                    "Topic: {topic_title}\n\n"
                    "Content to summarize:\n{content}\n\n"
                    "Provide a comprehensive yet concise summary of this content.",
                ),
            ]
        )

        chain = prompt | self.llm

        return chain

    def generate_summary_for_topic(self, topic_id: str) -> str:
        """Generate summary for a topic based on its associated chunks.

        Args:
            topic_id: Topic or subtopic ID

        Returns:
            Generated summary text

        Raises:
            ValueError: If topic not found or has no associated content
        """
        # Get topic
        topic = self.metadata_repo.get_topic_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic not found: {topic_id}")

        logger.info(f"Generating summary for topic: {topic.title}")

        try:
            # Get associated chunks
            chunks = self.metadata_repo.get_chunks_by_topic(topic_id)
            if not chunks:
                # If no specific chunks mapped, try to get from parent document
                logger.warning(
                    f"No chunks mapped to topic {topic_id}, using document chunks"
                )
                chunks = self.metadata_repo.get_chunks_by_document(topic.document_id)

            if not chunks:
                raise ValueError(f"No content found for topic: {topic_id}")

            # Combine chunk texts
            max_chars = 12000  # Limit input size for LLM
            content = ""
            for chunk in chunks:
                if len(content) + len(chunk.text) < max_chars:
                    content += chunk.text + "\n\n"
                else:
                    break

            # Create and run chain
            chain = self._create_summary_chain()
            result = chain.invoke({"topic_title": topic.title, "content": content})

            # Extract summary text
            if hasattr(result, "content"):
                summary = result.content
            else:
                summary = str(result)

            # Store summary in database
            self.metadata_repo.update_topic_summary(topic_id, summary)

            logger.info(f"Generated summary for topic {topic_id} ({len(summary)} chars)")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    def get_topic_content(self, topic_id: str) -> tuple[str, list[str]]:
        """Get full content for a topic from all associated chunks.

        Args:
            topic_id: Topic or subtopic ID

        Returns:
            Tuple of (full_text, chunk_ids)

        Raises:
            ValueError: If topic not found
        """
        # Get topic
        topic = self.metadata_repo.get_topic_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic not found: {topic_id}")

        # Get associated chunks
        chunks = self.metadata_repo.get_chunks_by_topic(topic_id)

        if not chunks:
            logger.warning(f"No chunks mapped to topic {topic_id}")
            return "", []

        # Combine chunk texts in order
        full_text = "\n\n".join([chunk.text for chunk in chunks])
        chunk_ids = [chunk.id for chunk in chunks]

        logger.info(
            f"Retrieved content for topic {topic_id}: {len(chunks)} chunks, {len(full_text)} chars"
        )

        return full_text, chunk_ids


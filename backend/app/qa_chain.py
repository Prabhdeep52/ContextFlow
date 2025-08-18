from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import count_tokens, calculate_cost, log_error, log_info
from .config import config
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.schema import Document

# ============================================================================
# ENHANCED QA CHAIN
# ============================================================================


class SimpleQAChain:
    """Hierarchical QA chain implementation with section and structure context."""

    def __init__(self):
        self.model = None
        self.chain = None

    def reset(self):
        self.model = None
        self.chain = None

    def _initialize(self):
        if not config.GOOGLE_API_KEY:
            raise ValueError("Google API key not configured")
        if self.model is None:
            try:
                self.model = ChatGoogleGenerativeAI(
                    model=config.CHAT_MODEL,
                    temperature=config.TEMPERATURE,
                    google_api_key=config.GOOGLE_API_KEY
                )
                log_info(f"Model initialized: {config.CHAT_MODEL}")
            except Exception as e:
                log_error(f"Failed to initialize model: {e}")
                raise
        if self.chain is None:
            try:
                prompt_template = """
                You are a research assistant that answers questions using the provided document context and structure.
                Use the section titles and hierarchy to give precise, grounded answers. Reference sections by name if relevant.
                Give detailed ans about the topic also , dont just give the brief response about the seciton.

                Section Context:
                {section_context}

                Content Context:
                {context}

                Question: {question}

                Answer:
                Please format your answer using Markdown.
                - Use bullet points or numbered lists for clarity where appropriate.
                - Use **bold** text for emphasis on key terms or concepts.
                - For mathematical formulas or equations, use inline code or block code. If complex, use LaTeX syntax within code blocks (e.g., `$E=mc^2$` or ````latex
\int_0^1 x^2 dx
````).

                """
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question", "section_context"]
                )
                self.chain = load_qa_chain(
                    self.model,
                    chain_type="stuff",
                    prompt=prompt
                )
                log_info("Hierarchical QA chain initialized")
            except Exception as e:
                log_error(f"Failed to initialize QA chain: {e}")
                raise

    def answer_question(self, question: str, documents: List[Dict[str, Any]], section_context: str = "") -> Dict[str, Any]:
        """Answer a question using the provided documents and section context."""
        try:
            self._initialize()
            input_docs = [
                Document(
                    page_content=doc["content"],
                    metadata={
                        "filename": doc.get("filename", "Unknown"),
                        "chunk_id": doc.get("chunk_id", "Unknown"),
                        "section_title": doc.get("section_title"),
                        "hierarchy_level": doc.get("hierarchy_level"),
                        "parent_section": doc.get("parent_section"),
                    }
                )
                for doc in documents
            ]
            result = self.chain.invoke({
                "input_documents": input_docs,
                "question": question,
                "section_context": section_context
            })
            return result
        except Exception as e:
            log_error(f"Error answering question: {e}")
            raise

# Global QA chain instance
qa_chain = SimpleQAChain()
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
    """Simplified QA chain implementation"""
    
    def __init__(self):
        self.model = None
        self.chain = None
        
    def reset(self):
        """Reset the model and chain"""
        self.model = None
        self.chain = None
        
    def _initialize(self):
        """Initialize the model and chain"""
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
                # Create simple QA chain
                prompt_template = """
                You are ResearchQ&A app built to answer the question based on the context provided , 
                you are a research assistant, who explain the questions in an easy way that is easy to understand and goes in depth if asked 
                to by the user. You are a RAG based pipeline that uses the context provided to answer the question
                One of your main advantage is that u only give the needed context to the chatbot , hence saving api cost.                .
                
                Context: {context}
                
                Question: {question}
                
                Answer:"""
                
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"]
                )
                
                self.chain = load_qa_chain(
                    self.model,
                    chain_type="stuff",
                    prompt=prompt
                )
                
                log_info("QA chain initialized")
                
            except Exception as e:
                log_error(f"Failed to initialize QA chain: {e}")
                raise
    
    def answer_question(self, question: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer a question using the provided documents"""
        try:
            self._initialize()
            
            # Prepare input for the chain - create proper Document objects
            input_docs = [
                Document(
                    page_content=doc["content"],
                    metadata={
                        "filename": doc.get("filename", "Unknown"),
                        "chunk_id": doc.get("chunk_id", "Unknown")
                    }
                ) 
                for doc in documents
            ]
            
            result = self.chain.invoke({
                "input_documents": input_docs,
                "question": question
            })
            
            return result
            
        except Exception as e:
            log_error(f"Error answering question: {e}")
            raise

# Global QA chain instance
qa_chain = SimpleQAChain()
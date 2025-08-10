from .config import config
import os

def configure_api_key(api_key: str):
    """Configure the Google API key"""
    # Update the config object
    config.GOOGLE_API_KEY = api_key
    
    # Set environment variable too
    os.environ["GOOGLE_API_KEY"] = api_key
    
    # Note: Component reinitialization will be handled by calling reinitialize_components()
    # This avoids circular import issues

def reinitialize_components():
    """Reinitialize components after API key configuration"""
    try:
        from .qa_chain import qa_chain
        from .vector_store import vector_store
        
        qa_chain.reset()
        vector_store.reset_embeddings()
        
        # Import logging function
        from .utils import log_info
        log_info("Components reinitialized with new API key")
    except Exception as e:
        # Import logging function
        from .utils import log_error
        log_error(f"Failed to reinitialize components: {e}")

def is_api_key_configured():
    return config.GOOGLE_API_KEY is not None and config.GOOGLE_API_KEY.strip() != ""

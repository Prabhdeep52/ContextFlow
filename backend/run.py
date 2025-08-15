# #!/usr/bin/env python3
# """
# Simple startup script for the RAG Pipeline
# """

# import os
# import sys

# def check_dependencies():
#     """Check if all required dependencies are available"""
#     try:
#         import fastapi
#         print(f"✓ FastAPI {fastapi.__version__}")
#     except ImportError as e:
#         print(f"✗ FastAPI import failed: {e}")
#         return False
    
#     try:
#         import uvicorn
#         print(f"✓ Uvicorn {uvicorn.__version__}")
#     except ImportError as e:
#         print(f"✗ Uvicorn import failed: {e}")
#         return False
    
#     try:
#         import langchain
#         print(f"✓ LangChain {langchain.__version__}")
#     except ImportError as e:
#         print(f"✗ LangChain import failed: {e}")
#         return False
    
#     try:
#         import langchain_google_genai
#         print(f"✓ LangChain Google GenAI")
#     except ImportError as e:
#         print(f"✗ LangChain Google GenAI import failed: {e}")
#         return False
    
#     try:
#         import faiss
#         print(f"✓ FAISS")
#     except ImportError as e:
#         print(f"✗ FAISS import failed: {e}")
#         return False
    
#     return True

# def check_environment():
#     """Check environment variables"""
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if api_key:
#         print(f"✓ Google API Key configured (length: {len(api_key)})")
#         return True
#     else:
#         print("⚠ Google API Key not configured - set GOOGLE_API_KEY environment variable")
#         return False

# def main():
#     """Main startup function"""
#     print("RAG Pipeline Startup Check")
#     print("=" * 30)
    
#     # Check dependencies
#     print("\nChecking dependencies...")
#     deps_ok = check_dependencies()
    
#     # Check environment
#     print("\nChecking environment...")
#     env_ok = check_environment()
    
#     if not deps_ok:
#         print("\n❌ Dependency check failed!")
#         print("Please install dependencies with: pip install -r requirements.txt")
#         return False
    
#     if not env_ok:
#         print("\n⚠ Environment check failed!")
#         print("Please set GOOGLE_API_KEY environment variable")
#         print("You can still run the app, but some features won't work")
    
#     print("\n✅ All checks passed! Starting app...")
    
#     # Import and run the app
#     try:
#         from app import app
#         import uvicorn
        
#         print("Starting server on http://localhost:8000")
#         uvicorn.run(app, host="0.0.0.0", port=8000)
        
#     except Exception as e:
#         print(f"❌ Failed to start app: {e}")
#         return False
    
#     return True

# if __name__ == "__main__":
#     success = main()
#     if not success:
#         sys.exit(1)


import uvicorn
from app.main import app
import logging

# Suppress verbose logging from langextract and absl
logging.getLogger("langextract").setLevel(logging.INFO)
logging.getLogger("absl").setLevel(logging.INFO)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

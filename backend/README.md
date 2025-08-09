# RAG Pipeline Backend

A FastAPI-based backend for a RAG (Retrieval-Augmented Generation) pipeline that can process PDFs and answer questions using Google's Gemini AI.

## Quick Start

### Option 1: Windows Batch File (Recommended for Windows)
```bash
# Double-click run.bat or run from command prompt:
run.bat
```

### Option 2: PowerShell Script
```powershell
# Run from PowerShell:
.\run.ps1
```

### Option 3: Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Google API key
set GOOGLE_API_KEY=your_api_key_here  # Windows
export GOOGLE_API_KEY=your_api_key_here  # Linux/Mac

# Run the app
python run.py
```

## Prerequisites

- Python 3.8 or higher
- Google API key for Gemini AI
- Internet connection

## Environment Variables

- `GOOGLE_API_KEY`: Your Google API key for Gemini AI access

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure you're in the `backend` directory
   - Ensure virtual environment is activated
   - Try reinstalling dependencies: `pip install -r requirements.txt`

2. **API Key Issues**
   - Set the `GOOGLE_API_KEY` environment variable
   - Restart your terminal/command prompt after setting the variable

3. **Port Already in Use**
   - The app runs on port 8000 by default
   - Change the port in `run.py` if needed

4. **Dependency Issues**
   - Try upgrading pip: `pip install --upgrade pip`
   - Clear pip cache: `pip cache purge`
   - Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Getting Help

If you encounter issues:

1. Run the startup check: `python run.py`
2. Check the error messages for specific import failures
3. Ensure all dependencies are installed correctly
4. Verify your Python version is 3.8+

## API Endpoints

Once running, the app will be available at:
- Main app: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Features

- PDF upload and processing
- Question answering using RAG
- Conversation history
- Cost tracking
- Vector search capabilities

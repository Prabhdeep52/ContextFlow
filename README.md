# RESEARCH_RAG

## Overview

RESEARCH_RAG is a Retrieval Augmented Generation (RAG) system designed to process PDF documents, extract structured information, and answer user questions based on the content of those documents. It features a Python-based backend (FastAPI) for document processing and AI interactions, and a React/TypeScript frontend for user interaction.

This project aims to provide a robust solution for querying large research papers or other PDF-based documentation, leveraging Google's Gemini models for advanced text understanding and question answering.

## Features

*   **PDF Document Ingestion:** Upload PDF files for processing and indexing.
*   **Hierarchical Text Extraction:** Utilizes `langextract` and Google Gemini 2.5 Flash to intelligently extract and structure content from PDFs, identifying sections, subsections, and their relationships.
*   **Intelligent Question Answering (RAG):** Answers user queries by retrieving relevant information from the processed documents and synthesizing responses using Google Gemini models (e.g., Gemini Pro) via LangChain.
*   **API-Driven Backend:** A FastAPI backend provides a clean and efficient API for all document processing and QA functionalities.
*   **Interactive Web Frontend:** A modern React application offers a user-friendly interface for uploading documents, asking questions, and viewing answers.
*   **Conversation Management:** (Implied by `conversation_manager.py`) Manages the flow of user interactions.
*   **Memory Store:** (Implied by `memory_store.py`) Likely stores conversation history or document metadata.
*   **Vector Store Integration:** (Implied by `vector_store.py`) Integrates with a vector database (e.g., FAISS, as seen in `.venv` dependencies) for efficient document chunk retrieval.

## Technologies Used

### Backend

*   **Python:** Core programming language.
*   **FastAPI:** Web framework for building the API.
*   **LangChain:** Framework for developing applications powered by language models.
*   **Google Gemini API:** Powers the LLM interactions for text extraction and question answering.
*   **`pypdf`:** For basic PDF text extraction.
*   **`langextract`:** For advanced hierarchical text structuring using LLMs.
*   **`faiss-cpu`:** (Likely used by `vector_store.py`) For efficient similarity search and retrieval.

### Frontend

*   **React:** JavaScript library for building user interfaces.
*   **TypeScript:** Superset of JavaScript that adds static typing.
*   **Vite:** Fast build tool for modern web projects.

## Setup and Installation

Follow these steps to set up and run the RESEARCH_RAG project locally.

### Prerequisites

*   **Python 3.9+**
*   **Node.js (LTS recommended)** and **npm** (or yarn)
*   **Google API Key:** You will need a Google API Key with access to the Gemini API. Obtain one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/RESEARCH_RAG.git
cd RESEARCH_RAG
```

### 2. Backend Setup

Navigate to the `backend` directory and set up the Python environment.

```bash
cd backend
python -m venv .venv
# On Windows
.venv\\Scripts\\activate
# On macOS/Linux
source .venv/bin/activate
```

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory and add your Google API Key:

```
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
```

### 3. Frontend Setup

Navigate to the `frontend_RAG` directory and install Node.js dependencies.

```bash
cd ../frontend_RAG
npm install
# or yarn install
```

### 4. Running the Application

You can use the provided `start-all.bat` script (for Windows) to start both the backend and frontend concurrently.

From the project root directory (`C:\projects\RESEARCH_RAG`):

```bash
start-all.bat
```

Alternatively, you can start them manually:

**Start Backend:**

Open a new terminal, navigate to the `backend` directory, activate the virtual environment, and run the FastAPI application:

```bash
cd backend
.venv\\Scripts\\activate # Windows
# source .venv/bin/activate # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

The backend will typically run on `http://localhost:8000`.

**Start Frontend:**

Open another new terminal, navigate to the `frontend_RAG` directory, and start the React development server:

```bash
cd frontend_RAG
npm run dev
# or yarn dev
```

The frontend will typically run on `http://localhost:5173` (or another port if 5173 is in use).

## Usage

1.  **Access the Frontend:** Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2.  **Upload PDFs:** Use the interface to upload your research papers or other PDF documents. The backend will process them, extracting structured information.
3.  **Ask Questions:** Once documents are processed, you can type your questions into the input field. The system will retrieve relevant information and provide answers based on the content of your uploaded PDFs.

## Project Structure

```
RESEARCH_RAG/
├── backend/                  # Python FastAPI application
│   ├── app/                  # Core application logic
│   │   ├── main.py           # FastAPI entry point
│   │   ├── pdf_processing.py # Handles PDF text extraction and hierarchical structuring
│   │   ├── qa_chain.py       # Manages the LangChain QA process
│   │   ├── vector_store.py   # Integration with vector database (e.g., FAISS)
│   │   ├── api_key_manager.py
│   │   ├── config.py
│   │   ├── conversation_manager.py
│   │   ├── memory_store.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Example for environment variables
├── frontend_RAG/             # React/TypeScript web application
│   ├── public/
│   ├── src/                  # Frontend source code
│   │   ├── App.tsx           # Main React component
│   │   ├── main.tsx          # React entry point
│   │   └── components/       # Reusable UI components
│   ├── package.json          # Node.js dependencies
│   ├── tsconfig.json         # TypeScript configuration
│   └── vite.config.ts        # Vite build configuration
├── start-all.bat             # Convenience script to start both backend and frontend (Windows)
├── README.md                 # This file
└── .venv/                    # Python virtual environment
```
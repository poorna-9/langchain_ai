Overview

This project allows users to start research sessions by submitting a query and optional supporting documents. The system uses an LLM (GPT-4o-mini via OpenAI API) to generate a report, summary, reasoning steps, and token usage cost. Users can continue research sessions, view their history, and inspect detailed results for each session.

Features
Start a research session with a query and optional documents
Continue an existing research session
Upload and store supporting documents (PDF or TXT)
Generate AI-based report, summary, and reasoning
Track token usage and cost for each session
Retrieve session history and detailed session results

Tech Stack
Backend Framework: Django 4.x (Python)
API Layer: Django REST Framework
Database: PostgreSQL (hosted on Railway)
AI Model: OpenAI GPT-4o-mini (via langchain and ChatOpenAI)
File Storage: Local or cloud storage (Cloudinary optional for deployment)
Server & Deployment: Gunicorn WSGI server, Railway for deployment
Parsing Libraries: PyPDF2 for PDF text extraction

[Client / Postman / Frontend]
          |
          v
  [Django REST API Views]
          |
          v
  [ResearchSession] --- stores session info
          |
  [UploadedDocument] -- stores uploaded files
          |
  [LLM] -------------- stores AI responses
          |
  [ResearchSummary] --- stores summaries
          |
  [ResearchReasoning] - stores reasoning & sources
          |
  [ResearchCost] ------ stores token usage & cost
          |
          v
[PostgreSQL Database]

API Endpoints
Endpoint	Method	Description
/start-research/	POST	Start a new research session with query and optional files.
/continue-research/<research_id>/	POST	Continue an existing session with new query and files.
/research-history/	GET	Get all research sessions for the user.
/research-detail/<research_id>/	GET	Get detailed results, summary, reasoning, sources, and cost.


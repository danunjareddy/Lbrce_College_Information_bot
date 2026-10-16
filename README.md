# LBRCE College Information Chatbot 🎓

An AI-powered college information chatbot that helps students find information from uploaded college documents, including examination notifications, registration schedules, examination fees, and results.

Built using **React, FastAPI, Python, Groq API, and document retrieval**.

## 🚀 Features

- **AI-powered question answering:** Ask questions in natural language.
- **College document retrieval:** Retrieves relevant information from uploaded PDF and text documents.
- **Examination information:** Answers questions about examination schedules, registration deadlines, and fees when supported by the available documents.
- **Source references:** Returns relevant document titles and available source links.
- **Greeting support:** Handles greetings, acknowledgements, and common conversational messages.
- **Fallback responses:** Indicates when the available documents do not contain enough information to answer a question.
- **React frontend:** Provides an interactive chat interface.
- **FastAPI backend:** Exposes API endpoints for health checks and chatbot requests.
- **Groq integration:** Uses a Groq-hosted language model to generate responses from retrieved context.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | React |
| Frontend development server | Vite |
| Backend | Python, FastAPI |
| AI inference | Groq API |
| Language model | Configurable through `GROQ_MODEL` |
| Document processing | Python, PDF and text extraction |
| Document storage | JSON (`college_docs.json`) |
| API server | Uvicorn |
| Environment configuration | Python dotenv |

## 🏗️ System Architecture

```text
                 Student
                    |
                    v
             React Frontend
                    |
                    v
              FastAPI Backend
                    |
                    v
          Question Preprocessing
                    |
                    v
        College Document Retrieval
                    |
                    v
        Relevant Document Context
                    |
                    v
                Groq API
                    |
                    v
           Generated Answer
                    |
                    v
       Answer + Relevant Sources
                    |
                    v
             React Frontend
```

The chatbot retrieves relevant document chunks before generating an answer. This helps ground responses in the available college information.

## 📁 Project Structure

```text
college-info-chatbot/
│
├── backend/
│   ├── main.py
│   ├── ingest.py
│   ├── college_docs.json
│   ├── .env
│   └── documents/
│       ├── pdfs/
│       └── *.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

The exact frontend structure may differ depending on your implementation.

**Important:** Do not commit `.env`, virtual environments, API keys, or private student information to GitHub.

## ✅ Prerequisites

Install the following before running the project:

- Python 3.10 or later, compatible with your installed dependencies
- Node.js and npm
- Git
- A Groq API key
- A modern web browser

Get your API key from the [Groq Console](https://console.groq.com/keys).

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/lbrce-college-info-chatbot.git
cd lbrce-college-info-chatbot
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Set up the backend

Open PowerShell in the project root:

```powershell
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the Python executable directly without activating the environment.

Install the dependencies:

```powershell
python -m pip install fastapi uvicorn groq python-dotenv pydantic
```

If your project uses additional packages for PDF extraction or OCR, install those as required by `ingest.py`.

### 3. Configure environment variables

Create a file named `.env` inside the `backend` directory.

Add:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Replace the placeholder with your own Groq API key.

Use a model ID currently available to your Groq account. If you tested a different model successfully, configure that model ID instead.

**Never upload your actual `.env` file to GitHub.**

### 4. Prepare the college documents

Place the authorized college PDFs and text files inside the appropriate folders under:

```text
backend/documents/
```

If your ingestion script uses a different input directory, follow the paths defined in `backend/ingest.py`.

Run the ingestion script from the backend directory:

```powershell
python ingest.py
```

This should extract document text and generate or update:

```text
backend/college_docs.json
```

Check the ingestion output for extraction errors, empty documents, and the number of chunks created.

Some scanned PDFs may require OCR software and additional Python packages.

### 5. Start the backend

From the `backend` directory, run:

```powershell
python -m uvicorn main:app --reload --port 8000
```

The backend should be available at:

- API root: http://localhost:8000/
- Health check: http://localhost:8000/api/health
- Interactive API documentation: http://localhost:8000/docs

Keep this terminal open while using the chatbot.

### 6. Start the frontend

Open a second PowerShell terminal:

```powershell
cd D:\anji\MyProjects\college-info-chatbot\frontend
npm install
npm run dev
```

Open the local address displayed by Vite, usually:

http://localhost:5173/

The frontend must be configured to send chat requests to the FastAPI backend at `http://localhost:8000`.

## 🔌 API Endpoints

### Health Check

**Endpoint:** `GET /api/health`

Example:

```http
GET http://localhost:8000/api/health
```

The endpoint reports backend status, provider configuration, model configuration, and loaded-document count.

### Chat

**Endpoint:** `POST /api/chat`

Example request:

```json
{
  "question": "What is the registration start date for the VII Semester R23 regular examinations?"
}
```

Example response structure:

```json
{
  "answer": "The registration date is based on the relevant college notification.",
  "sources": [
    {
      "title": "Examination Notification",
      "url": "https://www.lbrce.ac.in/examsection_pages/examnotific.php",
      "snippet": "Relevant extracted document text"
    }
  ]
}
```

The answer and source values above are illustrative. Actual responses depend on the uploaded documents and retrieval results.

## 🧪 Testing

Test the application with questions such as:

1. `Hi`
2. `How are you?`
3. `Thanks, that helped!`
4. `What is the registration start date for the VII Semester R23 regular examinations?`
5. `What is the last date to register without a late fee?`
6. `What is the Minor/Honors examination fee?`
7. `What is the R17 supplementary examination fee for two subjects?`
8. `Where can I find the official examination notification?`
9. `What is the registration date for an examination not covered by the uploaded documents?`

Verify factual answers against the original notifications. A test should pass only when the answer and source attribution meet the expected result.

## 🔐 Security and Privacy

- Store API keys in environment variables.
- Never commit `.env` or other secret files.
- Keep `.venv`, `node_modules`, and generated build files out of Git.
- Review uploaded PDFs, results, and student lists for personal information before publishing.
- Do not expose student results or personally identifiable information without authorization.
- Use HTTPS and appropriate access controls before deploying publicly.
- Apply API rate limiting and input validation for production deployments.

## ⚠️ Limitations

- The chatbot can only answer reliably when relevant information is present in the indexed documents.
- OCR errors in scanned documents may affect retrieval and answer accuracy.
- Keyword-based retrieval may miss semantically related content.
- Source links may point to an official listing page rather than a direct PDF.
- Groq availability, model access, rate limits, and quotas depend on the account and current service conditions.
- The local development configuration is not a production deployment.

## 🔮 Future Improvements

- Semantic search using embeddings and a vector database.
- Improved document ranking and metadata filtering.
- Automatic synchronization with authorized official college notices.
- Better PDF parsing and OCR validation.
- Automated unit tests and retrieval evaluation.
- Conversation history and follow-up questions.
- Deployment with authentication, monitoring, and rate limiting.

## 📚 Official Resources

- [LBRCE Official Website](https://www.lbrce.ac.in/)
- [LBRCE Examination Results](https://www.lbrce.ac.in/examsection_pages/examresults.php)
- [LBRCE Examination Notifications](https://www.lbrce.ac.in/examsection_pages/examnotific.php)
- [Groq Console](https://console.groq.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vite.dev/)

## 👨‍💻 Project Information

**Project:** LBRCE College Information Chatbot  
**Purpose:** Help students access information contained in college documents through a conversational interface.  
**Status:** Development and testing

---

If you find this project useful, consider starring the repository and contributing improvements.

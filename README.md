## AI Resume Reviewer (Backend)

Developed the backend for an AI-powered resume analysis platform that enables users to upload resumes and receive automated feedback based on job descriptions.

**Tech Stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, LangChain, Gemini AI, Supabase Storage

### Key Features

- Implemented secure **user authentication** with signup and login APIs using JWT-based authentication.
- Built a **resume upload system** allowing users to upload PDF resumes and store them securely in Supabase Storage.
- Integrated a **PDF parsing pipeline** to extract and process resume text from uploaded resumes.
- Designed an **AI-powered resume review endpoint** that evaluates resumes against job descriptions and generates structured feedback.
- Implemented a **modular service-layer backend architecture** separating routes, services, database logic, and utilities for maintainability and scalability.
- Prepared integration for **vector embeddings and Pinecone vector database**, which will be reconnected when implementing the AI chat system for semantic resume interaction.

### Backend Architecture

The backend follows a layered architecture:

- **Routes layer** – Defines API endpoints for authentication, resume management, and AI evaluation.
- **Services layer** – Contains the business logic for authentication, resume processing, and AI review.
- **Database layer** – Handles PostgreSQL database operations and storage integrations.
- **Schemas layer** – Defines request and response models using Pydantic.
- **Utilities layer** – Provides reusable components for authentication, PDF parsing, security, and text processing.

This modular structure allows the backend to scale easily and keeps responsibilities clearly separated.

### Environment Configuration

Sensitive configuration values are stored in a `.env` file to avoid exposing credentials inside the codebase.  
The `.env` file is loaded at runtime and provides environment-specific settings for the application.

Typical environment variables include:

DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
JWT_SECRET_KEY=
JWT_ALGORITHM=
GEMINI_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX=

These variables manage:

- Database connection credentials
- Supabase storage configuration
- JWT authentication secrets
- AI model API keys
- Vector database configuration

Using a `.env` file ensures secure configuration management across development and production environments.

### Planned Enhancements

- AI chat system for interacting with resume content.
- Semantic resume analysis using vector embeddings and Pinecone.
- Interview question generation based on extracted resume skills.
- ATS compatibility scoring and improvement recommendations.


# Setup Guide

Follow the steps below to run the **AI Resume Reviewer Backend** locally.

## 1. Clone the Repository

```bash
git clone <repository-url>
cd Resume-Reviewer
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a `.env` file in the project root and add the required configuration variables.

Example:

```env
DATABASE_URL=your_postgres_database_url
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
SUPABASE_BUCKET=resumes
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_pinecone_index
```

These variables configure:

- PostgreSQL database connection
- Supabase storage access
- JWT authentication
- Gemini AI model access
- Pinecone vector database configuration

## 5. Run the Backend Server

```bash
uvicorn main:app --reload
```

The server will start on:

```
http://127.0.0.1:8000
```

## 6. Access API Documentation

FastAPI automatically generates interactive documentation.

**Swagger UI:**
```
http://127.0.0.1:8000/docs
```

**ReDoc:**
```
http://127.0.0.1:8000/redoc
```

## 7. Typical Workflow

1. Create a user account using the signup endpoint.
2. Log in to obtain an authentication token.
3. Upload a resume in PDF format.
4. The backend parses the resume and stores it.
5. Call the AI review endpoint to receive feedback based on a job description.

## 8. Notes

- Vector embedding and Pinecone integration are currently disabled in the active pipeline.
- These components will be reconnected when the AI chat system is implemented for semantic resume interaction.
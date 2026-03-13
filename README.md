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
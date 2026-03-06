# 📄 Resume Reviewer — V0

An AI-powered resume reviewer that stores your resume in a vector database and uses Google Gemini to provide detailed feedback on strengths, weaknesses, and improvement suggestions.

---

## 🚀 Features

- 📥 Load resume from a PDF file
- 🧠 Generate embeddings using Google Gemini (`gemini-embedding-001`)
- 📦 Store and retrieve resume chunks from **Pinecone** vector database
- 💬 Send retrieved content to **Gemini LLM** for intelligent review
- ✅ Get detailed feedback on strengths, weaknesses, and suggestions

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| LangChain | LLM framework |
| Google Gemini | Embeddings + LLM |
| Pinecone | Vector database |
| PyPDF | PDF parsing |
| python-dotenv | Environment variables |

---

## 📁 Folder Structure

```
Resume-Reviewer/
│
├── venv/                  # Virtual environment (not pushed to git)
├── data/
│   └── resume.pdf         # Your resume PDF
├── src/
│   └── main.py            # Main script
├── .env                   # API keys (not pushed to git)
├── .gitignore             # Ignores venv, .env, __pycache__
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Resume-Reviewer.git
cd Resume-Reviewer
```

### 2. Create and activate virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

### 5. Set up Pinecone Index
- Go to [pinecone.io](https://pinecone.io)
- Create an index named `resume-reviewer` with **3072 dimensions**

### 6. Run the script
```bash
python src/main.py
```

---

## 🔑 Getting API Keys

- **Google Gemini API Key** → [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Pinecone API Key** → [Pinecone Console](https://app.pinecone.io)

---

## 📌 How It Works

1. The resume PDF is loaded and parsed using `PyPDFLoader`
2. The text is embedded using `GoogleGenerativeAIEmbeddings`
3. Embeddings are stored in **Pinecone** vector database
4. Relevant chunks are retrieved using semantic search
5. Retrieved content is sent to **Gemini LLM** with a review prompt
6. AI returns detailed feedback on the resume

---

## 🔮 Planned Upgrades (V1+)

- [ ] Streamlit web UI with drag & drop PDF upload
- [ ] Job description matching & scoring
- [ ] Resume score out of 100
- [ ] Cover letter generator
- [ ] Interview questions generator
- [ ] Multi-resume comparison

---

## 🙌 Author

**Sayan** — [LinkedIn](https://linkedin.com/in/sayan-dutta2006)

---

## 📝 License

MIT License
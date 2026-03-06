from dotenv import load_dotenv
import os
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage

# Load PDF
file_path = r"FILE_PATH_HERE.pdf"
loader = PyPDFLoader(file_path)
docs = loader.load()

# Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Store in Pinecone
vector_store = PineconeVectorStore.from_documents(
    docs,
    embedding=embeddings,
    index_name="resume-reviewer"
)

# Retrieve from Pinecone
results = vector_store.similarity_search("resume experience skills education", k=10)
resume_text = "\n".join([doc.page_content for doc in results])

# Send to Gemini for review
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

messages = [
    SystemMessage(content="You are an expert resume reviewer. Analyze the given resume and provide detailed feedback on its strengths, weaknesses, and suggestions for improvement."),
    HumanMessage(content=f"Please review this resume:\n\n{resume_text}")
]

response = model.invoke(messages)
print(response.content)
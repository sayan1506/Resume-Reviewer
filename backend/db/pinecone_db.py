from pinecone import Pinecone
from .config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(PINECONE_INDEX)


def store_embedding(resume_id, embedding, metadata=None):
    index.upsert([
    {
        "id": str(resume_id),
        "values": embedding,
        "metadata": {
            "resume_id": resume_id
        }
    }
    ])


def query_embedding(vector, top_k=5):
    return index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )
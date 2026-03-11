from db.pinecone_db import index
from utils.text_chunker import chunk_text
from utils.embedding import create_embedding


def store_resume_embeddings(resume_id: str, text: str):

    chunks = chunk_text(text)

    vectors = []

    for i, chunk in enumerate(chunks):

        embedding = create_embedding(chunk)

        vectors.append({
            "id": f"{resume_id}_{i}",
            "values": embedding,
            "metadata": {
                "resume_id": resume_id,
                "text": chunk
            }
        })

    index.upsert(vectors=vectors)
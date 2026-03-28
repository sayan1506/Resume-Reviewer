from db.pinecone_db import index
from utils.text_chunker import chunk_text
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def create_embedding(text: str) -> list[float]:
    return embedder.embed_query(text)


def store_resume_embeddings(resume_id: int, text: str, type: str):
    """
    type: "review" | "evaluate"
    Chunks the text, embeds each chunk, upserts all into Pinecone.
    """
    chunks = chunk_text(text)

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)

        vectors.append({
            "id": f"{resume_id}_{type}_{i}",
            "values": embedding,
            "metadata": {
                "resume_id": resume_id,
                "type": type,
                "text": chunk        # stored so chat can retrieve raw text as context
            }
        })

    index.upsert(vectors=vectors)


def query_resume_embeddings(resume_id: int, query: str, type: str = None, top_k: int = 5):
    """
    Queries Pinecone for chunks relevant to the user's question.
    Optionally filter by type ("review" or "evaluate").
    Returns list of matching text chunks.
    """
    query_vector = create_embedding(query)

    filter = {"resume_id": {"$eq": resume_id}}

    if type:
        filter["type"] = {"$eq": type}

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter
    )

    return [match["metadata"]["text"] for match in results["matches"]]
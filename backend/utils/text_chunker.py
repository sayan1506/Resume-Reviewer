# def chunk_text(text: str, chunk_size=800, overlap=100):

#     chunks = []

#     start = 0

#     while start < len(text):
#         end = start + chunk_size
#         chunks.append(text[start:end])
#         start += chunk_size - overlap

#     return chunks
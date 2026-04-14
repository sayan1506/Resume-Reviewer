def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Splits text into overlapping chunks on word boundaries.
    chunk_size and overlap are measured in characters (approximate).
    """
    words = text.split()
    chunks = []
    current_chars = 0
    current_words: list[str] = []
    overlap_words: list[str] = []

    for word in words:
        current_words.append(word)
        current_chars += len(word) + 1  # +1 for the space

        if current_chars >= chunk_size:
            chunk = " ".join(current_words)
            chunks.append(chunk)

            # Carry over the last `overlap` characters worth of words
            overlap_words = []
            overlap_chars = 0
            for w in reversed(current_words):
                overlap_chars += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_chars >= overlap:
                    break

            current_words = overlap_words[:]
            current_chars = sum(len(w) + 1 for w in current_words)

    # Append any remaining words as the last chunk
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
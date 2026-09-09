import re
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TenderRetriever:
    """
    Lightweight local retrieval for deployment.

    This MVP uses TF-IDF retrieval, which avoids downloading a large
    embedding model on Streamlit Cloud. It can later be replaced with
    Sentence Transformers + FAISS/Qdrant without changing the UI.
    """

    def __init__(self, text: str, chunk_size: int = 1200):
        self.chunks = self._chunk_text(text, chunk_size)

        if not self.chunks:
            self.chunks = ["No tender text available."]

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.matrix = self.vectorizer.fit_transform(self.chunks)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int) -> List[str]:
        clean = re.sub(r"\s+", " ", text).strip()

        return [
            clean[i : i + chunk_size]
            for i in range(0, len(clean), chunk_size)
            if clean[i : i + chunk_size].strip()
        ]

    def retrieve(self, query: str, top_k: int = 5) -> str:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]

        ranked = scores.argsort()[::-1][:top_k]

        selected = []
        for idx in ranked:
            if scores[idx] > 0:
                selected.append(
                    f"[Relevance: {scores[idx]:.3f}]\n{self.chunks[idx]}"
                )

        if not selected:
            selected = self.chunks[:top_k]

        return "\n\n".join(selected)

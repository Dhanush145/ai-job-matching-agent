
from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"

        self.model = SentenceTransformer(
            self.model_name
        )

    def generate_embedding(self, text: str):
        """
        Convert one text into a normalized embedding.
        """

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embedding.astype("float32")

    def generate_embeddings(self, texts: list[str]):
        """
        Generate embeddings for multiple documents.
        """

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        return embeddings.astype("float32")


# Reusable service instance
embedding_service = EmbeddingService()

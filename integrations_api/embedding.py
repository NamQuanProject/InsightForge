import os
import mimetypes
import numpy as np
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class GeminiEmbedder:
    def __init__(self, model: str = "gemini-embedding-2-preview"):
        # The client stays the same, but we will use the .aio property
        self.client = genai.Client()
        self.model = model

    # ---------- IMAGE (NOW ASYNC) ----------
    async def embed_image(self, image_path: str) -> np.ndarray:
        # Use asyncio.to_thread for file reading to avoid blocking the loop
        image_bytes = await asyncio.to_thread(open(image_path, "rb").read)

        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type = mime_type or "image/png"

        # USE THE .aio CLIENT FOR ASYNC CALLS
        result = await self.client.aio.models.embed_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            ],
        )

        return np.array(result.embeddings[0].values)

    # ---------- TEXT (NOW ASYNC) ----------
    async def embed_text(self, text: str) -> np.ndarray:
        # MUST use await and .aio
        result = await self.client.aio.models.embed_content(
            model=self.model,
            contents=text,
        )
        return np.array(result.embeddings[0].values)

    # ---------- SEARCH (STAYS SYNC) ----------
    # This is pure math/CPU, so it doesn't need to be async
    def search(
        self,
        query_vec: np.ndarray,
        db_vectors: list[np.ndarray],
        metadata: list[dict] | None = None,
        top_k: int = 3
    ):
        def cosine_similarity(v1, v2):
            v1 = v1 / (np.linalg.norm(v1) + 1e-9)
            v2 = v2 / (np.linalg.norm(v2) + 1e-9)
            return float(np.dot(v1, v2))

        sims = [cosine_similarity(query_vec, v) for v in db_vectors]
        top_indices = np.argsort(sims)[-top_k:][::-1]

        results = []
        for i in top_indices:
            item = {"score": float(sims[i])}
            if metadata is not None:
                item["meta"] = metadata[i]
            else:
                item["index"] = int(i)
            results.append(item)

        return results

# Initialize the embedder
embedder = GeminiEmbedder()
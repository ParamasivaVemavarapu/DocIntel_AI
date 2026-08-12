import uuid
from collections import OrderedDict
import httpx
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from .config import Settings
from .ingestion import PageText
from .schemas import Source


class DocumentStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = (
            QdrantClient(path=settings.qdrant_path)
            if settings.qdrant_path
            else QdrantClient(url=settings.qdrant_url)
        )
        self.encoder = SentenceTransformer(settings.embedding_model)
        self.vector_size = self.encoder.get_sentence_embedding_dimension()
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self.client.collection_exists(self.settings.collection_name):
            self.client.create_collection(
                collection_name=self.settings.collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
            )

    def add(self, filename: str, chunks: list[PageText]) -> tuple[str, int]:
        document_id = str(uuid.uuid4())
        vectors = self.encoder.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={"document_id": document_id, "filename": filename, "page": chunk.page, "chunk": chunk.text},
            )
            for vector, chunk in zip(vectors, chunks)
        ]
        if points:
            self.client.upsert(self.settings.collection_name, points=points, wait=True)
        return document_id, len(points)

    def search(self, question: str, top_k: int) -> list[Source]:
        vector = self.encoder.encode(question, normalize_embeddings=True).tolist()
        hits = self.client.query_points(self.settings.collection_name, query=vector, limit=top_k).points
        return [Source(**hit.payload, score=round(float(hit.score), 4)) for hit in hits]

    def list_documents(self) -> list[dict]:
        records: OrderedDict[str, dict] = OrderedDict()
        offset = None
        while True:
            points, offset = self.client.scroll(self.settings.collection_name, limit=100, offset=offset, with_payload=True)
            for point in points:
                doc_id = point.payload["document_id"]
                records.setdefault(doc_id, {"document_id": doc_id, "filename": point.payload["filename"], "chunks": 0})
                records[doc_id]["chunks"] += 1
            if offset is None:
                break
        return list(records.values())

    def delete(self, document_id: str) -> None:
        self.client.delete(
            self.settings.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))])
            ),
            wait=True,
        )


async def answer_question(question: str, sources: list[Source], settings: Settings) -> tuple[str, str]:
    if not sources:
        return "I could not find relevant content in the indexed documents.", "extractive"
    context = "\n\n".join(f"[{i}] {s.filename} page {s.page or 'n/a'}: {s.chunk}" for i, s in enumerate(sources, 1))
    prompt = (
        "Answer only from the supplied context. If the answer is absent, say so. "
        "Use citation markers like [1].\n\n"
        f"Question: {question}\n\nContext:\n{context}"
    )
    provider = settings.llm_provider.lower()
    if provider == "groq" and settings.groq_api_key:
        return await _openai_compatible("https://api.groq.com/openai/v1/chat/completions", settings.groq_api_key, "llama-3.3-70b-versatile", prompt), provider
    if provider == "mistral" and settings.mistral_api_key:
        return await _openai_compatible("https://api.mistral.ai/v1/chat/completions", settings.mistral_api_key, "mistral-large-latest", prompt), provider
    if provider == "gemini" and settings.google_api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.google_api_key}"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"], provider
    return f"The most relevant passage says: {sources[0].chunk} [1]", "extractive"


async def _openai_compatible(url: str, key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers={"Authorization": f"Bearer {key}"}, json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1})
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

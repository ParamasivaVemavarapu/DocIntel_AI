from functools import lru_cache
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_settings
from .ingestion import chunk_pages, parse_document
from .retrieval import DocumentStore, answer_question
from .schemas import DocumentRecord, QueryRequest, QueryResponse

app = FastAPI(title="DocIntel AI API", version="1.0.0")
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_store() -> DocumentStore:
    return DocumentStore(get_settings())


@app.get("/")
def root() -> dict:
    return {"service": "DocIntel AI API", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "provider": settings.llm_provider}


@app.post("/api/documents", response_model=DocumentRecord, status_code=201)
async def upload_document(file: UploadFile = File(...), store: DocumentStore = Depends(get_store)):
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")
    try:
        chunks = chunk_pages(parse_document(file.filename or "document", content))
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    if not chunks:
        raise HTTPException(422, "No readable text found in the document")
    document_id, count = store.add(file.filename or "document", chunks)
    return DocumentRecord(document_id=document_id, filename=file.filename or "document", chunks=count)


@app.get("/api/documents", response_model=list[DocumentRecord])
def list_documents(store: DocumentStore = Depends(get_store)):
    return store.list_documents()


@app.delete("/api/documents/{document_id}", status_code=204)
def delete_document(document_id: str, store: DocumentStore = Depends(get_store)):
    store.delete(document_id)


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, store: DocumentStore = Depends(get_store)):
    sources = store.search(request.question, request.top_k)
    answer, provider = await answer_question(request.question, sources, settings)
    return QueryResponse(answer=answer, provider=provider, sources=sources)

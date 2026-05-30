"""
Vector Database Store for GraftAI
Handles semantic search and embeddings for AI memory
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Document:
    """Document stored in vector database"""
    id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = None

class VectorStore:
    """
    Vector database for semantic search and AI memory

    Responsibilities:
    - Store and retrieve documents with embeddings
    - Semantic search for relevant context
    - Manage conversation history
    - Store scheduling patterns and preferences
    - Support RAG (Retrieval-Augmented Generation)
    """

    def __init__(self, embedding_dimension: int=1536):
        self.embedding_dimension = embedding_dimension
        self._collections: dict[str, list[Document]] = {}
        logger.info("VectorStore initialized with dimension: %s", embedding_dimension)

    async def add_document(self, collection: str, document: dict[str, Any], metadata: dict[str, Any] | None=None, document_id: str | None=None) -> str:
        """
        Add a document to the vector store

        Args:
            collection: Collection name (e.g., 'conversations', 'patterns', 'feedback')
            document: Document content
            metadata: Optional metadata for filtering
            document_id: Optional document ID (generated if not provided)

        Returns:
            Document ID
        """
        if document_id is None:
            content_str = json.dumps(document, sort_keys=True)
            document_id = hashlib.md5(content_str.encode()).hexdigest()
        content_str = json.dumps(document) if isinstance(document, dict) else str(document)
        embedding = await self._generate_embedding(content_str)
        doc = Document(id=document_id, content=content_str, embedding=embedding, metadata=metadata or {})
        if collection not in self._collections:
            self._collections[collection] = []
        self._collections[collection].append(doc)
        if len(self._collections[collection]) > 10000:
            self._collections[collection] = self._collections[collection][-5000:]
        logger.debug("Added document %s to collection %s", document_id, collection)
        return document_id

    async def search(self, collection: str, query: str | dict[str, Any], limit: int=10, filters: dict[str, Any] | None=None) -> list[dict[str, Any]]:
        """
        Search for documents by semantic similarity

        Args:
            collection: Collection to search
            query: Search query or document
            limit: Maximum results to return
            filters: Optional metadata filters

        Returns:
            List of matching documents with similarity scores
        """
        if collection not in self._collections:
            return []
        query_str = json.dumps(query) if isinstance(query, dict) else str(query)
        query_embedding = await self._generate_embedding(query_str)
        results = []
        for doc in self._collections[collection]:
            if filters and (not self._matches_filters(doc.metadata, filters)):
                continue
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                try:
                    content = json.loads(doc.content)
                except json.JSONDecodeError:
                    content = doc.content
                results.append({"id": doc.id, "content": content, "metadata": doc.metadata, "similarity": similarity})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    async def get_document(self, collection: str, document_id: str) -> dict[str, Any] | None:
        """Get a specific document by ID"""
        if collection not in self._collections:
            return None
        for doc in self._collections[collection]:
            if doc.id == document_id:
                try:
                    content = json.loads(doc.content)
                except json.JSONDecodeError:
                    content = doc.content
                return {"id": doc.id, "content": content, "metadata": doc.metadata}
        return None

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document by ID"""
        if collection not in self._collections:
            return False
        original_count = len(self._collections[collection])
        self._collections[collection] = [doc for doc in self._collections[collection] if doc.id != document_id]
        deleted = len(self._collections[collection]) < original_count
        if deleted:
            logger.debug("Deleted document %s from %s", document_id, collection)
        return deleted

    async def update_document(self, collection: str, document_id: str, document: dict[str, Any], metadata: dict[str, Any] | None=None) -> bool:
        """Update an existing document"""
        deleted = await self.delete_document(collection, document_id)
        if not deleted:
            return False
        await self.add_document(collection, document, metadata, document_id)
        return True

    async def get_similar(self, collection: str, document_id: str, limit: int=5) -> list[dict[str, Any]]:
        """Find documents similar to a given document"""
        doc = await self.get_document(collection, document_id)
        if not doc:
            return []
        results = await self.search(collection=collection, query=doc["content"], limit=limit + 1)
        filtered = [item for item in results if item.get("id") != document_id]
        return filtered[:limit]

    async def count(self, collection: str, filters: dict | None=None) -> int:
        """Count documents in a collection"""
        if collection not in self._collections:
            return 0
        if not filters:
            return len(self._collections[collection])
        count = 0
        for doc in self._collections[collection]:
            if self._matches_filters(doc.metadata, filters):
                count += 1
        return count

    async def clear_collection(self, collection: str) -> bool:
        """Clear all documents from a collection"""
        if collection in self._collections:
            self._collections[collection] = []
            logger.info("Cleared collection: %s", collection)
            return True
        return False

    async def get_collections(self) -> list[str]:
        """Get list of all collections"""
        return list(self._collections.keys())

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text

        In production, this would use:
        - OpenAI embeddings (text-embedding-3-small)
        - SentenceTransformers
        - Local embedding models
        """
        hash_val = hashlib.md5(text.encode()).hexdigest()
        embedding = []
        for i in range(self.embedding_dimension):
            idx = i * 2 % 32
            val = int(hash_val[idx:idx + 2], 16) / 255.0
            embedding.append(val)
        return embedding

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = sum((a * b for a, b in zip(vec1, vec2, strict=False)))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _matches_filters(self, metadata: dict | None, filters: dict[str, Any]) -> bool:
        """Check if metadata matches filters"""
        if not metadata:
            return not filters
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, dict):
                for op, op_val in value.items():
                    if (op == "$ne" and metadata[key] == op_val) or (op == "$gt" and metadata[key] <= op_val):
                        return False
                    if (op == "$lt" and metadata[key] >= op_val) or (op == "$in" and metadata[key] not in op_val):
                        return False
            elif metadata[key] != value:
                return False
        return True

    async def get_context_for_llm(self, user_id: str, query: str, max_tokens: int=2000) -> str:
        """
        Get relevant context for LLM from all collections

        This implements RAG (Retrieval-Augmented Generation)
        """
        context_parts = []
        patterns = await self.search(collection="scheduling_patterns", query=query, limit=5, filters={"user_id": user_id})
        if patterns:
            context_parts.append("## User Scheduling Patterns")
            for p in patterns:
                content = p["content"]
                if isinstance(content, dict):
                    context_parts.append(f"- {json.dumps(content)}")
        conversations = await self.search(collection="conversations", query=query, limit=3, filters={"user_id": user_id})
        if conversations:
            context_parts.append("## Relevant Past Conversations")
            for c in conversations:
                content = c["content"]
                if isinstance(content, dict):
                    msg = content.get("message", "")
                    context_parts.append(f"- Previous: {msg[:200]}...")
        feedback = await self.search(collection="feedback", query=query, limit=2, filters={"user_id": user_id})
        if feedback:
            context_parts.append("## User Feedback")
            for f in feedback:
                content = f["content"]
                if isinstance(content, dict):
                    rating = content.get("rating", "N/A")
                    comments = content.get("comments", "")
                    context_parts.append(f"- Rating: {rating}, Comments: {comments[:100]}...")
        return "\n\n".join(context_parts)
_vector_store: VectorStore | None = None

async def get_vector_store() -> VectorStore:
    """Get or create the global vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

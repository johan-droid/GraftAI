"""
Vector Database Store for GraftAI
Handles semantic search and embeddings for AI memory
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import hashlib
import json
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Document:
    """Document stored in vector database"""

    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None


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

    def __init__(self, embedding_dimension: int = 1536):
        self.embedding_dimension = embedding_dimension

        # In-memory storage (replace with actual vector DB in production)
        # Production: Pinecone, Weaviate, Chroma, pgvector, etc.
        self._collections: Dict[str, List[Document]] = {}

        logger.info(f"VectorStore initialized with dimension: {embedding_dimension}")

    async def add_document(
        self,
        collection: str,
        document: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
    ) -> str:
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
        # Generate ID if not provided
        if document_id is None:
            content_str = json.dumps(document, sort_keys=True)
            document_id = hashlib.md5(content_str.encode()).hexdigest()

        # Convert document to string for embedding
        content_str = (
            json.dumps(document) if isinstance(document, dict) else str(document)
        )

        # Generate embedding
        embedding = await self._generate_embedding(content_str)

        # Create document
        doc = Document(
            id=document_id,
            content=content_str,
            embedding=embedding,
            metadata=metadata or {},
        )

        # Add to collection
        if collection not in self._collections:
            self._collections[collection] = []

        self._collections[collection].append(doc)

        # Keep collection size manageable
        if len(self._collections[collection]) > 10000:
            self._collections[collection] = self._collections[collection][-5000:]

        logger.debug(f"Added document {document_id} to collection {collection}")

        return document_id

    async def search(
        self,
        collection: str,
        query: Union[str, Dict[str, Any]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
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
        # Check collection exists
        if collection not in self._collections:
            return []

        # Generate query embedding
        query_str = json.dumps(query) if isinstance(query, dict) else str(query)
        query_embedding = await self._generate_embedding(query_str)

        # Calculate similarities
        results = []
        for doc in self._collections[collection]:
            # Apply filters if provided
            if filters and not self._matches_filters(doc.metadata, filters):
                continue

            # Calculate cosine similarity
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)

                # Parse content back to dict if possible
                try:
                    content = json.loads(doc.content)
                except json.JSONDecodeError:
                    content = doc.content

                results.append(
                    {
                        "id": doc.id,
                        "content": content,
                        "metadata": doc.metadata,
                        "similarity": similarity,
                    }
                )

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:limit]

    async def get_document(
        self, collection: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
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
        self._collections[collection] = [
            doc for doc in self._collections[collection] if doc.id != document_id
        ]

        deleted = len(self._collections[collection]) < original_count

        if deleted:
            logger.debug(f"Deleted document {document_id} from {collection}")

        return deleted

    async def update_document(
        self,
        collection: str,
        document_id: str,
        document: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing document"""
        # Delete old version
        deleted = await self.delete_document(collection, document_id)

        if not deleted:
            return False

        # Add new version
        await self.add_document(collection, document, metadata, document_id)

        return True

    async def get_similar(
        self, collection: str, document_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""
        # Get the reference document
        doc = await self.get_document(collection, document_id)

        if not doc:
            return []

        # Search for similar documents, then exclude the reference doc
        results = await self.search(
            collection=collection, query=doc["content"], limit=limit + 1
        )

        filtered = [item for item in results if item.get("id") != document_id]
        return filtered[:limit]

    async def count(self, collection: str, filters: Optional[Dict] = None) -> int:
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
            logger.info(f"Cleared collection: {collection}")
            return True

        return False

    async def get_collections(self) -> List[str]:
        """Get list of all collections"""
        return list(self._collections.keys())

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text

        In production, this would use:
        - OpenAI embeddings (text-embedding-3-small)
        - SentenceTransformers
        - Local embedding models
        """
        # Placeholder: Simple hash-based embedding for demo
        # In production, use proper embedding model

        # Hash the text
        hash_val = hashlib.md5(text.encode()).hexdigest()

        # Convert to embedding vector (simple deterministic approach)
        embedding = []
        for i in range(self.embedding_dimension):
            # Use different parts of hash for each dimension
            idx = (i * 2) % 32
            val = int(hash_val[idx : idx + 2], 16) / 255.0  # Normalize to 0-1
            embedding.append(val)

        return embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _matches_filters(
        self, metadata: Optional[Dict], filters: Dict[str, Any]
    ) -> bool:
        """Check if metadata matches filters"""
        if not metadata:
            return not filters

        for key, value in filters.items():
            if key not in metadata:
                return False

            # Handle operators
            if isinstance(value, dict):
                for op, op_val in value.items():
                    if op == "$ne" and metadata[key] == op_val:
                        return False
                    elif op == "$gt" and metadata[key] <= op_val:
                        return False
                    elif op == "$lt" and metadata[key] >= op_val:
                        return False
                    elif op == "$in" and metadata[key] not in op_val:
                        return False
            else:
                if metadata[key] != value:
                    return False

        return True

    async def get_context_for_llm(
        self, user_id: str, query: str, max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for LLM from all collections

        This implements RAG (Retrieval-Augmented Generation)
        """
        context_parts = []

        # Search patterns
        patterns = await self.search(
            collection="scheduling_patterns",
            query=query,
            limit=5,
            filters={"user_id": user_id},
        )

        if patterns:
            context_parts.append("## User Scheduling Patterns")
            for p in patterns:
                content = p["content"]
                if isinstance(content, dict):
                    context_parts.append(f"- {json.dumps(content)}")

        # Search past conversations
        conversations = await self.search(
            collection="conversations",
            query=query,
            limit=3,
            filters={"user_id": user_id},
        )

        if conversations:
            context_parts.append("## Relevant Past Conversations")
            for c in conversations:
                content = c["content"]
                if isinstance(content, dict):
                    msg = content.get("message", "")
                    context_parts.append(f"- Previous: {msg[:200]}...")

        # Search feedback
        feedback = await self.search(
            collection="feedback", query=query, limit=2, filters={"user_id": user_id}
        )

        if feedback:
            context_parts.append("## User Feedback")
            for f in feedback:
                content = f["content"]
                if isinstance(content, dict):
                    rating = content.get("rating", "N/A")
                    comments = content.get("comments", "")
                    context_parts.append(
                        f"- Rating: {rating}, Comments: {comments[:100]}..."
                    )

        return "\n\n".join(context_parts)


# Global instance
_vector_store: Optional[VectorStore] = None


async def get_vector_store() -> VectorStore:
    """Get or create the global vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

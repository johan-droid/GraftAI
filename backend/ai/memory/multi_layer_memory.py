"""
Multi-Layer Memory Architecture for GraftAI Agents

Agent Memory = Short-Term + Medium-Term + Long-Term

┌─────────────────────────────────────────────────┐
│         MULTI-LAYER MEMORY                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  SHORT-TERM (Current Execution)                 │
│  ├─ Current booking details                    │
│  ├─ Active tool outputs                        │
│  ├─ Recent decisions                           │
│  └─ Conversation history                       │
│     (Expires: End of workflow)                  │
│                                                 │
│  MEDIUM-TERM (Session/User)                     │
│  ├─ User preferences                           │
│  ├─ Recent patterns                            │
│  ├─ Learning from this user                    │
│  └─ Contextual rules                           │
│     (Expires: Days)                           │
│                                                 │
│  LONG-TERM (Knowledge Base)                     │
│  ├─ All past booking outcomes                  │
│  ├─ Learned patterns across users              │
│  ├─ Best practices discovered                  │
│  ├─ Edge cases encountered                     │
│  └─ Vector embeddings of workflows             │
│     (Expires: Never)                            │
│                                                 │
└─────────────────────────────────────────────────┘

Implementation:
├─ Short-term: In-process cache/context
├─ Medium-term: Redis/Cache with TTL
├─ Long-term: Vector DB + Graph DB
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import hashlib

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryLayer(Enum):
    """The three memory layers"""
    SHORT_TERM = "short_term"      # Current execution
    MEDIUM_TERM = "medium_term"    # Session/user level
    LONG_TERM = "long_term"        # Persistent knowledge


class MemoryPriority(Enum):
    """Priority levels for memory retrieval"""
    CRITICAL = 1    # Must retrieve
    HIGH = 2        # Important context
    MEDIUM = 3      # Nice to have
    LOW = 4         # Background info


@dataclass
class MemoryEntry:
    """A single memory entry with metadata"""
    key: str
    value: Any
    layer: MemoryLayer
    priority: MemoryPriority
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None  # Which agent/tool created this
    
    def is_expired(self) -> bool:
        """Check if memory entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def touch(self):
        """Update access metadata"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


@dataclass
class ShortTermMemory:
    """
    SHORT-TERM MEMORY (Current Execution Context)
    
    Duration: End of workflow
    Storage: In-process dictionary
    Use: Active conversation, current booking, recent decisions
    """
    # Current execution context
    current_goal: Optional[str] = None
    current_plan: Optional[Dict] = None
    current_decision: Optional[Dict] = None
    
    # Tool outputs and intermediate results
    tool_outputs: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: List[Dict] = field(default_factory=list)
    
    # Conversation history (last N messages)
    conversation_history: List[Dict] = field(default_factory=list)
    max_history: int = 10
    
    # Active entity tracking
    current_entities: Dict[str, Any] = field(default_factory=dict)
    
    # Working variables
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def set_tool_output(self, tool_name: str, output: Any):
        """Store tool output"""
        self.tool_outputs[tool_name] = {
            "output": output,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_recent_context(self, n_messages: int = 5) -> str:
        """Get recent conversation as formatted string"""
        recent = self.conversation_history[-n_messages:]
        return "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in recent
        ])
    
    def clear(self):
        """Clear all short-term memory"""
        self.current_goal = None
        self.current_plan = None
        self.current_decision = None
        self.tool_outputs.clear()
        self.intermediate_results.clear()
        self.conversation_history.clear()
        self.current_entities.clear()
        self.variables.clear()


@dataclass
class MediumTermMemory:
    """
    MEDIUM-TERM MEMORY (Session/User Level)
    
    Duration: Days
    Storage: Redis/Cache with TTL
    Use: User preferences, recent patterns, learned rules
    """
    # User preferences (cached)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Recent booking patterns for this user
    recent_patterns: List[Dict] = field(default_factory=list)
    max_patterns: int = 50
    
    # Learned contextual rules
    contextual_rules: List[Dict] = field(default_factory=list)
    
    # User-specific insights
    user_insights: Dict[str, Any] = field(default_factory=dict)
    
    # Session state (persists across requests)
    session_state: Dict[str, Any] = field(default_factory=dict)
    
    # Recent successful strategies
    successful_strategies: List[Dict] = field(default_factory=list)
    
    def add_pattern(self, pattern_type: str, pattern_data: Dict, outcome: str):
        """Add a learned pattern"""
        entry = {
            "type": pattern_type,
            "data": pattern_data,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 1.0  # Will be adjusted over time
        }
        self.recent_patterns.append(entry)
        
        # Keep only recent patterns
        if len(self.recent_patterns) > self.max_patterns:
            self.recent_patterns = self.recent_patterns[-self.max_patterns:]
    
    def add_rule(self, condition: str, action: str, confidence: float = 0.5):
        """Add a contextual rule"""
        rule = {
            "condition": condition,
            "action": action,
            "confidence": confidence,
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        }
        self.contextual_rules.append(rule)
    
    def get_relevant_rules(self, context: str) -> List[Dict]:
        """Get rules relevant to current context"""
        relevant = []
        for rule in self.contextual_rules:
            if rule["condition"] in context:
                relevant.append(rule)
        # Sort by confidence
        return sorted(relevant, key=lambda r: r["confidence"], reverse=True)
    
    def update_preference(self, key: str, value: Any, confidence: float = 0.8):
        """Update user preference with confidence"""
        self.user_preferences[key] = {
            "value": value,
            "confidence": confidence,
            "updated_at": datetime.utcnow().isoformat(),
            "source": "learned"
        }


@dataclass
class LongTermMemory:
    """
    LONG-TERM MEMORY (Persistent Knowledge Base)
    
    Duration: Never expires
    Storage: Vector DB + Graph DB
    Use: Historical outcomes, learned patterns, best practices
    """
    # Reference to vector store
    vector_store: Optional[Any] = None
    
    # Reference to graph store
    graph_store: Optional[Any] = None
    
    # Episodic memories (key experiences)
    episodic_memories: List[Dict] = field(default_factory=list)
    max_episodes: int = 1000
    
    # Semantic knowledge (embeddings)
    knowledge_embeddings: Dict[str, List[float]] = field(default_factory=dict)
    
    # Best practices discovered
    best_practices: List[Dict] = field(default_factory=list)
    
    # Edge cases and their solutions
    edge_cases: List[Dict] = field(default_factory=list)
    
    # Cross-user patterns (anonymized)
    global_patterns: Dict[str, Any] = field(default_factory=dict)
    
    async def store_episode(self, episode: Dict):
        """Store an episodic memory"""
        episode["stored_at"] = datetime.utcnow().isoformat()
        self.episodic_memories.append(episode)
        
        # Keep size manageable
        if len(self.episodic_memories) > self.max_episodes:
            # Remove oldest with lowest importance
            self.episodic_memories = sorted(
                self.episodic_memories,
                key=lambda e: (e.get("importance", 0.5), e.get("stored_at", "")),
                reverse=True
            )[:self.max_episodes]
        
        # Also store in vector DB if available
        if self.vector_store:
            await self._store_in_vector_db(episode)
    
    async def _store_in_vector_db(self, episode: Dict):
        """Store episode in vector database"""
        try:
            text = json.dumps({
                "type": episode.get("type"),
                "description": episode.get("description"),
                "outcome": episode.get("outcome"),
                "context": episode.get("context")
            })
            
            metadata = {
                "user_id": episode.get("user_id", "unknown"),
                "timestamp": episode.get("timestamp"),
                "importance": episode.get("importance", 0.5),
                "tags": episode.get("tags", [])
            }
            
            # Store in vector store
            await self.vector_store.add_document(text, metadata)
        except Exception as e:
            logger.error(f"Failed to store in vector DB: {e}")
    
    async def retrieve_similar_episodes(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Retrieve similar past episodes"""
        if self.vector_store:
            try:
                results = await self.vector_store.similarity_search(query, n_results)
                return results
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # Fallback: simple text matching
        return self._fallback_retrieval(query, n_results)
    
    def _fallback_retrieval(self, query: str, n_results: int) -> List[Dict]:
        """Fallback retrieval using simple matching"""
        query_words = set(query.lower().split())
        scored = []
        
        for episode in self.episodic_memories:
            text = json.dumps(episode).lower()
            score = len(query_words.intersection(set(text.split())))
            if score > 0:
                scored.append((score, episode))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [e for _, e in scored[:n_results]]
    
    def add_best_practice(self, situation: str, solution: str, effectiveness: float):
        """Add a discovered best practice"""
        practice = {
            "situation": situation,
            "solution": solution,
            "effectiveness": effectiveness,
            "discovered_at": datetime.utcnow().isoformat(),
            "usage_count": 0,
            "verified": effectiveness > 0.8
        }
        self.best_practices.append(practice)
    
    def add_edge_case(self, scenario: str, issue: str, resolution: str):
        """Add an edge case with resolution"""
        edge_case = {
            "scenario": scenario,
            "issue": issue,
            "resolution": resolution,
            "encountered_at": datetime.utcnow().isoformat(),
            "frequency": 1
        }
        self.edge_cases.append(edge_case)
    
    def get_relevant_best_practices(self, situation: str) -> List[Dict]:
        """Get best practices relevant to current situation"""
        relevant = []
        situation_words = set(situation.lower().split())
        
        for practice in self.best_practices:
            practice_words = set(practice["situation"].lower().split())
            overlap = len(situation_words.intersection(practice_words))
            if overlap > 0:
                relevant.append((overlap, practice))
        
        relevant.sort(reverse=True, key=lambda x: x[0])
        return [p for _, p in relevant[:5]]


class MultiLayerMemoryManager:
    """
    Central manager for all three memory layers
    
    Coordinates between:
    - Short-term (in-process)
    - Medium-term (Redis/cache)
    - Long-term (Vector/Graph DB)
    
    Handles:
    - Memory promotion (short → medium → long)
    - Memory retrieval across layers
    - Expiration and cleanup
    - Persistence
    """
    
    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        vector_store: Optional[Any] = None,
        graph_store: Optional[Any] = None,
        redis_client: Optional[Any] = None
    ):
        self.user_id = user_id
        self.session_id = session_id or self._generate_session_id()
        
        # Initialize memory layers
        self.short_term = ShortTermMemory()
        self.medium_term = MediumTermMemory()
        self.long_term = LongTermMemory(
            vector_store=vector_store,
            graph_store=graph_store
        )
        
        # External storage
        self.redis = redis_client
        
        # Memory entry registry
        self._entries: Dict[str, MemoryEntry] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"MultiLayerMemory initialized for user {user_id}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_hash = hashlib.md5(
            f"{self.user_id}{timestamp}".encode()
        ).hexdigest()[:8]
        return f"sess_{timestamp}_{random_hash}"
    
    # ═════════════════════════════════════════════════════════════════
    # WRITE OPERATIONS
    # ═════════════════════════════════════════════════════════════════
    
    async def store(
        self,
        key: str,
        value: Any,
        layer: MemoryLayer,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None
    ):
        """Store value in specified memory layer"""
        async with self._lock:
            # Create memory entry
            entry = MemoryEntry(
                key=key,
                value=value,
                layer=layer,
                priority=priority,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None,
                tags=tags or [],
                source=source
            )
            
            self._entries[key] = entry
            
            # Store in appropriate layer
            if layer == MemoryLayer.SHORT_TERM:
                self._store_short_term(key, value)
            elif layer == MemoryLayer.MEDIUM_TERM:
                await self._store_medium_term(key, value, ttl_seconds)
            elif layer == MemoryLayer.LONG_TERM:
                await self._store_long_term(key, value, entry)
            
            logger.debug(f"Stored {key} in {layer.value}")
    
    def _store_short_term(self, key: str, value: Any):
        """Store in short-term memory (in-process)"""
        self.short_term.variables[key] = value
    
    async def _store_medium_term(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int]
    ):
        """Store in medium-term memory (Redis/cache)"""
        if self.redis:
            try:
                data = {
                    "value": value,
                    "stored_at": datetime.utcnow().isoformat()
                }
                await self.redis.setex(
                    f"medium_term:{self.user_id}:{key}",
                    ttl_seconds or 86400,  # Default 1 day
                    json.dumps(data)
                )
            except Exception as e:
                logger.error(f"Redis store failed: {e}")
                # Fallback to in-memory
                self.medium_term.session_state[key] = value
        else:
            # No Redis, store in memory with expiration tracking
            self.medium_term.session_state[key] = {
                "value": value,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds or 86400)
            }
    
    async def _store_long_term(self, key: str, value: Any, entry: MemoryEntry):
        """Store in long-term memory (Vector/Graph DB)"""
        # Store as episode
        episode = {
            "key": key,
            "value": value,
            "type": "knowledge",
            "description": str(value)[:200],
            "context": {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "priority": entry.priority.value,
                "tags": entry.tags
            },
            "timestamp": datetime.utcnow().isoformat(),
            "importance": self._priority_to_importance(entry.priority)
        }
        
        await self.long_term.store_episode(episode)
    
    # ═════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═════════════════════════════════════════════════════════════════
    
    async def retrieve(
        self,
        key: str,
        layer: Optional[MemoryLayer] = None
    ) -> Optional[Any]:
        """Retrieve value from memory"""
        async with self._lock:
            # Check all layers if not specified
            layers_to_check = [layer] if layer else [
                MemoryLayer.SHORT_TERM,
                MemoryLayer.MEDIUM_TERM,
                MemoryLayer.LONG_TERM
            ]
            
            for mem_layer in layers_to_check:
                value = await self._retrieve_from_layer(key, mem_layer)
                if value is not None:
                    # Update access metadata
                    if key in self._entries:
                        self._entries[key].touch()
                    return value
            
            return None
    
    async def _retrieve_from_layer(
        self,
        key: str,
        layer: MemoryLayer
    ) -> Optional[Any]:
        """Retrieve from specific layer"""
        if layer == MemoryLayer.SHORT_TERM:
            return self.short_term.variables.get(key)
        
        elif layer == MemoryLayer.MEDIUM_TERM:
            return await self._retrieve_medium_term(key)
        
        elif layer == MemoryLayer.LONG_TERM:
            return await self._retrieve_long_term(key)
        
        return None
    
    async def _retrieve_medium_term(self, key: str) -> Optional[Any]:
        """Retrieve from medium-term memory"""
        if self.redis:
            try:
                data = await self.redis.get(f"medium_term:{self.user_id}:{key}")
                if data:
                    parsed = json.loads(data)
                    return parsed.get("value")
            except Exception as e:
                logger.error(f"Redis retrieve failed: {e}")
        
        # Fallback to in-memory
        entry = self.medium_term.session_state.get(key)
        if isinstance(entry, dict) and "value" in entry:
            # Check expiration
            expires = entry.get("expires_at")
            if expires:
                try:
                    expires_at = datetime.fromisoformat(expires)
                except (TypeError, ValueError):
                    logger.warning(f"Invalid expires_at in medium-term memory: {expires}")
                    del self.medium_term.session_state[key]
                    return None
                if datetime.utcnow() > expires_at:
                    del self.medium_term.session_state[key]
                    return None
            return entry["value"]
        return entry
    
    async def _retrieve_long_term(self, key: str) -> Optional[Any]:
        """Retrieve from long-term memory"""
        # Search for episode with matching key
        for episode in self.long_term.episodic_memories:
            if episode.get("key") == key:
                return episode.get("value")
        return None
    
    async def retrieve_by_context(
        self,
        context: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Retrieve memories relevant to context"""
        results = []
        
        # Search long-term memory
        long_term_results = await self.long_term.retrieve_similar_episodes(context, n_results)
        results.extend([
            {"layer": "long_term", "data": r} for r in long_term_results
        ])
        
        # Get relevant rules from medium-term
        rules = self.medium_term.get_relevant_rules(context)
        results.extend([
            {"layer": "medium_term", "type": "rule", "data": r} for r in rules
        ])
        
        return results[:n_results]
    
    # ═════════════════════════════════════════════════════════════════
    # PROMOTION OPERATIONS
    # ═════════════════════════════════════════════════════════════════
    
    async def promote_to_medium(
        self,
        key: str,
        ttl_seconds: int = 86400
    ):
        """Promote short-term memory to medium-term"""
        value = self.short_term.variables.get(key)
        if value is not None:
            await self.store(
                key=key,
                value=value,
                layer=MemoryLayer.MEDIUM_TERM,
                ttl_seconds=ttl_seconds
            )
            logger.debug(f"Promoted {key} to medium-term")
    
    async def promote_to_long_term(
        self,
        key: str,
        importance: float = 0.7
    ):
        """Promote memory to long-term"""
        # Try to retrieve from any layer
        value = await self.retrieve(key)
        if value is not None:
            await self.store(
                key=key,
                value=value,
                layer=MemoryLayer.LONG_TERM,
                priority=MemoryPriority.HIGH if importance > 0.7 else MemoryPriority.MEDIUM
            )
            logger.debug(f"Promoted {key} to long-term")
    
    async def consolidate_short_term(self):
        """Consolidate important short-term memories to long-term"""
        # Promote key variables that should be remembered
        important_keys = [
            "user_goal", "successful_strategy", "discovered_pattern"
        ]
        
        for key in important_keys:
            if key in self.short_term.variables:
                await self.promote_to_long_term(key)
    
    # ═════════════════════════════════════════════════════════════════
    # CLEANUP OPERATIONS
    # ═════════════════════════════════════════════════════════════════
    
    async def cleanup_expired(self):
        """Remove expired entries from all layers"""
        async with self._lock:
            # Clean up entry registry
            expired_keys = [
                key for key, entry in self._entries.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._entries[key]
                # Also remove from short-term if present
                if key in self.short_term.variables:
                    del self.short_term.variables[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
    
    def clear_short_term(self):
        """Clear short-term memory (end of workflow)"""
        self.short_term.clear()
        logger.debug("Cleared short-term memory")
    
    def reset_session(self):
        """Reset entire session"""
        self.short_term.clear()
        self.medium_term = MediumTermMemory()
        self._entries.clear()
        logger.info(f"Reset session {self.session_id}")
    
    # ═════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═════════════════════════════════════════════════════════════════
    
    def _priority_to_importance(self, priority: MemoryPriority) -> float:
        """Convert priority to importance score"""
        mapping = {
            MemoryPriority.CRITICAL: 1.0,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.MEDIUM: 0.5,
            MemoryPriority.LOW: 0.3
        }
        return mapping.get(priority, 0.5)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        return {
            "short_term": {
                "variables": len(self.short_term.variables),
                "conversation_history": len(self.short_term.conversation_history),
                "tool_outputs": len(self.short_term.tool_outputs)
            },
            "medium_term": {
                "patterns": len(self.medium_term.recent_patterns),
                "rules": len(self.medium_term.contextual_rules),
                "preferences": len(self.medium_term.user_preferences)
            },
            "long_term": {
                "episodic_memories": len(self.long_term.episodic_memories),
                "best_practices": len(self.long_term.best_practices),
                "edge_cases": len(self.long_term.edge_cases)
            },
            "total_entries": len(self._entries)
        }
    
    async def dump_memory(self) -> Dict[str, Any]:
        """Dump all memory contents (for debugging)"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "short_term": {
                "current_goal": self.short_term.current_goal,
                "current_plan": self.short_term.current_plan,
                "variables": self.short_term.variables,
                "conversation_history": self.short_term.conversation_history,
                "tool_outputs": self.short_term.tool_outputs
            },
            "medium_term": {
                "user_preferences": self.medium_term.user_preferences,
                "recent_patterns": self.medium_term.recent_patterns[-10:],  # Last 10
                "contextual_rules": self.medium_term.contextual_rules,
                "successful_strategies": self.medium_term.successful_strategies[-5:]
            },
            "long_term": {
                "episodic_count": len(self.long_term.episodic_memories),
                "recent_episodes": self.long_term.episodic_memories[-5:],
                "best_practices_count": len(self.long_term.best_practices),
                "edge_cases_count": len(self.long_term.edge_cases)
            }
        }


# ═══════════════════════════════════════════════════════════════════
# AGENT MEMORY INTEGRATION
# ═══════════════════════════════════════════════════════════════════

class AgentMemoryContext:
    """
    Wrapper that integrates MultiLayerMemory with the Agent execution
    
    Provides convenient methods for agents to:
    - Store context during execution
    - Retrieve relevant memories
    - Promote learnings between layers
    - Consolidate at end of workflow
    """
    
    def __init__(self, memory_manager: MultiLayerMemoryManager):
        self.memory = memory_manager
        self._phase_memories: Dict[str, Any] = {}
    
    async def store_phase_result(
        self,
        phase: str,
        key: str,
        value: Any,
        promote_to_long_term: bool = False
    ):
        """Store result from a specific phase"""
        # Store in short-term (active execution)
        await self.memory.store(
            key=f"{phase}:{key}",
            value=value,
            layer=MemoryLayer.SHORT_TERM,
            priority=MemoryPriority.HIGH,
            source=f"agent_phase_{phase}"
        )
        
        # Optionally promote to long-term
        if promote_to_long_term:
            await self.memory.promote_to_long_term(f"{phase}:{key}")
    
    async def get_relevant_context(
        self,
        query: str,
        include_short_term: bool = True,
        include_medium_term: bool = True,
        include_long_term: bool = True
    ) -> Dict[str, List[Any]]:
        """Get context from all relevant memory layers"""
        context = {
            "short_term": [],
            "medium_term": [],
            "long_term": []
        }
        
        if include_short_term:
            # Get current goal, plan, etc.
            context["short_term"] = [
                {"type": "goal", "value": self.memory.short_term.current_goal},
                {"type": "plan", "value": self.memory.short_term.current_plan},
                {"type": "recent_tools", "value": list(self.memory.short_term.tool_outputs.keys())}
            ]
        
        if include_medium_term:
            # Get relevant rules and patterns
            rules = self.memory.medium_term.get_relevant_rules(query)
            context["medium_term"] = [
                {"type": "rule", "value": r} for r in rules
            ]
        
        if include_long_term:
            # Get similar episodes
            episodes = await self.memory.retrieve_by_context(query, 5)
            context["long_term"] = episodes
        
        return context
    
    async def learn(
        self,
        pattern_type: str,
        pattern_data: Dict,
        outcome: str,
        confidence: float = 0.5
    ):
        """Learn from execution outcome"""
        # Store in medium-term (user-specific learning)
        self.memory.medium_term.add_pattern(pattern_type, pattern_data, outcome)
        
        # If high confidence, promote to long-term
        if confidence > 0.8 and outcome == "success":
            episode = {
                "type": "learned_pattern",
                "pattern_type": pattern_type,
                "pattern": pattern_data,
                "outcome": outcome,
                "confidence": confidence,
                "user_id": self.memory.user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "importance": confidence
            }
            await self.memory.long_term.store_episode(episode)
    
    async def end_workflow(self):
        """End workflow - consolidate and cleanup"""
        # Consolidate important memories to long-term
        await self.memory.consolidate_short_term()
        
        # Clear short-term (end of workflow)
        self.memory.clear_short_term()
        
        # Cleanup expired entries
        await self.memory.cleanup_expired()
        
        logger.info(f"Workflow ended for session {self.memory.session_id}")


# Factory function for easy instantiation
async def create_memory_manager(
    user_id: str,
    vector_store: Optional[Any] = None,
    graph_store: Optional[Any] = None,
    redis_client: Optional[Any] = None
) -> MultiLayerMemoryManager:
    """Create a memory manager for a user session"""
    return MultiLayerMemoryManager(
        user_id=user_id,
        vector_store=vector_store,
        graph_store=graph_store,
        redis_client=redis_client
    )

"""
Graph Database Store for GraftAI
Handles knowledge graph and relationship mapping
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NodeType(Enum):
    """Types of nodes in the knowledge graph"""
    USER = "user"
    MEETING = "meeting"
    CONTACT = "contact"
    TEAM = "team"
    EVENT_TYPE = "event_type"
    TOPIC = "topic"
    TIME_SLOT = "time_slot"
    INTEGRATION = "integration"


class EdgeType(Enum):
    """Types of relationships between nodes"""
    ATTENDS = "attends"
    ORGANIZES = "organizes"
    KNOWS = "knows"
    MEMBER_OF = "member_of"
    SCHEDULED_AT = "scheduled_at"
    RELATED_TO = "related_to"
    PREFERS = "prefers"
    CONFLICTS_WITH = "conflicts_with"
    CONNECTED_TO = "connected_to"


@dataclass
class Node:
    """Node in the knowledge graph"""
    id: str
    type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Edge:
    """Edge (relationship) in the knowledge graph"""
    source: str  # Node ID
    target: str  # Node ID
    type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    
    def __hash__(self):
        return hash((self.source, self.target, self.type.value))


class GraphStore:
    """
    Graph database for knowledge representation and relationship mapping
    
    Responsibilities:
    - Store entities and relationships
    - Find connections between users, meetings, contacts
    - Query meeting networks
    - Analyze collaboration patterns
    - Support intelligent recommendations
    """
    
    def __init__(self):
        # In-memory graph storage
        # Production: Neo4j, Amazon Neptune, ArangoDB, etc.
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._node_edges: Dict[str, Set[str]] = {}  # node_id -> edge_ids
        
        logger.info("GraphStore initialized")
    
    async def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        properties: Optional[Dict[str, Any]] = None
    ) -> Node:
        """
        Add a node to the graph
        
        Args:
            node_id: Unique identifier
            node_type: Type of node
            properties: Node properties
            
        Returns:
            Created node
        """
        node = Node(
            id=node_id,
            type=node_type,
            properties=properties or {}
        )
        
        self._nodes[node_id] = node
        self._node_edges[node_id] = set()
        
        logger.debug(f"Added node: {node_id} ({node_type.value})")
        
        return node
    
    async def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ) -> Edge:
        """
        Add an edge (relationship) between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship
            properties: Edge properties
            weight: Relationship weight (0-1)
            
        Returns:
            Created edge
        """
        # Ensure nodes exist
        if source_id not in self._nodes:
            logger.warning(f"Source node {source_id} not found, creating placeholder")
            await self.add_node(source_id, NodeType.USER)
        
        if target_id not in self._nodes:
            logger.warning(f"Target node {target_id} not found, creating placeholder")
            await self.add_node(target_id, NodeType.USER)
        
        # Create edge
        edge_id = f"{source_id}-{edge_type.value}-{target_id}"
        
        edge = Edge(
            source=source_id,
            target=target_id,
            type=edge_type,
            properties=properties or {},
            weight=weight
        )
        
        self._edges[edge_id] = edge
        self._node_edges[source_id].add(edge_id)
        self._node_edges[target_id].add(edge_id)
        
        logger.debug(f"Added edge: {edge_id}")
        
        return edge
    
    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self._nodes.get(node_id)
    
    async def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "both"  # out, in, both
    ) -> List[Tuple[Node, Edge]]:
        """
        Get neighboring nodes connected to a given node
        
        Args:
            node_id: Center node
            edge_type: Filter by edge type
            direction: Direction of relationships
            
        Returns:
            List of (neighbor_node, edge) tuples
        """
        if node_id not in self._nodes:
            return []
        
        neighbors = []
        edge_ids = self._node_edges.get(node_id, set())
        
        for edge_id in edge_ids:
            edge = self._edges.get(edge_id)
            if not edge:
                continue
            
            # Filter by edge type
            if edge_type and edge.type != edge_type:
                continue
            
            # Determine direction
            if edge.source == node_id:
                if direction in ["out", "both"]:
                    neighbor = self._nodes.get(edge.target)
                    if neighbor:
                        neighbors.append((neighbor, edge))
            
            if edge.target == node_id:
                if direction in ["in", "both"]:
                    neighbor = self._nodes.get(edge.source)
                    if neighbor:
                        neighbors.append((neighbor, edge))
        
        return neighbors
    
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[Edge]]:
        """
        Find path between two nodes (shortest path)
        
        Args:
            source_id: Starting node
            target_id: Target node
            max_depth: Maximum path length
            
        Returns:
            List of edges forming the path, or None if no path
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        
        # BFS for shortest path
        from collections import deque
        
        visited = {source_id}
        queue = deque([(source_id, [])])
        
        while queue:
            current, path = queue.popleft()
            
            if current == target_id:
                return path
            
            if len(path) >= max_depth:
                continue
            
            # Get outgoing edges
            edge_ids = self._node_edges.get(current, set())
            for edge_id in edge_ids:
                edge = self._edges.get(edge_id)
                if edge and edge.source == current:
                    next_node = edge.target
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((next_node, path + [edge]))
        
        return None
    
    async def find_common_neighbors(
        self,
        node_id1: str,
        node_id2: str,
        edge_type: Optional[EdgeType] = None
    ) -> List[Node]:
        """
        Find nodes that are neighbors of both given nodes
        
        Useful for finding common contacts, shared meetings, etc.
        """
        neighbors1 = {n.id for n, _ in await self.get_neighbors(node_id1, edge_type)}
        neighbors2 = {n.id for n, _ in await self.get_neighbors(node_id2, edge_type)}
        
        common = neighbors1 & neighbors2
        
        return [self._nodes[nid] for nid in common if nid in self._nodes]
    
    async def query(
        self,
        node_type: Optional[NodeType] = None,
        edge_type: Optional[EdgeType] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Node]:
        """
        Query nodes with filters
        
        Args:
            node_type: Filter by node type
            edge_type: Filter by connected edge type
            properties: Filter by properties
            limit: Maximum results
            
        Returns:
            Matching nodes
        """
        results = []
        
        for node in self._nodes.values():
            # Filter by node type
            if node_type and node.type != node_type:
                continue
            
            # Filter by properties
            if properties:
                matches = all(
                    node.properties.get(k) == v
                    for k, v in properties.items()
                )
                if not matches:
                    continue
            
            # Filter by edge type (if node has this edge type)
            if edge_type:
                has_edge = False
                for edge_id in self._node_edges.get(node.id, set()):
                    edge = self._edges.get(edge_id)
                    if edge and edge.type == edge_type:
                        has_edge = True
                        break
                if not has_edge:
                    continue
            
            results.append(node)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_collaboration_network(
        self,
        user_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get collaboration network for a user
        
        Shows who they meet with, team connections, etc.
        
        Args:
            user_id: User to analyze
            depth: How many levels of connections
            
        Returns:
            Network structure with nodes and edges
        """
        visited = {user_id}
        current_level = {user_id}
        network_nodes = [self._nodes[user_id]]
        network_edges = []
        
        for _ in range(depth):
            next_level = set()
            
            for node_id in current_level:
                neighbors = await self.get_neighbors(node_id)
                
                for neighbor, edge in neighbors:
                    network_edges.append(edge)
                    
                    if neighbor.id not in visited:
                        visited.add(neighbor.id)
                        network_nodes.append(neighbor)
                        next_level.add(neighbor.id)
            
            current_level = next_level
            
            if not current_level:
                break
        
        return {
            "user_id": user_id,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "properties": n.properties
                }
                for n in network_nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.type.value,
                    "weight": e.weight
                }
                for e in network_edges
            ],
            "total_connections": len(visited) - 1
        }
    
    async def get_meeting_clusters(self) -> List[List[str]]:
        """
        Find clusters of people who frequently meet together
        
        Returns:
            List of clusters (each cluster is list of user IDs)
        """
        # Simple clustering based on meeting attendance
        from collections import defaultdict
        
        # Get all meetings
        meetings = await self.query(node_type=NodeType.MEETING)
        
        # Build attendance matrix
        attendance_groups = []
        for meeting in meetings:
            attendees = await self.get_neighbors(meeting.id, EdgeType.ATTENDS, "in")
            attendee_ids = [a.id for a, _ in attendees]
            if len(attendee_ids) > 1:
                attendance_groups.append(set(attendee_ids))
        
        # Find overlapping groups (cliques)
        clusters = []
        processed = set()
        
        for group in attendance_groups:
            # Check if this group overlaps with existing clusters
            merged = False
            for cluster in clusters:
                if cluster & group:  # Overlap found
                    cluster.update(group)
                    merged = True
                    break
            
            if not merged and frozenset(group) not in processed:
                clusters.append(group)
                processed.add(frozenset(group))
        
        return [list(c) for c in clusters]
    
    async def recommend_collaborators(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend people for a user to collaborate with
        
        Based on:
        - Mutual connections
        - Similar meeting patterns
        - Team proximity
        """
        recommendations = []
        
        # Get user's network
        network = await self.get_collaboration_network(user_id, depth=2)
        
        # Get current collaborators
        current_collaborators = await self.get_neighbors(user_id, EdgeType.ATTENDS)
        collaborator_ids = {n.id for n, _ in current_collaborators}
        
        # Find potential collaborators (2nd degree connections not yet collaborated with)
        for node_data in network["nodes"]:
            if node_data["id"] == user_id:
                continue
            if node_data["id"] in collaborator_ids:
                continue
            if node_data["type"] != "user":
                continue
            
            # Calculate score
            score = 0.0
            reasons = []
            
            # Check for mutual connections
            common = await self.find_common_neighbors(user_id, node_data["id"])
            if common:
                score += len(common) * 0.3
                reasons.append(f"{len(common)} mutual connections")
            
            # Check team membership
            user_teams = await self.get_neighbors(user_id, EdgeType.MEMBER_OF)
            their_teams = await self.get_neighbors(node_data["id"], EdgeType.MEMBER_OF)
            
            shared_teams = set(t.id for t, _ in user_teams) & set(t.id for t, _ in their_teams)
            if shared_teams:
                score += len(shared_teams) * 0.4
                reasons.append(f"Same team(s)")
            
            if score > 0:
                recommendations.append({
                    "user_id": node_data["id"],
                    "name": node_data["properties"].get("name", "Unknown"),
                    "score": min(score, 1.0),
                    "reasons": reasons
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:limit]
    
    async def build_user_knowledge_graph(self, user_id: str):
        """
        Build complete knowledge graph for a user
        
        Includes:
        - User node
        - Contacts
        - Meetings they've attended
        - Teams they're in
        - Topics of interest
        """
        # Add user node if not exists
        if user_id not in self._nodes:
            await self.add_node(user_id, NodeType.USER, {"created_from_db": True})
        
        # Get user data from database
        from backend.utils import db as db_utils
        # Query user's meetings, contacts, teams, etc.
        # Placeholder: Would query actual database
        
        logger.info(f"Built knowledge graph for user: {user_id}")
    
    async def analyze_scheduling_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user's scheduling patterns using graph
        
        Returns:
            Insights about meeting habits, collaborations, etc.
        """
        insights = {
            "user_id": user_id,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        # Get all meetings for user
        meetings = await self.get_neighbors(user_id, EdgeType.ATTENDS)
        
        if not meetings:
            insights["message"] = "No meeting data available"
            return insights
        
        # Calculate metrics
        total_meetings = len(meetings)
        insights["total_meetings"] = total_meetings
        
        # Most frequent collaborators
        collaborator_counts = {}
        for meeting, _ in meetings:
            attendees = await self.get_neighbors(meeting.id, EdgeType.ATTENDS, "in")
            for attendee, _ in attendees:
                if attendee.id != user_id:
                    collaborator_counts[attendee.id] = collaborator_counts.get(attendee.id, 0) + 1
        
        top_collaborators = sorted(
            collaborator_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        insights["top_collaborators"] = [
            {
                "user_id": uid,
                "meetings_together": count,
                "name": self._nodes.get(uid, Node("", NodeType.USER)).properties.get("name", "Unknown")
            }
            for uid, count in top_collaborators
        ]
        
        # Team participation
        teams = await self.get_neighbors(user_id, EdgeType.MEMBER_OF)
        insights["team_count"] = len(teams)
        insights["teams"] = [t.properties.get("name", "Unknown") for t, _ in teams]
        
        return insights


# Global instance
_graph_store: Optional[GraphStore] = None


async def get_graph_store() -> GraphStore:
    """Get or create the global graph store"""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store

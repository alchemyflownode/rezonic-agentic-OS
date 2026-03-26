from collections import deque
import json
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class AgentMemory:
    """
    Episodic and semantic memory for agents
    """
    def __init__(self, capacity=1000, short_term_capacity=100):
        self.short_term = deque(maxlen=short_term_capacity)
        self.long_term = {}
        self.semantic_memory = {}
        self.capacity = capacity
        self.episodic_memory = []
        self.importance_threshold = 0.5
        
    def remember(self, experience, importance=1.0, tags=None):
        """
        Store an experience in memory
        """
        memory_id = hashlib.md5(f"{experience}_{datetime.now().timestamp()}".encode()).hexdigest()
        
        memory = {
            'id': memory_id,
            'experience': experience,
            'importance': importance,
            'tags': tags or [],
            'timestamp': datetime.now().isoformat(),
            'recall_count': 0,
            'last_recall': None
        }
        
        self.short_term.append(memory)
        self.episodic_memory.append(memory)
        
        if importance > self.importance_threshold:
            self.long_term[memory_id] = memory
            logger.debug(f"Stored important memory: {memory_id}")
            
        return memory_id
        
    def recall(self, query, limit=5, include_semantic=True):
        """
        Recall relevant memories
        """
        results = []
        query_lower = query.lower()
        
        for mem in reversed(self.short_term):
            if self._matches_query(mem, query_lower):
                mem['recall_count'] += 1
                mem['last_recall'] = datetime.now().isoformat()
                results.append(mem)
                if len(results) >= limit:
                    break
                    
        if len(results) < limit:
            for mem in self.long_term.values():
                if mem not in results and self._matches_query(mem, query_lower):
                    mem['recall_count'] += 1
                    mem['last_recall'] = datetime.now().isoformat()
                    results.append(mem)
                    if len(results) >= limit:
                        break
                        
        if include_semantic and query in self.semantic_memory:
            results.append({
                'type': 'semantic',
                'content': self.semantic_memory[query],
                'importance': 0.9,
                'timestamp': 'semantic'
            })
            
        return sorted(results, key=lambda x: x.get('importance', 0), reverse=True)[:limit]
        
    def _matches_query(self, memory, query):
        """Check if memory matches query"""
        if query in str(memory.get('experience', '')).lower():
            return True
            
        for tag in memory.get('tags', []):
            if query in tag.lower():
                return True
                
        return False
        
    def consolidate(self):
        """
        Move important short-term memories to long-term
        """
        consolidated = 0
        for mem in list(self.short_term):
            recall_factor = min(mem['recall_count'] / 10, 1.0)
            current_importance = (mem['importance'] + recall_factor) / 2
            
            if current_importance > self.importance_threshold:
                if mem['id'] not in self.long_term:
                    self.long_term[mem['id']] = mem
                    consolidated += 1
                    
        logger.info(f"Consolidated {consolidated} memories to long-term")
        return consolidated
        
    def learn_semantic(self, concept, definition):
        """
        Store semantic knowledge
        """
        self.semantic_memory[concept] = {
            'definition': definition,
            'timestamp': datetime.now().isoformat()
        }
        
    def forget_old(self, days=30):
        """
        Forget memories older than specified days
        """
        cutoff = datetime.now() - timedelta(days=days)
        before_count = len(self.long_term)
        
        self.long_term = {
            k: v for k, v in self.long_term.items()
            if datetime.fromisoformat(v['timestamp']) > cutoff
        }
        
        forgotten = before_count - len(self.long_term)
        logger.info(f"Forgot {forgotten} old memories")
        return forgotten
        
    def get_stats(self):
        """
        Get memory statistics
        """
        return {
            'short_term_size': len(self.short_term),
            'long_term_size': len(self.long_term),
            'semantic_size': len(self.semantic_memory),
            'total_memories': len(self.episodic_memory),
            'consolidation_ratio': len(self.long_term) / max(len(self.episodic_memory), 1)
        }

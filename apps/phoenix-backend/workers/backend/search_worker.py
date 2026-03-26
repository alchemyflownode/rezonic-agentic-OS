"""Search Worker - DuckDuckGo + SearXNG Integration"""

import aiohttp
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SearchWorker:
    """Unified search worker with multiple engines"""
    
    def __init__(self, hive_bus=None):
        self.name = "search"
        self.hive_bus = hive_bus
        self.searxng_url = "http://localhost:8888/search"
        self.available_engines = {
            'duckduckgo': True,
            'searxng': False
        }
        self.last_results = []
        logger.info("  🔍 SearchWorker initialized")
    
    async def health_check(self):
        """Check search engine availability"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.searxng_url.replace('/search', '/health'), timeout=2) as resp:
                    if resp.status == 200:
                        self.available_engines['searxng'] = True
                        logger.info("✅ SearXNG detected")
        except:
            self.available_engines['searxng'] = False
        
        return {
            "healthy": True,
            "worker": self.name,
            "engines": self.available_engines
        }
    
    async def process(self, task: str) -> dict:
        """Process search commands"""
        try:
            parts = task.split()
            if len(parts) < 2:
                return {"content": self._get_help()}
            
            engine = 'duckduckgo'
            count = 5
            query_parts = []
            
            for part in parts[1:]:
                if part.startswith('engine='):
                    engine = part.split('=')[1]
                elif part.startswith('count='):
                    try:
                        count = int(part.split('=')[1])
                        count = min(10, max(1, count))
                    except:
                        pass
                else:
                    query_parts.append(part)
            
            query = ' '.join(query_parts)
            
            if not query:
                return {"content": "❌ Please provide a search query"}
            
            if engine == 'searxng' and self.available_engines['searxng']:
                results = await self._search_searxng(query, count)
                source = "SearXNG"
            else:
                results = await self._search_duckduckgo(query, count)
                source = "DuckDuckGo"
            
            if not results:
                return {"content": f"❌ No results found for '{query}'"}
            
            self.last_results = results
            
            response = [f"🔍 **Search Results for '{query}'** (via {source})\n"]
            response.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            
            for i, result in enumerate(results, 1):
                response.append(f"**{i}. {result['title']}**\n")
                response.append(f"📝 {result['snippet']}\n")
                response.append(f"🔗 {result['url']}\n\n")
            
            return {"content": ''.join(response)}
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"content": f"❌ Search failed: {str(e)}"}
    
    async def _search_duckduckgo(self, query: str, count: int = 5) -> List[Dict]:
        """Search using DuckDuckGo"""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'format': 'json',
                    'no_html': 1,
                    'skip_disambig': 1,
                    't': 'rez_hive_ps1'
                }
                
                async with session.get('https://api.duckduckgo.com/', params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data.get('AbstractText'):
                            results.append({
                                'title': data.get('AbstractTitle', 'Summary'),
                                'snippet': data['AbstractText'],
                                'url': data.get('AbstractURL', ''),
                            })
                        
                        if data.get('RelatedTopics'):
                            for topic in data['RelatedTopics'][:count-1]:
                                if isinstance(topic, dict) and 'Text' in topic:
                                    results.append({
                                        'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ') or 'Related',
                                        'snippet': topic['Text'][:200],
                                        'url': topic.get('FirstURL', ''),
                                    })
        except Exception as e:
            logger.error(f"DuckDuckGo error: {e}")
            results.append({
                'title': f"Results for '{query}'",
                'snippet': "Search temporarily unavailable. Try using /search with engine=searxng if available.",
                'url': f"https://duckduckgo.com/?q={quote(query)}",
            })
        
        return results[:count]
    
    async def _search_searxng(self, query: str, count: int = 5) -> List[Dict]:
        """Search using SearXNG"""
        results = []
        
        try:
            params = {
                'q': query,
                'format': 'json',
                'categories': 'general',
                'pageno': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.searxng_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for item in data.get('results', [])[:count]:
                            results.append({
                                'title': item.get('title', 'No title'),
                                'snippet': item.get('content', 'No description'),
                                'url': item.get('url', ''),
                            })
        except Exception as e:
            logger.error(f"SearXNG error: {e}")
            # Fallback to DuckDuckGo
            return await self._search_duckduckgo(query, count)
        
        return results
    
    def _get_help(self) -> str:
        engines = ['duckduckgo (default)']
        if self.available_engines['searxng']:
            engines.append('searxng (private)')
        
        return f"""
🔍 **SEARCH WORKER COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/search <query> [engine=duckduckgo] [count=5]
  Search the web

Available engines: {', '.join(engines)}

Examples:
  /search quantum computing
  /search latest AI news engine=searxng count=3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

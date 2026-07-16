"""
Analytics and metrics tracking system for agent usage and performance.
Uses Redis for real-time metrics storage.
"""
import time
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis
from config.settings import settings


class AnalyticsTracker:
    """Track agent usage, performance metrics, and system health."""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB, 
            decode_responses=True
        )
    
    def track_agent_request(self, agent_type: str, success: bool = True, 
                          latency_ms: float = 0, cache_hit: bool = False):
        """Track a single agent request."""
        timestamp = int(time.time())
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Increment request counters
        self.redis.hincrby(f"analytics:requests:{date_key}", agent_type, 1)
        self.redis.hincrby(f"analytics:requests:{date_key}", "total", 1)
        
        # Track success/failure
        if success:
            self.redis.hincrby(f"analytics:success:{date_key}", agent_type, 1)
        else:
            self.redis.hincrby(f"analytics:failure:{date_key}", agent_type, 1)
        
        # Track cache hits
        if cache_hit:
            self.redis.hincrby(f"analytics:cache:{date_key}", "hits", 1)
        else:
            self.redis.hincrby(f"analytics:cache:{date_key}", "misses", 1)
        
        # Track latency
        latency_key = f"analytics:latency:{date_key}:{agent_type}"
        self.redis.lpush(latency_key, latency_ms)
        self.redis.ltrim(latency_key, 0, 999)  # Keep last 1000 samples
        
        # Set expiry for all keys (30 days)
        for key_pattern in ["analytics:requests", "analytics:success", 
                           "analytics:failure", "analytics:cache", "analytics:latency"]:
            self.redis.expire(f"{key_pattern}:{date_key}", 30 * 24 * 3600)
    
    def track_escalation(self, question: str, customer_email: Optional[str] = None):
        """Track escalated support questions for knowledge base gaps."""
        timestamp = int(time.time())
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        
        escalation_data = {
            "question": question,
            "customer_email": customer_email,
            "timestamp": timestamp
        }
        
        self.redis.lpush(f"analytics:escalations:{date_key}", json.dumps(escalation_data))
        self.redis.ltrim(f"analytics:escalations:{date_key}", 0, 999)  # Keep last 1000
        self.redis.expire(f"analytics:escalations:{date_key}", 30 * 24 * 3600)
    
    def track_popular_question(self, question: str):
        """Track frequently asked questions."""
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        self.redis.hincrby(f"analytics:popular_questions:{date_key}", question, 1)
        self.redis.expire(f"analytics:popular_questions:{date_key}", 30 * 24 * 3600)
    
    def get_daily_metrics(self, date: Optional[str] = None) -> Dict:
        """Get metrics for a specific date."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        requests = self.redis.hgetall(f"analytics:requests:{date}") or {}
        successes = self.redis.hgetall(f"analytics:success:{date}") or {}
        failures = self.redis.hgetall(f"analytics:failure:{date}") or {}
        cache_stats = self.redis.hgetall(f"analytics:cache:{date}") or {}
        
        # Calculate agent-specific metrics
        agent_metrics = {}
        for agent_type in ["support", "content", "analyst"]:
            if agent_type in requests:
                agent_metrics[agent_type] = {
                    "requests": int(requests.get(agent_type, 0)),
                    "successes": int(successes.get(agent_type, 0)),
                    "failures": int(failures.get(agent_type, 0)),
                    "success_rate": self._calculate_rate(
                        int(successes.get(agent_type, 0)),
                        int(requests.get(agent_type, 0))
                    )
                }
        
        # Cache metrics
        cache_hits = int(cache_stats.get("hits", 0))
        cache_misses = int(cache_stats.get("misses", 0))
        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        return {
            "date": date,
            "total_requests": int(requests.get("total", 0)),
            "agent_metrics": agent_metrics,
            "cache": {
                "hits": cache_hits,
                "misses": cache_misses,
                "hit_rate": cache_hit_rate
            }
        }
    
    def get_latency_stats(self, agent_type: str, date: Optional[str] = None) -> Dict:
        """Get latency statistics for an agent."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        latency_key = f"analytics:latency:{date}:{agent_type}"
        latencies = self.redis.lrange(latency_key, 0, -1)
        
        if not latencies:
            return {"count": 0, "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0}
        
        latencies = [float(l) for l in latencies]
        latencies.sort()
        
        count = len(latencies)
        avg = sum(latencies) / count
        p50 = latencies[int(count * 0.5)]
        p95 = latencies[int(count * 0.95)]
        p99 = latencies[int(count * 0.99)]
        
        return {
            "count": count,
            "avg_ms": round(avg, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2)
        }
    
    def get_escalations(self, date: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get recent escalated questions."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        escalation_data = self.redis.lrange(f"analytics:escalations:{date}", 0, limit - 1)
        return [json.loads(e) for e in escalation_data]
    
    def get_popular_questions(self, date: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get most frequently asked questions."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        questions = self.redis.hgetall(f"analytics:popular_questions:{date}") or {}
        sorted_questions = sorted(questions.items(), key=lambda x: int(x[1]), reverse=True)
        
        return [
            {"question": q, "count": int(c)} 
            for q, c in sorted_questions[:limit]
        ]
    
    def get_trends(self, days: int = 7) -> Dict:
        """Get usage trends over multiple days."""
        trends = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = self.get_daily_metrics(date)
            trends.append(metrics)
        
        return {"trends": trends}
    
    def _calculate_rate(self, numerator: int, denominator: int) -> float:
        """Calculate percentage rate safely."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)


# Global instance
analytics = AnalyticsTracker()

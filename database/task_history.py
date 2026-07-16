"""
Task history persistence using PostgreSQL.
Stores long-term task history that persists beyond Redis result expiration.
"""
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict
from config.settings import settings


class TaskHistoryStore:
    """Manage persistent task history in PostgreSQL."""
    
    def __init__(self):
        self.pool = None
    
    async def _get_pool(self):
        """Get or create connection pool."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=2,
                max_size=10
            )
        return self.pool
    
    async def initialize_schema(self):
        """Create task history table if it doesn't exist."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) UNIQUE NOT NULL,
                    task_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    input_data JSONB,
                    result_data JSONB,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    completed_at TIMESTAMP WITH TIME ZONE
                );
                
                CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);
                CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_history(status);
                CREATE INDEX IF NOT EXISTS idx_task_history_type ON task_history(task_type);
                CREATE INDEX IF NOT EXISTS idx_task_history_created_at ON task_history(created_at);
                
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_task_history_updated_at ON task_history;
                CREATE TRIGGER update_task_history_updated_at
                    BEFORE UPDATE ON task_history
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)
    
    async def create_task(self, task_id: str, task_type: str, 
                         input_data: Optional[Dict] = None) -> None:
        """Create a new task record."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO task_history (task_id, task_type, status, input_data)
                VALUES ($1, $2, 'queued', $3)
                ON CONFLICT (task_id) DO NOTHING
                """,
                task_id, task_type, input_data
            )
    
    async def update_task_status(self, task_id: str, status: str, 
                                 error_message: Optional[str] = None) -> None:
        """Update task status."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if status == "completed":
                await conn.execute(
                    """
                    UPDATE task_history 
                    SET status = $1, completed_at = NOW(), error_message = $2
                    WHERE task_id = $3
                    """,
                    status, error_message, task_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE task_history 
                    SET status = $1, error_message = $2
                    WHERE task_id = $3
                    """,
                    status, error_message, task_id
                )
    
    async def update_task_result(self, task_id: str, result_data: Dict) -> None:
        """Update task with result data."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE task_history 
                SET result_data = $1, status = 'completed', completed_at = NOW()
                WHERE task_id = $2
                """,
                result_data, task_id
            )
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM task_history WHERE task_id = $1",
                task_id
            )
            if row:
                return dict(row)
            return None
    
    async def get_tasks_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """Get tasks by status."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM task_history 
                WHERE status = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                status, limit
            )
            return [dict(row) for row in rows]
    
    async def get_tasks_by_type(self, task_type: str, limit: int = 100) -> List[Dict]:
        """Get tasks by type."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM task_history 
                WHERE task_type = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                task_type, limit
            )
            return [dict(row) for row in rows]
    
    async def get_recent_tasks(self, limit: int = 50) -> List[Dict]:
        """Get recent tasks across all types."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM task_history 
                ORDER BY created_at DESC 
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]
    
    async def get_task_statistics(self) -> Dict:
        """Get task statistics."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                    COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued_tasks,
                    COUNT(CASE WHEN status = 'started' THEN 1 END) as started_tasks
                FROM task_history
            """)
            
            # Get stats by task type
            type_stats = await conn.fetch("""
                SELECT 
                    task_type,
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                FROM task_history
                GROUP BY task_type
            """)
            
            return {
                "overall": dict(stats),
                "by_type": [dict(row) for row in type_stats]
            }


# Global instance
task_history = TaskHistoryStore()

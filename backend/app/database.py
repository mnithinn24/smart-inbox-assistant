"""
Smart Inbox Assistant — MySQL Database Connection Pool
Uses aiomysql for async database operations.
"""
import aiomysql
import pymysql
import json
import logging
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
pool: Optional[aiomysql.Pool] = None


async def init_db():
    """Initialize the MySQL connection pool."""
    global pool
    pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        charset="utf8mb4",
        autocommit=True,
        minsize=2,
        maxsize=10,
    )
    logger.info("MySQL connection pool initialized")


async def close_db():
    """Close the MySQL connection pool."""
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("MySQL connection pool closed")


async def execute_query(query: str, params: tuple = None) -> int:
    """Execute an INSERT/UPDATE/DELETE query. Returns last insert ID."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            return cur.lastrowid


async def fetch_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """Fetch a single row as a dictionary."""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()


async def fetch_all(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Fetch all rows as a list of dictionaries."""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()


async def execute_many(query: str, params_list: list) -> int:
    """Execute a query with multiple parameter sets."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(query, params_list)
            return cur.rowcount

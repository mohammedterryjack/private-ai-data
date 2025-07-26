"""
Database operations for KnowledgeBase service.

Provides functions for initializing the database, managing tables,
and performing CRUD operations on images, captions, markdown, keywords, sources, and vectors.
"""

import os
import json
from datetime import datetime
import uuid
from sqlalchemy import text, Column, String, DateTime, Text, ARRAY, Float
from sqlalchemy.ext.declarative import declarative_base
import logging
from typing import Any
from .client import engine, SessionLocal, get_db

# SQLAlchemy setup
Base = declarative_base()

# Define base table model
class DynamicTable(Base):
    """Legacy dynamic table model for backward compatibility"""
    __tablename__ = "dynamic_tables"
    
    id = Column(String, primary_key=True)
    table_name = Column(String, nullable=False)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _execute_safe_query(db, query: str, params: dict | None = None):
    """Safely execute a database query with error handling"""
    try:
        if params:
            result = db.execute(text(query), params)
        else:
            result = db.execute(text(query))
        return result
    except Exception as e:
        logging.error(f"Query execution error: {e}")
        db.rollback()
        raise

async def init_database() -> None:
    """Initialize database with default tables"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Enable pgvector extension
        _execute_safe_query(db, "CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create images table
        _execute_safe_query(db, """
            CREATE TABLE IF NOT EXISTS images (
                uuid UUID PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create captions table
        _execute_safe_query(db, """
            CREATE TABLE IF NOT EXISTS captions (
                uuid UUID PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create documents table (using uuid for consistency)
        _execute_safe_query(db, """
            CREATE TABLE IF NOT EXISTS documents (
                uuid UUID PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create raw_file_paths table for tracking PDF file locations
        _execute_safe_query(db, """
            CREATE TABLE IF NOT EXISTS raw_file_paths (
                uuid UUID PRIMARY KEY,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_size BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create keywords table
        _execute_safe_query(db, """
            CREATE TABLE IF NOT EXISTS keywords (
                keyword VARCHAR(255) PRIMARY KEY,
                uuids UUID[] NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if vectors table exists with old schema and migrate it
        result = _execute_safe_query(db, """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vectors' AND column_name = 'content'
        """)
        
        if result.fetchone():
            # Old schema exists, migrate to new schema
            print("Migrating vectors table to pgvector schema...")
            
            # Drop the old vectors table (this will lose existing data)
            _execute_safe_query(db, "DROP TABLE IF EXISTS vectors")
            
            # Create new vectors table with pgvector
            _execute_safe_query(db, """
                CREATE TABLE vectors (
                    uuid UUID PRIMARY KEY,
                    embedding vector(384), -- 384 dimensions for all-minilm model
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for vector similarity search
            _execute_safe_query(db, """
                CREATE INDEX vectors_embedding_idx 
                ON vectors 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            print("Vectors table migrated successfully to pgvector schema")
        else:
            # Create vectors table with pgvector (new installation)
            _execute_safe_query(db, """
                CREATE TABLE IF NOT EXISTS vectors (
                    uuid UUID PRIMARY KEY,
                    embedding vector(384), -- 384 dimensions for all-minilm model
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for vector similarity search
            _execute_safe_query(db, """
                CREATE INDEX IF NOT EXISTS vectors_embedding_idx 
                ON vectors 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
        
        db.commit()
        print("Database initialized successfully with pgvector support")
        
    except Exception as e:
        db.rollback()
        print(f"Database initialization error: {str(e)}")
        raise
    finally:
        db.close()

async def get_health_status() -> dict[str, Any]:
    """Get health status with database information"""
    try:
        db = SessionLocal()
        
        # Get table information
        result = _execute_safe_query(db, """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in result.fetchall()]
        
        # Get table counts
        table_counts = {}
        for table_name in tables:
            try:
                result = _execute_safe_query(db, f"SELECT COUNT(*) FROM {table_name}")
                count = result.fetchone()[0]
                table_counts[table_name] = count
            except Exception as e:
                table_counts[table_name] = f"Error: {str(e)}"
        
        # Get document count
        result = _execute_safe_query(db, "SELECT COUNT(*) FROM documents")
        doc_count = result.fetchone()[0]
        
        # Get database size
        result = _execute_safe_query(db, """
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        db_size = result.fetchone()[0]
        
        db.close()
        
        return {
            "status": "healthy",
            "service": "knowledgebase",
            "tables": tables,
            "table_counts": table_counts,
            "document_count": doc_count,
            "database_size": db_size,
            "database_url": engine.url.render_as_string(hide_password=True)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "knowledgebase",
            "error": str(e)
        }

async def query_table(table_name: str, query: str) -> dict[str, Any]:
    """Query a table with custom SQL"""
    db = SessionLocal()
    try:
        # Execute query
        result = _execute_safe_query(db, query)
        
        # Get results
        rows = result.fetchall()
        columns = result.keys()
        
        results = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Handle PostgreSQL arrays and other special types
                if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    # Convert iterables (like arrays) to lists
                    try:
                        value = list(value)
                    except:
                        pass
                # Only try to parse JSON for string values that look like JSON
                elif isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                row_dict[column] = value
            results.append(row_dict)
        
        return {
            "results": results,
            "count": len(results),
            "table": table_name
        }
        
    except Exception as e:
        raise Exception(f"Query error: {str(e)}")
    finally:
        db.close()

async def add_image(content: str) -> dict[str, Any]:
    """Add an image entry to the images table"""
    db = SessionLocal()
    try:
        result = _execute_safe_query(db, """
            INSERT INTO images (content, created_at, updated_at)
            VALUES (:content, :created_at, :updated_at)
            RETURNING id
        """, {
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        image_id = result.fetchone()[0]
        db.commit()
        
        return {
            "message": "Image added successfully",
            "id": str(image_id),
            "table": "images"
        }
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close()

async def add_caption(content: str) -> dict[str, Any]:
    """Add a caption entry to the captions table"""
    db = SessionLocal()
    try:
        result = _execute_safe_query(db, """
            INSERT INTO captions (content, created_at, updated_at)
            VALUES (:content, :created_at, :updated_at)
            RETURNING id
        """, {
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        caption_id = result.fetchone()[0]
        db.commit()
        
        return {
            "message": "Caption added successfully",
            "id": str(caption_id),
            "table": "captions"
        }
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close()

async def add_keyword(keyword: str, sources: list[str]) -> dict[str, Any]:
    """Add or update a keyword entry in the keywords table"""
    db = SessionLocal()
    try:
        # Convert string UUIDs to UUID objects for PostgreSQL
        source_uuids = [uuid.UUID(source) for source in sources]
        
        result = _execute_safe_query(db, """
            INSERT INTO keywords (keyword, uuids, created_at, updated_at)
            VALUES (:keyword, :uuids, :created_at, :updated_at)
            ON CONFLICT (keyword) 
            DO UPDATE SET 
                uuids = keywords.uuids || :uuids,
                updated_at = :updated_at
            RETURNING keyword
        """, {
            "keyword": keyword,
            "uuids": source_uuids,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        keyword_name = result.fetchone()[0]
        db.commit()
        
        return {
            "message": "Keyword added/updated successfully",
            "keyword": keyword_name,
            "table": "keywords"
        }
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close()

async def find_similar_vectors(query_vector: list[float], limit: int = 10, similarity_threshold: float = 0.7) -> list[dict]:
    """Find similar vectors using pgvector cosine similarity"""
    db = SessionLocal()
    try:
        # Convert list to vector format for pgvector
        vector_str = f"[{','.join(map(str, query_vector))}]"
        
        result = _execute_safe_query(db, """
            SELECT 
                uuid,
                embedding,
                1 - (embedding <=> %s::vector) as similarity
            FROM vectors 
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (vector_str, vector_str, similarity_threshold, vector_str, limit))
        
        rows = result.fetchall()
        results = []
        for row in rows:
            results.append({
                "uuid": str(row[0]),
                "embedding": list(row[1]) if row[1] else [],
                "similarity": float(row[2])
            })
        
        return results
        
    except Exception as e:
        raise Exception(f"Vector similarity search error: {str(e)}")
    finally:
        db.close()

async def add_vector(uuid_str: str, embedding: list[float]) -> dict[str, Any]:
    """Add a vector entry to the vectors table using pgvector"""
    db = SessionLocal()
    try:
        result = _execute_safe_query(db, """
            INSERT INTO vectors (uuid, embedding)
            VALUES (%s, %s::vector)
            ON CONFLICT (uuid) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
            RETURNING uuid
        """, (uuid_str, embedding))
        
        vector_uuid = result.fetchone()[0]
        db.commit()
        
        return {
            "message": "Vector added successfully",
            "uuid": str(vector_uuid),
            "table": "vectors"
        }
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close() 
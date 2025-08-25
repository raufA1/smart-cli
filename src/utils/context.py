"""Context management and conversation persistence for Smart CLI."""

import sqlite3
import json
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from .config import ConfigManager
from .ai_client import ChatMessage


class ContextScope(Enum):
    """Context scope levels."""
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    TASK = "task"


@dataclass
class ConversationContext:
    """Conversation context data."""
    context_id: str
    scope: ContextScope
    title: str
    messages: List[ChatMessage]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    project_path: Optional[str] = None
    session_id: Optional[str] = None
    parent_context_id: Optional[str] = None


@dataclass
class ContextSummary:
    """Summary of conversation context for memory optimization."""
    context_id: str
    summary_text: str
    key_points: List[str]
    token_count: int
    created_at: datetime


class ContextManager:
    """Manages conversation context and persistence."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.logger = structlog.get_logger()
        
        # Database setup
        self.db_path = Path.home() / ".smart-cli" / "context.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # Context limits
        self.max_context_length = self.config.get_config('max_context_length', 8000)
        self.max_messages_per_context = self.config.get_config('max_messages_per_context', 50)
        self.context_ttl_days = self.config.get_config('context_ttl_days', 30)
    
    def _init_database(self):
        """Initialize SQLite database for context storage."""
        conn = sqlite3.connect(str(self.db_path))
        
        # Contexts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contexts (
                context_id TEXT PRIMARY KEY,
                scope TEXT NOT NULL,
                title TEXT NOT NULL,
                messages BLOB,
                metadata TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                project_path TEXT,
                session_id TEXT,
                parent_context_id TEXT
            )
        ''')
        
        # Context summaries table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS context_summaries (
                context_id TEXT PRIMARY KEY,
                summary_text TEXT NOT NULL,
                key_points TEXT,
                token_count INTEGER,
                created_at TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts (context_id)
            )
        ''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_scope ON contexts(scope)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_session ON contexts(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_project ON contexts(project_path)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_updated ON contexts(updated_at)')
        
        conn.commit()
        conn.close()
    
    def create_context(
        self,
        scope: ContextScope,
        title: str,
        project_path: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation context."""
        
        context_id = f"{scope.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(title) % 10000:04d}"
        
        context = ConversationContext(
            context_id=context_id,
            scope=scope,
            title=title,
            messages=[],
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_path=project_path,
            session_id=session_id,
            parent_context_id=parent_context_id
        )
        
        self._save_context(context)
        
        self.logger.info("Created new context", context_id=context_id, scope=scope.value, title=title)
        
        return context_id
    
    def add_message(self, context_id: str, message: ChatMessage) -> bool:
        """Add a message to the conversation context."""
        context = self.get_context(context_id)
        
        if not context:
            self.logger.warning("Context not found", context_id=context_id)
            return False
        
        # Add message
        context.messages.append(message)
        context.updated_at = datetime.now()
        
        # Check if context needs optimization
        if len(context.messages) > self.max_messages_per_context:
            self._optimize_context(context)
        
        # Save updated context
        self._save_context(context)
        
        self.logger.debug("Added message to context", context_id=context_id, role=message.role)
        
        return True
    
    def get_context(self, context_id: str) -> Optional[ConversationContext]:
        """Get conversation context by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM contexts WHERE context_id = ?
        ''', (context_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_context(row)
    
    def get_contexts(
        self,
        scope: Optional[ContextScope] = None,
        project_path: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationContext]:
        """Get contexts based on filters."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT * FROM contexts WHERE 1=1"
        params = []
        
        if scope:
            query += " AND scope = ?"
            params.append(scope.value)
        
        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_context(row) for row in rows]
    
    def get_context_messages(
        self,
        context_id: str,
        include_summary: bool = True,
        max_tokens: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get optimized context messages for AI consumption."""
        context = self.get_context(context_id)
        
        if not context:
            return []
        
        messages = context.messages.copy()
        
        # Include summary if available and requested
        if include_summary:
            summary = self._get_context_summary(context_id)
            if summary:
                summary_message = ChatMessage(
                    role="system",
                    content=f"Previous conversation summary: {summary.summary_text}\n\nKey points: {', '.join(summary.key_points)}"
                )
                messages.insert(0, summary_message)
        
        # Optimize for token limit
        if max_tokens:
            messages = self._optimize_messages_for_tokens(messages, max_tokens)
        
        return messages
    
    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """Update context metadata."""
        context = self.get_context(context_id)
        
        if not context:
            return False
        
        context.metadata.update(metadata)
        context.updated_at = datetime.now()
        
        self._save_context(context)
        return True
    
    def delete_context(self, context_id: str) -> bool:
        """Delete a conversation context."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Delete summary first
        cursor.execute('DELETE FROM context_summaries WHERE context_id = ?', (context_id,))
        
        # Delete context
        cursor.execute('DELETE FROM contexts WHERE context_id = ?', (context_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            self.logger.info("Deleted context", context_id=context_id)
        
        return deleted
    
    def cleanup_expired_contexts(self) -> int:
        """Clean up expired contexts."""
        cutoff_date = datetime.now() - timedelta(days=self.context_ttl_days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get expired context IDs
        cursor.execute('''
            SELECT context_id FROM contexts WHERE updated_at < ?
        ''', (cutoff_date,))
        
        expired_context_ids = [row[0] for row in cursor.fetchall()]
        
        # Delete summaries
        cursor.execute('DELETE FROM context_summaries WHERE context_id IN (SELECT context_id FROM contexts WHERE updated_at < ?)', (cutoff_date,))
        
        # Delete contexts
        cursor.execute('DELETE FROM contexts WHERE updated_at < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            self.logger.info("Cleaned up expired contexts", count=deleted_count)
        
        return deleted_count
    
    def _save_context(self, context: ConversationContext):
        """Save context to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO contexts 
            (context_id, scope, title, messages, metadata, created_at, updated_at, project_path, session_id, parent_context_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            context.context_id,
            context.scope.value,
            context.title,
            pickle.dumps(context.messages),
            json.dumps(context.metadata),
            context.created_at,
            context.updated_at,
            context.project_path,
            context.session_id,
            context.parent_context_id
        ))
        
        conn.commit()
        conn.close()
    
    def _row_to_context(self, row) -> ConversationContext:
        """Convert database row to ConversationContext."""
        return ConversationContext(
            context_id=row[0],
            scope=ContextScope(row[1]),
            title=row[2],
            messages=pickle.loads(row[3]) if row[3] else [],
            metadata=json.loads(row[4]) if row[4] else {},
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            updated_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
            project_path=row[7],
            session_id=row[8],
            parent_context_id=row[9]
        )
    
    def _optimize_context(self, context: ConversationContext):
        """Optimize context by summarizing old messages."""
        if len(context.messages) <= self.max_messages_per_context:
            return
        
        # Keep recent messages, summarize older ones
        recent_messages = context.messages[-20:]  # Keep last 20 messages
        old_messages = context.messages[:-20]
        
        if old_messages:
            # Create summary (placeholder - would use AI in real implementation)
            summary_text = f"Previous conversation with {len(old_messages)} messages about {context.title}"
            key_points = ["Code generation", "Problem solving", "Best practices"]
            
            summary = ContextSummary(
                context_id=context.context_id,
                summary_text=summary_text,
                key_points=key_points,
                token_count=len(summary_text.split()) * 1.3,  # Rough estimate
                created_at=datetime.now()
            )
            
            self._save_context_summary(summary)
            
            # Update context with only recent messages
            context.messages = recent_messages
            
            self.logger.info("Optimized context", context_id=context.context_id, old_messages=len(old_messages))
    
    def _save_context_summary(self, summary: ContextSummary):
        """Save context summary to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO context_summaries 
            (context_id, summary_text, key_points, token_count, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            summary.context_id,
            summary.summary_text,
            json.dumps(summary.key_points),
            summary.token_count,
            summary.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def _get_context_summary(self, context_id: str) -> Optional[ContextSummary]:
        """Get context summary by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM context_summaries WHERE context_id = ?
        ''', (context_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ContextSummary(
            context_id=row[0],
            summary_text=row[1],
            key_points=json.loads(row[2]) if row[2] else [],
            token_count=row[3],
            created_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4]
        )
    
    def _optimize_messages_for_tokens(self, messages: List[ChatMessage], max_tokens: int) -> List[ChatMessage]:
        """Optimize message list to fit within token limit."""
        # Simple implementation - keep most recent messages
        # In a real implementation, this would use tokenization
        
        total_length = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_length * 0.75  # Rough estimate
        
        if estimated_tokens <= max_tokens:
            return messages
        
        # Keep system message if present
        optimized_messages = []
        if messages and messages[0].role == "system":
            optimized_messages.append(messages[0])
            remaining_messages = messages[1:]
        else:
            remaining_messages = messages
        
        # Add messages from the end until we approach the limit
        current_tokens = len(optimized_messages[0].content) * 0.75 if optimized_messages else 0
        
        for message in reversed(remaining_messages):
            message_tokens = len(message.content) * 0.75
            
            if current_tokens + message_tokens <= max_tokens:
                optimized_messages.insert(-1 if optimized_messages and optimized_messages[0].role == "system" else 0, message)
                current_tokens += message_tokens
            else:
                break
        
        self.logger.debug("Optimized messages for token limit", 
                         original_count=len(messages), 
                         optimized_count=len(optimized_messages))
        
        return optimized_messages
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute('SELECT COUNT(*) FROM contexts')
        total_contexts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM context_summaries')
        total_summaries = cursor.fetchone()[0]
        
        # Context by scope
        cursor.execute('SELECT scope, COUNT(*) FROM contexts GROUP BY scope')
        contexts_by_scope = dict(cursor.fetchall())
        
        # Recent activity
        cutoff_date = datetime.now() - timedelta(days=7)
        cursor.execute('SELECT COUNT(*) FROM contexts WHERE updated_at > ?', (cutoff_date,))
        recent_contexts = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_contexts': total_contexts,
            'total_summaries': total_summaries,
            'contexts_by_scope': contexts_by_scope,
            'recent_contexts_7d': recent_contexts,
            'max_context_length': self.max_context_length,
            'context_ttl_days': self.context_ttl_days,
        }
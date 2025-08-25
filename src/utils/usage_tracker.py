"""Usage tracking and cost management for Smart CLI."""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from .config import ConfigManager


class UsageType(Enum):
    """Types of usage to track."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CUSTOM_PROMPT = "custom_prompt"
    API_GENERATION = "api_generation"
    DOCUMENTATION = "documentation"


@dataclass
class UsageEntry:
    """Usage tracking entry."""
    entry_id: str
    usage_type: UsageType
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    actual_cost: Optional[float]
    session_id: Optional[str]
    context_id: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class BudgetAlert:
    """Budget alert configuration."""
    alert_id: str
    budget_type: str  # 'daily', 'weekly', 'monthly'
    budget_amount: float
    current_spend: float
    threshold_percentage: float  # Alert when this % of budget is reached
    is_active: bool
    created_at: datetime


class UsageTracker:
    """Tracks API usage and manages costs."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.logger = structlog.get_logger()
        
        # Database setup
        self.db_path = Path.home() / ".smart-cli" / "usage.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # Budget settings
        self.daily_budget = self.config.get_config('daily_budget', 5.0)
        self.weekly_budget = self.config.get_config('weekly_budget', 25.0)
        self.monthly_budget = self.config.get_config('monthly_budget', 100.0)
        
        # Alert thresholds
        self.budget_alert_thresholds = [0.5, 0.8, 0.9, 1.0]  # 50%, 80%, 90%, 100%
    
    def _init_database(self):
        """Initialize SQLite database for usage tracking."""
        conn = sqlite3.connect(str(self.db_path))
        
        # Usage entries table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usage_entries (
                entry_id TEXT PRIMARY KEY,
                usage_type TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                estimated_cost REAL,
                actual_cost REAL,
                session_id TEXT,
                context_id TEXT,
                metadata TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        # Budget alerts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budget_alerts (
                alert_id TEXT PRIMARY KEY,
                budget_type TEXT NOT NULL,
                budget_amount REAL NOT NULL,
                current_spend REAL DEFAULT 0.0,
                threshold_percentage REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP,
                last_triggered TIMESTAMP
            )
        ''')
        
        # Usage summaries table (for quick lookups)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usage_summaries (
                summary_id TEXT PRIMARY KEY,
                summary_type TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
                date_key TEXT NOT NULL,      -- '2024-01-01', '2024-W01', '2024-01'
                total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                request_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP
            )
        ''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_entries(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_type ON usage_entries(usage_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_entries(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_summaries_date ON usage_summaries(date_key)')
        
        conn.commit()
        conn.close()
    
    def track_usage(
        self,
        usage_type: UsageType,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost: float,
        session_id: Optional[str] = None,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        actual_cost: Optional[float] = None
    ) -> str:
        """Track a usage event."""
        
        entry_id = f"{usage_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        total_tokens = prompt_tokens + completion_tokens
        
        entry = UsageEntry(
            entry_id=entry_id,
            usage_type=usage_type,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            session_id=session_id,
            context_id=context_id,
            metadata=metadata or {},
            timestamp=datetime.now()
        )
        
        self._save_usage_entry(entry)
        self._update_usage_summaries(entry)
        self._check_budget_alerts(estimated_cost)
        
        self.logger.info(
            "Usage tracked",
            usage_type=usage_type.value,
            model=model,
            tokens=total_tokens,
            cost=estimated_cost
        )
        
        return entry_id
    
    def get_usage_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        usage_type: Optional[UsageType] = None
    ) -> Dict[str, Any]:
        """Get usage summary for a date range."""
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT 
                COUNT(*) as request_count,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_estimated_cost,
                SUM(actual_cost) as total_actual_cost,
                AVG(total_tokens) as avg_tokens_per_request,
                AVG(estimated_cost) as avg_cost_per_request,
                usage_type,
                model
            FROM usage_entries 
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if usage_type:
            query += " AND usage_type = ?"
            params.append(usage_type.value)
        
        query += " GROUP BY usage_type, model ORDER BY total_estimated_cost DESC"
        
        cursor.execute(query, params)
        detailed_results = cursor.fetchall()
        
        # Overall summary
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_estimated_cost,
                SUM(actual_cost) as total_actual_cost
            FROM usage_entries 
            WHERE timestamp >= ? AND timestamp <= ?
        ''' + (" AND usage_type = ?" if usage_type else ""), 
        params[:2] + ([usage_type.value] if usage_type else []))
        
        overall = cursor.fetchone()
        
        conn.close()
        
        return {
            'summary_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'usage_type': usage_type.value if usage_type else 'all'
            },
            'overall': {
                'total_requests': overall[0] or 0,
                'total_tokens': overall[1] or 0,
                'total_estimated_cost': overall[2] or 0.0,
                'total_actual_cost': overall[3] or 0.0,
                'average_cost_per_request': (overall[2] / overall[0]) if overall[0] else 0.0
            },
            'by_type_and_model': [
                {
                    'usage_type': row[6],
                    'model': row[7],
                    'request_count': row[0],
                    'total_tokens': row[1],
                    'total_estimated_cost': row[2],
                    'total_actual_cost': row[3],
                    'avg_tokens_per_request': row[4],
                    'avg_cost_per_request': row[5]
                }
                for row in detailed_results
            ]
        }
    
    def get_daily_usage(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage for a specific day."""
        if not date:
            date = datetime.now()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.get_usage_summary(start_of_day, end_of_day)
    
    def get_weekly_usage(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage for a specific week."""
        if not date:
            date = datetime.now()
        
        # Start of week (Monday)
        start_of_week = date - timedelta(days=date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)
        
        return self.get_usage_summary(start_of_week, end_of_week)
    
    def get_monthly_usage(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage for a specific month."""
        if not date:
            date = datetime.now()
        
        start_of_month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # End of month
        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(month=start_of_month.month + 1)
        
        return self.get_usage_summary(start_of_month, end_of_month)
    
    def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget status."""
        now = datetime.now()
        
        daily_usage = self.get_daily_usage(now)
        weekly_usage = self.get_weekly_usage(now)
        monthly_usage = self.get_monthly_usage(now)
        
        daily_cost = daily_usage['overall']['total_estimated_cost']
        weekly_cost = weekly_usage['overall']['total_estimated_cost']
        monthly_cost = monthly_usage['overall']['total_estimated_cost']
        
        return {
            'daily': {
                'budget': self.daily_budget,
                'spent': daily_cost,
                'remaining': max(0, self.daily_budget - daily_cost),
                'percentage_used': (daily_cost / self.daily_budget * 100) if self.daily_budget > 0 else 0,
                'over_budget': daily_cost > self.daily_budget
            },
            'weekly': {
                'budget': self.weekly_budget,
                'spent': weekly_cost,
                'remaining': max(0, self.weekly_budget - weekly_cost),
                'percentage_used': (weekly_cost / self.weekly_budget * 100) if self.weekly_budget > 0 else 0,
                'over_budget': weekly_cost > self.weekly_budget
            },
            'monthly': {
                'budget': self.monthly_budget,
                'spent': monthly_cost,
                'remaining': max(0, self.monthly_budget - monthly_cost),
                'percentage_used': (monthly_cost / self.monthly_budget * 100) if self.monthly_budget > 0 else 0,
                'over_budget': monthly_cost > self.monthly_budget
            }
        }
    
    def set_budget(self, budget_type: str, amount: float) -> bool:
        """Set budget for daily, weekly, or monthly usage."""
        if budget_type == 'daily':
            self.daily_budget = amount
            self.config.set_config('daily_budget', amount)
        elif budget_type == 'weekly':
            self.weekly_budget = amount
            self.config.set_config('weekly_budget', amount)
        elif budget_type == 'monthly':
            self.monthly_budget = amount
            self.config.set_config('monthly_budget', amount)
        else:
            return False
        
        self.logger.info("Budget updated", budget_type=budget_type, amount=amount)
        return True
    
    def get_top_usage_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top usage patterns by cost."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                usage_type,
                model,
                COUNT(*) as usage_count,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(estimated_cost) as avg_cost
            FROM usage_entries 
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY usage_type, model
            ORDER BY total_cost DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'usage_type': row[0],
                'model': row[1],
                'usage_count': row[2],
                'total_tokens': row[3],
                'total_cost': row[4],
                'average_cost': row[5]
            }
            for row in results
        ]
    
    def export_usage_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json'
    ) -> str:
        """Export usage data to JSON or CSV."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT * FROM usage_entries WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        if format.lower() == 'json':
            data = [dict(zip(column_names, row)) for row in rows]
            return json.dumps(data, indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(column_names)
            writer.writerows(rows)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_usage_entry(self, entry: UsageEntry):
        """Save usage entry to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_entries 
            (entry_id, usage_type, model, prompt_tokens, completion_tokens, total_tokens,
             estimated_cost, actual_cost, session_id, context_id, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.entry_id,
            entry.usage_type.value,
            entry.model,
            entry.prompt_tokens,
            entry.completion_tokens,
            entry.total_tokens,
            entry.estimated_cost,
            entry.actual_cost,
            entry.session_id,
            entry.context_id,
            json.dumps(entry.metadata),
            entry.timestamp
        ))
        
        conn.commit()
        conn.close()
    
    def _update_usage_summaries(self, entry: UsageEntry):
        """Update usage summaries for quick lookups."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Update daily summary
        daily_key = entry.timestamp.strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR IGNORE INTO usage_summaries 
            (summary_id, summary_type, date_key, total_tokens, total_cost, request_count, last_updated)
            VALUES (?, 'daily', ?, 0, 0.0, 0, ?)
        ''', (f"daily_{daily_key}", daily_key, entry.timestamp))
        
        cursor.execute('''
            UPDATE usage_summaries 
            SET total_tokens = total_tokens + ?,
                total_cost = total_cost + ?,
                request_count = request_count + 1,
                last_updated = ?
            WHERE summary_type = 'daily' AND date_key = ?
        ''', (entry.total_tokens, entry.estimated_cost, entry.timestamp, daily_key))
        
        conn.commit()
        conn.close()
    
    def _check_budget_alerts(self, cost: float):
        """Check if budget alerts should be triggered."""
        budget_status = self.check_budget_status()
        
        for period, status in budget_status.items():
            percentage_used = status['percentage_used']
            
            for threshold in self.budget_alert_thresholds:
                if percentage_used >= threshold * 100:
                    self.logger.warning(
                        "Budget alert triggered",
                        period=period,
                        percentage_used=percentage_used,
                        threshold=threshold * 100,
                        spent=status['spent'],
                        budget=status['budget']
                    )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage tracker statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total usage
        cursor.execute('SELECT COUNT(*), SUM(total_tokens), SUM(estimated_cost) FROM usage_entries')
        total_stats = cursor.fetchone()
        
        # Usage by type
        cursor.execute('''
            SELECT usage_type, COUNT(*), SUM(estimated_cost) 
            FROM usage_entries 
            GROUP BY usage_type 
            ORDER BY SUM(estimated_cost) DESC
        ''')
        usage_by_type = cursor.fetchall()
        
        # Recent usage (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*), SUM(estimated_cost) 
            FROM usage_entries 
            WHERE timestamp > datetime('now', '-1 day')
        ''')
        recent_stats = cursor.fetchone()
        
        conn.close()
        
        budget_status = self.check_budget_status()
        
        return {
            'total_requests': total_stats[0] or 0,
            'total_tokens': total_stats[1] or 0,
            'total_cost': total_stats[2] or 0.0,
            'recent_requests_24h': recent_stats[0] or 0,
            'recent_cost_24h': recent_stats[1] or 0.0,
            'usage_by_type': [
                {'type': row[0], 'count': row[1], 'cost': row[2]}
                for row in usage_by_type
            ],
            'budget_status': budget_status,
            'configured_budgets': {
                'daily': self.daily_budget,
                'weekly': self.weekly_budget,
                'monthly': self.monthly_budget
            }
        }
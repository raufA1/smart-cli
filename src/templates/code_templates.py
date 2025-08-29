"""Code Templates - Built-in code generation templates."""

from .template_manager import Template


class PythonTemplate(Template):
    """Basic Python application template."""
    
    def __init__(self):
        super().__init__(
            name="python_basic",
            description="Basic Python application with main function",
            category="python",
            files={
                "{{project_name}}.py": """{{description}}

import sys


def main():
    \"\"\"Main function.\"\"\"
    print("Hello from {{project_name}}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
""",
                "README.md": """# {{project_name}}

{{description}}

## Usage

```bash
python {{project_name}}.py
```

## Requirements

See requirements.txt for dependencies.
"""
            },
            variables={
                "project_name": "my_app",
                "description": "A simple Python application"
            },
            dependencies=[]
        )


class WebScraperTemplate(Template):
    """Web scraper template with modern tools."""
    
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Professional web scraper with proxy support",
            category="scraping",
            files={
                "scraper.py": """{{description}} - Web Scraper

import asyncio
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class {{class_name}}:
    \"\"\"Professional web scraper with proxy rotation and user-agent rotation.\"\"\"
    
    def __init__(self, db_path: str = "{{project_name}}.db"):
        self.db_path = db_path
        self.session = None
        self.ua = UserAgent()
        self.proxies = []
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        \"\"\"Setup logging configuration.\"\"\"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('{{project_name}}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        \"\"\"Initialize SQLite database.\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            \"\"\")
    
    async def get_session(self) -> aiohttp.ClientSession:
        \"\"\"Get or create aiohttp session.\"\"\"
        if not self.session:
            headers = {'User-Agent': self.ua.random}
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def scrape_url(self, url: str) -> Optional[Dict]:
        \"\"\"Scrape a single URL.\"\"\"
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract data
                    data = {
                        'url': url,
                        'title': soup.title.text if soup.title else '',
                        'content': soup.get_text(strip=True),
                        'metadata': json.dumps({
                            'status_code': response.status,
                            'content_type': response.headers.get('content-type', ''),
                            'content_length': len(html)
                        })
                    }
                    
                    # Save to database
                    self.save_data(data)
                    self.logger.info(f"Scraped: {url}")
                    return data
                else:
                    self.logger.warning(f"Failed to scrape {url}: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
        
        return None
    
    def save_data(self, data: Dict):
        \"\"\"Save scraped data to database.\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                \"\"\"INSERT INTO scraped_data (url, title, content, metadata) 
                   VALUES (?, ?, ?, ?)\"\"\",
                (data['url'], data['title'], data['content'], data['metadata'])
            )
    
    async def scrape_urls(self, urls: List[str]) -> List[Dict]:
        \"\"\"Scrape multiple URLs concurrently.\"\"\"
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]
    
    async def export_data(self, format: str = 'json') -> str:
        \"\"\"Export scraped data.\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM scraped_data')
            data = [dict(zip([col[0] for col in cursor.description], row)) 
                   for row in cursor.fetchall()]
        
        if format == 'json':
            filename = f"{{project_name}}_export_{datetime.now():%Y%m%d_%H%M%S}.json"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
        
        return filename
    
    async def close(self):
        \"\"\"Close the session.\"\"\"
        if self.session:
            await self.session.close()


async def main():
    \"\"\"Main scraping function.\"\"\"
    scraper = {{class_name}}()
    
    # Example URLs to scrape
    urls = [
        "{{target_url}}"
    ]
    
    try:
        results = await scraper.scrape_urls(urls)
        print(f"Scraped {len(results)} URLs successfully")
        
        # Export results
        export_file = await scraper.export_data('json')
        print(f"Data exported to: {export_file}")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
""",
                "config.py": """Configuration settings for {{project_name}}.

import os
from pathlib import Path

# Database settings
DATABASE_PATH = "{{project_name}}.db"

# Request settings
REQUEST_DELAY = 1.0  # seconds between requests
CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 30

# Proxy settings (optional)
PROXIES = []

# User agents rotation
USE_RANDOM_USER_AGENT = True

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = "{{project_name}}.log"

# Export settings
EXPORT_FORMAT = "json"  # json, csv, xlsx
""",
                "requirements.txt": """aiohttp>=3.8.0
aiofiles>=0.8.0
beautifulsoup4>=4.11.0
fake-useragent>=1.1.0
lxml>=4.6.0
"""
            },
            variables={
                "project_name": "web_scraper",
                "class_name": "WebScraper",
                "description": "Professional web scraper",
                "target_url": "https://example.com"
            },
            dependencies=[
                "aiohttp>=3.8.0",
                "aiofiles>=0.8.0", 
                "beautifulsoup4>=4.11.0",
                "fake-useragent>=1.1.0",
                "lxml>=4.6.0"
            ]
        )


class APITemplate(Template):
    """FastAPI REST API template."""
    
    def __init__(self):
        super().__init__(
            name="fastapi_api",
            description="FastAPI REST API with database and authentication",
            category="api",
            files={
                "main.py": """{{description}} - FastAPI Application

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="{{project_name}}",
    description="{{description}}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Pydantic models
class {{model_name}}(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class {{model_name}}Create(BaseModel):
    name: str
    description: Optional[str] = None


# Mock database
{{model_name_lower}}_db = []


# Dependencies
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    \"\"\"Validate token and return current user.\"\"\"
    # TODO: Implement actual authentication
    return {"user_id": 1, "username": "admin"}


# Routes
@app.get("/")
async def root():
    \"\"\"Root endpoint.\"\"\"
    return {"message": "Welcome to {{project_name}} API"}


@app.get("/{{endpoint_name}}/", response_model=List[{{model_name}}])
async def get_{{model_name_lower}}s(
    skip: int = 0,
    limit: int = 100,
    user=Depends(get_current_user)
):
    \"\"\"Get all {{model_name_lower}}s.\"\"\"
    return {{model_name_lower}}_db[skip:skip + limit]


@app.get("/{{endpoint_name}}/{{{model_name_lower}}_id}", response_model={{model_name}})
async def get_{{model_name_lower}}(
    {{model_name_lower}}_id: int,
    user=Depends(get_current_user)
):
    \"\"\"Get {{model_name_lower}} by ID.\"\"\"
    for item in {{model_name_lower}}_db:
        if item.id == {{model_name_lower}}_id:
            return item
    raise HTTPException(status_code=404, detail="{{model_name}} not found")


@app.post("/{{endpoint_name}}/", response_model={{model_name}})
async def create_{{model_name_lower}}(
    {{model_name_lower}}: {{model_name}}Create,
    user=Depends(get_current_user)
):
    \"\"\"Create new {{model_name_lower}}.\"\"\"
    new_{{model_name_lower}} = {{model_name}}(
        id=len({{model_name_lower}}_db) + 1,
        name={{model_name_lower}}.name,
        description={{model_name_lower}}.description,
        created_at=datetime.now()
    )
    {{model_name_lower}}_db.append(new_{{model_name_lower}})
    return new_{{model_name_lower}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
            },
            variables={
                "project_name": "MyAPI",
                "description": "A FastAPI REST API",
                "model_name": "Item",
                "model_name_lower": "item",
                "endpoint_name": "items"
            },
            dependencies=[
                "fastapi>=0.68.0",
                "uvicorn[standard]>=0.15.0",
                "python-multipart>=0.0.5"
            ]
        )


class CLITemplate(Template):
    """CLI application template with Typer."""
    
    def __init__(self):
        super().__init__(
            name="cli_app",
            description="CLI application with Typer and Rich",
            category="cli",
            files={
                "{{project_name}}.py": """{{description}} - CLI Application

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

app = typer.Typer(help="{{description}}")
console = Console()


@app.command()
def hello(
    name: str = typer.Argument("World", help="Name to greet"),
    count: int = typer.Option(1, "--count", "-c", help="Number of greetings")
):
    \"\"\"Say hello to NAME.\"\"\"
    for i in range(count):
        console.print(f"Hello {name}!", style="bold green")


@app.command()
def list_files(
    directory: Path = typer.Argument(".", help="Directory to list"),
    show_hidden: bool = typer.Option(False, "--hidden", "-h", help="Show hidden files")
):
    \"\"\"List files in directory.\"\"\"
    if not directory.exists():
        console.print(f"❌ Directory {directory} does not exist", style="red")
        raise typer.Exit(1)
    
    table = Table(title=f"Files in {directory}")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Size", style="yellow")
    
    for item in directory.iterdir():
        if not show_hidden and item.name.startswith('.'):
            continue
        
        item_type = "📁 Directory" if item.is_dir() else "📄 File"
        size = str(item.stat().st_size) if item.is_file() else "-"
        
        table.add_row(item.name, item_type, size)
    
    console.print(table)


@app.command()
def version():
    \"\"\"Show version information.\"\"\"
    console.print("{{project_name}} v1.0.0", style="bold blue")


if __name__ == "__main__":
    app()
"""
            },
            variables={
                "project_name": "mycli",
                "description": "A command line application"
            },
            dependencies=[
                "typer>=0.6.0",
                "rich>=12.0.0"
            ]
        )


class DatabaseTemplate(Template):
    """Database application template with SQLAlchemy."""
    
    def __init__(self):
        super().__init__(
            name="database_app",
            description="Database application with SQLAlchemy ORM",
            category="database", 
            files={
                "models.py": """Database models for {{project_name}}.

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class {{model_name}}(Base):
    \"\"\"{{model_name}} model.\"\"\"
    __tablename__ = "{{table_name}}"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<{{model_name}}(id={self.id}, name='{self.name}')>"
""",
                "database.py": """Database connection and session management.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from models import Base
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///{{project_name}}.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("DEBUG") else False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    \"\"\"Create all database tables.\"\"\"
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session() -> Session:
    \"\"\"Get database session with context manager.\"\"\"
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Session:
    \"\"\"Get database session (for dependency injection).\"\"\"
    return SessionLocal()
""",
                "main.py": """Main application for {{project_name}}.

from database import create_tables, get_db_session
from models import {{model_name}}


def main():
    \"\"\"Main function.\"\"\"
    # Create tables
    create_tables()
    print("✅ Database tables created")
    
    # Example usage
    with get_db_session() as db:
        # Create
        {{model_name_lower}} = {{model_name}}(
            name="Example {{model_name}}", 
            description="This is an example {{model_name_lower}}"
        )
        db.add({{model_name_lower}})
        print(f"✅ Created {{model_name_lower}}: {{{model_name_lower}}}")


if __name__ == "__main__":
    main()
"""
            },
            variables={
                "project_name": "db_app",
                "model_name": "Item",
                "model_name_lower": "item",
                "table_name": "items"
            },
            dependencies=[
                "sqlalchemy>=1.4.0",
                "python-dotenv>=0.19.0"
            ]
        )


class TestTemplate(Template):
    """Test suite template with pytest."""
    
    def __init__(self):
        super().__init__(
            name="test_suite",
            description="Complete test suite with pytest",
            category="testing",
            files={
                "test_{{module_name}}.py": """Tests for {{module_name}} module.

import pytest
from unittest.mock import Mock, patch
from {{module_name}} import {{class_name}}


class Test{{class_name}}:
    \"\"\"Test suite for {{class_name}} class.\"\"\"
    
    def setup_method(self):
        \"\"\"Setup for each test method.\"\"\"
        self.{{instance_name}} = {{class_name}}()
    
    def test_initialization(self):
        \"\"\"Test {{class_name}} initialization.\"\"\"
        assert self.{{instance_name}} is not None
    
    def test_{{method_name}}_success(self):
        \"\"\"Test {{method_name}} success case.\"\"\"
        # Arrange
        expected_result = "expected"
        
        # Act
        result = self.{{instance_name}}.{{method_name}}("input")
        
        # Assert
        assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
            },
            variables={
                "module_name": "main",
                "class_name": "MyClass",
                "instance_name": "my_instance",
                "method_name": "process"
            },
            dependencies=[
                "pytest>=6.0.0",
                "pytest-asyncio>=0.18.0",
                "pytest-mock>=3.6.0",
                "pytest-cov>=3.0.0"
            ]
        )
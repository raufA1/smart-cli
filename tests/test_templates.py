"""Tests for template system."""

import pytest
import tempfile
from pathlib import Path
from src.templates import TemplateManager


class TestTemplateManager:
    """Test suite for TemplateManager."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.template_manager = TemplateManager()
    
    def test_initialization(self):
        """Test TemplateManager initialization."""
        assert self.template_manager is not None
        assert len(self.template_manager.templates) > 0
    
    def test_list_templates(self):
        """Test listing templates."""
        templates = self.template_manager.list_templates()
        assert len(templates) > 0
        
        # Check specific templates exist
        template_names = [t.name for t in templates]
        assert "python_basic" in template_names
        assert "web_scraper" in template_names
        assert "fastapi_api" in template_names
    
    def test_get_template(self):
        """Test getting specific template."""
        template = self.template_manager.get_template("python_basic")
        assert template is not None
        assert template.name == "python_basic"
        assert template.category == "python"
        assert len(template.files) > 0
    
    def test_get_categories(self):
        """Test getting template categories."""
        categories = self.template_manager.get_categories()
        assert len(categories) > 0
        assert "python" in categories
        assert "scraping" in categories
        assert "api" in categories
    
    def test_generate_from_template(self):
        """Test generating files from template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate python basic template
            created_files = self.template_manager.generate_from_template(
                "python_basic",
                {
                    "project_name": "test_app",
                    "description": "Test application"
                },
                temp_dir
            )
            
            assert len(created_files) > 0
            
            # Check files were created
            for file_path in created_files:
                assert Path(file_path).exists()
                
                # Check content has variables replaced
                with open(file_path, 'r') as f:
                    content = f.read()
                    assert "test_app" in content
                    assert "Test application" in content
                    assert "{{project_name}}" not in content
    
    def test_create_requirements_file(self):
        """Test creating requirements file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            req_file = self.template_manager.create_requirements_file(
                "web_scraper", 
                temp_dir
            )
            
            assert req_file is not None
            assert Path(req_file).exists()
            
            with open(req_file, 'r') as f:
                content = f.read()
                assert "aiohttp" in content
                assert "beautifulsoup4" in content
    
    def test_get_template_info(self):
        """Test getting template information."""
        info = self.template_manager.get_template_info("web_scraper")
        
        assert info is not None
        assert info["name"] == "web_scraper"
        assert info["category"] == "scraping"
        assert "files" in info
        assert "variables" in info
        assert "dependencies" in info
        assert len(info["dependencies"]) > 0
    
    def test_invalid_template(self):
        """Test handling invalid template."""
        template = self.template_manager.get_template("nonexistent")
        assert template is None
        
        info = self.template_manager.get_template_info("nonexistent")
        assert info is None
        
        with pytest.raises(ValueError):
            self.template_manager.generate_from_template(
                "nonexistent",
                {},
                "."
            )


class TestSpecificTemplates:
    """Test specific template implementations."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.template_manager = TemplateManager()
    
    def test_python_template(self):
        """Test Python basic template."""
        template = self.template_manager.get_template("python_basic")
        
        assert template.name == "python_basic"
        assert template.category == "python"
        assert len(template.files) == 2  # main.py and README.md
        assert "{{project_name}}.py" in template.files
        assert "README.md" in template.files
    
    def test_web_scraper_template(self):
        """Test web scraper template."""
        template = self.template_manager.get_template("web_scraper")
        
        assert template.name == "web_scraper"
        assert template.category == "scraping"
        assert len(template.files) >= 3  # scraper.py, config.py, requirements.txt
        assert len(template.dependencies) > 0
        
        # Check for required dependencies
        deps = template.dependencies
        assert any("aiohttp" in dep for dep in deps)
        assert any("beautifulsoup4" in dep for dep in deps)
    
    def test_api_template(self):
        """Test FastAPI template."""
        template = self.template_manager.get_template("fastapi_api")
        
        assert template.name == "fastapi_api"
        assert template.category == "api"
        assert "main.py" in template.files
        
        # Check for FastAPI-specific content
        main_content = template.files["main.py"]
        assert "FastAPI" in main_content
        assert "uvicorn" in main_content
    
    def test_cli_template(self):
        """Test CLI template."""
        template = self.template_manager.get_template("cli_app")
        
        assert template.name == "cli_app"
        assert template.category == "cli"
        
        # Check for Typer usage
        main_file = list(template.files.keys())[0]
        main_content = template.files[main_file]
        assert "typer" in main_content
        assert "rich" in main_content
    
    def test_database_template(self):
        """Test database template."""
        template = self.template_manager.get_template("database_app")
        
        assert template.name == "database_app"
        assert template.category == "database"
        assert "models.py" in template.files
        assert "database.py" in template.files
        assert "crud.py" in template.files
        
        # Check for SQLAlchemy content
        models_content = template.files["models.py"]
        assert "SQLAlchemy" in models_content or "sqlalchemy" in models_content
    
    def test_test_template(self):
        """Test testing template."""
        template = self.template_manager.get_template("test_suite")
        
        assert template.name == "test_suite"
        assert template.category == "testing"
        
        # Check for pytest content
        test_files = [f for f in template.files.keys() if "test_" in f]
        assert len(test_files) > 0
        
        test_content = template.files[test_files[0]]
        assert "pytest" in test_content
        assert "@pytest" in test_content


class TestTemplateGeneration:
    """Test template generation with various scenarios."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.template_manager = TemplateManager()
    
    def test_generate_web_scraper(self):
        """Test generating complete web scraper project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            created_files = self.template_manager.generate_from_template(
                "web_scraper",
                {
                    "project_name": "news_scraper",
                    "class_name": "NewsScraper",
                    "description": "News scraper for articles",
                    "target_url": "https://news.ycombinator.com"
                },
                temp_dir
            )
            
            assert len(created_files) >= 3
            
            # Check specific files exist
            files = [Path(f).name for f in created_files]
            assert "scraper.py" in files
            assert "config.py" in files
            assert "requirements.txt" in files
            
            # Check content
            scraper_file = next(f for f in created_files if "scraper.py" in f)
            with open(scraper_file, 'r') as f:
                content = f.read()
                assert "NewsScraper" in content
                assert "news_scraper" in content
                assert "News scraper for articles" in content
                assert "https://news.ycombinator.com" in content
    
    def test_generate_api_project(self):
        """Test generating FastAPI project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            created_files = self.template_manager.generate_from_template(
                "fastapi_api",
                {
                    "project_name": "TaskAPI",
                    "model_name": "Task",
                    "model_name_lower": "task",
                    "endpoint_name": "tasks"
                },
                temp_dir
            )
            
            assert len(created_files) >= 1
            
            # Check content
            main_file = created_files[0]
            with open(main_file, 'r') as f:
                content = f.read()
                assert "TaskAPI" in content
                assert "Task" in content
                assert "/tasks/" in content
                assert "task_db" in content
    
    @pytest.mark.parametrize("template_name", [
        "python_basic",
        "web_scraper", 
        "fastapi_api",
        "cli_app",
        "database_app",
        "test_suite"
    ])
    def test_all_templates_generate(self, template_name):
        """Test that all templates can be generated without errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template = self.template_manager.get_template(template_name)
            
            created_files = self.template_manager.generate_from_template(
                template_name,
                template.variables,  # Use default variables
                temp_dir
            )
            
            assert len(created_files) > 0
            
            # Verify all files were created
            for file_path in created_files:
                assert Path(file_path).exists()
                
                # Basic content check
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Should not contain unreplaced variables
                    assert "{{" not in content or "}}" not in content
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "devflow-default-secret-key-2026")
    
    # Database
    db_path = (BASE_DIR / "devflow.db").as_posix()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{db_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # AI Provider Settings ('demo', 'groq', 'deepseek', 'gemini')
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "demo").lower()
    
    # Groq Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # DeepSeek Settings
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # Google Gemini Settings (Gemini 2.5 Flash / Gemini 2.0 Flash)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # GitHub Integration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    
    # Workspace & Storage Paths
    STORAGE_DIR = BASE_DIR / "storage"
    REPOSITORY_DIR = BASE_DIR / "repositories"
    WORKSPACE_DIR = BASE_DIR / "repositories" / "workspace"
    ORIGINAL_REPO_DIR = BASE_DIR / "repositories" / "original"
    PATCHES_DIR = BASE_DIR / "repositories" / "patches"
    VECTOR_DB_DIR = BASE_DIR / "vector_db"
    REPORTS_DIR = BASE_DIR / "reports"
    DEMO_REPO_DIR = BASE_DIR / "demo_repository"
    
    # Operational Limits & Safety
    MAX_AGENT_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "3"))
    MAX_EXECUTION_TIMEOUT = int(os.getenv("MAX_EXECUTION_TIMEOUT_SECONDS", "60"))
    DOCKER_ENABLED = os.getenv("DOCKER_ENABLED", "false").lower() in ("true", "1", "yes")
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    
    @classmethod
    def init_directories(cls):
        """Ensure runtime storage directories exist."""
        for path in [
            cls.STORAGE_DIR,
            cls.REPOSITORY_DIR,
            cls.WORKSPACE_DIR,
            cls.ORIGINAL_REPO_DIR,
            cls.PATCHES_DIR,
            cls.VECTOR_DB_DIR,
            cls.REPORTS_DIR,
            cls.DEMO_REPO_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)

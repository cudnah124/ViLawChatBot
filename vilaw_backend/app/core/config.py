import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ViLaw")
    
    # OpenRouter Config
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL")
    
    # Vector DB
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./vilaw_db")

    #Pinecone Config
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_HOST: str = os.getenv("PINECONE_HOST")

settings = Settings()
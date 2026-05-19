import os

os.environ["APP_ENV"] = "test"
os.environ["DEFAULT_TENANT_ID"] = "default"
os.environ["DEFAULT_WORKSPACE_ID"] = "default"
os.environ["DATABASE_URL"] = "postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream"

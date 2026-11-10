from sqlalchemy import text
from claims_agent.core.config import get_settings
from claims_agent.db.session import make_engine

engine = make_engine(get_settings().database_url.get_secret_value())
with engine.connect() as conn:
    row = conn.execute(text("SELECT current_database(), current_user")).one()
print(f"connected to {row[0]} as {row[1]}") 
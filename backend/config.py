import os
from dotenv import load_dotenv

load_dotenv()

# Example: DATABASE_URL=postgresql+asyncpg://user:password@localhost/placement_focusbar
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/placement_focusbar")

# Additional config can be added here

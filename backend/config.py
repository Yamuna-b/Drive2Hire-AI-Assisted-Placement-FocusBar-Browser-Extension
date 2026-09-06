import os
from dotenv import load_dotenv

load_dotenv()

# Leave unset to run without PostgreSQL (Phases 1–2 work fine without DB).
# When ready, copy .env.example → .env and set your local Postgres credentials.
DATABASE_URL = os.getenv("DATABASE_URL") or None
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "758501915824-n03vtotgp025jc2gmn7hnsg5gh6lik0k.apps.googleusercontent.com",
)

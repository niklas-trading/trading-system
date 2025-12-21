import os
from lib.config import REQUIRED_ENV

missing = [e for e in REQUIRED_ENV if e not in os.environ]

if missing:
    raise RuntimeError(f"Missing env vars: {missing}")

print("✔ Environment OK")

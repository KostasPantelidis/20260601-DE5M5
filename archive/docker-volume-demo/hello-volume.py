from pathlib import Path
from datetime import datetime

out = Path("/data/hello.txt")

with out.open("a") as f:
    f.write(f"Hello docker volume: {datetime.now()}\n")
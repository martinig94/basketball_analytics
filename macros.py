import sys
from pathlib import Path

from datetime import datetime
sys.path.append(str(Path(__file__).parent))
from constants import SEASON

# ── markdown vars──────────────────────────────────────────────────────────────
def define_env(env):
    print("MACROS LOADED ✅")
    env.variables['today'] = datetime.now().strftime("%Y-%m-%d")
    env.variables['season'] = f"{SEASON}-{SEASON + 1}"
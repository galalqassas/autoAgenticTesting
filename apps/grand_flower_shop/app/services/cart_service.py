from pathlib import Path
import sys

# Add parent to path to resolve imports correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.cart import Cart

# In-memory cart (per-session in production use session/cookies)
app_cart = Cart()

def get_cart() -> Cart:
    return app_cart

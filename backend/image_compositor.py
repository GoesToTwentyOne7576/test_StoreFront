"""
Step 5: image compositing. Pillow is the whole dependency here -- no need
for anything heavier for a simple alpha-composite overlay.
"""
import io

from PIL import Image

from config import PLANTER_ASSET_PATH


def overlay_planter(storefront_bytes: bytes) -> bytes:
    """
    Loads the storefront photo, pastes the transparent planter PNG near the
    bottom of the frame at a reasonable scale, and returns a JPEG buffer.
    """
    base = Image.open(io.BytesIO(storefront_bytes)).convert("RGBA")
    planter = Image.open(PLANTER_ASSET_PATH).convert("RGBA")

    # Scale the planter to ~22% of the storefront's width, keep aspect ratio.
    target_w = int(base.width * 0.22)
    scale = target_w / planter.width
    target_h = int(planter.height * scale)
    planter = planter.resize((target_w, target_h))

    # Place it bottom-left-ish, just inset from the edge, sitting on the
    # "ground" near the doorway. Good-enough heuristic for a PoC.
    x = int(base.width * 0.06)
    y = base.height - target_h - int(base.height * 0.04)

    composited = base.copy()
    composited.alpha_composite(planter, dest=(x, y))

    out = io.BytesIO()
    composited.convert("RGB").save(out, format="JPEG", quality=90)
    return out.getvalue()

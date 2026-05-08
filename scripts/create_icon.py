# scripts/create_icon.py
"""Generate a clean SentinelX icon."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def create_icon():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("PIL not installed: pip install pillow")
        return

    icon_dir = Path("assets/icons")
    icon_dir.mkdir(parents=True, exist_ok=True)

    def draw_sentinel_icon(size: int) -> Image.Image:
        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        s    = size

        # Background circle — dark navy
        draw.ellipse([s*0.03, s*0.03, s*0.97, s*0.97],
                     fill=(10, 14, 26, 255))

        # Outer shield — cyan glow
        shield_pts = [
            (s*0.50, s*0.06),
            (s*0.92, s*0.22),
            (s*0.92, s*0.56),
            (s*0.50, s*0.94),
            (s*0.08, s*0.56),
            (s*0.08, s*0.22),
        ]
        draw.polygon(shield_pts, fill=(0, 212, 255, 255))

        # Inner shield — dark
        inner_pts = [
            (s*0.50, s*0.14),
            (s*0.84, s*0.28),
            (s*0.84, s*0.54),
            (s*0.50, s*0.86),
            (s*0.16, s*0.54),
            (s*0.16, s*0.28),
        ]
        draw.polygon(inner_pts, fill=(10, 14, 26, 255))

        # X mark — green
        lw = max(2, int(s * 0.07))
        x1, y1 = s * 0.33, s * 0.33
        x2, y2 = s * 0.67, s * 0.67
        draw.line([(x1, y1), (x2, y2)], fill=(0, 255, 136, 255), width=lw)
        draw.line([(x2, y1), (x1, y2)], fill=(0, 255, 136, 255), width=lw)

        # Cyan border on X arms (thinner overlay for glow effect)
        lw2 = max(1, int(s * 0.025))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 255, 200, 180), width=lw2)
        draw.line([(x2, y1), (x1, y2)], fill=(0, 255, 200, 180), width=lw2)

        return img

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_sentinel_icon(s) for s in sizes]

    ico_path = icon_dir / "sentinel.ico"
    images[0].save(
        str(ico_path),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )

    # Also save a PNG for reference
    images[-1].save(str(icon_dir / "sentinel_256.png"))
    print(f"Icon created: {ico_path}")


if __name__ == "__main__":
    create_icon()
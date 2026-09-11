from pathlib import Path
import re


ANIMATION_DURATION = "90000ms"
STYLE_OVERRIDE = ".c{animation-name:none!important}.u{display:none}"


for svg_path in (
    Path("dist/github-snake.svg"),
    Path("dist/github-snake-dark.svg"),
):
    svg = svg_path.read_text()
    svg = re.sub(
        r"animation:none \d+ms linear infinite",
        f"animation:none {ANIMATION_DURATION} linear infinite",
        svg,
    )

    if STYLE_OVERRIDE not in svg:
        svg = svg.replace("</style>", f"{STYLE_OVERRIDE}</style>", 1)

    svg_path.write_text(svg)

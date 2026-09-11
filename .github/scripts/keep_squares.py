from pathlib import Path
from collections import deque
import re


ANIMATION_DURATION = "150000ms"
GRID_STEP = 16
SNAKE_SEGMENTS = 4
STYLE_START = "/* avoid-green-start */"
STYLE_END = "/* avoid-green-end */"


def contribution_cells(svg: str) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    cells: dict[tuple[int, int], bool] = {}
    pattern = re.compile(
        r'<rect class="(c(?: [^"]+)?)" x="(\d+)" y="(\d+)"'
    )

    for class_name, x_value, y_value in pattern.findall(svg):
        column = (int(x_value) - 2) // GRID_STEP
        row = (int(y_value) - 2) // GRID_STEP
        cells[(column, row)] = class_name != "c"

    if not cells:
        raise RuntimeError("No contribution cells found in generated SVG")

    free = {cell for cell, occupied in cells.items() if not occupied}
    occupied = {cell for cell, is_occupied in cells.items() if is_occupied}
    return free, occupied


def shortest_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    free: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    queue = deque([start])
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break

        column, row = current
        for neighbor in (
            (column + 1, row),
            (column, row + 1),
            (column - 1, row),
            (column, row - 1),
        ):
            if neighbor in free and neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)

    if goal not in previous:
        raise RuntimeError(f"No empty-cell route from {start} to {goal}")

    path = []
    current: tuple[int, int] | None = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    return list(reversed(path))


def avoidance_route(free: set[tuple[int, int]]) -> list[tuple[int, int]]:
    max_column = max(column for column, _ in free)
    max_row = max(row for _, row in free)
    border = {
        (column, row)
        for column in range(-1, max_column + 2)
        for row in (-1, max_row + 1)
    } | {
        (column, row)
        for column in (-1, max_column + 1)
        for row in range(max_row + 1)
    }
    navigable = free | border

    start = (-1, -1)
    connected = {start}
    queue = deque([start])
    while queue:
        column, row = queue.popleft()
        for neighbor in (
            (column + 1, row),
            (column, row + 1),
            (column - 1, row),
            (column, row - 1),
        ):
            if neighbor in navigable and neighbor not in connected:
                connected.add(neighbor)
                queue.append(neighbor)

    min_column = min(column for column, _ in connected)
    min_row = min(row for _, row in connected)
    max_column = max(column for column, _ in connected)
    max_row = max(row for _, row in connected)
    targets = []

    for row in range(min_row, max_row + 1):
        columns = range(min_column, max_column + 1)
        if (row - min_row) % 2:
            columns = reversed(range(min_column, max_column + 1))
        targets.extend(
            (column, row) for column in columns if (column, row) in connected
        )

    route = [targets[0]]
    for target in targets[1:]:
        route.extend(shortest_path(route[-1], target, connected)[1:])
    route.extend(shortest_path(route[-1], route[0], connected)[1:])
    return route


def animation_css(route: list[tuple[int, int]]) -> str:
    points = route[:-1]
    step_count = len(points)
    rules = [STYLE_START, ".c{animation-name:none!important}.u{display:none}"]

    for segment in range(SNAKE_SEGMENTS):
        frames = []
        for step in range(step_count + 1):
            column, row = points[(step - segment) % step_count]
            percentage = 100 * step / step_count
            frames.append(
                f"{percentage:.3f}%{{transform:translate("
                f"{column * GRID_STEP}px,{row * GRID_STEP}px)}}"
            )
        rules.append(f"@keyframes avoid{segment}{{{''.join(frames)}}}")
        rules.append(
            f".s.s{segment}{{animation-name:avoid{segment}!important;"
            f"animation-duration:{ANIMATION_DURATION}!important}}"
        )

    rules.append(STYLE_END)
    return "".join(rules)


for svg_path in (
    Path("dist/github-snake.svg"),
    Path("dist/github-snake-dark.svg"),
):
    svg = svg_path.read_text()
    free_cells, occupied_cells = contribution_cells(svg)
    route = avoidance_route(free_cells)

    if any(cell in occupied_cells for cell in route):
        raise RuntimeError("Generated snake route crosses a contribution square")

    svg = re.sub(
        r"animation:none \d+ms linear infinite",
        f"animation:none {ANIMATION_DURATION} linear infinite",
        svg,
    )
    svg = re.sub(
        rf"{re.escape(STYLE_START)}.*?{re.escape(STYLE_END)}",
        "",
        svg,
        flags=re.DOTALL,
    )
    svg = svg.replace("</style>", f"{animation_css(route)}</style>", 1)

    svg_path.write_text(svg)
    print(
        f"{svg_path}: {len(route) - 1} empty-cell steps, "
        f"avoiding {len(occupied_cells)} contribution squares"
    )

import datetime as dt
import html
import json
import math
import os
from pathlib import Path
import urllib.request


username = os.environ.get("GITHUB_REPOSITORY_OWNER", "varunsharma101")
token = os.environ["GITHUB_TOKEN"]
today = dt.datetime.now(dt.timezone.utc).date()


def github_request(url: str, payload: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "github-profile-activity",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


profile = github_request(f"https://api.github.com/users/{username}")
created = dt.datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00")).date()

query = """query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""

counts: dict[str, int] = {}
range_start = created
while range_start <= today:
    range_end = min(range_start + dt.timedelta(days=364), today)
    payload = {
        "query": query,
        "variables": {
            "login": username,
            "from": f"{range_start.isoformat()}T00:00:00Z",
            "to": f"{range_end.isoformat()}T23:59:59Z",
        },
    }
    data = github_request("https://api.github.com/graphql", payload)
    if data.get("errors"):
        raise RuntimeError("GitHub could not return lifetime contribution data")
    weeks = data["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]["weeks"]
    counts.update(
        {
            day["date"]: day["contributionCount"]
            for week in weeks
            for day in week["contributionDays"]
        }
    )
    range_start = range_end + dt.timedelta(days=1)

months = []
month_cursor = created.replace(day=1)
while month_cursor <= today:
    months.append(month_cursor)
    if month_cursor.month == 12:
        month_cursor = dt.date(month_cursor.year + 1, 1, 1)
    else:
        month_cursor = dt.date(month_cursor.year, month_cursor.month + 1, 1)

values = []
for month in months:
    next_month = (
        dt.date(month.year + 1, 1, 1)
        if month.month == 12
        else dt.date(month.year, month.month + 1, 1)
    )
    first_day = max(month, created)
    last_day = min(next_month - dt.timedelta(days=1), today)
    values.append(
        sum(
            counts.get((first_day + dt.timedelta(days=offset)).isoformat(), 0)
            for offset in range((last_day - first_day).days + 1)
        )
    )

maximum = max(values, default=0)
tick = max(1, math.ceil(maximum / 4))
ceiling = tick * 4
width, height = 900, 270
left, top, plot_width, plot_height = 60, 66, 810, 154
point_denominator = max(1, len(values) - 1)
points = [
    (
        left + index * plot_width / point_denominator,
        top + plot_height - value * plot_height / ceiling,
    )
    for index, value in enumerate(values)
]
line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
area = f"{left},{top + plot_height} {line} {left + plot_width},{top + plot_height}"
total = sum(values)
created_label = created.strftime("%b %-d, %Y")

parts = [
    f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(username)} lifetime contribution activity</title>
<desc id="desc">Monthly public GitHub contributions from {created} to {today}. Total: {total}.</desc>
<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8250df" stop-opacity=".28"/><stop offset="100%" stop-color="#8250df" stop-opacity=".03"/></linearGradient></defs>
<rect x=".5" y=".5" width="899" height="269" rx="8" fill="#ffffff" stroke="#d0d7de"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
<text x="450" y="29" text-anchor="middle" font-size="16" font-weight="600" fill="#24292f">Lifetime Contribution Activity</text>
<text x="450" y="48" text-anchor="middle" font-size="11" fill="#57606a">{total} public contributions since {created_label}</text>'''
]

for index in range(5):
    y = top + plot_height - index * plot_height / 4
    parts.append(
        f'<path d="M{left} {y}H{left + plot_width}" stroke="#d8dee4"/>'
        f'<text x="{left - 12}" y="{y + 4}" text-anchor="end" fill="#57606a" font-size="11">{tick * index}</text>'
    )

label_every = max(1, math.ceil(len(months) / 8))
label_indexes = set(range(0, len(months), label_every)) | {len(months) - 1}
for index in sorted(label_indexes):
    x = points[index][0]
    label = months[index].strftime("%b %Y")
    parts.append(
        f'<path d="M{x} {top}V{top + plot_height}" stroke="#d8dee4" stroke-opacity=".65"/>'
        f'<text x="{x}" y="243" text-anchor="middle" fill="#57606a" font-size="10">{label}</text>'
    )

parts.extend(
    [
        f'<polygon points="{area}" fill="url(#fill)"/>',
        f'<polyline points="{line}" fill="none" stroke="#8250df" stroke-width="2.5" stroke-linejoin="round"/>',
    ]
)
for (x, y), value, month in zip(points, values, months):
    parts.append(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#bf91f3" stroke="#8250df" stroke-width="1">'
        f'<title>{month.strftime("%B %Y")}: {value} contributions</title></circle>'
    )

parts.append("</g></svg>")
Path("dist").mkdir(exist_ok=True)
Path("dist/activity.svg").write_text("\n".join(parts))
print(
    f"Generated lifetime activity chart for {username}: "
    f"{total} contributions across {len(months)} months."
)

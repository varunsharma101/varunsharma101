import datetime as dt
import html
import json
import math
import os
from pathlib import Path
import urllib.request

username = os.environ.get('GITHUB_REPOSITORY_OWNER', 'varunsharma101')
today = dt.datetime.now(dt.timezone.utc).date()
start = today - dt.timedelta(days=30)
query = '''query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}'''
payload = {'query': query, 'variables': {'login': username,
    'from': f'{start.isoformat()}T00:00:00Z', 'to': f'{today.isoformat()}T23:59:59Z'}}
request = urllib.request.Request('https://api.github.com/graphql',
    data=json.dumps(payload).encode(), headers={
        'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
        'Content-Type': 'application/json', 'User-Agent': 'github-profile-activity'})
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)
if data.get('errors'):
    raise RuntimeError('GitHub could not return contribution calendar data.')
weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
counts = {d['date']: d['contributionCount'] for w in weeks for d in w['contributionDays']}
dates = [start + dt.timedelta(days=i) for i in range(31)]
values = [counts.get(d.isoformat(), 0) for d in dates]
maximum = max(values)
tick = max(1, math.ceil(maximum / 4))
ceiling = tick * 4
width, height = 900, 270
left, top, plot_w, plot_h = 60, 66, 810, 154
points = [(left + i * plot_w / 30, top + plot_h - value * plot_h / ceiling) for i, value in enumerate(values)]
line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
area = f'{left},{top+plot_h} ' + line + f' {left+plot_w},{top+plot_h}'
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(username)} contribution activity</title>
<desc id="desc">Daily GitHub contributions from {start} to {today}. Total: {sum(values)}.</desc>
<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#70a5fd" stop-opacity=".35"/><stop offset="100%" stop-color="#70a5fd" stop-opacity=".02"/></linearGradient></defs>
<rect x=".5" y=".5" width="899" height="269" rx="8" fill="#1a1b27" stroke="#414868"/>
<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
<text x="450" y="29" text-anchor="middle" font-size="16" font-weight="600" fill="#70a5fd">Contribution Activity</text>
<text x="450" y="48" text-anchor="middle" font-size="11" fill="#9aa5ce">{sum(values)} contributions over the last 31 days</text>''']
for i in range(5):
    y = top + plot_h - i * plot_h / 4
    parts.append(f'<path d="M{left} {y}H{left+plot_w}" stroke="#414868" stroke-opacity=".6"/><text x="{left-12}" y="{y+4}" text-anchor="end" fill="#9aa5ce" font-size="11">{tick*i}</text>')
for i in range(0,31,5):
    x=points[i][0]
    label=dates[i].strftime('%b %d')
    parts.append(f'<path d="M{x} {top}V{top+plot_h}" stroke="#414868" stroke-opacity=".35"/><text x="{x}" y="243" text-anchor="middle" fill="#9aa5ce" font-size="11">{label}</text>')
parts.extend([f'<polygon points="{area}" fill="url(#fill)"/>', f'<polyline points="{line}" fill="none" stroke="#70a5fd" stroke-width="2" stroke-linejoin="round"/>'])
for (x,y),value,date in zip(points,values,dates):
    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="#bf91f3"><title>{date}: {value} contributions</title></circle>')
parts.append('</g></svg>')
Path('dist').mkdir(exist_ok=True)
Path('dist/activity.svg').write_text('\n'.join(parts))
print(f'Generated activity chart for {username}: {sum(values)} contributions across 31 days.')

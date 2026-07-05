#!/usr/bin/env python3
"""
Fast Wikipedia data scraper for 2026 FIFA World Cup.
Fetches the entire page in ONE request, then parses all group tables.
Zero dependencies beyond stdlib. Runs in <5 seconds.
"""

import json
import re
import sys
import os
import subprocess
import urllib.parse
import html as html_mod

WIKI_API = "https://en.wikipedia.org/w/api.php"
PAGE = "2026_FIFA_World_Cup"


def fetch_full_page_html() -> str:
    """Fetch the full parsed HTML of the Wikipedia page in one request using curl."""
    params = {
        "action": "parse",
        "page": PAGE,
        "prop": "text",
        "format": "json",
    }
    qs = urllib.parse.urlencode(params)
    url = f"{WIKI_API}?{qs}"
    
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", url],
        capture_output=True, text=True, timeout=35
    )
    if result.returncode != 0:
        print(f"curl failed: {result.stderr}", file=sys.stderr)
        return ""
    
    data = json.loads(result.stdout)
    return data.get("parse", {}).get("text", {}).get("*", "")


def parse_group_name(heading_html: str) -> str | None:
    """Extract 'Group X' from a heading element like <h3>Group A</h3>."""
    m = re.search(r'<h\d[^>]*>\s*Group\s+([A-L])\s*</h\d', heading_html, re.IGNORECASE)
    if m:
        return f"Group {m.group(1)}"
    # Also try with span
    m = re.search(r'id="Group_([A-L])"', heading_html)
    if m:
        return f"Group {m.group(1)}"
    return None


def parse_standings_table(table_html: str) -> list[dict]:
    """Parse a single Wikipedia standings table."""
    rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
    results = []
    
    for row in rows:
        cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', row, re.DOTALL)
        if not cells or len(cells) < 2:
            continue
        
        # Clean each cell
        cleaned = []
        for cell in cells:
            # Remove nested tables (sometimes stats are in inner tables)
            text = re.sub(r'<table[^>]*>.*?</table>', '', cell, flags=re.DOTALL)
            # Remove style tags
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            # Keep <a> text, remove tags
            text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text)
            # Remove span/img/sup/sub and other tags
            text = re.sub(r'<(?:span|img|sup|sub|abbr|small|b|i|br)[^>]*/?>', '', text)
            text = re.sub(r'<[^>]+>', '', text)
            # Remove Wikipedia reference brackets
            text = re.sub(r'\[[a-z]+\]', '', text)
            # Decode HTML entities like &#160; &amp; etc
            text = html_mod.unescape(text)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            text = text.strip('\'"')
            if text:
                cleaned.append(text)
        
        # Skip header rows
        first = cleaned[0].lower() if cleaned else ''
        if first in ('pos', 'position', 'rk', 'rank', 'vte', ''):
            continue
        
        # Need at least position, team name, and some stats
        if len(cleaned) < 3:
            continue
        
        try:
            team_name = cleaned[1]
            # Strip qualification markers like (H), (Q), etc.
            team_name = re.sub(r'\s*\([A-Z]\)', '', team_name).strip()
            
            # Extract numbers — handle unicode minus (−), plus signs, etc.
            def extract_num(s):
                # Replace unicode minus with regular dash
                s = str(s).replace('\u2212', '-').replace('\u2013', '-').replace('\u2014', '-')
                s = s.replace('+', '')
                m = re.search(r'(-?\d+)', s)
                return int(m.group(1)) if m else 0
            
            pos = extract_num(cleaned[0])
            pld = extract_num(cleaned[2]) if len(cleaned) > 2 else 0
            won = extract_num(cleaned[3]) if len(cleaned) > 3 else 0
            drawn = extract_num(cleaned[4]) if len(cleaned) > 4 else 0
            lost = extract_num(cleaned[5]) if len(cleaned) > 5 else 0
            gf = extract_num(cleaned[6]) if len(cleaned) > 6 else 0
            ga = extract_num(cleaned[7]) if len(cleaned) > 7 else 0
            # GD might be in its own column or computed
            gd = extract_num(cleaned[8]) if len(cleaned) > 8 else (gf - ga)
            pts = extract_num(cleaned[9]) if len(cleaned) > 9 else 0
            
            # Validate: skip rows that don't look like team standings
            if pld == 0 and pos > 4:
                continue
            if not team_name or len(team_name) < 2:
                continue
            
            results.append({
                "pos": pos,
                "team": team_name,
                "played": pld,
                "won": won,
                "drawn": drawn,
                "lost": lost,
                "gf": gf,
                "ga": ga,
                "gd": gd,
                "pts": pts,
            })
        except (IndexError, ValueError):
            continue
    
    return results


def get_flag_emoji(team_name: str) -> str:
    """Map team names to flag emojis."""
    FLAGS = {
        "Canada": "🇨🇦", "Mexico": "🇲🇽", "United States": "🇺🇸",
        "Japan": "🇯🇵", "South Korea": "🇰🇷", "Iran": "🇮🇷",
        "Saudi Arabia": "🇸🇦", "Australia": "🇦🇺", "China": "🇨🇳",
        "Qatar": "🇶🇦", "United Arab Emirates": "🇦🇪", "Uzbekistan": "🇺🇿",
        "Iraq": "🇮🇶", "Oman": "🇴🇲",
        "Morocco": "🇲🇦", "Senegal": "🇸🇳", "Nigeria": "🇳🇬", "Egypt": "🇪🇬",
        "Ghana": "🇬🇭", "Algeria": "🇩🇿", "Ivory Coast": "🇨🇮", "Cameroon": "🇨🇲",
        "Tunisia": "🇹🇳", "South Africa": "🇿🇦", "Mali": "🇲🇱",
        "DR Congo": "🇨🇩", "Burkina Faso": "🇧🇫",
        "Costa Rica": "🇨🇷", "Panama": "🇵🇦", "Jamaica": "🇯🇲",
        "Honduras": "🇭🇳", "El Salvador": "🇸🇻",
        "Brazil": "🇧🇷", "Argentina": "🇦🇷", "Uruguay": "🇺🇾",
        "Colombia": "🇨🇴", "Ecuador": "🇪🇨", "Peru": "🇵🇪",
        "Chile": "🇨🇱", "Paraguay": "🇵🇾", "Venezuela": "🇻🇪",
        "Bolivia": "🇧🇴",
        "New Zealand": "🇳🇿", "Fiji": "🇫🇯",
        "France": "🇫🇷", "Spain": "🇪🇸", "England": "🏴", "Germany": "🇩🇪",
        "Italy": "🇮🇹", "Netherlands": "🇳🇱", "Portugal": "🇵🇹",
        "Belgium": "🇧🇪", "Croatia": "🇭🇷", "Denmark": "🇩🇰",
        "Switzerland": "🇨🇭", "Serbia": "🇷🇸", "Poland": "🇵🇱",
        "Ukraine": "🇺🇦", "Sweden": "🇸🇪", "Norway": "🇳🇴",
        "Austria": "🇦🇹", "Scotland": "🏴", "Wales": "🏴",
        "Turkey": "🇹🇷", "Czech Republic": "🇨🇿", "Hungary": "🇭🇺",
        "Romania": "🇷🇴", "Slovakia": "🇸🇰", "Greece": "🇬🇷",
        "Korea Republic": "🇰🇷", "IR Iran": "🇮🇷",
        "Côte d'Ivoire": "🇨🇮", "USA": "🇺🇸",
    }
    return FLAGS.get(team_name, "🏳️")


def main():
    print("📡 Fetching 2026 FIFA World Cup page from Wikipedia...")
    html = fetch_full_page_html()
    print(f"   Got {len(html):,} chars of HTML")
    
    # Find all group headings and their following tables
    # Pattern: heading with "Group X" followed by a wikitable
    standings = {}
    
    # Split the HTML by group headings
    # First, find all positions of "Group_" IDs
    group_pattern = re.compile(
        r'<h[234][^>]*>\s*(?:<span[^>]*>\s*)*Group\s+([A-L])\s*(?:</span>\s*)*</h[234]>',
        re.IGNORECASE
    )
    
    # Alternative: find by anchor IDs
    sections = re.split(
        r'(<h[234][^>]*id="Group_[A-L]"[^>]*>.*?</h[234]>)',
        html
    )
    
    current_group = None
    
    for i, part in enumerate(sections):
        # Check if this is a group heading
        m = re.search(r'id="Group_([A-L])"', part)
        if m:
            current_group = f"Group {m.group(1)}"
            continue
        
        if current_group and part:
            # Find all wikitables in this section
            tables = re.findall(
                r'<table[^>]*class="wikitable[^"]*"[^>]*>(.*?)</table>',
                part, re.DOTALL
            )
            
            if tables:
                # The first wikitable after a group heading is the standings table
                team_rows = parse_standings_table(tables[0])
                if team_rows and len(team_rows) >= 2:
                    standings[current_group] = team_rows
                    print(f"  {current_group}: {len(team_rows)} teams")
                    current_group = None  # Only take first table per section
    
    if not standings:
        print("❌ No standings found! Trying fallback method...", file=sys.stderr)
        # Fallback: find all wikitables and try to match them to groups
        all_tables = re.findall(
            r'<table[^>]*class="wikitable[^"]*"[^>]*>(.*?)</table>',
            html, re.DOTALL
        )
        print(f"  Found {len(all_tables)} wikitables on the page")
        
        # The first N tables after the group stage heading are likely our groups
        groups_order = ["Group A", "Group B", "Group C", "Group D", 
                       "Group E", "Group F", "Group G", "Group H",
                       "Group I", "Group J", "Group K", "Group L"]
        
        # Find where "Group stage" section starts
        gs_idx = html.find('id="Group_stage"')
        if gs_idx > 0:
            post_gs = html[gs_idx:]
            post_tables = re.findall(
                r'<table[^>]*class="wikitable[^"]*"[^>]*>(.*?)</table>',
                post_gs, re.DOTALL
            )
            for j, table in enumerate(post_tables[:12]):
                rows = parse_standings_table(table)
                if rows and len(rows) >= 2:
                    gname = groups_order[j] if j < 12 else f"Group {j+1}"
                    standings[gname] = rows
                    print(f"  {gname}: {len(rows)} teams (fallback)")
    
    if not standings:
        print("❌ Failed to fetch any standings data!", file=sys.stderr)
        sys.exit(1)
    
    # Extract teams
    teams = []
    seen = set()
    for group_name, entries in standings.items():
        for entry in entries:
            name = entry["team"]
            if name not in seen:
                seen.add(name)
                teams.append({
                    "name": name,
                    "group": group_name,
                    "flag": get_flag_emoji(name),
                })
    
    # Write output
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    from datetime import datetime, timezone
    output = {
        "standings": standings,
        "teams": teams,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    
    outpath = os.path.join(data_dir, "data.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(teams)} teams across {len(standings)} groups")
    print(f"   Saved to {outpath}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Collect public RSS technology news and GitHub Trending snapshots."""
from __future__ import annotations
import json, os, re, time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
HEADERS = {"User-Agent": "TechRadarBot/1.0 (personal public technology digest; source links retained)", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
FEEDS = [
    ("GitHub Blog", "https://github.blog/feed/"),
    ("Microsoft Azure Blog", "https://azure.microsoft.com/en-us/blog/feed/"),
    ("Microsoft DevBlogs", "https://devblogs.microsoft.com/feed/"),
    ("Google Developers Blog", "https://developers.googleblog.com/feeds/posts/default?alt=rss"),
    ("AWS Developer Tools Blog", "https://aws.amazon.com/blogs/developer/feed/"),
    ("Cloudflare Blog", "https://blog.cloudflare.com/rss/"),
    ("Vercel Blog", "https://vercel.com/atom"),
    ("Hacker News", "https://news.ycombinator.com/rss"),
    ("OpenAI News", "https://openai.com/news/rss.xml"),
]
KEYWORDS = {
    "AI & Agents": ["ai", "artificial intelligence", "llm", "agent", "model", "inference", "machine learning", "openai", "anthropic", "gemini"],
    "Developer Tools": ["developer", "coding", "code", "ide", "github", "copilot", "terminal", "framework", "typescript", "javascript", "python"],
    "Cloud & DevOps": ["cloud", "azure", "aws", "kubernetes", "docker", "devops", "deploy", "serverless", "infrastructure", "ci/cd"],
    "Security": ["security", "vulnerability", "cve", "authentication", "cybersecurity", "privacy", "patch"],
    "Data & Databases": ["database", "postgres", "sql", "data", "analytics", "vector", "supabase"],
    "Open Source": ["open source", "release", "repository", "github", "linux", "maintainer"],
}

def clean(value: str) -> str:
    value = BeautifulSoup(unescape(value or ""), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", value).strip()

def categorize(text: str) -> str:
    lower = text.lower()
    for category, words in KEYWORDS.items():
        if any(word in lower for word in words):
            return category
    return "Technology"

def load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def get(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=22)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        print(f"WARN fetch failed {url}: {exc}")
        return None

def collect_feed_items() -> list[dict]:
    items, seen = [], set()
    for source, feed_url in FEEDS:
        response = get(feed_url)
        if response is None:
            continue
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            print(f"WARN invalid feed {feed_url}: {exc}")
            continue
        for entry in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            def field(names):
                for name in names:
                    node = entry.find(name)
                    if node is not None:
                        if name.endswith("}link") and node.attrib.get("href"):
                            return node.attrib["href"]
                        if node.text:
                            return node.text
                return ""
            title = clean(field(["title", "{http://www.w3.org/2005/Atom}title"]))
            link = field(["link", "{http://www.w3.org/2005/Atom}link"])
            if not link:
                link_node = entry.find("{http://www.w3.org/2005/Atom}link")
                link = link_node.attrib.get("href", "") if link_node is not None else ""
            link = link.strip()
            description = clean(field(["description", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"]))
            published = clean(field(["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"]))
            if not title or not link or link in seen:
                continue
            if urlparse(link).scheme not in ("https", "http"):
                continue
            seen.add(link)
            summary = description[:360].rstrip()
            if len(description) > 360:
                summary = summary.rsplit(" ", 1)[0] + "…"
            items.append({"title": title, "summary": summary or "Open the original source for the full announcement and technical details.", "description": description, "url": link, "source": source, "published": published, "category": categorize(title + " " + description)})
    items.sort(key=lambda item: item.get("published", ""), reverse=True)
    return items[:90]

def collect_trending(period: str) -> list[dict]:
    url = "https://github.com/trending?since=" + period + "&spoken_language_code="
    response = get(url)
    if response is None:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    found = []
    for article in soup.select("article.Box-row"):
        heading = article.select_one("h2 a")
        if not heading:
            continue
        path = heading.get("href", "").strip("/")
        parts = path.split("/")
        if len(parts) != 2:
            continue
        full_name = "/".join(parts)
        link = "https://github.com/" + full_name
        description_node = article.select_one("p")
        description = clean(description_node.get_text(" ", strip=True)) if description_node else ""
        language_node = article.select_one('[itemprop="programmingLanguage"]')
        language = clean(language_node.get_text(" ", strip=True)) if language_node else ""
        stars_node = article.select_one('a[href$="/stargazers"]')
        stars = clean(stars_node.get_text(" ", strip=True)) if stars_node else ""
        period_node = article.select_one("span.d-inline-block.float-sm-right")
        period_stars = clean(period_node.get_text(" ", strip=True)) if period_node else ""
        found.append({"name": full_name.split("/")[-1], "full_name": full_name, "description": description, "url": link, "language": language, "stars_label": stars or "See GitHub", "period_stars": period_stars, "trend_period": period.capitalize()})
    print(f"GitHub trending {period}: {len(found)} repositories parsed")
    return found

def collect_developers() -> list[dict]:
    response = get("https://github.com/trending/developers")
    if response is None:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    found, seen = [], set()
    for row in soup.select("article.Box-row"):
        link = row.select_one('h1 a, h2 a, a[href^="/"]')
        if not link:
            continue
        href = link.get("href", "").strip("/")
        username = href.split("/")[0]
        if not username or username in seen or username in ("trending", "features", "topics"):
            continue
        seen.add(username)
        name_node = row.select_one("h1, h2")
        name = clean(name_node.get_text(" ", strip=True)) if name_node else username
        found.append({"name": name, "username": username, "url": "https://github.com/" + username})
        if len(found) >= 20:
            break
    print(f"GitHub trending developers: {len(found)} profiles parsed")
    return found

def main():
    DATA.mkdir(exist_ok=True)
    old_news = load_json(DATA / "tech-updates.json", {"items": []})
    old_repos = load_json(DATA / "github-repositories.json", {"items": [], "developers": []})
    history = load_json(DATA / "history.json", {"seen_repositories": []})
    news_items = collect_feed_items()
    if not news_items:
        print("WARN no feed succeeded; keeping previous news data")
        news_items = old_news.get("items", [])
    save_json(DATA / "tech-updates.json", {"updated_at": NOW, "items": news_items})

    candidates = []
    candidate_urls = set()
    # Daily trends first, then weekly and monthly; only new repositories are featured.
    for period in ("daily", "weekly", "monthly"):
        for repo in collect_trending(period):
            if repo["url"] not in candidate_urls:
                candidate_urls.add(repo["url"])
                candidates.append(repo)
        time.sleep(1)
    seen = set(history.get("seen_repositories", []))
    fresh = [repo for repo in candidates if repo["url"] not in seen]
    picks = fresh[:10]
    # Preserve the strict no-repeat rule. If fewer than 10 new candidates exist, publish fewer.
    history["seen_repositories"] = list(dict.fromkeys(history.get("seen_repositories", []) + [r["url"] for r in picks]))
    history["updated_at"] = NOW
    save_json(DATA / "history.json", history)

    developers = collect_developers()
    if not developers:
        developers = old_repos.get("developers", [])
    if not picks:
        print("WARN no unseen repository candidates; retaining current repository cards")
        # Do not blank the dashboard when every current trending repository has
        # already been featured. The saved history still prevents these cards
        # from being recommended again in a new shortlist.
        picks = old_repos.get("items", [])
    save_json(DATA / "github-repositories.json", {"updated_at": NOW, "items": picks, "developers": developers})
    print(f"Updated {len(news_items)} news items, {len(picks)} fresh repositories and {len(developers)} developer profiles at {NOW}")

if __name__ == "__main__":
    main()

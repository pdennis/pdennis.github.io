#!/usr/bin/env python3
"""
build.py — Static site generator for take.town

Reads markdown posts from _posts/, pages from pages/, renders them through
Jinja2 templates, and outputs static HTML to _site/.
"""

import os
import re
import shutil
import math
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import feedgenerator


ROOT = Path(__file__).parent
SITE_DIR = ROOT / "_site"
POSTS_DIR = ROOT / "_posts"
PAGES_DIR = ROOT / "pages"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_config():
    with open(ROOT / "site.yml") as f:
        return yaml.safe_load(f)


def parse_front_matter(text):
    """Parse YAML front matter and return (metadata_dict, body_text)."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    raw_yaml = match.group(1)
    meta = yaml.safe_load(raw_yaml) or {}
    body = text[match.end():]
    return meta, body


def normalize_meta(meta):
    """Handle capitalized front matter keys (Title, Date) from Telegram bot."""
    result = {}
    for key, value in meta.items():
        result[key.lower()] = value
    return result


def parse_date(date_val):
    """Parse a date from front matter. Accepts str, datetime, or date."""
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, date):
        return datetime(date_val.year, date_val.month, date_val.day)
    if isinstance(date_val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_val.strip(), fmt)
            except ValueError:
                continue
    return datetime.now()


def make_slug(filename):
    """Convert _posts filename to URL slug.
    e.g. '2022-11-06-Why-Did-I-Build-This-Site?.md' -> 'Why-Did-I-Build-This-Site'
    """
    name = Path(filename).stem  # strip .md
    # Remove leading date (YYYY-MM-DD-)
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    # Remove characters not safe for URLs
    name = re.sub(r"[?]", "", name)
    return name


def generate_excerpt(html_body, length=200):
    """Strip tags and return first `length` characters."""
    text = re.sub(r"<[^>]+>", "", html_body)
    text = text.strip()
    if len(text) > length:
        return text[:length].rsplit(" ", 1)[0] + "..."
    return text


def load_posts():
    """Load and parse all posts from _posts/."""
    md = markdown.Markdown(extensions=["fenced_code", "codehilite", "tables", "toc"])
    posts = []

    if not POSTS_DIR.exists():
        return posts

    for filepath in sorted(POSTS_DIR.glob("*.md")):
        raw = filepath.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)
        meta = normalize_meta(meta)

        title = meta.get("title", "Untitled")
        if title == "null" or title is None:
            continue  # skip broken posts

        date = parse_date(meta.get("date", ""))
        slug = make_slug(filepath.name)
        url = f"/posts/{slug}/"

        md.reset()
        html_body = md.convert(body)
        excerpt = generate_excerpt(html_body)

        posts.append({
            "title": title,
            "date": date,
            "date_str": date.strftime("%Y-%m-%d"),
            "slug": slug,
            "url": url,
            "body": html_body,
            "excerpt": excerpt,
        })

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def load_pages():
    """Load and parse all pages from pages/."""
    md = markdown.Markdown(extensions=["fenced_code", "codehilite", "tables", "toc"])
    pages = []

    if not PAGES_DIR.exists():
        return pages

    for filepath in sorted(PAGES_DIR.glob("*.md")):
        raw = filepath.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)
        meta = normalize_meta(meta)

        title = meta.get("title", filepath.stem.title())
        permalink = meta.get("permalink", f"/{filepath.stem}/")

        md.reset()
        html_body = md.convert(body)

        pages.append({
            "title": title,
            "permalink": permalink,
            "body": html_body,
        })

    return pages


def copy_assets():
    """Copy static assets to _site/."""
    dest = SITE_DIR / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ASSETS_DIR, dest)


def copy_cname():
    """Copy CNAME file if it exists."""
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, SITE_DIR / "CNAME")


def generate_feed(config, posts):
    """Generate RSS feed at _site/feed.xml."""
    feed = feedgenerator.Rss201rev2Feed(
        title=config["title"],
        link=config["url"],
        description=config["description"],
        language="en",
    )
    for post in posts[:20]:
        post_date = post["date"]
        if post_date.tzinfo is None:
            post_date = post_date.replace(tzinfo=timezone.utc)
        feed.add_item(
            title=post["title"],
            link=config["url"] + post["url"],
            description=post["excerpt"],
            pubdate=post_date,
        )
    feed_path = SITE_DIR / "feed.xml"
    with open(feed_path, "w", encoding="utf-8") as f:
        feed.write(f, "utf-8")


def generate_sitemap(config, posts, pages):
    """Generate a simple sitemap.xml."""
    urls = [config["url"] + "/"]
    for page in pages:
        urls.append(config["url"] + page["permalink"])
    for post in posts:
        urls.append(config["url"] + post["url"])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")

    sitemap_path = SITE_DIR / "sitemap.xml"
    sitemap_path.write_text("\n".join(lines), encoding="utf-8")


def build():
    config = load_config()
    posts = load_posts()
    pages = load_pages()

    # Set up Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    env.globals["site"] = config
    env.globals["pages"] = pages

    # Clean and create output dir
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir()

    # Copy static assets and CNAME
    copy_assets()
    copy_cname()

    # Build paginated home pages
    per_page = config.get("posts_per_page", 10)
    total_pages = max(1, math.ceil(len(posts) / per_page))
    home_tmpl = env.get_template("home.html")

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * per_page
        page_posts = posts[start : start + per_page]

        html = home_tmpl.render(
            posts=page_posts,
            current_page=page_num,
            total_pages=total_pages,
            all_posts=posts,
        )

        if page_num == 1:
            out = SITE_DIR / "index.html"
        else:
            out = SITE_DIR / "page" / str(page_num) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)

        out.write_text(html, encoding="utf-8")

    # Build individual posts
    post_tmpl = env.get_template("post.html")
    for post in posts:
        html = post_tmpl.render(post=post)
        out = SITE_DIR / "posts" / post["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    # Build pages
    page_tmpl = env.get_template("page.html")
    for page in pages:
        html = page_tmpl.render(page=page)
        permalink = page["permalink"].strip("/")
        if permalink:
            out = SITE_DIR / permalink / "index.html"
        else:
            out = SITE_DIR / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    # Generate feed and sitemap
    generate_feed(config, posts)
    generate_sitemap(config, posts, pages)

    print(f"Built {len(posts)} posts, {len(pages)} pages, {total_pages} home page(s)")
    print(f"Output: {SITE_DIR}/")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Scrape all Real Don Music lyrics from Bandcamp."""

import json
import os
import re
import time
import urllib.request
from html import unescape
from html.parser import HTMLParser

BASE = "https://realdonmusic.bandcamp.com"

ALBUM_PAGES = [
    "/album/pet-care-or-the-righteous-one-takes-care-of-their-animal",
    "/album/dank-zappa-ep",
    "/album/dank-sinatra-ep",
]

SINGLE_PAGES = [
    "/track/free-dogs-leave-marks",
    "/track/wired-and-wide-awake",
    "/track/outlook-not-so-good",
    "/track/eyes-on-me",
    "/track/got-one",
    "/track/crazy-bob",
    "/track/downwinders",
    "/track/for-real",
    "/track/born-on-inauguration-day",
    "/track/smoke-by-day",
    "/track/emeralds-and-angels",
]


class LyricsParser(HTMLParser):
    """Extract text content from the lyricsText div only."""

    def __init__(self):
        super().__init__()
        self._in_lyrics = False
        self._depth = 0
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if "lyricsText" in cls:
            self._in_lyrics = True
            self._depth = 1
            return
        if self._in_lyrics:
            self._depth += 1
            if tag == "br":
                self._chunks.append("\n")

    def handle_endtag(self, tag):
        if self._in_lyrics:
            self._depth -= 1
            if self._depth <= 0:
                self._in_lyrics = False

    def handle_data(self, data):
        if self._in_lyrics:
            self._chunks.append(data)

    @property
    def lyrics(self):
        raw = "".join(self._chunks)
        lines = raw.split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            # Stop at JS artifacts from Bandcamp's truncation script
            if "$(" in line or "bcTruncate" in line or "TruncateProfile" in line:
                break
            cleaned.append(line)
        # Remove trailing blanks
        while cleaned and not cleaned[-1]:
            cleaned.pop()
        return "\n".join(cleaned).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_track_links_from_album(html):
    raw = re.findall(r'href="(/track/[^"#?]+)"', html)
    return list(set(raw))


def extract_title(html):
    m = re.search(r'<h2 class="trackTitle">\s*(.+?)\s*</h2>', html, re.S)
    if m:
        return unescape(m.group(1).strip())
    return None


def extract_album_from_ld_json(html):
    """Extract album name from the LD+JSON structured data."""
    m = re.search(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        if "inAlbum" in data:
            album = data["inAlbum"]
            if isinstance(album, dict):
                return album.get("name")
            return str(album)
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def extract_album_from_page(html):
    m = re.search(r'<h2 class="trackTitle">\s*(.+?)\s*</h2>', html, re.S)
    if m:
        return unescape(m.group(1).strip())
    return None


def extract_lyrics(html):
    parser = LyricsParser()
    parser.feed(html)
    text = parser.lyrics
    return text if text else None


def extract_release_date(html):
    m = re.search(r'released\s+(\w+ \d+,\s*\d{4})', html)
    if m:
        return m.group(1).strip()
    return None


def main():
    # Collect track URLs from albums
    track_paths = set()
    album_track_map = {}

    for page in ALBUM_PAGES:
        url = BASE + page
        print(f"Fetching album: {url}")
        html = fetch(url)
        album_name = extract_album_from_page(html)
        links = get_track_links_from_album(html)
        for link in links:
            track_paths.add(link)
            if album_name:
                album_track_map[link] = album_name
        print(f"  {album_name} ({len(links)} tracks)")
        time.sleep(0.5)

    for page in SINGLE_PAGES:
        track_paths.add(page)

    print(f"\n{len(track_paths)} unique tracks to fetch\n")

    # Fetch each track
    results = []
    for path in sorted(track_paths):
        url = BASE + path
        slug = path.split("/")[-1]
        print(f"  {slug}...", end=" ", flush=True)
        html = fetch(url)

        title = extract_title(html) or slug.replace("-", " ").title()
        album = album_track_map.get(path) or extract_album_from_ld_json(html)
        lyrics = extract_lyrics(html)
        release_date = extract_release_date(html)

        results.append({
            "title": title,
            "album": album,
            "url": url,
            "slug": slug,
            "release_date": release_date,
            "has_lyrics": bool(lyrics),
            "lyrics": lyrics,
        })

        if lyrics:
            print(f"LYRICS ({len(lyrics.splitlines())} lines)")
        else:
            print("(no lyrics)")
        time.sleep(0.3)

    # Deduplicate: if same title appears as both single and album track, prefer album version
    seen = {}
    deduped = []
    for r in results:
        key = r["title"].lower()
        if key in seen:
            existing = seen[key]
            # Prefer the one with an album, or the one with lyrics
            if r["album"] and not existing["album"]:
                deduped.remove(existing)
                deduped.append(r)
                seen[key] = r
            elif r["has_lyrics"] and not existing["has_lyrics"]:
                deduped.remove(existing)
                deduped.append(r)
                seen[key] = r
            # else skip duplicate
        else:
            seen[key] = r
            deduped.append(r)

    results = deduped

    # Summary
    with_lyrics = [r for r in results if r["has_lyrics"]]
    without_lyrics = [r for r in results if not r["has_lyrics"]]

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(results)} unique songs")
    print(f"  With lyrics: {len(with_lyrics)}")
    print(f"  Without:     {len(without_lyrics)}")
    print(f"{'='*60}")

    if with_lyrics:
        print("\nSongs WITH lyrics:")
        for r in with_lyrics:
            print(f"  + {r['title']} ({r['album'] or 'Single'})")

    if without_lyrics:
        print("\nSongs WITHOUT lyrics on Bandcamp:")
        for r in without_lyrics:
            print(f"  - {r['title']} ({r['album'] or 'Single'})")

    # Save JSON
    out_path = "/tmp/realdonmusic_lyrics.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON: {out_path}")

    # Save markdown files
    md_dir = "/tmp/realdonmusic_lyrics"
    if os.path.exists(md_dir):
        for fname in os.listdir(md_dir):
            os.remove(os.path.join(md_dir, fname))
    os.makedirs(md_dir, exist_ok=True)

    for r in results:
        if not r["has_lyrics"]:
            continue
        md_path = os.path.join(md_dir, f"{r['slug']}.md")
        with open(md_path, "w") as f:
            f.write("---\n")
            f.write(f'title: "{r["title"]}"\n')
            if r["album"]:
                f.write(f'album: "{r["album"]}"\n')
            if r["release_date"]:
                f.write(f'releaseDate: "{r["release_date"]}"\n')
            f.write(f'bandcampUrl: "{r["url"]}"\n')
            f.write("---\n\n")
            f.write(r["lyrics"])
            f.write("\n")

    print(f"Markdown files: {md_dir}/ ({len(with_lyrics)} files)")


if __name__ == "__main__":
    main()

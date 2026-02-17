#!/usr/bin/env python3
"""Scrape album/track art from Real Don Music's Bandcamp."""

import json
import os
import re
import urllib.request

BANDCAMP_URL = "https://realdonmusic.bandcamp.com"
OUT_DIR = "/Users/dan/dev/realdonmusic/lyrics/public/images/covers"

os.makedirs(OUT_DIR, exist_ok=True)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_binary(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"['']+", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def get_all_release_urls():
    """Get all album and track URLs from the music page."""
    html = fetch(BANDCAMP_URL + "/music")
    links = []
    seen = set()
    for match in re.finditer(r'href="(/(?:album|track)/[^"]+)"', html):
        path = match.group(1).split("?")[0].split("#")[0].rstrip("/")
        url = BANDCAMP_URL + path
        if url not in seen:
            seen.add(url)
            links.append(url)
    return links


def get_art_url(page_url):
    """Extract album art URL from a Bandcamp page using tralbumArt img tag.
    Returns the _10 size (1200x1200) for high resolution."""
    html = fetch(page_url)
    # Primary: tralbumArt div contains the actual album art
    match = re.search(
        r'<div id="tralbumArt"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.S
    )
    if match:
        art_url = match.group(1)
        # Replace size code with _10 for 1200x1200
        return re.sub(r"_\d+\.(\w+)$", r"_10.\1", art_url)
    # Fallback: popupImage link (already _10)
    match = re.search(r'class="popupImage"[^>]*href="([^"]+)"', html)
    if match:
        return match.group(1)
    return None


def main():
    print("Fetching release URLs...")
    urls = get_all_release_urls()
    print(f"Found {len(urls)} releases\n")

    # Track unique art URLs to avoid duplicate downloads
    seen_art = {}  # art_url -> filename
    results = {}

    for url in urls:
        name = url.rstrip("/").split("/")[-1]
        slug = slugify(name)
        is_album = "/album/" in url
        release_type = "album" if is_album else "track"
        print(f"[{release_type}] {slug}: {url}")

        art_url = get_art_url(url)
        if not art_url:
            print(f"  No art found, skipping")
            continue

        # Check if we already downloaded this exact image
        art_id = re.search(r"/img/(a?\d+)_", art_url)
        art_key = art_id.group(1) if art_id else art_url

        if art_key in seen_art:
            print(f"  Same art as {seen_art[art_key]}, skipping duplicate download")
            results[slug] = {
                "url": url,
                "type": release_type,
                "art": seen_art[art_key],
            }
            continue

        ext = "jpg"
        if ".png" in art_url:
            ext = "png"
        filename = f"{slug}.{ext}"
        filepath = os.path.join(OUT_DIR, filename)

        try:
            data = fetch_binary(art_url)
            with open(filepath, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  Art: {art_url}")
            print(f"  Saved: {filename} ({size_kb:.0f} KB)")
            seen_art[art_key] = filename
            results[slug] = {"url": url, "type": release_type, "art": filename}
        except Exception as e:
            print(f"  Download failed: {e}")

    # Save manifest
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved: {manifest_path}")
    print(f"Unique images downloaded: {len(seen_art)}")
    print(f"Total releases mapped: {len(results)}")


if __name__ == "__main__":
    main()

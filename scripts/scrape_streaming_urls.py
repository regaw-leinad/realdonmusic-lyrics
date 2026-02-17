#!/usr/bin/env python3
"""Find Spotify and Apple Music URLs for Real Don Music songs."""

import json
import os
import re
import urllib.request
import urllib.parse
import time

SONGS_DIR = "/Users/dan/dev/realdonmusic/lyrics/src/content/songs"
ARTIST_NAME = "Real Don Music"
SPOTIFY_ARTIST_ID = "1JrFtL3TcqqLeCYcJOoMvm"
APPLE_ARTIST_ID = "683291983"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def normalize(title):
    """Normalize a title for fuzzy matching."""
    t = title.lower().strip()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def get_apple_music_urls():
    """Use iTunes Search API to find Apple Music track URLs."""
    print("=== Apple Music (iTunes Search API) ===\n")
    url = (
        "https://itunes.apple.com/lookup"
        f"?id={APPLE_ARTIST_ID}&entity=song&limit=200"
    )
    data = fetch_json(url)
    results = data.get("results", [])

    # First result is the artist, rest are songs
    tracks = {}
    for item in results:
        if item.get("wrapperType") != "track":
            continue
        name = item.get("trackName", "")
        track_url = item.get("trackViewUrl", "")
        if name and track_url:
            key = normalize(name)
            tracks[key] = {"name": name, "url": track_url}
            print(f"  Found: {name}")

    print(f"\n  Total: {len(tracks)} tracks\n")
    return tracks


def get_spotify_urls():
    """Scrape Spotify artist page for album/track data."""
    print("=== Spotify ===\n")

    # Try to get an anonymous access token from Spotify's web player
    try:
        req = urllib.request.Request(
            "https://open.spotify.com/get_access_token?reason=transport&productType=web_player",
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        )
        token_data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        token = token_data.get("accessToken")
    except Exception as e:
        print(f"  Could not get anonymous token: {e}")
        print("  Trying album page scraping instead...\n")
        token = None

    tracks = {}

    if token:
        # Use Spotify Web API with anonymous token to get artist's albums
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"Bearer {token}",
        }

        # Get all albums
        albums_url = f"https://api.spotify.com/v1/artists/{SPOTIFY_ARTIST_ID}/albums?include_groups=album,single,ep&limit=50"
        req = urllib.request.Request(albums_url, headers=headers)
        try:
            albums_data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
            albums = albums_data.get("items", [])
            print(f"  Found {len(albums)} albums/singles/EPs\n")

            for album in albums:
                album_id = album["id"]
                album_name = album["name"]
                # Get tracks for this album
                tracks_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?limit=50"
                req = urllib.request.Request(tracks_url, headers=headers)
                try:
                    tracks_data = json.loads(
                        urllib.request.urlopen(req).read().decode("utf-8")
                    )
                    for t in tracks_data.get("items", []):
                        name = t.get("name", "")
                        track_url = t.get("external_urls", {}).get("spotify", "")
                        if name and track_url:
                            key = normalize(name)
                            tracks[key] = {
                                "name": name,
                                "url": track_url,
                                "album": album_name,
                            }
                            print(f"  Found: {name} (from {album_name})")
                except Exception as e:
                    print(f"  Error fetching tracks for {album_name}: {e}")
                time.sleep(0.2)
        except Exception as e:
            print(f"  Error fetching albums: {e}")

    print(f"\n  Total: {len(tracks)} tracks\n")
    return tracks


def get_song_files():
    """Read all song markdown files and return their titles and paths."""
    songs = []
    for fname in sorted(os.listdir(SONGS_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(SONGS_DIR, fname)
        with open(path) as f:
            content = f.read()
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.M)
        if title_match:
            songs.append(
                {"file": fname, "path": path, "title": title_match.group(1), "content": content}
            )
    return songs


def match_track(title, track_db):
    """Try to match a song title against a track database."""
    key = normalize(title)
    if key in track_db:
        return track_db[key]
    # Fuzzy: check if one contains the other
    for db_key, db_val in track_db.items():
        if key in db_key or db_key in key:
            return db_val
    return None


def update_frontmatter(content, field, value):
    """Add or update a frontmatter field."""
    if re.search(rf"^{field}:", content, re.M):
        return re.sub(rf'^{field}:.*$', f'{field}: "{value}"', content, flags=re.M)
    # Add after bandcampUrl or title
    for anchor in ["bandcampUrl", "title"]:
        if re.search(rf"^{anchor}:", content, re.M):
            return re.sub(
                rf"^({anchor}:.*)",
                rf'\1\n{field}: "{value}"',
                content,
                count=1,
                flags=re.M,
            )
    return content


def main():
    songs = get_song_files()
    print(f"Found {len(songs)} song files\n")

    apple_tracks = get_apple_music_urls()
    spotify_tracks = get_spotify_urls()

    print("=== Matching songs ===\n")
    matched = {"spotify": 0, "apple": 0}
    unmatched = []

    for song in songs:
        title = song["title"]
        content = song["content"]
        updated = False

        # Apple Music
        apple = match_track(title, apple_tracks)
        if apple:
            content = update_frontmatter(content, "appleMusicUrl", apple["url"])
            matched["apple"] += 1
            updated = True

        # Spotify
        spotify = match_track(title, spotify_tracks)
        if spotify:
            content = update_frontmatter(content, "spotifyUrl", spotify["url"])
            matched["spotify"] += 1
            updated = True

        if updated:
            with open(song["path"], "w") as f:
                f.write(content)
            status = []
            if apple:
                status.append("Apple Music")
            if spotify:
                status.append("Spotify")
            print(f"  {title}: {', '.join(status)}")
        else:
            unmatched.append(title)
            print(f"  {title}: NO MATCH")

    print(f"\nResults:")
    print(f"  Spotify: {matched['spotify']}/{len(songs)}")
    print(f"  Apple Music: {matched['apple']}/{len(songs)}")
    if unmatched:
        print(f"\n  Unmatched songs:")
        for t in unmatched:
            print(f"    - {t}")


if __name__ == "__main__":
    main()

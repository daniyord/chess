#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["chess>=1.11"]
# ///
"""Sync a local repertoire PGN into a Lichess study, one chapter per game.

Chapters are matched by their ChapterName tag. Unchanged chapters are left
alone; changed or new ones are imported and the old copy is deleted.

Token: LICHESS_TOKEN env var or ~/.config/lichess-token
(scopes study:read and study:write).
"""
import argparse
import io
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import chess.pgn

API = "https://lichess.org/api/study"
TOKEN_FILE = Path.home() / ".config" / "lichess-token"


def load_token():
    token = os.environ.get("LICHESS_TOKEN")
    if not token and TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
    if not token:
        sys.exit(f"Missing token: set LICHESS_TOKEN or write it to {TOKEN_FILE}")
    return token


def request(method, url, token, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    for attempt in range(2):
        req = urllib.request.Request(
            url, data=body, method=method, headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                # Lichess asks clients to wait a full minute after a 429.
                print("rate limited, waiting 60s...")
                time.sleep(60)
                continue
            sys.exit(f"{method} {url} -> HTTP {e.code}: {e.read().decode()[:300]}")


def read_games(text):
    stream = io.StringIO(text)
    games = []
    while (game := chess.pgn.read_game(stream)) is not None:
        games.append(game)
    return games


def moves_and_comments(game):
    # Compared through python-chess on both sides so Lichess's formatting
    # differences (spacing, NAG style) don't count as changes.
    return game.accept(chess.pgn.StringExporter(headers=False, variations=True, comments=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pgn", help="local PGN file, e.g. repertoire/white.pgn")
    parser.add_argument("study_id", help="the part of the study URL after lichess.org/study/")
    parser.add_argument("--orientation", choices=["white", "black"], default="white")
    parser.add_argument("--dry-run", action="store_true", help="only show what would change")
    parser.add_argument("--prune", action="store_true", help="delete study chapters missing from the local file")
    args = parser.parse_args()
    token = load_token()

    local = read_games(Path(args.pgn).read_text(encoding="utf-8"))
    names = [game.headers.get("ChapterName") for game in local]
    if None in names or len(set(names)) != len(names):
        sys.exit("Every game in the local PGN needs a unique ChapterName tag")

    exported = request("GET", f"{API}/{args.study_id}.pgn?clocks=false", token)
    remote = {}
    for game in read_games(exported):
        chapter_id = game.headers.get("ChapterURL", "").rstrip("/").rsplit("/", 1)[-1]
        remote.setdefault(game.headers.get("ChapterName", ""), []).append(
            (chapter_id, moves_and_comments(game))
        )

    for game, name in zip(local, names):
        existing = remote.pop(name, [])
        if len(existing) == 1 and existing[0][1] == moves_and_comments(game):
            print(f"unchanged  {name}")
            continue
        print(f"{'update' if existing else 'add':<10} {name}")
        if args.dry_run:
            continue
        # Import before deleting so the study is never left empty.
        request(
            "POST",
            f"{API}/{args.study_id}/import-pgn",
            token,
            {"pgn": str(game), "name": name, "orientation": args.orientation},
        )
        for chapter_id, _ in existing:
            request("DELETE", f"{API}/{args.study_id}/{chapter_id}", token)

    for name, chapters in remote.items():
        if not args.prune:
            print(f"untouched  {name} (not in {args.pgn}; --prune deletes it)")
            continue
        print(f"delete     {name}")
        if not args.dry_run:
            for chapter_id, _ in chapters:
                request("DELETE", f"{API}/{args.study_id}/{chapter_id}", token)


if __name__ == "__main__":
    main()

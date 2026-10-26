# Chess repertoire

Opening repertoire PGNs in `repertoire/`, synced to Lichess studies with
`tools/lichess_sync.py`.

## Setup

- Install [uv](https://docs.astral.sh/uv/). The script declares its own
  dependencies, so there's no virtualenv to set up.
- Create a Lichess API token at
  <https://lichess.org/account/oauth/token/create>. Tick **Read private
  studies and broadcasts** (`study:read`) and **Create, update, delete
  studies and broadcasts** (`study:write`), then copy the `lip_...` token.
  It's shown only once.
- Paste it into `.env` (git-ignored) as `LICHESS_TOKEN=lip_...`. The
  Makefile loads it automatically. When you run the script directly, set
  `LICHESS_TOKEN` in your environment or save the token to
  `~/.config/lichess-token` instead.

## Usage

`STUDY` is the part of the study URL after `lichess.org/study/`.

```sh
make dry-run STUDY=abcd1234   # show what would change
make sync    STUDY=abcd1234   # import new/changed chapters
make prune   STUDY=abcd1234   # sync and delete chapters missing locally
```

Each chapter is matched by its `ChapterName` tag. Chapters that haven't
changed are left alone.

`COLOR` picks the repertoire file and board orientation. It defaults to
`white` (`repertoire/white.pgn`):

```sh
make sync STUDY=efgh5678 COLOR=black
```

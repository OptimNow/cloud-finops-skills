#!/usr/bin/env python3
"""Fetch English transcripts (and metadata) for every video on a YouTube channel.

Run this on a normal machine: a laptop on a home or office connection. YouTube
blocks transcript and player requests coming from cloud-provider IP ranges, so
this does not work from a hosted container (tested 2026-10-11: both the
transcript API and yt-dlp are refused from a cloud session).

Setup (once), in a terminal opened in this folder:
    python -m venv yt-env
    yt-env\\Scripts\\activate              (Windows PowerShell or cmd)
    source yt-env/bin/activate            (macOS / Linux)
    pip install yt-dlp youtube-transcript-api

Usage:
    python fetch_youtube_transcripts.py --out transcripts --limit 20     # trial run, 20 videos
    python fetch_youtube_transcripts.py --out transcripts                # whole channel
    python fetch_youtube_transcripts.py --out transcripts --catalogue channel-catalogue.tsv --tiers 1
                                                                         # committed listing, tier 1 only
    python fetch_youtube_transcripts.py --out transcripts --catalogue channel-catalogue.tsv \
        --playlist Tokenomicon --playlist "FinOps X 2026"                # the 81-video scope of 2026-10-11
    python fetch_youtube_transcripts.py --out transcripts --no-metadata  # transcripts only, faster

The run is resumable: a video that already has <out>/<id>.json is skipped, so
you can stop it (Ctrl+C) and start it again later. One JSON file per video:

    {id, title, duration_s, view_count,
     upload_date, description, chapters,        <- from yt-dlp (metadata step)
     language, is_generated,                    <- is_generated: auto-captions (noisier) vs human captions
     text,                                      <- the whole transcript as one string
     segments: [{start, duration, text}, ...]}  <- timestamped, for citing a moment in the talk

Failures are written to <out>/<id>.error.txt and do not stop the run. An IP
block stops the run so the block does not get worse; rerun later.
"""

import argparse
import json
import sys
import time
from pathlib import Path

CHANNEL = "https://www.youtube.com/@finopsfoundation/videos"


def enumerate_channel(url):
    import yt_dlp

    opts = {
        "extract_flat": True,
        "quiet": True,
        "ignoreerrors": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    rows = []
    for e in info.get("entries") or []:
        if not e or not e.get("id"):
            continue
        rows.append(
            {
                "id": e["id"],
                "title": e.get("title") or "",
                "duration_s": e.get("duration"),
                "view_count": e.get("view_count"),
            }
        )
    return rows


def load_catalogue(path, tiers=None, playlists=None):
    """Accept the committed channel-catalogue.tsv (header + columns) or a raw yt-dlp listing.

    tiers: optional set of tier numbers to keep (the committed catalogue has a tier column).
    playlists: optional list of substrings; keep a row whose playlists column contains any of them."""
    rows = []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t") if lines else []
    if header and header[0] == "id":
        idx = {name: i for i, name in enumerate(header)}
        for line in lines[1:]:
            p = line.split("\t")
            if len(p) < len(header):
                continue
            if tiers and "tier" in idx and p[idx["tier"]] not in tiers:
                continue
            if playlists and "playlists" in idx:
                cell = p[idx["playlists"]].lower()
                if not any(x.lower() in cell for x in playlists):
                    continue
            rows.append(
                {
                    "id": p[idx["id"]],
                    "title": p[idx["title"]],
                    "duration_s": int(p[idx["duration_s"]])
                    if p[idx["duration_s"]].isdigit()
                    else None,
                    "view_count": int(p[idx["view_count"]])
                    if p[idx["view_count"]].isdigit()
                    else None,
                }
            )
        return rows
    for line in lines:
        p = line.replace("\\t", "\t").split("\t")
        if len(p) < 4:
            continue
        rows.append(
            {
                "id": p[0],
                "title": "\t".join(p[3:]),
                "duration_s": int(p[1]) if p[1].isdigit() else None,
                "view_count": int(p[2]) if p[2].isdigit() else None,
            }
        )
    return rows


def fetch_transcript(api, vid):
    """Prefer a human-made English track, then an auto-generated one, then a translation."""
    from youtube_transcript_api import NoTranscriptFound

    listing = api.list(vid)
    try:
        t = listing.find_manually_created_transcript(["en", "en-US", "en-GB"])
    except NoTranscriptFound:
        try:
            t = listing.find_generated_transcript(["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            t = next(iter(listing), None)
            if t is None:
                raise
            if t.is_translatable and not t.language_code.startswith("en"):
                t = t.translate("en")
    fetched = t.fetch()
    segs = [
        {"start": round(s.start, 2), "duration": round(s.duration, 2), "text": s.text}
        for s in fetched
    ]
    return {
        "language": t.language_code,
        "is_generated": t.is_generated,
        "segments": segs,
        "text": " ".join(s["text"].replace("\n", " ") for s in segs),
    }


def fetch_metadata(vid):
    """Upload date, description and chapters, one yt-dlp call per video (slower, skippable)."""
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}", download=False
            )
    except Exception as e:  # noqa: BLE001 - metadata is optional
        return {"metadata_error": f"{type(e).__name__}: {e}"[:300]}
    return {
        "upload_date": info.get("upload_date"),
        "description": info.get("description"),
        "chapters": [
            {"start": c.get("start_time"), "title": c.get("title")}
            for c in (info.get("chapters") or [])
        ],
        "channel": info.get("channel"),
    }


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--channel",
        default=CHANNEL,
        help="channel videos URL (default: FinOps Foundation)",
    )
    ap.add_argument(
        "--catalogue",
        help="reuse a listing (channel-catalogue.tsv or a raw yt-dlp print) instead of enumerating",
    )
    ap.add_argument("--out", default="transcripts", help="output folder")
    ap.add_argument(
        "--limit", type=int, default=0, help="stop after N new videos (0 = all)"
    )
    ap.add_argument(
        "--sleep", type=float, default=2.0, help="seconds to wait between videos"
    )
    ap.add_argument(
        "--tiers",
        help="with --catalogue channel-catalogue.tsv: keep only these tiers, e.g. 1 or 1,2",
    )
    ap.add_argument(
        "--playlist",
        action="append",
        help="with --catalogue channel-catalogue.tsv: keep only videos in a playlist whose name contains this text; repeatable",
    )
    ap.add_argument(
        "--no-metadata",
        action="store_true",
        help="skip the per-video yt-dlp metadata call",
    )
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.catalogue:
        tiers = {t.strip() for t in args.tiers.split(",")} if args.tiers else None
        rows = load_catalogue(args.catalogue, tiers, args.playlist)
    else:
        print(f"Enumerating {args.channel} ...", flush=True)
        rows = enumerate_channel(args.channel)
        (out / "_catalogue.json").write_text(
            json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8"
        )
    print(f"{len(rows)} videos in the catalogue", flush=True)

    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import IpBlocked, RequestBlocked

    api = YouTubeTranscriptApi()

    done = skipped = failed = 0
    for i, row in enumerate(rows, 1):
        if args.limit and done + failed >= args.limit:
            break
        target = out / f"{row['id']}.json"
        if target.exists():
            skipped += 1
            continue
        try:
            data = fetch_transcript(api, row["id"])
        except (IpBlocked, RequestBlocked) as e:
            print(
                f"\nSTOP: YouTube is blocking this IP ({type(e).__name__}). "
                f"Wait a few hours or run from another connection, then rerun (the run resumes)."
            )
            break
        except Exception as e:  # noqa: BLE001 - record and move on
            failed += 1
            (out / f"{row['id']}.error.txt").write_text(
                f"{type(e).__name__}: {e}", encoding="utf-8"
            )
            print(
                f"[{i}/{len(rows)}] FAIL {row['id']} {type(e).__name__}: {row['title'][:60]}",
                flush=True,
            )
        else:
            done += 1
            record = {**row, **data}
            if not args.no_metadata:
                record.update(fetch_metadata(row["id"]))
            target.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            kind = "auto" if data["is_generated"] else "manual"
            print(
                f"[{i}/{len(rows)}] ok ({kind}, {len(data['text'].split())} words) {row['title'][:60]}",
                flush=True,
            )
        time.sleep(args.sleep)

    print(
        f"\nfetched {done}, already present {skipped}, failed {failed}, output in {out.resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

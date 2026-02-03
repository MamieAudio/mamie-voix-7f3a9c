import json
import os
import random
from datetime import datetime, timezone

OWNER = "MamieAudio"
REPO = "mamie-voix-7f3a9c"
BASE = f"https://{OWNER.lower()}.github.io/{REPO}"

# IMPORTANT : le tag de ta Release (créée dans GitHub Releases)
LECTURE_RELEASE_TAG = "livre"  # <- si tu as mis un autre tag, change ici

FEED_PIANO = "feed-piano.xml"
FEED_OISEAUX = "feed-oiseaux.xml"
FEED_LECTURE = "feed-lecture.xml"

STATE_FILE = "state.json"

def utc_rfc2822_now():
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))

def list_mp3(folder: str):
    if not os.path.isdir(folder):
        return []
    files = []
    for name in os.listdir(folder):
        if name.lower().endswith(".mp3"):
            files.append(os.path.join(folder, name))
    files.sort()
    return files

def ghpages_url(path: str) -> str:
    return f"{BASE}/{path.replace(os.sep, '/')}"

def release_url(filename: str) -> str:
    # URL directe d’un asset de Release
    return f"https://github.com/{OWNER}/{REPO}/releases/download/{LECTURE_RELEASE_TAG}/{filename}"

def file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except:
        return 0

def build_feed(title: str, description: str, items: list):
    now = utc_rfc2822_now()
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<rss version="2.0">')
    out.append('  <channel>')
    out.append(f'    <title>{xml_escape(title)}</title>')
    out.append(f'    <description>{xml_escape(description)}</description>')
    out.append(f'    <link>{xml_escape(BASE + "/")}</link>')
    out.append('    <language>fr-fr</language>')
    out.append(f'    <lastBuildDate>{xml_escape(now)}</lastBuildDate>')

    for it in items:
        out.append('    <item>')
        out.append(f'      <title>{xml_escape(it["title"])}</title>')
        out.append(f'      <guid isPermaLink="false">{xml_escape(it["guid"])}</guid>')
        out.append(f'      <pubDate>{xml_escape(it["pubDate"])}</pubDate>')
        out.append(f'      <enclosure url="{xml_escape(it["url"])}" length="{it["length"]}" type="audio/mpeg"/>')
        out.append('    </item>')

    out.append('  </channel>')
    out.append('</rss>')
    out.append('')
    return "\n".join(out)

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"lecture_index": 1}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

def pick_random_mp3(folder: str):
    files = list_mp3(folder)
    if not files:
        return None
    return random.choice(files)

def clamp_lecture_index(n: int) -> int:
    if n < 1:
        return 1
    if n > 7:
        return 1
    return n

def main():
    random.seed()

    state = load_state()
    lecture_index = clamp_lecture_index(int(state.get("lecture_index", 1)))

    # --- Piano (random daily) ---
    piano_pick = pick_random_mp3("audio/piano")
    piano_items = []
    if piano_pick:
        rel = piano_pick.replace("\\", "/")
        piano_items.append({
            "title": "Piano du jour",
            "guid": f"piano-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "pubDate": utc_rfc2822_now(),
            "url": ghpages_url(rel),
            "length": file_size(piano_pick),
        })

    # --- Oiseaux (random daily) ---
    oiseaux_pick = pick_random_mp3("audio/oiseaux")
    oiseaux_items = []
    if oiseaux_pick:
        rel = oiseaux_pick.replace("\\", "/")
        oiseaux_items.append({
            "title": "Oiseaux du jour",
            "guid": f"oiseaux-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "pubDate": utc_rfc2822_now(),
            "url": ghpages_url(rel),
            "length": file_size(oiseaux_pick),
        })

    # --- Lecture (sequential daily via Releases) ---
    # On ne met PAS les mp3 du livre dans le repo : ils sont dans la Release tag "livre"
    lecture_filename = f"partie{lecture_index}.mp3"
    lecture_items = [{
        "title": f"Livre – Partie {lecture_index}",
        "guid": f"lecture-partie-{lecture_index}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "pubDate": utc_rfc2822_now(),
        "url": release_url(lecture_filename),
        # taille inconnue côté repo => 0 (fonctionne dans la pratique pour beaucoup d’apps)
        "length": 0,
    }]

    # Write feeds
    with open(FEED_PIANO, "w", encoding="utf-8") as f:
        f.write(build_feed(
            "Mamie – Piano",
            "Piano calme (un morceau différent chaque jour)",
            piano_items
        ))

    with open(FEED_OISEAUX, "w", encoding="utf-8") as f:
        f.write(build_feed(
            "Mamie – Oiseaux",
            "Ambiance oiseaux (un son différent chaque jour)",
            oiseaux_items
        ))

    with open(FEED_LECTURE, "w", encoding="utf-8") as f:
        f.write(build_feed(
            "Mamie – Lecture",
            "Livre audio en 7 parties (avance automatiquement)",
            lecture_items
        ))

    # Advance lecture for next day
    lecture_index += 1
    if lecture_index > 7:
        lecture_index = 1
    state["lecture_index"] = lecture_index
    save_state(state)

    print("Feeds generated.")
    print(f"Next lecture_index={lecture_index}")

if __name__ == "__main__":
    main()

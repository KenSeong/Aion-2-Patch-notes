import json, os, requests

API_URL = "https://api-global-community.plaync.com/aion2_global/board/update_en/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0"
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
POST_URL = "https://aion2.plaync.com/en-us/board/update/view?articleId={id}"  # use your confirmed format
STATE = "seen.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://aion2.plaync.com",
    "Referer": "https://aion2.plaync.com/",
}
ID_KEYS = ["articleId", "id", "contentId", "postId"]
TITLE_KEYS = ["title", "subject", "name"]

def find_list(obj):
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            r = find_list(v)
            if r:
                return r
    return None

def pick(d, keys):
    for k in keys:
        if k in d:
            return d[k]
    raise KeyError(f"None of {keys} found. Fields available: {list(d)}")

data = requests.get(API_URL, headers=HEADERS, timeout=20).json()
items = find_list(data)
if not items:
    raise SystemExit(f"No post list found. Top-level keys: {list(data)}")
posts = [(str(pick(p, ID_KEYS)), str(pick(p, TITLE_KEYS))) for p in items]

seen = set(json.load(open(STATE))) if os.path.exists(STATE) else None
if seen is None:  # first run: record, don't post
    seen = {pid for pid, _ in posts}
else:
    new = sorted([x for x in posts if x[0] not in seen], key=lambda x: x[0])
    for pid, title in new:
        requests.post(WEBHOOK, json={"content": f"**{title}**\n{POST_URL.format(id=pid)}"}, timeout=20)
        seen.add(pid)

json.dump(sorted(seen), open(STATE, "w"))

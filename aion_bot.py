import json, os, requests

SOURCES = {
    "updates": {
        "api": "https://api-global-community.plaync.com/aion2_global/board/update_en/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0",
        "link": "https://aion2.plaync.com/en-us/board/update/view?articleId={id}",
        "webhooks": [
            os.environ["DISCORD_WEBHOOK"],
            os.environ["DISCORD_WEBHOOK2"],
        ],
    },
    "announcements": {
        "api": "https://api-global-community.plaync.com/aion2_global/board/notice_en/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0",
        "link": "https://aion2.plaync.com/en-us/board/notice/view?articleId={id}",
        "webhooks": [
            os.environ["DISCORD_WEBHOOK3"],
        ],
    },
}

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


state = json.load(open(STATE)) if os.path.exists(STATE) else {}
if isinstance(state, list):  # convert the old single-list format
    state = {"updates": state}

for name, src in SOURCES.items():
    try:
        data = requests.get(src["api"], headers=HEADERS, timeout=20).json()
        items = find_list(data)
        if not items:
            print(f"{name}: no post list found. Top-level keys: {list(data)}")
            continue
        posts = [(str(pick(p, ID_KEYS)), str(pick(p, TITLE_KEYS))) for p in items]
    except Exception as e:
        print(f"{name}: error: {e}")
        continue

    seen = set(state[name]) if name in state else None
    if seen is None:  # first time for this section: record silently
        seen = {pid for pid, _ in posts}
    else:
        new = sorted([x for x in posts if x[0] not in seen], key=lambda x: x[0])
        for pid, title in new:
            message = {"content": f"**{title}**\n{src['link'].format(id=pid)}"}
            for hook in src["webhooks"]:
                try:
                    requests.post(hook, json=message, timeout=20)
                except Exception as e:
                    print(f"{name}: webhook failed: {e}")
            seen.add(pid)
    state[name] = sorted(seen)

json.dump(state, open(STATE, "w"))

import json, os, urllib.request

# Each source has its own list of webhooks.
# Updates -> webhooks 1 and 2, Announcements -> webhook 3.
SOURCES = {
    "updates": {
        "api": "https://api-global-community.plaync.com/aion2_global/board/update_en/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0",
        "link": "https://aion2.plaync.com/en-us/board/update/view?articleId={id}",
        "webhooks": [
            {"url": os.environ["DISCORD_WEBHOOK"],  "roles": ["927570462651854868"], "thread": "1572972788027756756"}
        ],
    },
    "announcements": {
        "api": "https://api-global-community.plaync.com/aion2_global/board/notice_en/article/search/moreArticle?isVote=true&moreSize=18&moreDirection=BEFORE&previousArticleId=0",
        "link": "https://aion2.plaync.com/en-us/board/notice/view?articleId={id}",
        "webhooks": [
            {"url": os.environ["DISCORD_WEBHOOK"],  "roles": ["927570462651854868"], "thread": "1572972788027756756"}
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


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def post_webhook(url, payload):
    # Discord rejects urllib's default User-Agent, so a custom one is required.
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (aion-update-bot, 1.0)",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=20).close()


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


state = {}
if os.path.exists(STATE):
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                state = json.loads(content)
    except json.JSONDecodeError:
        state = {}
if isinstance(state, list):  # convert the old single-list format
    state = {"updates": state}

for name, src in SOURCES.items():
    try:
        data = get_json(src["api"])
        items = find_list(data)
        if not items:
            print(f"{name}: no post list found. Top-level keys: {list(data)}")
            continue
        posts = [(str(pick(p, ID_KEYS)), str(pick(p, TITLE_KEYS))) for p in items]
    except Exception as e:
        print(f"{name}: error: {e}")
        continue

    chronological = list(reversed(posts))
    saved = state.get(name)
    if saved is None:  # first time for this section: record silently
        saved = [pid for pid, _ in chronological]
    else:
        known = set(saved)
        for pid, title in chronological:
            if pid in known:
                continue
            for hook in src["webhooks"]:
                ping = " ".join(f"<@&{r}>" for r in hook["roles"])
                text = f"**{title}**\n{src['link'].format(id=pid)}"
                message = {
                    "content": f"{ping}\n{text}" if ping else text,
                    "allowed_mentions": {"roles": hook["roles"]},
                }
                try:
                    url = hook["url"]
                    if hook.get("thread"):
                        url += f"?thread_id={hook['thread']}"
                    post_webhook(url, message)
                except Exception as e:
                    print(f"{name}: webhook failed: {e}")
            saved.append(pid)
            known.add(pid)
    state[name] = saved
json.dump(state, open(STATE, "w"), indent=2)

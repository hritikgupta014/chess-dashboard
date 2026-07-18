"""
fetch_and_store.py
Runs in GitHub Actions every 2 hours.
Fetches all Lichess games for hritikgupta, analyses them,
stores the result as a single JSON blob in Supabase.
"""
import requests
import json
import os
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict, Counter

USERNAME      = "hritikgupta"
HEADERS       = {"User-Agent": "ChessDashboard/1.0 hritikgupta"}
TITLES        = {"GM","IM","FM","CM","NM","WGM","WIM","WFM","WCM","LM"}
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_KEY"]
LICHESS_TOKEN = os.environ.get("LICHESS_TOKEN", "")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── FETCH GAMES ───────────────────────────────────────────────────────────────
def fetch_all_games():
    params = {"opening":"true","clocks":"false","evals":"false",
              "moves":"false","tags":"false"}
    hdrs = {**HEADERS, "Accept":"application/x-ndjson"}
    if LICHESS_TOKEN:
        hdrs["Authorization"] = f"Bearer {LICHESS_TOKEN}"

    games = []
    log("Streaming games from Lichess...")
    try:
        with requests.get(
            f"https://lichess.org/api/games/user/{USERNAME}",
            params=params, headers=hdrs,
            stream=True, timeout=(10, 600)
        ) as r:
            if r.status_code == 429:
                log("Rate limited by Lichess — aborting"); sys.exit(1)
            if r.status_code != 200:
                log(f"Lichess error: {r.status_code}"); sys.exit(1)
            for line in r.iter_lines():
                if line:
                    try:
                        games.append(json.loads(line))
                        if len(games) % 2000 == 0:
                            log(f"  {len(games):,} games loaded...")
                    except: pass
    except Exception as e:
        log(f"Fetch error: {e}"); sys.exit(1)
    log(f"Fetched {len(games):,} games total")
    return games

# ── FETCH PROFILE ─────────────────────────────────────────────────────────────
def fetch_profile():
    try:
        r = requests.get(f"https://lichess.org/api/user/{USERNAME}",
                         headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except: pass
    return {}

# ── ANALYSE ───────────────────────────────────────────────────────────────────
def analyse(games):
    uname = USERNAME.lower()
    stats = {
        "total":         len(games),
        "by_format":     defaultdict(lambda:{"w":0,"l":0,"d":0,"games":0}),
        "color_stats":   {"white":{"w":0,"l":0,"d":0},"black":{"w":0,"l":0,"d":0}},
        "titled_wins":   [], "titled_losses":  [],
        "high_rated_wins":[],
        "streaks":       defaultdict(lambda:{"cur":0,"best":0}),
        "opening_res_w": defaultdict(lambda:[0,0,0]),
        "opening_res_b": defaultdict(lambda:[0,0,0]),
        "openings_w":    Counter(), "openings_b": Counter(),
        "terminations":  Counter(),
        "hourly":        defaultdict(lambda:{"w":0,"g":0}),
        "weekday":       defaultdict(lambda:{"w":0,"g":0}),
        "opp_buckets":   defaultdict(lambda:{"w":0,"l":0,"d":0,"g":0}),
        "session_data":  [],
    }
    last_ts = None; session_results = []

    for g in games:
        players = g.get("players",{})
        white   = players.get("white",{}); black = players.get("black",{})
        wu = (white.get("user",{}).get("name") or white.get("user",{}).get("id","")).lower()
        bu = (black.get("user",{}).get("name") or black.get("user",{}).get("id","")).lower()
        if   wu == uname: my_side,my_data,opp_data = "white",white,black
        elif bu == uname: my_side,my_data,opp_data = "black",black,white
        else: continue

        winner = g.get("winner"); status = g.get("status","")
        if   winner == my_side:                                result = "w"
        elif winner is None or status in ("draw","stalemate"): result = "d"
        else:                                                  result = "l"

        perf = g.get("perf","unknown")
        stats["by_format"][perf]["games"] += 1
        stats["by_format"][perf][result]  += 1
        stats["color_stats"][my_side][result] += 1

        my_rating  = my_data.get("rating")
        opp_rating = opp_data.get("rating")
        opp_user   = opp_data.get("user",{})
        opp_name   = opp_user.get("name") or opp_user.get("id","")
        opp_title  = opp_user.get("title","")

        if opp_title in TITLES:
            entry = {"title":opp_title,"name":opp_name,
                     "rating":opp_rating,"perf":perf,"id":g.get("id","")}
            (stats["titled_wins"] if result=="w" else stats["titled_losses"]).append(entry)

        if result=="w" and my_rating and opp_rating and (opp_rating-my_rating)>=150:
            stats["high_rated_wins"].append({
                "name":opp_name,"opp_rating":opp_rating,"my_rating":my_rating,
                "diff":opp_rating-my_rating,"perf":perf,
                "id":g.get("id",""),"title":opp_title
            })

        op = g.get("opening",{})
        if op:
            op_name = op.get("name","Unknown").split(":")[0].strip()
            if my_side=="white":
                stats["openings_w"][op_name]+=1; arr=stats["opening_res_w"][op_name]
            else:
                stats["openings_b"][op_name]+=1; arr=stats["opening_res_b"][op_name]
            if result=="w": arr[0]+=1
            elif result=="d": arr[1]+=1
            else: arr[2]+=1

        stats["terminations"][status] += 1

        tk = stats["streaks"][perf]
        if result=="w": tk["cur"]+=1; tk["best"]=max(tk["best"],tk["cur"])
        else:           tk["cur"]=0

        ts = g.get("createdAt",0)
        if ts:
            dt      = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            hour    = dt.hour
            weekday = dt.strftime("%a")
            stats["hourly"][hour]["g"]    += 1
            stats["weekday"][weekday]["g"] += 1
            if result=="w":
                stats["hourly"][hour]["w"]    += 1
                stats["weekday"][weekday]["w"] += 1
            if last_ts and (ts - last_ts) > 1800000:
                if session_results:
                    stats["session_data"].append(session_results[:])
                session_results = []
            session_results.append(result)
            last_ts = ts

        if opp_rating:
            bucket = f"{(opp_rating//100)*100}-{(opp_rating//100)*100+99}"
            b = stats["opp_buckets"][bucket]
            b["g"]+=1; b[result]+=1

    if session_results:
        stats["session_data"].append(session_results)

    def wr_list(res_dict):
        out = []
        for op,(w,d,l) in res_dict.items():
            t = w+d+l
            if t>=5: out.append((op, round(w/t*100,1), t, w, d, l))
        return sorted(out, key=lambda x:x[1], reverse=True)

    # Convert to JSON-serialisable plain dicts
    return {
        "total":           stats["total"],
        "by_format":       dict(stats["by_format"]),
        "color_stats":     stats["color_stats"],
        "titled_wins":     stats["titled_wins"][:50],
        "titled_losses":   stats["titled_losses"][:50],
        "high_rated_wins": sorted(stats["high_rated_wins"],
                                  key=lambda x:x["diff"],reverse=True)[:20],
        "streaks":         {k:{"best":v["best"]} for k,v in stats["streaks"].items()},
        "wr_w":            wr_list(stats["opening_res_w"]),
        "wr_b":            wr_list(stats["opening_res_b"]),
        "openings_w":      dict(stats["openings_w"].most_common(20)),
        "openings_b":      dict(stats["openings_b"].most_common(20)),
        "terminations":    dict(stats["terminations"]),
        "hourly":          {str(k):v for k,v in stats["hourly"].items()},
        "weekday":         dict(stats["weekday"]),
        "opp_buckets":     dict(stats["opp_buckets"]),
        "session_data":    stats["session_data"][-200:],
    }

# ── STORE IN SUPABASE ─────────────────────────────────────────────────────────
def store(profile, stats):
    payload = {
        "username":     USERNAME,
        "updated_at":   datetime.now(timezone.utc).isoformat(),
        "profile":      profile,
        "stats":        stats,
    }
    hdrs = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=minimal",
    }
    # Upsert — inserts on first run, updates on every subsequent run
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/chess_dashboard",
        headers=hdrs,
        json={"id": USERNAME, "data": payload},
        timeout=30
    )
    if r.status_code in (200, 201):
        log(f"Stored to Supabase OK ({len(json.dumps(payload))//1024} KB)")
    else:
        log(f"Supabase error {r.status_code}: {r.text[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    log(f"Starting fetch for {USERNAME}")
    profile = fetch_profile()
    log(f"Profile: {profile.get('username','?')} — "
        f"Blitz {profile.get('perfs',{}).get('blitz',{}).get('rating','?')}")
    games   = fetch_all_games()
    log("Analysing...")
    stats   = analyse(games)
    log(f"Analysis done — {stats['total']:,} games, "
        f"{len(stats['titled_wins'])} titled wins, "
        f"{len(stats['high_rated_wins'])} upsets")
    store(profile, stats)
    log("All done.")

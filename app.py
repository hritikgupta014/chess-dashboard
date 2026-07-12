import streamlit as st
import requests
import json
import re
import os
import time
from datetime import datetime, timezone
from collections import defaultdict, Counter
from dotenv import load_dotenv

load_dotenv()

# ── KEYS — loaded from .env file ─────────────────────────────────────────────
# Create a file called .env in your chess-dashboard folder with:
#   GROQ_API_KEY=your_key_here
#   LICHESS_TOKEN=your_token_here
_GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
_LICHESS_TOKEN = os.getenv("LICHESS_TOKEN", "")

st.set_page_config(
    page_title="♟ hritikgupta — Chess Dashboard",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[data-testid="stApp"]{background:#0a0a0a !important;color:#e8e4dc !important;}
[data-testid="stSidebar"]{background:#111 !important;border-right:1px solid #1f1f1f !important;}
[data-testid="stSidebar"] *{color:#a09a8e !important;}
[data-testid="stSidebar"] .stButton button{background:#1a1a1a !important;border:1px solid #2a2a2a !important;color:#c9a84c !important;width:100% !important;border-radius:4px !important;padding:.5rem !important;font-family:'Inter',sans-serif !important;font-size:13px !important;letter-spacing:.05em !important;}
[data-testid="stSidebar"] .stButton button:hover{background:#c9a84c !important;color:#0a0a0a !important;}
[data-testid="stSidebar"] input{background:#1a1a1a !important;border:1px solid #2a2a2a !important;color:#e8e4dc !important;border-radius:4px !important;font-family:'JetBrains Mono',monospace !important;font-size:12px !important;}
[data-testid="stSidebar"] label{color:#555 !important;font-size:11px !important;letter-spacing:.1em !important;text-transform:uppercase !important;}
.block-container{padding:0 !important;max-width:100% !important;}
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none !important;}
.masthead{background:#0d0d0d;border-bottom:1px solid #1f1f1f;padding:2.5rem 3rem 2rem;position:relative;overflow:hidden;}
.masthead::before{content:'♟';position:absolute;right:3rem;top:50%;transform:translateY(-50%);font-size:9rem;color:rgba(201,168,76,.04);pointer-events:none;}
.masthead-eyebrow{font-family:'JetBrains Mono',monospace;font-size:10px;color:#c9a84c;letter-spacing:.3em;text-transform:uppercase;margin-bottom:.5rem;}
.masthead-title{font-family:'Playfair Display',serif;font-size:3.2rem;font-weight:900;color:#e8e4dc;line-height:1.1;margin:0;}
.masthead-title span{color:#c9a84c;}
.masthead-meta{font-family:'Inter',sans-serif;font-size:12px;color:#555;margin-top:.75rem;letter-spacing:.05em;}
.stat-strip{display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #1a1a1a;}
.stat-cell{padding:1.2rem 2rem;border-right:1px solid #1a1a1a;}
.stat-cell:last-child{border-right:none;}
.stat-val{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:700;color:#c9a84c;line-height:1;}
.stat-lbl{font-family:'Inter',sans-serif;font-size:10px;color:#555;text-transform:uppercase;letter-spacing:.15em;margin-top:.3rem;}
.section-wrap{padding:2.5rem 3rem;border-bottom:1px solid #141414;}
.section-head{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;border-bottom:1px solid #1f1f1f;padding-bottom:.75rem;}
.section-title{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#e8e4dc;}
.section-pill{font-family:'JetBrains Mono',monospace;font-size:9px;background:#1a1a1a;color:#c9a84c;border:1px solid #2a2a2a;padding:2px 8px;letter-spacing:.1em;text-transform:uppercase;}
.perf-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;background:#1a1a1a;}
.perf-card{background:#0d0d0d;padding:1.2rem 1rem;text-align:center;}
.perf-format{font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.4rem;}
.perf-rating{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:700;color:#e8e4dc;line-height:1;}
.perf-prog{font-family:'JetBrains Mono',monospace;font-size:10px;margin-top:.2rem;}
.perf-prog.up{color:#4a8c3f;} .perf-prog.dn{color:#8c3f3f;}
.perf-games{font-family:'Inter',sans-serif;font-size:10px;color:#444;margin-top:.2rem;}
.wdl-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;background:#1a1a1a;}
.wdl-w{background:#4a8c3f;} .wdl-d{background:#555;} .wdl-l{background:#8c3f3f;}
.wdl-labels{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-top:3px;}
.win-card{background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid #c9a84c;padding:.9rem 1rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem;}
.win-rank{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#2a2a2a;min-width:2rem;text-align:center;}
.win-rank.gold{color:#c9a84c;}
.win-opp{font-family:'Inter',sans-serif;font-size:13px;font-weight:500;color:#e8e4dc;flex:1;}
.win-title-badge{font-family:'JetBrains Mono',monospace;font-size:9px;background:#c9a84c;color:#0a0a0a;padding:1px 5px;font-weight:600;margin-left:.3rem;}
.win-rating{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:#c9a84c;text-align:right;}
.win-link{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;text-decoration:none;}
.opening-row{display:flex;align-items:center;gap:.75rem;padding:.6rem 0;border-bottom:1px solid #141414;font-family:'Inter',sans-serif;font-size:13px;}
.opening-row:last-child{border-bottom:none;}
.opening-name{flex:1;color:#e8e4dc;}
.opening-bar-wrap{width:100px;height:4px;background:#1a1a1a;border-radius:2px;overflow:hidden;}
.opening-bar-fill{height:100%;border-radius:2px;background:#c9a84c;}
.opening-bar-fill.bad{background:#8c3f3f;}
.opening-wr{font-family:'JetBrains Mono',monospace;font-size:11px;min-width:40px;text-align:right;}
.opening-wr.good{color:#4a8c3f;} .opening-wr.bad{color:#8c3f3f;}
.opening-games{font-size:10px;color:#444;min-width:50px;text-align:right;}
.streak-box{background:#0d0d0d;border:1px solid #1a1a1a;padding:1rem 1.5rem;display:flex;align-items:center;gap:1.5rem;margin-bottom:.5rem;}
.streak-num{font-family:'Playfair Display',serif;font-size:3rem;font-weight:700;color:#c9a84c;line-height:1;}
.streak-format{font-family:'JetBrains Mono',monospace;font-size:11px;color:#a09a8e;margin-bottom:.2rem;}
.streak-detail{font-family:'Inter',sans-serif;font-size:12px;color:#555;}
.color-compare{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#1a1a1a;margin-bottom:1rem;}
.color-side{background:#0d0d0d;padding:1.2rem 1.5rem;text-align:center;}
.color-piece{font-size:2rem;margin-bottom:.3rem;}
.color-label{font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.8rem;}
.color-big{font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;color:#c9a84c;}
.ai-box{background:#0d0d0d;border:1px solid #1f1f1f;border-top:2px solid #c9a84c;padding:1.5rem;}
.ai-eyebrow{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;letter-spacing:.2em;text-transform:uppercase;margin-bottom:1rem;}
.ai-section-title{font-family:'Playfair Display',serif;font-size:1rem;color:#e8e4dc;margin:1rem 0 .4rem;}
.ai-body{font-family:'Inter',sans-serif;font-size:13px;color:#888;line-height:1.8;margin-bottom:.3rem;}
.insight-card{background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid #c9a84c;padding:.9rem 1.2rem;margin-bottom:.6rem;}
.insight-label{font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.3rem;}
.insight-val{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#c9a84c;}
.insight-sub{font-family:'Inter',sans-serif;font-size:12px;color:#555;margin-top:.2rem;}
.no-data{font-family:'Inter',sans-serif;font-size:13px;color:#333;padding:2rem;text-align:center;background:#0d0d0d;border:1px dashed #1a1a1a;}
.loading-msg{font-family:'JetBrains Mono',monospace;font-size:12px;color:#c9a84c;padding:1.5rem 3rem;}
.bucket-row{display:flex;align-items:center;gap:1rem;padding:.6rem 0;border-bottom:1px solid #141414;font-size:13px;}
.bucket-label{font-family:'JetBrains Mono',monospace;font-size:11px;color:#a09a8e;min-width:90px;}
.bucket-bar-wrap{flex:1;height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden;}
.bucket-bar{height:100%;border-radius:3px;background:#c9a84c;}
.bucket-wr{font-family:'JetBrains Mono',monospace;font-size:11px;min-width:45px;text-align:right;color:#c9a84c;}
.bucket-games{font-size:10px;color:#444;min-width:55px;text-align:right;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
USERNAME = "hritikgupta"
HEADERS  = {"User-Agent": "ChessDashboard/1.0 personal-use hritikgupta"}
TITLES   = {"GM","IM","FM","CM","NM","WGM","WIM","WFM","WCM","LM"}

# ── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=0, show_spinner=False)
def fetch_profile():
    try:
        r = requests.get(f"https://lichess.org/api/user/{USERNAME}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except: pass
    return {}

def stream_all_games(token=None):
    params = {"opening":"true","clocks":"false","evals":"false","moves":"false","tags":"false"}
    hdrs   = {**HEADERS, "Accept":"application/x-ndjson"}
    if token: hdrs["Authorization"] = f"Bearer {token}"
    games = []
    try:
        with requests.get(f"https://lichess.org/api/games/user/{USERNAME}",
                          params=params, headers=hdrs, stream=True, timeout=(10,600)) as r:
            if r.status_code == 429:
                st.warning("Lichess rate limit — wait 60 seconds then refresh.")
                return []
            if r.status_code != 200:
                st.error(f"Lichess error: {r.status_code}")
                return []
            for line in r.iter_lines():
                if line:
                    try: games.append(json.loads(line))
                    except: pass
    except requests.exceptions.Timeout:
        st.warning(f"Timeout — loaded {len(games):,} games. Refresh to retry.")
    except Exception as e:
        st.error(f"Fetch error: {e}")
    return games

# ── ANALYSIS ──────────────────────────────────────────────────────────────────
def analyse(games):
    uname = USERNAME.lower()
    stats = {
        "total":          len(games),
        "by_format":      defaultdict(lambda:{"w":0,"l":0,"d":0,"games":0}),
        "color_stats":    {"white":{"w":0,"l":0,"d":0},"black":{"w":0,"l":0,"d":0}},
        "titled_wins":    [], "titled_losses":  [],
        "high_rated_wins":[],
        "streaks":        defaultdict(lambda:{"cur":0,"best":0}),
        "opening_res_w":  defaultdict(lambda:[0,0,0]),
        "opening_res_b":  defaultdict(lambda:[0,0,0]),
        "openings_w":     Counter(), "openings_b": Counter(),
        "terminations":   Counter(),
        "hourly":         defaultdict(lambda:{"w":0,"g":0}),
        "weekday":        defaultdict(lambda:{"w":0,"g":0}),
        "monthly_rating": defaultdict(list),
        "game_lengths":   {"win":[],"loss":[],"draw":[]},
        "opp_buckets":    defaultdict(lambda:{"w":0,"l":0,"d":0,"g":0}),
        "move_loss":      Counter(),
        "comeback_wins":  0,
        "session_data":   [],
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
        opp_user   = opp_data.get("user",{}); opp_name = opp_user.get("name") or opp_user.get("id","")
        opp_title  = opp_user.get("title","")

        if opp_title in TITLES:
            entry = {"title":opp_title,"name":opp_name,"rating":opp_rating,"perf":perf,"id":g.get("id","")}
            (stats["titled_wins"] if result=="w" else stats["titled_losses"]).append(entry)

        if result=="w" and my_rating and opp_rating and (opp_rating-my_rating)>=150:
            stats["high_rated_wins"].append({"name":opp_name,"opp_rating":opp_rating,
                "my_rating":my_rating,"diff":opp_rating-my_rating,"perf":perf,
                "id":g.get("id",""),"title":opp_title})

        # Openings
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

        # Streaks
        tk = stats["streaks"][perf]
        if result=="w": tk["cur"]+=1; tk["best"]=max(tk["best"],tk["cur"])
        else:           tk["cur"]=0

        # Timestamp-based insights
        ts = g.get("createdAt",0)
        if ts:
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            hour    = dt.hour
            weekday = dt.strftime("%a")
            month   = dt.strftime("%Y-%m")
            stats["hourly"][hour]["g"]   += 1
            stats["weekday"][weekday]["g"]+= 1
            if result=="w":
                stats["hourly"][hour]["w"]   +=1
                stats["weekday"][weekday]["w"]+=1
            if my_rating:
                stats["monthly_rating"][f"{month}_{perf}"].append(my_rating)

            # Session detection (gap > 30 mins = new session)
            if last_ts and (ts - last_ts) > 1800000:
                if session_results:
                    stats["session_data"].append(session_results[:])
                session_results = []
            session_results.append(result)
            last_ts = ts

        # Opponent rating buckets
        if opp_rating:
            bucket = f"{(opp_rating//100)*100}-{(opp_rating//100)*100+99}"
            b = stats["opp_buckets"][bucket]
            b["g"]+=1; b[result]+=1

    if session_results:
        stats["session_data"].append(session_results)

    def wr_list(res_dict):
        out=[]
        for op,(w,d,l) in res_dict.items():
            t=w+d+l
            if t>=5: out.append((op,round(w/t*100,1),t,w,d,l))
        return sorted(out,key=lambda x:x[1],reverse=True)

    stats["wr_w"] = wr_list(stats["opening_res_w"])
    stats["wr_b"] = wr_list(stats["opening_res_b"])
    stats["high_rated_wins"].sort(key=lambda x:x["diff"],reverse=True)
    stats["titled_wins"].sort(key=lambda x:x.get("rating") or 0,reverse=True)
    return stats

# ── GROQ — fast, free, 14,400 req/day, no daily burnout ──────────────────────
def call_gemini(prompt, api_key):
    models = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama3-8b-8192"]
    system = (
        "You are an expert chess coach with 20+ years experience coaching players from 1500 to GM. "
        "Write in a direct, analytical, encouraging style. Use ** for section headers. "
        "Be specific — always cite actual numbers and opening names from the data. "
        "Each section should be concise, actionable, and tailored to a 2000+ rated player."
    )
    for model in models:
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body, timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                st.info("Rate limit — waiting 15s then retrying...")
                time.sleep(15)
                continue
            elif r.status_code in (400, 404):
                continue
            else:
                return f"Groq error {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return f"Connection error: {e}"
    return "Could not reach Groq. Check your API key at console.groq.com."

def build_prompt(stats, profile):
    """Build a concise prompt — avoids TPM limits on free tier."""
    perfs = profile.get("perfs",{}) if profile else {}
    lines = [f"Chess coaching for Lichess user: {USERNAME} ({stats['total']:,} career games)\n"]

    lines.append("RATINGS: " + " | ".join(
        f"{pf} {perfs[pf].get('rating','?')} ({perfs[pf].get('games',0):,}g {perfs[pf].get('prog',0):+d})"
        for pf in ["bullet","blitz","rapid","classical"] if pf in perfs
    ))

    lines.append("\nFORMAT W/D/L:")
    for pf,d in sorted(stats["by_format"].items(),key=lambda x:x[1]["games"],reverse=True):
        g=d["games"]
        if g<10: continue
        wr=round(d["w"]/g*100,1)
        lines.append(f"  {pf}: {wr}% ({g:,}g, {d['w']}W/{d['d']}D/{d['l']}L)")

    cs=stats["color_stats"]
    for color,d in cs.items():
        t=d["w"]+d["d"]+d["l"]
        if t: lines.append(f"As {color}: {round(d['w']/t*100,1)}% win rate ({t:,}g)")

    if stats["wr_w"]:
        lines.append("\nOPENINGS AS WHITE (win% / games):")
        lines.append("Best: " + ", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_w"][:4]))
        lines.append("Worst: " + ", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_w"][-4:]))
    if stats["wr_b"]:
        lines.append("OPENINGS AS BLACK:")
        lines.append("Best: " + ", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_b"][:4]))
        lines.append("Worst: " + ", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_b"][-4:]))

    if stats["hourly"]:
        best_h=max(stats["hourly"].items(),key=lambda x:x[1]["w"]/max(x[1]["g"],1) if x[1]["g"]>10 else 0)
        worst_h=min(stats["hourly"].items(),key=lambda x:x[1]["w"]/max(x[1]["g"],1) if x[1]["g"]>10 else 1)
        lines.append(f"\nBEST HOUR: {best_h[0]}:00 UTC | WORST HOUR: {worst_h[0]}:00 UTC")

    tilt=sum(1 for s in stats["session_data"] if len(s)>=6 and s[:3].count("w")>=2 and s[-3:].count("l")>=2)
    best_streak=max((v["best"] for v in stats["streaks"].values()),default=0)
    lines.append(f"TILT SESSIONS: {tilt} | BEST STREAK: {best_streak}")
    lines.append(f"TITLED WINS: {len(stats['titled_wins'])} | TITLED LOSSES: {len(stats['titled_losses'])}")
    lines.append(f"UPSETS (beat 150+ higher rated): {len(stats['high_rated_wins'])}")

    lines.append("""
Write a chess coaching report with these 7 sections (use ** for headers):
**Player Overview** — 2 sentences on level and profile
**Strengths** — 3 specific strengths with numbers
**Critical Weaknesses** — 3 weaknesses with numbers, why they matter at 2000+
**Opening Surgery** — openings to keep, drop, and exact replacements to study
**Psychological Patterns** — colour gap, tilt, time-of-day findings
**Weekly Study Plan** — Mon-Sun, each day one specific task (name exact puzzle themes, opening lines, endgame types)
**Study Resources** — 5 named resources matching weaknesses (exact YouTube channels, Chessable courses, book titles)""")
    return "\n".join(lines)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ♟ Dashboard")
    st.markdown("---")
    gemini_key = st.text_input("Groq API Key",type="password",
        value=st.session_state.get("groq_key", _GROQ_KEY),
        help="Free key from console.groq.com — no card needed")
    if gemini_key: st.session_state["groq_key"]=gemini_key

    lichess_token = st.text_input("Lichess Token",type="password",
        value=st.session_state.get("lichess_token", _LICHESS_TOKEN),
        help="Free key from console.groq.com — no card needed")
    if lichess_token: st.session_state["lichess_token"]=lichess_token

    st.markdown("---")
    st.markdown("""<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#444;line-height:1.9'>
        Fetches <strong style='color:#c9a84c'>ALL games</strong> — no cap<br>
        Keys auto-load from .env file<br>
        429 errors: auto-retry with backoff
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("⟳  Refresh / Load games"):
        for k in ["profile","games","stats","last_refresh","ai_report","study_plan"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
    if "last_refresh" in st.session_state:
        st.markdown(f"<div style='font-size:10px;color:#333;font-family:JetBrains Mono,monospace;margin-top:.5rem'>Last refreshed<br>{st.session_state['last_refresh']}</div>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#1f1f1f;font-family:JetBrains Mono,monospace;line-height:1.8'>DATA: LICHESS API<br>AI: GROQ (LLAMA 70B)<br>BUILT WITH STREAMLIT</div>",unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
if "profile" not in st.session_state:
    st.session_state["profile"] = fetch_profile()

if "games" not in st.session_state:
    token   = st.session_state.get("lichess_token","") or None
    box     = st.empty()
    box.markdown('<div class="loading-msg">♟ Fetching ALL your games from Lichess...<br><span style="color:#555;font-size:11px">17,000+ games — takes 2–4 mins. Leave tab open.</span></div>',unsafe_allow_html=True)
    games   = stream_all_games(token)
    st.session_state["games"] = games
    if games:
        st.session_state["stats"]        = analyse(games)
        st.session_state["last_refresh"] = datetime.now().strftime("%d %b %Y, %H:%M")
        box.empty()
    else:
        box.markdown('<div class="loading-msg" style="color:#8c3f3f">⚠ No games loaded. Check token or refresh.</div>',unsafe_allow_html=True)

profile = st.session_state.get("profile",{})
games   = st.session_state.get("games",[])
stats   = st.session_state.get("stats",None)
perfs   = profile.get("perfs",{}) if profile else {}

# ── MASTHEAD ──────────────────────────────────────────────────────────────────
blitz_r  = perfs.get("blitz",{}).get("rating","—")
rapid_r  = perfs.get("rapid",{}).get("rating","—")
bullet_r = perfs.get("bullet",{}).get("rating","—")
title_b  = profile.get("title","") if profile else ""
title_h  = f"<span style='font-family:JetBrains Mono;font-size:1rem;color:#c9a84c'>{title_b} </span>" if title_b else ""
created  = profile.get("createdAt",0)
since    = datetime.fromtimestamp(created/1000,tz=timezone.utc).strftime("%B %Y") if created else "—"
total_lc = profile.get("count",{}).get("all",len(games)) if profile else len(games)

st.markdown(f"""<div class="masthead">
    <div class="masthead-eyebrow">Lichess · Personal Intelligence Dashboard</div>
    <div class="masthead-title">{title_h}<span>hritik</span>gupta</div>
    <div class="masthead-meta">Member since {since} &nbsp;·&nbsp; {total_lc:,} lifetime games &nbsp;·&nbsp; {len(games):,} analysed &nbsp;·&nbsp; Blitz {blitz_r} &nbsp;·&nbsp; Rapid {rapid_r} &nbsp;·&nbsp; Bullet {bullet_r}</div>
</div>""",unsafe_allow_html=True)

# ── STAT STRIP ────────────────────────────────────────────────────────────────
if stats:
    all_w=sum(d["w"] for d in stats["by_format"].values())
    all_l=sum(d["l"] for d in stats["by_format"].values())
    all_d=sum(d["d"] for d in stats["by_format"].values())
    total=stats["total"]; wr=round(all_w/total*100,1) if total else 0
    best_streak=max((v["best"] for v in stats["streaks"].values()),default=0)
    st.markdown(f"""<div class="stat-strip">
        <div class="stat-cell"><div class="stat-val">{total:,}</div><div class="stat-lbl">Games analysed</div></div>
        <div class="stat-cell"><div class="stat-val">{all_w:,}</div><div class="stat-lbl">Total wins</div></div>
        <div class="stat-cell"><div class="stat-val">{wr}%</div><div class="stat-lbl">Win rate</div></div>
        <div class="stat-cell"><div class="stat-val">{best_streak}</div><div class="stat-lbl">Best streak</div></div>
        <div class="stat-cell"><div class="stat-val">{len(stats['titled_wins'])}</div><div class="stat-lbl">Titled scalps</div></div>
    </div>""",unsafe_allow_html=True)

# ── RATINGS ───────────────────────────────────────────────────────────────────
if perfs:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Current Ratings</div><div class="section-pill">Live · Lichess</div></div>',unsafe_allow_html=True)
    fmt_order=["bullet","ultraBullet","blitz","rapid","classical","correspondence","chess960","antichess","atomic","horde","kingOfTheHill","racingKings","crazyhouse","threeCheck","puzzle"]
    html='<div class="perf-grid">'
    for pf in fmt_order:
        if pf not in perfs: continue
        p=perfs[pf]; r=p.get("rating","?"); prog=p.get("prog",0); g=p.get("games",0)
        if g==0: continue
        ps=f"+{prog}" if prog>0 else str(prog); pc="up" if prog>0 else "dn" if prog<0 else ""
        lbl=pf.replace("kingOfTheHill","KotH").replace("racingKings","Racing").replace("ultraBullet","UltraBlt")
        html+=f'<div class="perf-card"><div class="perf-format">{lbl}</div><div class="perf-rating">{r}</div><div class="perf-prog {pc}">{ps if prog!=0 else "—"}</div><div class="perf-games">{g:,} games</div></div>'
    html+='</div>'
    st.markdown(html,unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── FORMAT BREAKDOWN ──────────────────────────────────────────────────────────
if stats:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Performance by Format</div><div class="section-pill">All time</div></div>',unsafe_allow_html=True)
    by_fmt=[(pf,d) for pf,d in sorted(stats["by_format"].items(),key=lambda x:x[1]["games"],reverse=True) if d["games"]>0]
    if by_fmt:
        cols=st.columns(max(1,min(len(by_fmt),4)))
        for i,(pf,d) in enumerate(by_fmt[:8]):
            g=d["games"]; w=d["w"]; dr=d["d"]; l=d["l"]
            wr_pct=round(w/g*100,1) if g else 0
            wp=round(w/g*100,1) if g else 0; dp=round(dr/g*100,1) if g else 0; lp=round(l/g*100,1) if g else 0
            with cols[i%4]:
                st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:1rem;margin-bottom:.5rem">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#555;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem">{pf}</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:#c9a84c">{wr_pct}%</div>
                    <div style="margin:.4rem 0"><div class="wdl-bar"><div class="wdl-w" style="width:{wp}%"></div><div class="wdl-d" style="width:{dp}%"></div><div class="wdl-l" style="width:{lp}%"></div></div>
                    <div class="wdl-labels"><span style="color:#4a8c3f">{w:,}W</span><span>{dr:,}D</span><span style="color:#8c3f3f">{l:,}L</span></div></div>
                    <div style="font-family:'Inter',sans-serif;font-size:10px;color:#333">{g:,} games</div>
                </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── WHITE VS BLACK ────────────────────────────────────────────────────────────
if stats:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">White vs Black</div><div class="section-pill">Colour performance</div></div>',unsafe_allow_html=True)
    cs=stats["color_stats"]; html='<div class="color-compare">'
    for color,piece in [("white","♔"),("black","♚")]:
        d=cs[color]; t=d["w"]+d["d"]+d["l"]
        wr_c=round(d["w"]/t*100,1) if t else 0
        wp=round(d["w"]/t*100,1) if t else 0; dp=round(d["d"]/t*100,1) if t else 0; lp=round(d["l"]/t*100,1) if t else 0
        html+=f"""<div class="color-side"><div class="color-piece">{piece}</div><div class="color-label">As {color}</div>
            <div class="color-big">{wr_c}%</div>
            <div style="max-width:160px;margin:.5rem auto 0"><div class="wdl-bar"><div class="wdl-w" style="width:{wp}%"></div><div class="wdl-d" style="width:{dp}%"></div><div class="wdl-l" style="width:{lp}%"></div></div>
            <div class="wdl-labels"><span style="color:#4a8c3f">{d['w']:,}W</span><span>{d['d']:,}D</span><span style="color:#8c3f3f">{d['l']:,}L</span></div></div>
            <div style="font-family:'Inter',sans-serif;font-size:10px;color:#333;margin-top:.3rem">{t:,} games</div></div>"""
    html+='</div>'
    st.markdown(html,unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── OPPONENT RATING BUCKETS ───────────────────────────────────────────────────
if stats and stats["opp_buckets"]:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Performance vs Rating Ranges</div><div class="section-pill">Where you win and lose</div></div>',unsafe_allow_html=True)
    buckets=sorted(stats["opp_buckets"].items(),key=lambda x:int(x[0].split("-")[0]))
    html=""
    for bkt,d in buckets:
        g=d["g"]
        if g<5: continue
        wr=round(d["w"]/g*100,1) if g else 0
        bar_w=min(wr,100)
        col="#4a8c3f" if wr>=50 else "#c9a84c" if wr>=40 else "#8c3f3f"
        html+=f"""<div class="bucket-row">
            <div class="bucket-label">{bkt}</div>
            <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar_w}%;background:{col}"></div></div>
            <div class="bucket-wr" style="color:{col}">{wr}%</div>
            <div class="bucket-games">{g:,} games</div>
        </div>"""
    st.markdown(html,unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── TIME OF DAY ───────────────────────────────────────────────────────────────
if stats and stats["hourly"]:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">When You Play Best</div><div class="section-pill">Hour of day · UTC</div></div>',unsafe_allow_html=True)
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.8rem">Win rate by hour (UTC)</div>',unsafe_allow_html=True)
        hours=sorted(stats["hourly"].items())
        html=""
        for h,d in hours:
            if d["g"]<5: continue
            wr=round(d["w"]/d["g"]*100,1)
            bar=min(wr,100)
            col="#4a8c3f" if wr>=52 else "#c9a84c" if wr>=48 else "#8c3f3f"
            html+=f"""<div class="bucket-row">
                <div class="bucket-label">{h:02d}:00</div>
                <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar}%;background:{col}"></div></div>
                <div class="bucket-wr" style="color:{col}">{wr}%</div>
                <div class="bucket-games">{d['g']} games</div>
            </div>"""
        st.markdown(html,unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.8rem">Win rate by day of week</div>',unsafe_allow_html=True)
        day_order=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        html=""
        for day in day_order:
            d=stats["weekday"].get(day,{"w":0,"g":0})
            if d["g"]<5: continue
            wr=round(d["w"]/d["g"]*100,1)
            bar=min(wr,100)
            col="#4a8c3f" if wr>=52 else "#c9a84c" if wr>=48 else "#8c3f3f"
            html+=f"""<div class="bucket-row">
                <div class="bucket-label">{day}</div>
                <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar}%;background:{col}"></div></div>
                <div class="bucket-wr" style="color:{col}">{wr}%</div>
                <div class="bucket-games">{d['g']:,} games</div>
            </div>"""
        st.markdown(html,unsafe_allow_html=True)

        # Tilt detector
        tilt=sum(1 for s in stats["session_data"] if len(s)>=6 and s[:3].count("w")>=2 and s[-3:].count("l")>=2)
        st.markdown(f"""<div style="margin-top:1.5rem;background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid {'#8c3f3f' if tilt>10 else '#c9a84c'};padding:1rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-bottom:.3rem">TILT SESSIONS DETECTED</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:{'#8c3f3f' if tilt>10 else '#c9a84c'}">{tilt}</div>
            <div style="font-family:'Inter',sans-serif;font-size:11px;color:#555">Sessions where you started well but ended badly</div>
        </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── BEST WINS + TITLED SCALPS ─────────────────────────────────────────────────
if stats:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div class="section-head"><div class="section-title">Best Wins</div><div class="section-pill">Biggest upsets</div></div>',unsafe_allow_html=True)
        top=sorted(stats["high_rated_wins"],key=lambda x:x["opp_rating"],reverse=True)[:10]
        if top:
            for i,hw in enumerate(top):
                rc="gold" if i==0 else ""; medal="🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else ""
                tb=f'<span class="win-title-badge">{hw.get("title","")}</span>' if hw.get("title") else ""
                lnk=f'<a class="win-link" href="https://lichess.org/{hw["id"]}" target="_blank">view ↗</a>' if hw.get("id") else ""
                st.markdown(f"""<div class="win-card">
                    <div class="win-rank {rc}">{medal or i+1}</div>
                    <div style="flex:1"><div class="win-opp">{hw['name']}{tb}</div><div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#444">{hw['perf']} · +{hw['diff']} pts</div></div>
                    <div><div class="win-rating">{hw.get('opp_rating','?')}</div>{lnk}</div>
                </div>""",unsafe_allow_html=True)
        else:
            st.markdown('<div class="no-data">No upsets in this sample</div>',unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-head"><div class="section-title">Titled Scalps</div><div class="section-pill">GM · IM · FM wins</div></div>',unsafe_allow_html=True)
        if stats["titled_wins"]:
            by_title=defaultdict(list)
            for tw in stats["titled_wins"]: by_title[tw["title"]].append(tw)
            for tc in ["GM","IM","FM","CM","NM","WGM","WIM","WFM"]:
                if tc not in by_title: continue
                wins=by_title[tc]; names=", ".join(w["name"] for w in wins[:3])
                more=f" +{len(wins)-3} more" if len(wins)>3 else ""
                st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid #c9a84c;padding:.8rem 1rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;background:#c9a84c;color:#0a0a0a;padding:2px 6px;font-weight:600;flex-shrink:0">{tc}</div>
                    <div style="flex:1;font-family:'Inter',sans-serif;font-size:13px;color:#e8e4dc">{len(wins)} win{'s' if len(wins)>1 else ''}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#555">{names}{more}</div>
                </div>""",unsafe_allow_html=True)
        else:
            st.markdown('<div class="no-data">No titled wins yet</div>',unsafe_allow_html=True)
        st.markdown(f"""<div style="margin-top:1rem;background:#0d0d0d;border:1px solid #1a1a1a;padding:.8rem 1rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-bottom:.3rem">TITLED LOSSES</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#8c3f3f">{len(stats['titled_losses'])}</div>
        </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── STREAKS ───────────────────────────────────────────────────────────────────
if stats:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Best Winning Streaks</div><div class="section-pill">Per format</div></div>',unsafe_allow_html=True)
    streaks=sorted([(pf,v["best"]) for pf,v in stats["streaks"].items() if v["best"]>=2],key=lambda x:x[1],reverse=True)
    if streaks:
        cols=st.columns(max(1,min(len(streaks),5)))
        for i,(pf,best) in enumerate(streaks[:5]):
            with cols[i]:
                st.markdown(f"""<div class="streak-box"><div class="streak-num">{best}</div>
                    <div><div class="streak-format">{pf.upper()}</div><div class="streak-detail">best streak</div></div>
                </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── OPENINGS ──────────────────────────────────────────────────────────────────
if stats:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Opening Analysis</div><div class="section-pill">Min 5 games</div></div>',unsafe_allow_html=True)
    def op_html(wr_list,top=True,limit=8):
        items=wr_list[:limit] if top else wr_list[-limit:]
        if not items: return '<div class="no-data">Not enough data</div>'
        html=""
        for op,wr,t,w,d,l in items:
            cls="good" if top else "bad"; bar="opening-bar-fill" if top else "opening-bar-fill bad"
            html+=f"""<div class="opening-row">
                <div class="opening-name">{op[:34]}</div>
                <div class="opening-bar-wrap"><div class="{bar}" style="width:{wr}%"></div></div>
                <div class="opening-wr {cls}">{wr}%</div>
                <div class="opening-games">{t} games</div>
            </div>"""
        return html
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.5rem">♔ Best as White</div>',unsafe_allow_html=True)
        st.markdown(op_html(stats["wr_w"],True),unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin:1.2rem 0 .5rem">♔ Worst as White</div>',unsafe_allow_html=True)
        st.markdown(op_html(stats["wr_w"],False),unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.5rem">♚ Best as Black</div>',unsafe_allow_html=True)
        st.markdown(op_html(stats["wr_b"],True),unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin:1.2rem 0 .5rem">♚ Worst as Black</div>',unsafe_allow_html=True)
        st.markdown(op_html(stats["wr_b"],False),unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── AI COACHING ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
st.markdown('<div class="section-head"><div class="section-title">AI Coaching Report</div><div class="section-pill">Groq · Llama 70B · Free</div></div>',unsafe_allow_html=True)
gemini_key=st.session_state.get("groq_key","")
if not gemini_key:
    st.markdown("""<div class="ai-box"><div class="ai-eyebrow">Setup required</div>
        <div class="ai-body">Add your Gemini API key in the sidebar or in your .env file.<br>
        Get a free key at <strong style='color:#e8e4dc'>console.groq.com</strong> — no credit card needed.</div>
    </div>""",unsafe_allow_html=True)
elif not stats:
    st.markdown('<div class="no-data">Load games first</div>',unsafe_allow_html=True)
else:
    col_a,col_b=st.columns(2)
    with col_a:
        if st.button("✦  Generate full coaching report",key="gen_ai"):
            with st.spinner("Gemini is analysing your 17,000+ games... (auto-retries on rate limit)"):
                prompt=build_prompt(stats,profile)
                report=call_gemini(prompt,gemini_key)
                st.session_state["ai_report"]=report
    with col_b:
        if st.button("📅  Generate weekly study plan",key="gen_plan"):
            with st.spinner("Building your personalised study plan..."):
                plan_prompt = build_prompt(stats,profile).replace(
                    "Write a full coaching report with these 7 sections",
                    "Write ONLY a detailed 7-day study plan. Monday through Sunday. Each day: specific task, time allocation, and exactly what to study (name specific Lichess puzzle themes, opening variations, endgame types). Tailor it to this player's weaknesses. Format: **Monday** — task details. Start immediately with Monday.")
                st.session_state["study_plan"]=call_gemini(plan_prompt,gemini_key)

    if "ai_report" in st.session_state:
        report=st.session_state["ai_report"]
        sections=re.split(r'\*\*(.+?)\*\*',report)
        html='<div class="ai-box"><div class="ai-eyebrow">♟ Groq Coach · Full Career Analysis</div>'
        for i,part in enumerate(sections):
            part=part.strip()
            if not part: continue
            if i%2==1: html+=f'<div class="ai-section-title">— {part}</div>'
            else:
                for line in part.split('\n'):
                    l=line.strip()
                    if l: html+=f'<div class="ai-body">{l}</div>'
        html+='</div>'
        st.markdown(html,unsafe_allow_html=True)

    if "study_plan" in st.session_state:
        plan=st.session_state["study_plan"]
        sections=re.split(r'\*\*(.+?)\*\*',plan)
        html='<div class="ai-box" style="margin-top:1rem"><div class="ai-eyebrow">♟ Weekly Study Plan</div>'
        for i,part in enumerate(sections):
            part=part.strip()
            if not part: continue
            if i%2==1: html+=f'<div class="ai-section-title">— {part}</div>'
            else:
                for line in part.split('\n'):
                    l=line.strip()
                    if l: html+=f'<div class="ai-body">{l}</div>'
        html+='</div>'
        st.markdown(html,unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""<div style="text-align:center;padding:2rem;border-top:1px solid #141414">
    <div style="font-family:'Playfair Display',serif;font-size:1rem;color:#2a2a2a">♟ hritikgupta · Chess Intelligence Dashboard</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#1f1f1f;margin-top:.3rem;letter-spacing:.1em">DATA: LICHESS.ORG FREE API · AI: GROQ (LLAMA 70B) · BUILT WITH STREAMLIT</div>
</div>""",unsafe_allow_html=True)

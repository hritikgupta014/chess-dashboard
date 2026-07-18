import streamlit as st
import requests
import json
import re
import os
import time
from datetime import datetime, timezone
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _get(name):
    try:    return st.secrets[name]
    except: return os.getenv(name, "")

SUPABASE_URL = _get("SUPABASE_URL")
SUPABASE_KEY = _get("SUPABASE_KEY")
GROQ_KEY     = _get("GROQ_API_KEY")
NEWS_KEY     = _get("NEWS_API_KEY")   # optional — free at newsapi.org
USERNAME     = "hritikgupta"
LI_HEADERS   = {"User-Agent": "ChessDashboard/1.0 hritikgupta"}

st.set_page_config(
    page_title="♟ hritikgupta · Chess Dashboard",
    page_icon="♟", layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,[data-testid="stApp"]{background:#0a0a0a !important;color:#e8e4dc !important;}
[data-testid="stSidebar"]{background:#111 !important;border-right:1px solid #1f1f1f !important;}
[data-testid="stSidebar"] *{color:#a09a8e !important;}
[data-testid="stSidebar"] .stButton button{background:#1a1a1a !important;border:1px solid #2a2a2a !important;color:#c9a84c !important;width:100% !important;border-radius:4px !important;padding:.5rem !important;font-family:'Inter',sans-serif !important;font-size:13px !important;}
[data-testid="stSidebar"] .stButton button:hover{background:#c9a84c !important;color:#0a0a0a !important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{background:#1a1a1a !important;border:1px solid #2a2a2a !important;color:#e8e4dc !important;border-radius:4px !important;font-family:'JetBrains Mono',monospace !important;font-size:12px !important;}
[data-testid="stSidebar"] label{color:#555 !important;font-size:11px !important;letter-spacing:.1em !important;text-transform:uppercase !important;}
[data-testid="stSidebar"] p{color:#666 !important;font-size:12px !important;}
.block-container{padding:0 !important;max-width:100% !important;}
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none !important;}
div[data-testid="stTabs"] > div > div > button{background:#111 !important;color:#555 !important;border:none !important;border-bottom:2px solid #1a1a1a !important;font-family:'JetBrains Mono',monospace !important;font-size:11px !important;letter-spacing:.1em !important;text-transform:uppercase !important;padding:.6rem 1.2rem !important;border-radius:0 !important;}
div[data-testid="stTabs"] > div > div > button[aria-selected="true"]{color:#c9a84c !important;border-bottom:2px solid #c9a84c !important;}
div[data-testid="stTabContent"]{padding:0 !important;}

/* Masthead */
.masthead{background:#0d0d0d;border-bottom:1px solid #1f1f1f;padding:1.5rem 2rem;position:relative;overflow:hidden;}
.masthead::before{content:'♟';position:absolute;right:2rem;top:50%;transform:translateY(-50%);font-size:6rem;color:rgba(201,168,76,.04);pointer-events:none;}
.masthead-eyebrow{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;letter-spacing:.3em;text-transform:uppercase;margin-bottom:.3rem;}
.masthead-title{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:900;color:#e8e4dc;line-height:1.1;margin:0;}
.masthead-title span{color:#c9a84c;}
.masthead-meta{font-family:'Inter',sans-serif;font-size:11px;color:#555;margin-top:.5rem;}

/* Stat strip */
.stat-strip{display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #1a1a1a;}
@media(max-width:768px){.stat-strip{grid-template-columns:repeat(3,1fr);}}
.stat-cell{padding:.8rem 1.2rem;border-right:1px solid #1a1a1a;}
.stat-cell:last-child{border-right:none;}
.stat-val{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:700;color:#c9a84c;line-height:1;}
.stat-lbl{font-family:'Inter',sans-serif;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-top:.2rem;}

/* Section */
.section-wrap{padding:1.5rem 2rem;border-bottom:1px solid #141414;}
@media(max-width:768px){.section-wrap{padding:1rem 1rem;}}
.section-head{display:flex;align-items:baseline;gap:.8rem;margin-bottom:1.2rem;border-bottom:1px solid #1f1f1f;padding-bottom:.6rem;}
.section-title{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:#e8e4dc;}
.section-pill{font-family:'JetBrains Mono',monospace;font-size:9px;background:#1a1a1a;color:#c9a84c;border:1px solid #2a2a2a;padding:2px 8px;letter-spacing:.1em;text-transform:uppercase;}

/* Rating cards */
.perf-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;background:#1a1a1a;}
.perf-card{background:#0d0d0d;padding:1rem .8rem;text-align:center;}
.perf-format{font-family:'JetBrains Mono',monospace;font-size:8px;color:#555;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.3rem;}
.perf-rating{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:#e8e4dc;line-height:1;}
.perf-prog{font-family:'JetBrains Mono',monospace;font-size:9px;margin-top:.2rem;}
.perf-prog.up{color:#4a8c3f;}.perf-prog.dn{color:#8c3f3f;}
.perf-games{font-family:'Inter',sans-serif;font-size:9px;color:#444;margin-top:.2rem;}

/* WDL */
.wdl-bar{display:flex;height:5px;border-radius:3px;overflow:hidden;background:#1a1a1a;}
.wdl-w{background:#4a8c3f;}.wdl-d{background:#555;}.wdl-l{background:#8c3f3f;}
.wdl-labels{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:8px;color:#555;margin-top:2px;}

/* Game links */
.game-card{background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid #c9a84c;padding:.8rem 1rem;margin-bottom:.4rem;display:flex;align-items:center;gap:.8rem;}
.game-rank{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:#2a2a2a;min-width:1.8rem;text-align:center;}
.game-rank.gold{color:#c9a84c;}
.game-opp{font-family:'Inter',sans-serif;font-size:13px;font-weight:500;color:#e8e4dc;flex:1;}
.game-meta{font-family:'JetBrains Mono',monospace;font-size:9px;color:#444;}
.game-rating{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#c9a84c;text-align:right;}
.game-link{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:9px;color:#0a0a0a;background:#c9a84c;padding:2px 8px;text-decoration:none;margin-top:2px;}
.title-badge{font-family:'JetBrains Mono',monospace;font-size:9px;background:#c9a84c;color:#0a0a0a;padding:1px 5px;font-weight:600;margin-left:.3rem;}

/* Opening rows */
.opening-row{display:flex;align-items:center;gap:.6rem;padding:.5rem 0;border-bottom:1px solid #141414;}
.opening-row:last-child{border-bottom:none;}
.opening-name{flex:1;font-family:'Inter',sans-serif;font-size:12px;color:#e8e4dc;}
.opening-bar-wrap{width:80px;height:4px;background:#1a1a1a;border-radius:2px;overflow:hidden;}
.opening-bar-fill{height:100%;border-radius:2px;background:#c9a84c;}
.opening-bar-fill.bad{background:#8c3f3f;}
.opening-wr{font-family:'JetBrains Mono',monospace;font-size:10px;min-width:38px;text-align:right;}
.opening-wr.good{color:#4a8c3f;}.opening-wr.bad{color:#8c3f3f;}
.opening-games{font-size:9px;color:#444;min-width:45px;text-align:right;}

/* Bucket rows */
.bucket-row{display:flex;align-items:center;gap:.8rem;padding:.5rem 0;border-bottom:1px solid #141414;}
.bucket-label{font-family:'JetBrains Mono',monospace;font-size:10px;color:#a09a8e;min-width:80px;}
.bucket-bar-wrap{flex:1;height:5px;background:#1a1a1a;border-radius:3px;overflow:hidden;}
.bucket-bar{height:100%;border-radius:3px;}
.bucket-wr{font-family:'JetBrains Mono',monospace;font-size:10px;min-width:40px;text-align:right;}
.bucket-games{font-size:9px;color:#444;min-width:50px;text-align:right;}

/* News */
.news-featured{background:#111;border:1px solid #1f1f1f;border-top:3px solid #c9a84c;padding:1.2rem;}
.news-cat{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.4rem;}
.news-title{font-family:'Playfair Display',serif;font-size:1.1rem;color:#e8e4dc;margin-bottom:.4rem;line-height:1.4;}
.news-body{font-family:'Inter',sans-serif;font-size:12px;color:#666;line-height:1.7;}
.news-meta{font-family:'JetBrains Mono',monospace;font-size:9px;color:#333;margin-top:.5rem;}
.news-card{background:#0d0d0d;border:1px solid #1a1a1a;border-left:2px solid #2a2a2a;padding:.7rem 1rem;margin-bottom:.5rem;transition:border-left-color .2s;}
.news-card-title{font-family:'Inter',sans-serif;font-size:13px;font-weight:500;color:#e0e0e0;line-height:1.4;margin-bottom:.2rem;}
.news-source{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;}

/* Tournaments */
.tourn-card{background:#0d0d0d;border:1px solid #1a1a1a;padding:.8rem 1rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem;}
.tourn-badge{font-family:'JetBrains Mono',monospace;font-size:8px;background:#4a8c3f;color:#fff;padding:2px 6px;letter-spacing:.1em;flex-shrink:0;}
.tourn-badge.live{background:#8c3f3f;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.tourn-name{font-family:'Inter',sans-serif;font-size:13px;font-weight:500;color:#e8e4dc;flex:1;}
.tourn-meta{font-family:'JetBrains Mono',monospace;font-size:9px;color:#444;}
.tourn-link{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;text-decoration:none;}

/* AI */
.ai-box{background:#0d0d0d;border:1px solid #1f1f1f;border-top:2px solid #c9a84c;padding:1.5rem;margin-bottom:1rem;}
.ai-eyebrow{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c9a84c;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.8rem;}
.ai-section-title{font-family:'Playfair Display',serif;font-size:.95rem;color:#e8e4dc;margin:1rem 0 .4rem;}
.ai-body{font-family:'Inter',sans-serif;font-size:12px;color:#888;line-height:1.8;margin-bottom:.2rem;}

/* Phase cards */
.phase-card{background:#111;border:1px solid #1a1a1a;padding:1rem;margin-bottom:.5rem;}
.phase-label{font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.3rem;}
.phase-val{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#c9a84c;}
.phase-sub{font-family:'Inter',sans-serif;font-size:11px;color:#555;margin-top:.2rem;}

/* No data */
.no-data{font-family:'Inter',sans-serif;font-size:12px;color:#333;padding:1.5rem;text-align:center;background:#0d0d0d;border:1px dashed #1a1a1a;}

/* Mobile responsive helpers */
@media(max-width:768px){
  .masthead-title{font-size:1.6rem;}
  .stat-val{font-size:1.4rem;}
  .section-title{font-size:1rem;}
}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_supabase():
    hdrs = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/chess_dashboard",
                         headers=hdrs,
                         params={"id": f"eq.{USERNAME}", "select": "data"},
                         timeout=15)
        if r.status_code == 200:
            rows = r.json()
            if rows: return rows[0]["data"]
    except Exception as e:
        st.error(f"Supabase error: {e}")
    return None

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(api_key, query="chess tournament 2025", count=9):
    if not api_key: return []
    try:
        r = requests.get("https://newsapi.org/v2/everything",
                         params={"q":query,"language":"en","sortBy":"publishedAt",
                                 "pageSize":count,"apiKey":api_key}, timeout=8)
        if r.status_code == 200:
            return [a for a in r.json().get("articles",[])
                    if a.get("title") and "[Removed]" not in a.get("title","")]
    except: pass
    return []

@st.cache_data(ttl=120, show_spinner=False)
def fetch_tournaments():
    try:
        r = requests.get("https://lichess.org/api/broadcast/top",
                         headers=LI_HEADERS, timeout=8)
        if r.status_code == 200:
            return r.json().get("active",[]) + r.json().get("upcoming",[])
    except: pass
    return []

# ── GROQ ─────────────────────────────────────────────────────────────────────
def call_groq(prompt, api_key, max_tokens=2000):
    models = ["llama-3.3-70b-versatile","llama3-70b-8192","llama3-8b-8192"]
    system = ("You are an expert chess coach. Write directly and analytically. "
              "Use ** for section headers. Cite actual numbers. Be specific and actionable.")
    for model in models:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                json={"model":model,"messages":[
                    {"role":"system","content":system},
                    {"role":"user","content":prompt}],
                    "max_tokens":max_tokens,"temperature":0.7},
                timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                time.sleep(15); continue
            elif r.status_code in (400,404): continue
            else: return f"Groq error {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return f"Error: {e}"
    return "Could not reach Groq. Check your API key."

def render_ai(text, eyebrow):
    parts = re.split(r'\*\*(.+?)\*\*', text)
    html  = f'<div class="ai-box"><div class="ai-eyebrow">{eyebrow}</div>'
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
        if i % 2 == 1:
            html += f'<div class="ai-section-title">— {part}</div>'
        else:
            for line in part.split('\n'):
                l = line.strip()
                if l: html += f'<div class="ai-body">{l}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def time_ago(pub_date_str):
    if not pub_date_str: return ""
    try:
        dt   = datetime.fromisoformat(pub_date_str.replace("Z","+00:00"))
        diff = datetime.now(dt.tzinfo) - dt
        h    = int(diff.total_seconds() // 3600)
        if h < 1:   return "Just now"
        if h < 24:  return f"{h}h ago"
        return f"{h//24}d ago"
    except: return ""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ♟ Settings")
    st.markdown("---")
    groq_key = st.text_input("Groq API Key", type="password",
        value=st.session_state.get("groq_key", GROQ_KEY),
        help="Free at console.groq.com")
    if groq_key: st.session_state["groq_key"] = groq_key

    news_key = st.text_input("NewsAPI Key (optional)", type="password",
        value=st.session_state.get("news_key", NEWS_KEY),
        help="Free at newsapi.org — 100 req/day")
    if news_key: st.session_state["news_key"] = news_key

    st.markdown("---")
    st.markdown("""<p>Data auto-refreshes every 2 hrs via GitHub Actions → Supabase.</p>""",
                unsafe_allow_html=True)
    st.markdown("---")
    if st.button("⟳  Reload data"):
        st.cache_data.clear()
        for k in ["ai_report","study_plan","phase_report","ai_news"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#1f1f1f;font-family:JetBrains Mono,monospace;line-height:1.8'>DATA: LICHESS + SUPABASE<br>AI: GROQ LLAMA 70B<br>NEWS: NEWSAPI FREE<br>REFRESH: 2HRS AUTO</div>",
                unsafe_allow_html=True)

# ── LOAD ──────────────────────────────────────────────────────────────────────
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Add SUPABASE_URL and SUPABASE_KEY to Streamlit Secrets.")
    st.stop()

with st.spinner("Loading..."):
    db_data = load_supabase()

if not db_data:
    st.markdown("""<div style='padding:3rem;text-align:center;font-family:JetBrains Mono,monospace;color:#555'>
        <div style='font-size:2rem'>♟</div>
        <div style='color:#c9a84c;font-size:13px;margin:.5rem 0'>No data yet</div>
        <div style='font-size:11px'>Go to GitHub repo → Actions → Refresh Chess Dashboard → Run workflow</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

profile  = db_data.get("profile", {})
stats    = db_data.get("stats", {})
updated  = db_data.get("updated_at","")[:16].replace("T"," ")
perfs    = profile.get("perfs",{}) if profile else {}

# ── MASTHEAD ──────────────────────────────────────────────────────────────────
blitz_r  = perfs.get("blitz",{}).get("rating","—")
rapid_r  = perfs.get("rapid",{}).get("rating","—")
bullet_r = perfs.get("bullet",{}).get("rating","—")
title_b  = profile.get("title","") if profile else ""
title_h  = f"<span style='font-family:JetBrains Mono;font-size:.9rem;color:#c9a84c'>{title_b} </span>" if title_b else ""
created  = profile.get("createdAt",0)
since    = datetime.fromtimestamp(created/1000,tz=timezone.utc).strftime("%b %Y") if created else "—"
total_lc = profile.get("count",{}).get("all", stats.get("total",0))

st.markdown(f"""<div class="masthead">
    <div class="masthead-eyebrow">Lichess · Chess Intelligence Dashboard</div>
    <div class="masthead-title">{title_h}<span>hritik</span>gupta</div>
    <div class="masthead-meta">Since {since} &nbsp;·&nbsp; {total_lc:,} lifetime games &nbsp;·&nbsp; Blitz {blitz_r} &nbsp;·&nbsp; Rapid {rapid_r} &nbsp;·&nbsp; Bullet {bullet_r} &nbsp;·&nbsp; Updated {updated} UTC</div>
</div>""", unsafe_allow_html=True)

# ── STAT STRIP ────────────────────────────────────────────────────────────────
all_w = sum(d["w"] for d in stats.get("by_format",{}).values())
total = stats.get("total",0)
wr    = round(all_w/total*100,1) if total else 0
best_streak = max((v["best"] for v in stats.get("streaks",{}).values()),default=0)
titled_w    = len(stats.get("titled_wins",[]))

st.markdown(f"""<div class="stat-strip">
    <div class="stat-cell"><div class="stat-val">{total:,}</div><div class="stat-lbl">Games</div></div>
    <div class="stat-cell"><div class="stat-val">{all_w:,}</div><div class="stat-lbl">Wins</div></div>
    <div class="stat-cell"><div class="stat-val">{wr}%</div><div class="stat-lbl">Win rate</div></div>
    <div class="stat-cell"><div class="stat-val">{best_streak}</div><div class="stat-lbl">Best streak</div></div>
    <div class="stat-cell"><div class="stat-val">{titled_w}</div><div class="stat-lbl">Titled scalps</div></div>
</div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 My Stats", "♟ Game Analysis", "🧠 AI Coach", "📰 News", "🏆 Tournaments"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MY STATS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    # Ratings
    if perfs:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">Ratings</div><div class="section-pill">Live · Lichess</div></div>', unsafe_allow_html=True)
        fmt_order = ["bullet","ultraBullet","blitz","rapid","classical",
                     "chess960","antichess","atomic","horde","kingOfTheHill",
                     "racingKings","crazyhouse","threeCheck","puzzle"]
        html = '<div class="perf-grid">'
        for pf in fmt_order:
            if pf not in perfs: continue
            p=perfs[pf]; r=p.get("rating","?"); prog=p.get("prog",0); g=p.get("games",0)
            if g==0: continue
            ps=f"+{prog}" if prog>0 else str(prog); pc="up" if prog>0 else "dn" if prog<0 else ""
            lbl=pf.replace("kingOfTheHill","KotH").replace("racingKings","Racing").replace("ultraBullet","UltraBlt").replace("correspondence","Corr")
            html+=f'<div class="perf-card"><div class="perf-format">{lbl}</div><div class="perf-rating">{r}</div><div class="perf-prog {pc}">{ps if prog!=0 else "—"}</div><div class="perf-games">{g:,} games</div></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Format breakdown
    by_fmt = [(pf,d) for pf,d in sorted(stats.get("by_format",{}).items(),key=lambda x:x[1]["games"],reverse=True) if d["games"]>0]
    if by_fmt:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">By Format</div><div class="section-pill">All time</div></div>', unsafe_allow_html=True)
        cols = st.columns(max(1, min(len(by_fmt), 4)))
        for i,(pf,d) in enumerate(by_fmt[:8]):
            g=d["games"]; w=d["w"]; dr=d["d"]; l=d["l"]
            wr_p=round(w/g*100,1) if g else 0
            wp=round(w/g*100,1) if g else 0; dp=round(dr/g*100,1) if g else 0; lp=round(l/g*100,1) if g else 0
            with cols[i%4]:
                st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:.8rem;margin-bottom:.5rem">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem">{pf}</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#c9a84c">{wr_p}%</div>
                    <div style="margin:.3rem 0"><div class="wdl-bar"><div class="wdl-w" style="width:{wp}%"></div><div class="wdl-d" style="width:{dp}%"></div><div class="wdl-l" style="width:{lp}%"></div></div>
                    <div class="wdl-labels"><span style="color:#4a8c3f">{w:,}W</span><span>{dr:,}D</span><span style="color:#8c3f3f">{l:,}L</span></div></div>
                    <div style="font-size:9px;color:#333">{g:,} games</div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # White vs Black
    cs = stats.get("color_stats",{})
    if cs:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">White vs Black</div><div class="section-pill">Colour split</div></div>', unsafe_allow_html=True)
        col1,col2 = st.columns(2)
        for col, (color, piece) in zip([col1,col2],[("white","♔"),("black","♚")]):
            d=cs.get(color,{"w":0,"d":0,"l":0}); t=d["w"]+d["d"]+d["l"]
            wr_c=round(d["w"]/t*100,1) if t else 0
            wp=round(d["w"]/t*100,1) if t else 0; dp=round(d["d"]/t*100,1) if t else 0; lp=round(d["l"]/t*100,1) if t else 0
            with col:
                st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:1.2rem;text-align:center">
                    <div style="font-size:1.8rem">{piece}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#555;letter-spacing:.2em;text-transform:uppercase;margin:.3rem 0">As {color}</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:700;color:#c9a84c">{wr_c}%</div>
                    <div style="max-width:160px;margin:.4rem auto 0">
                        <div class="wdl-bar"><div class="wdl-w" style="width:{wp}%"></div><div class="wdl-d" style="width:{dp}%"></div><div class="wdl-l" style="width:{lp}%"></div></div>
                        <div class="wdl-labels"><span style="color:#4a8c3f">{d['w']:,}W</span><span>{d['d']:,}D</span><span style="color:#8c3f3f">{d['l']:,}L</span></div>
                    </div>
                    <div style="font-size:9px;color:#333;margin-top:.3rem">{t:,} games</div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Rating buckets
    opp_buckets = stats.get("opp_buckets",{})
    if opp_buckets:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">vs Rating Ranges</div><div class="section-pill">Where you win and lose</div></div>', unsafe_allow_html=True)
        buckets = sorted(opp_buckets.items(), key=lambda x:int(x[0].split("-")[0]))
        html = ""
        for bkt,d in buckets:
            g=d["g"]
            if g<5: continue
            wr_b=round(d["w"]/g*100,1); bar=min(wr_b,100)
            col="#4a8c3f" if wr_b>=50 else "#c9a84c" if wr_b>=40 else "#8c3f3f"
            html+=f"""<div class="bucket-row">
                <div class="bucket-label">{bkt}</div>
                <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar}%;background:{col}"></div></div>
                <div class="bucket-wr" style="color:{col}">{wr_b}%</div>
                <div class="bucket-games">{g:,} games</div>
            </div>"""
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Time analysis
    hourly  = stats.get("hourly",{})
    weekday = stats.get("weekday",{})
    if hourly or weekday:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">When You Play Best</div><div class="section-pill">Hour · Day</div></div>', unsafe_allow_html=True)
        col1,col2 = st.columns(2)
        with col1:
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.6rem">By hour (UTC)</div>', unsafe_allow_html=True)
            html=""
            for h in range(24):
                d=hourly.get(str(h),{"w":0,"g":0})
                if d["g"]<10: continue
                wr_h=round(d["w"]/d["g"]*100,1); bar=min(wr_h,100)
                col="#4a8c3f" if wr_h>=52 else "#c9a84c" if wr_h>=48 else "#8c3f3f"
                html+=f"""<div class="bucket-row">
                    <div class="bucket-label">{h:02d}:00</div>
                    <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar}%;background:{col}"></div></div>
                    <div class="bucket-wr" style="color:{col}">{wr_h}%</div>
                    <div class="bucket-games">{d['g']:,}</div>
                </div>"""
            st.markdown(html, unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.6rem">By day of week</div>', unsafe_allow_html=True)
            html=""
            for day in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
                d=weekday.get(day,{"w":0,"g":0})
                if d["g"]<10: continue
                wr_d=round(d["w"]/d["g"]*100,1); bar=min(wr_d,100)
                col="#4a8c3f" if wr_d>=52 else "#c9a84c" if wr_d>=48 else "#8c3f3f"
                html+=f"""<div class="bucket-row">
                    <div class="bucket-label">{day}</div>
                    <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar}%;background:{col}"></div></div>
                    <div class="bucket-wr" style="color:{col}">{wr_d}%</div>
                    <div class="bucket-games">{d['g']:,}</div>
                </div>"""
            st.markdown(html, unsafe_allow_html=True)
            tilt=sum(1 for s in stats.get("session_data",[]) if len(s)>=6 and s[:3].count("w")>=2 and s[-3:].count("l")>=2)
            tc="#8c3f3f" if tilt>10 else "#c9a84c"
            st.markdown(f"""<div style="margin-top:1rem;background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid {tc};padding:.8rem 1rem">
                <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-bottom:.2rem">TILT SESSIONS</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:{tc}">{tilt}</div>
                <div style="font-size:10px;color:#555">Started well, ended badly</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Streaks
    streaks = sorted([(pf,v["best"]) for pf,v in stats.get("streaks",{}).items() if v["best"]>=2], key=lambda x:x[1], reverse=True)
    if streaks:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">Best Streaks</div><div class="section-pill">Per format</div></div>', unsafe_allow_html=True)
        cols = st.columns(max(1,min(len(streaks),5)))
        for i,(pf,best) in enumerate(streaks[:5]):
            with cols[i]:
                st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:.8rem 1rem;display:flex;align-items:center;gap:1rem;margin-bottom:.4rem">
                    <div style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:700;color:#c9a84c;line-height:1">{best}</div>
                    <div><div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#a09a8e">{pf.upper()}</div><div style="font-size:11px;color:#555">best streak</div></div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Best wins WITH game links
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-head"><div class="section-title">Best Wins</div><div class="section-pill">Click to view game</div></div>', unsafe_allow_html=True)
        top = sorted(stats.get("high_rated_wins",[]), key=lambda x:x.get("opp_rating",0), reverse=True)[:10]
        if top:
            for i,hw in enumerate(top):
                rc="gold" if i==0 else ""; medal="🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else ""
                tb=f'<span class="title-badge">{hw.get("title","")}</span>' if hw.get("title") else ""
                game_id = hw.get("id","")
                link_html = f'<a class="game-link" href="https://lichess.org/{game_id}" target="_blank">Open on Lichess ↗</a>' if game_id else ""
                st.markdown(f"""<div class="game-card">
                    <div class="game-rank {rc}">{medal or i+1}</div>
                    <div style="flex:1">
                        <div class="game-opp">{hw['name']}{tb}</div>
                        <div class="game-meta">{hw.get('perf','')} · +{hw.get('diff',0)} pts</div>
                        {link_html}
                    </div>
                    <div class="game-rating">{hw.get('opp_rating','?')}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="no-data">No upsets yet</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-head"><div class="section-title">Titled Scalps</div><div class="section-pill">Click to view game</div></div>', unsafe_allow_html=True)
        titled_wins = stats.get("titled_wins",[])
        if titled_wins:
            by_title = defaultdict(list)
            for tw in titled_wins: by_title[tw["title"]].append(tw)
            for tc in ["GM","IM","FM","CM","NM","WGM","WIM","WFM"]:
                if tc not in by_title: continue
                wins = by_title[tc]
                for w in wins[:3]:
                    game_id = w.get("id","")
                    link_html = f'<a class="game-link" href="https://lichess.org/{game_id}" target="_blank">View ↗</a>' if game_id else ""
                    st.markdown(f"""<div class="game-card">
                        <div style="font-family:'JetBrains Mono',monospace;font-size:9px;background:#c9a84c;color:#0a0a0a;padding:2px 6px;font-weight:600;flex-shrink:0">{tc}</div>
                        <div style="flex:1">
                            <div class="game-opp">{w['name']}</div>
                            <div class="game-meta">{w.get('perf','')} · rated {w.get('rating','?')}</div>
                            {link_html}
                        </div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="no-data">No titled wins yet</div>', unsafe_allow_html=True)
        tl = len(stats.get("titled_losses",[]))
        st.markdown(f"""<div style="margin-top:.8rem;background:#0d0d0d;border:1px solid #1a1a1a;padding:.8rem 1rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-bottom:.2rem">TITLED LOSSES</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#8c3f3f">{tl}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Openings
    wr_w = stats.get("wr_w",[]); wr_b = stats.get("wr_b",[])
    if wr_w or wr_b:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">Opening Analysis</div><div class="section-pill">Min 5 games</div></div>', unsafe_allow_html=True)
        def op_html(wr_list, top=True, limit=8):
            items = wr_list[:limit] if top else wr_list[-limit:]
            if not items: return '<div class="no-data">Not enough data</div>'
            html = ""
            for row in items:
                op,wr,t = row[0],row[1],row[2]
                cls="good" if top else "bad"; bar="opening-bar-fill" if top else "opening-bar-fill bad"
                html+=f"""<div class="opening-row">
                    <div class="opening-name">{op[:34]}</div>
                    <div class="opening-bar-wrap"><div class="{bar}" style="width:{wr}%"></div></div>
                    <div class="opening-wr {cls}">{wr}%</div>
                    <div class="opening-games">{t}g</div>
                </div>"""
            return html
        col1,col2 = st.columns(2)
        with col1:
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem">♔ Best as White</div>', unsafe_allow_html=True)
            st.markdown(op_html(wr_w, True), unsafe_allow_html=True)
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin:1rem 0 .4rem">♔ Worst as White</div>', unsafe_allow_html=True)
            st.markdown(op_html(wr_w, False), unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem">♚ Best as Black</div>', unsafe_allow_html=True)
            st.markdown(op_html(wr_b, True), unsafe_allow_html=True)
            st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin:1rem 0 .4rem">♚ Worst as Black</div>', unsafe_allow_html=True)
            st.markdown(op_html(wr_b, False), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GAME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Analyse a Game</div><div class="section-pill">Lichess Engine</div></div>', unsafe_allow_html=True)

    st.markdown("""<div style="font-family:'Inter',sans-serif;font-size:13px;color:#666;margin-bottom:1rem;line-height:1.6">
        Enter a Lichess game ID or full URL to open it with full Stockfish engine analysis. 
        Or paste PGN below to analyse any game directly in the browser.
    </div>""", unsafe_allow_html=True)

    col1,col2 = st.columns([2,1])
    with col1:
        game_input = st.text_input("Game ID or Lichess URL",
            placeholder="e.g. GZp7ehzJ or https://lichess.org/GZp7ehzJ",
            label_visibility="collapsed")
    with col2:
        open_btn = st.button("Open on Lichess ↗", use_container_width=True)

    if open_btn and game_input:
        # Extract game ID from URL or use as-is
        gid = game_input.strip().rstrip("/").split("/")[-1].split("#")[0]
        st.markdown(f"""<div style="margin:.5rem 0">
            <a href="https://lichess.org/{gid}" target="_blank" style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#c9a84c">
                → Open https://lichess.org/{gid} with Stockfish analysis ↗
            </a>
        </div>""", unsafe_allow_html=True)
        # Also embed the game
        st.markdown(f"""<iframe src="https://lichess.org/embed/game/{gid}?theme=brown&bg=dark"
            width="100%" height="500" frameborder="0" style="border:1px solid #1a1a1a;"></iframe>""",
            unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid #1f1f1f;margin:1.5rem 0">', unsafe_allow_html=True)

    # PGN paste analyser using chess.js
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.5rem">Paste PGN to analyse</div>', unsafe_allow_html=True)
    pgn_input = st.text_area("", height=120,
        placeholder="Paste any PGN here...\ne.g. 1. e4 e5 2. Nf3 Nc6 3. Bb5",
        label_visibility="collapsed", key="pgn_paste")

    if pgn_input.strip():
        # URL-encode PGN and open in Lichess analysis
        import urllib.parse
        pgn_encoded = urllib.parse.quote(pgn_input.strip())
        lichess_url = f"https://lichess.org/paste"
        st.markdown(f"""<div style="margin:.5rem 0 1rem">
            <a href="{lichess_url}" target="_blank" style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#0a0a0a;background:#c9a84c;padding:6px 14px;text-decoration:none;display:inline-block">
                → Paste & analyse on Lichess with Stockfish ↗
            </a>
        </div>""", unsafe_allow_html=True)
        st.info("💡 Tip: Copy your PGN, click the button above, paste it on Lichess and get full Stockfish analysis at any depth.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Quick links to recent games with analysis
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Your Notable Games</div><div class="section-pill">Quick analysis links</div></div>', unsafe_allow_html=True)

    top_wins = sorted(stats.get("high_rated_wins",[]), key=lambda x:x.get("opp_rating",0), reverse=True)[:5]
    titled   = stats.get("titled_wins",[])[:5]
    all_notable = top_wins + titled
    if all_notable:
        for g in all_notable:
            game_id = g.get("id","")
            if not game_id: continue
            name = g.get("name","?")
            title_str = f"[{g.get('title','')}] " if g.get("title") else ""
            diff = f"+{g.get('diff',0)} pts" if g.get("diff",0) > 0 else ""
            opp_r = g.get("opp_rating","?") or g.get("rating","?")
            st.markdown(f"""<div style="display:flex;align-items:center;gap:1rem;padding:.6rem 0;border-bottom:1px solid #141414">
                <div style="flex:1;font-family:'Inter',sans-serif;font-size:13px;color:#e8e4dc">{title_str}{name} <span style="color:#555;font-size:11px">({opp_r})</span> {diff}</div>
                <a href="https://lichess.org/{game_id}" target="_blank" style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#0a0a0a;background:#c9a84c;padding:3px 10px;text-decoration:none;flex-shrink:0">Analyse ↗</a>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="no-data">No notable games found yet</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI COACH
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    groq_key = st.session_state.get("groq_key","")

    if not groq_key:
        st.markdown("""<div class="section-wrap"><div class="ai-box">
            <div class="ai-eyebrow">Setup required</div>
            <div class="ai-body">Add your free Groq API key in the sidebar.<br>
            Get it at <strong style="color:#e8e4dc">console.groq.com</strong> — no credit card, takes 2 minutes.</div>
        </div></div>""", unsafe_allow_html=True)
    else:
        # ── PHASE ANALYSIS ───────────────────────────────────────────────────
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">Game Phase Analysis</div><div class="section-pill">Openings · Middlegame · Endgame</div></div>', unsafe_allow_html=True)

        wr_w = stats.get("wr_w",[]); wr_b = stats.get("wr_b",[])
        cs   = stats.get("color_stats",{})
        terminations = stats.get("terminations",{})

        # Show phase data cards
        col1,col2,col3 = st.columns(3)
        with col1:
            st.markdown("""<div class="phase-card">
                <div class="phase-label">Opening phase</div>
                <div class="phase-val">♔♚</div>
                <div class="phase-sub">Based on your opening win rates</div>
            </div>""", unsafe_allow_html=True)
            if wr_w:
                st.markdown(f"""<div style="font-size:11px;color:#555;font-family:'Inter',sans-serif;margin-top:.5rem">
                    Best White opening: <span style="color:#c9a84c">{wr_w[0][0]} ({wr_w[0][1]}%)</span><br>
                    Worst White opening: <span style="color:#8c3f3f">{wr_w[-1][0]} ({wr_w[-1][1]}%)</span>
                </div>""", unsafe_allow_html=True)
            if wr_b:
                st.markdown(f"""<div style="font-size:11px;color:#555;font-family:'Inter',sans-serif;margin-top:.3rem">
                    Best Black opening: <span style="color:#c9a84c">{wr_b[0][0]} ({wr_b[0][1]}%)</span><br>
                    Worst Black opening: <span style="color:#8c3f3f">{wr_b[-1][0]} ({wr_b[-1][1]}%)</span>
                </div>""", unsafe_allow_html=True)
        with col2:
            wh = cs.get("white",{"w":0,"d":0,"l":0}); bk = cs.get("black",{"w":0,"d":0,"l":0})
            wt = wh["w"]+wh["d"]+wh["l"]; bt = bk["w"]+bk["d"]+bk["l"]
            wr_w_pct = round(wh["w"]/wt*100,1) if wt else 0
            wr_b_pct = round(bk["w"]/bt*100,1) if bt else 0
            gap = round(wr_w_pct - wr_b_pct, 1)
            st.markdown(f"""<div class="phase-card">
                <div class="phase-label">Colour gap</div>
                <div class="phase-val" style="color:{'#8c3f3f' if gap>5 else '#c9a84c'}">{gap:+.1f}%</div>
                <div class="phase-sub">White {wr_w_pct}% vs Black {wr_b_pct}%</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            resign_rate = round(terminations.get("resign",0) / total * 100, 1) if total else 0
            timeout_rate = round(terminations.get("outoftime",0) / total * 100, 1) if total else 0
            st.markdown(f"""<div class="phase-card">
                <div class="phase-label">How games end</div>
                <div class="phase-val">📊</div>
                <div class="phase-sub">Resign: {resign_rate}% · Timeout: {timeout_rate}%</div>
            </div>""", unsafe_allow_html=True)

        if st.button("✦  Generate phase-by-phase AI analysis", key="gen_phase"):
            with st.spinner("Analysing your openings, middlegame and endgame patterns..."):
                phase_prompt = f"""Chess player: {USERNAME} | {stats.get('total',0):,} games | Blitz {perfs.get('blitz',{}).get('rating','?')} Rapid {perfs.get('rapid',{}).get('rating','?')}

OPENING DATA (win rate, games, white/black):
Best as White: {', '.join(f"{r[0]} {r[1]}%/{r[2]}g" for r in (wr_w or [])[:5])}
Worst as White: {', '.join(f"{r[0]} {r[1]}%/{r[2]}g" for r in (wr_w or [])[-5:])}
Best as Black: {', '.join(f"{r[0]} {r[1]}%/{r[2]}g" for r in (wr_b or [])[:5])}
Worst as Black: {', '.join(f"{r[0]} {r[1]}%/{r[2]}g" for r in (wr_b or [])[-5:])}

COLOR GAP: White {wr_w_pct}% vs Black {wr_b_pct}% (gap: {gap:+.1f}%)
HOW GAMES END: {dict(list(terminations.items())[:8])}
TILT SESSIONS: {sum(1 for s in stats.get('session_data',[]) if len(s)>=6 and s[:3].count('w')>=2 and s[-3:].count('l')>=2)}

Write a detailed analysis covering exactly these 5 sections (use ** for headers):

**Opening Repertoire Analysis**
For each of your main openings as White and Black: current win rate, verdict (keep/drop/study more), and exactly what variation or alternative to study. Be specific — name exact opening lines.

**Endgame Assessment**
Based on how games end (resignation rates, game lengths implied by format) and opening choices: assess likely endgame strengths and weaknesses. Cover: pawn endgames, rook endgames, bishop/knight endgames, queen endgames. Grade each from A (strong) to D (weak) with reasoning.

**Colour Imbalance Deep-dive**
The {gap:.1f}% gap between White and Black performance is significant. Explain exactly why this happens and what to do about it.

**Tactical vs Positional Profile**
Based on opening choices and win rates, characterise this player's style and where they lose most games.

**Top 5 Improvement Actions**
Specific, ordered, actionable. Name exact resources for each."""
                st.session_state["phase_report"] = call_groq(phase_prompt, groq_key, max_tokens=2000)

        if "phase_report" in st.session_state:
            render_ai(st.session_state["phase_report"], "♟ Phase Analysis · Groq Llama 70B")
        st.markdown('</div>', unsafe_allow_html=True)

        # ── FULL COACHING REPORT ─────────────────────────────────────────────
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div class="section-title">Full Coaching Report</div><div class="section-pill">Career overview + study plan</div></div>', unsafe_allow_html=True)

        col_a,col_b = st.columns(2)
        with col_a:
            if st.button("✦  Generate full coaching report", key="gen_ai"):
                with st.spinner("Groq is analysing your career..."):
                    perfs_str = " | ".join(f"{pf} {perfs[pf].get('rating','?')} ({perfs[pf].get('games',0):,}g {perfs[pf].get('prog',0):+d})" for pf in ["bullet","blitz","rapid","classical"] if pf in perfs)
                    fmt_str   = " | ".join(f"{pf} {round(d['w']/d['games']*100,1)}% ({d['games']:,}g)" for pf,d in sorted(stats.get("by_format",{}).items(),key=lambda x:x[1]["games"],reverse=True) if d["games"]>10)
                    prompt = f"""Chess coaching for {USERNAME} | {stats.get('total',0):,} career games
RATINGS: {perfs_str}
FORMATS: {fmt_str}
WHITE: {wr_w_pct}% | BLACK: {wr_b_pct}% (gap {gap:+.1f}%)
TITLED WINS: {len(stats.get('titled_wins',[]))} | LOSSES: {len(stats.get('titled_losses',[]))}
UPSETS (150+): {len(stats.get('high_rated_wins',[]))}
BEST STREAK: {max((v['best'] for v in stats.get('streaks',{}).values()),default=0)}
Write a coaching report: **Player Overview** | **Strengths** (3, with numbers) | **Critical Weaknesses** (3, with numbers) | **Opening Surgery** (keep/drop/replace with specifics) | **Psychological Patterns** | **Weekly Study Plan** (Mon-Sun, specific tasks) | **Study Resources** (5 named: YouTube channels, Chessable courses, books)"""
                    st.session_state["ai_report"] = call_groq(prompt, groq_key)
        with col_b:
            if st.button("📅  Weekly study plan only", key="gen_plan"):
                with st.spinner("Building study plan..."):
                    prompt = f"""Chess player {USERNAME}, 2000+ rated, {stats.get('total',0):,} games.
Weak openings as White: {', '.join(r[0] for r in (wr_w or [])[-3:])}
Weak openings as Black: {', '.join(r[0] for r in (wr_b or [])[-3:])}
Colour gap: White {wr_w_pct}% vs Black {wr_b_pct}%
Write ONLY a 7-day study plan. **Monday** through **Sunday**. Each day: one specific 45-min task. Name exact Lichess puzzle themes, opening variations to drill, endgame types. Make it progressive and realistic."""
                    st.session_state["study_plan"] = call_groq(prompt, groq_key)

        if "ai_report"  in st.session_state: render_ai(st.session_state["ai_report"],  "♟ Full Coaching Report · Groq Llama 70B")
        if "study_plan" in st.session_state: render_ai(st.session_state["study_plan"], "♟ Weekly Study Plan")
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — NEWS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Chess News</div><div class="section-pill">Live · NewsAPI</div></div>', unsafe_allow_html=True)

    news_key = st.session_state.get("news_key","")
    if not news_key:
        st.markdown("""<div class="ai-box">
            <div class="ai-eyebrow">Free setup required</div>
            <div class="ai-body">
                Get a free NewsAPI key at <strong style="color:#e8e4dc">newsapi.org</strong> — takes 2 mins, no card needed, 100 free requests/day.<br>
                Add it in the sidebar under "NewsAPI Key".
            </div>
        </div>""", unsafe_allow_html=True)

        # AI-generated chess briefing as fallback
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.12em;margin:1.2rem 0 .5rem">AI Chess Briefing (no API key needed)</div>', unsafe_allow_html=True)
        groq_key = st.session_state.get("groq_key","")
        if groq_key:
            if st.button("📰 Generate chess world briefing", key="gen_news"):
                with st.spinner("Writing chess briefing..."):
                    brief = call_groq(
                        "Write a chess world briefing covering: current top players (Magnus Carlsen, Gukesh, Firouzja, Nepomniachtchi, Praggnanandhaa), recent major tournaments (Candidates 2024, World Championship 2024, Norway Chess, Speed Chess Championship), and one interesting recent chess story. Write 5 punchy paragraphs, magazine style. Current approximate date: July 2025.",
                        groq_key, max_tokens=1000)
                    st.session_state["ai_news"] = brief
            if "ai_news" in st.session_state:
                render_ai(st.session_state["ai_news"], "♟ Chess World Briefing · Groq")
        else:
            st.markdown('<div class="no-data">Add Groq API key for AI briefing, or NewsAPI key for live news</div>', unsafe_allow_html=True)
    else:
        articles = fetch_news(news_key, "chess tournament chess player 2025", count=9)
        if not articles:
            st.warning("No articles found. Try a different search or check your NewsAPI key.")
        else:
            # Featured
            a = articles[0]
            src  = a.get("source",{}).get("name","Chess News")
            desc = (a.get("description","") or a.get("content","") or "")[:300] + "..."
            pub  = time_ago(a.get("publishedAt",""))
            url  = a.get("url","")
            st.markdown(f"""<div class="news-featured">
                <div class="news-cat">{src} · {pub}</div>
                <div class="news-title">{a.get('title','')}</div>
                <div class="news-body">{desc}</div>
                <div class="news-meta">{"<a href='" + url + "' target='_blank' style='color:#c9a84c;text-decoration:none'>Read full article ↗</a>" if url else ""}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div style="margin-top:.8rem">', unsafe_allow_html=True)
            for a in articles[1:]:
                src  = a.get("source",{}).get("name","")
                pub  = time_ago(a.get("publishedAt",""))
                url  = a.get("url","")
                link = f"<a href='{url}' target='_blank' style='color:#555;font-size:9px;font-family:JetBrains Mono,monospace'>Read ↗</a>" if url else ""
                st.markdown(f"""<div class="news-card">
                    <div class="news-card-title">{a.get('title','')}</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.3rem">
                        <span class="news-source">{src}</span>
                        <span style="font-family:JetBrains Mono,monospace;font-size:9px;color:#333">{pub} &nbsp; {link}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TOURNAMENTS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Live & Upcoming Tournaments</div><div class="section-pill">Lichess Broadcasts · Auto-refresh</div></div>', unsafe_allow_html=True)

    tournaments = fetch_tournaments()
    if tournaments:
        for t in tournaments[:15]:
            tour  = t.get("tour",{})
            rd    = t.get("round",{})
            name  = tour.get("name","Unknown Tournament")
            slug  = tour.get("slug","")
            tid   = tour.get("id","")
            is_live = rd.get("ongoing", False)
            status  = "LIVE" if is_live else "UPCOMING"
            badge_c = "live" if is_live else ""

            # Build links
            watch_url   = f"https://lichess.org/broadcast/{slug}/{tid}" if slug and tid else f"https://lichess.org/broadcast"
            analyse_url = f"https://lichess.org/broadcast/{slug}/{tid}" if slug and tid else ""

            tier_labels = {5:"Elite",4:"Major",3:"Premium",2:"Standard",1:"Community"}
            tier = tier_labels.get(tour.get("tier",1),"")

            st.markdown(f"""<div class="tourn-card">
                <span class="tourn-badge {badge_c}">{status}</span>
                <div style="flex:1">
                    <div class="tourn-name">{name}</div>
                    <div class="tourn-meta">{tier}</div>
                </div>
                <div style="display:flex;gap:.8rem;flex-shrink:0">
                    <a class="tourn-link" href="{watch_url}" target="_blank">Watch ↗</a>
                    {f'<a class="tourn-link" href="{analyse_url}" target="_blank">Analyse ↗</a>' if analyse_url else ''}
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="no-data">
            No live tournaments right now.<br>
            <a href="https://lichess.org/broadcast" target="_blank" style="color:#c9a84c;font-family:'JetBrains Mono',monospace;font-size:11px">Browse all broadcasts on Lichess ↗</a>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid #1f1f1f;margin:1.5rem 0">', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center">
        <a href="https://lichess.org/broadcast" target="_blank" style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#0a0a0a;background:#c9a84c;padding:8px 20px;text-decoration:none;display:inline-block">
            View all tournaments on Lichess ↗
        </a>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center;padding:1.5rem;border-top:1px solid #141414">
    <div style="font-family:'Playfair Display',serif;font-size:.9rem;color:#2a2a2a">♟ hritikgupta · Chess Intelligence Dashboard</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1a1a1a;margin-top:.3rem;letter-spacing:.1em">
        LICHESS API · SUPABASE · GROQ LLAMA 70B · NEWSAPI · AUTO-REFRESH 2HRS
    </div>
</div>""", unsafe_allow_html=True)

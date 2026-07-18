import streamlit as st
import requests
import json
import re
import os
import time
from datetime import datetime, timezone
from collections import defaultdict, Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _get(name):
    try:    return st.secrets[name]
    except: return os.getenv(name, "")

SUPABASE_URL  = _get("SUPABASE_URL")
SUPABASE_KEY  = _get("SUPABASE_KEY")
GROQ_KEY      = _get("GROQ_API_KEY")
USERNAME      = "hritikgupta"

st.set_page_config(
    page_title="♟ hritikgupta · Chess Dashboard",
    page_icon="♟", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[data-testid="stApp"]{background:#0a0a0a !important;color:#e8e4dc !important;}
[data-testid="stSidebar"]{background:#111 !important;border-right:1px solid #1f1f1f !important;}
[data-testid="stSidebar"] *{color:#a09a8e !important;}
[data-testid="stSidebar"] .stButton button{background:#1a1a1a !important;border:1px solid #2a2a2a !important;color:#c9a84c !important;width:100% !important;border-radius:4px !important;padding:.5rem !important;font-family:'Inter',sans-serif !important;font-size:13px !important;}
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
.bucket-row{display:flex;align-items:center;gap:1rem;padding:.6rem 0;border-bottom:1px solid #141414;font-size:13px;}
.bucket-label{font-family:'JetBrains Mono',monospace;font-size:11px;color:#a09a8e;min-width:90px;}
.bucket-bar-wrap{flex:1;height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden;}
.bucket-bar{height:100%;border-radius:3px;background:#c9a84c;}
.bucket-wr{font-family:'JetBrains Mono',monospace;font-size:11px;min-width:45px;text-align:right;color:#c9a84c;}
.bucket-games{font-size:10px;color:#444;min-width:55px;text-align:right;}
.no-data{font-family:'Inter',sans-serif;font-size:13px;color:#333;padding:2rem;text-align:center;background:#0d0d0d;border:1px dashed #1a1a1a;}
.update-badge{font-family:'JetBrains Mono',monospace;font-size:10px;color:#555;background:#111;border:1px solid #1a1a1a;padding:4px 10px;display:inline-block;}
</style>
""", unsafe_allow_html=True)

# ── SUPABASE READ ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)   # cache 5 mins
def load_from_supabase():
    hdrs = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/chess_dashboard",
            headers=hdrs,
            params={"id": f"eq.{USERNAME}", "select": "data"},
            timeout=15
        )
        if r.status_code == 200:
            rows = r.json()
            if rows:
                return rows[0]["data"]
    except Exception as e:
        st.error(f"Could not reach Supabase: {e}")
    return None

# ── GROQ AI ───────────────────────────────────────────────────────────────────
def call_groq(prompt, api_key):
    models = ["llama-3.3-70b-versatile","llama3-70b-8192","llama3-8b-8192"]
    system = ("You are an expert chess coach with 20+ years experience. "
              "Write in a direct, analytical, encouraging style. "
              "Use ** for section headers. Cite actual numbers from the data. "
              "Be concise and actionable. Tailored to a 2000+ rated player.")
    for model in models:
        body = {"model":model,
                "messages":[{"role":"system","content":system},
                            {"role":"user","content":prompt}],
                "max_tokens":2000,"temperature":0.7}
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}",
                         "Content-Type":"application/json"},
                json=body, timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                st.info("Rate limit — waiting 15s..."); time.sleep(15); continue
            elif r.status_code in (400,404): continue
            else: return f"Groq error {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return f"Error: {e}"
    return "Could not reach Groq. Check API key at console.groq.com."

def build_prompt(stats, profile):
    perfs = profile.get("perfs",{}) if profile else {}
    lines = [f"Chess coaching for Lichess user: {USERNAME} ({stats['total']:,} career games)\n"]
    lines.append("RATINGS: " + " | ".join(
        f"{pf} {perfs[pf].get('rating','?')} ({perfs[pf].get('games',0):,}g {perfs[pf].get('prog',0):+d})"
        for pf in ["bullet","blitz","rapid","classical"] if pf in perfs))
    lines.append("\nFORMAT W/D/L:")
    for pf,d in sorted(stats["by_format"].items(),key=lambda x:x[1]["games"],reverse=True):
        g=d["games"]
        if g<10: continue
        wr=round(d["w"]/g*100,1)
        lines.append(f"  {pf}: {wr}% ({g:,}g {d['w']}W/{d['d']}D/{d['l']}L)")
    cs=stats["color_stats"]
    for color,d in cs.items():
        t=d["w"]+d["d"]+d["l"]
        if t: lines.append(f"As {color}: {round(d['w']/t*100,1)}% ({t:,}g)")
    if stats.get("wr_w"):
        lines.append("BEST OPENINGS WHITE: "+", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_w"][:4]))
        lines.append("WORST OPENINGS WHITE: "+", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_w"][-4:]))
    if stats.get("wr_b"):
        lines.append("BEST OPENINGS BLACK: "+", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_b"][:4]))
        lines.append("WORST OPENINGS BLACK: "+", ".join(f"{o} {wr}%/{t}g" for o,wr,t,*_ in stats["wr_b"][-4:]))
    hourly = stats.get("hourly",{})
    if hourly:
        best_h  = max(hourly.items(),key=lambda x:x[1]["w"]/max(x[1]["g"],1) if x[1]["g"]>20 else 0)
        worst_h = min(hourly.items(),key=lambda x:x[1]["w"]/max(x[1]["g"],1) if x[1]["g"]>20 else 1)
        lines.append(f"BEST HOUR: {best_h[0]}:00 UTC | WORST HOUR: {worst_h[0]}:00 UTC")
    tilt = sum(1 for s in stats.get("session_data",[]) if len(s)>=6 and s[:3].count("w")>=2 and s[-3:].count("l")>=2)
    best_streak = max((v["best"] for v in stats.get("streaks",{}).values()),default=0)
    lines.append(f"TILT SESSIONS: {tilt} | BEST STREAK: {best_streak}")
    lines.append(f"TITLED WINS: {len(stats.get('titled_wins',[]))} | TITLED LOSSES: {len(stats.get('titled_losses',[]))}")
    lines.append(f"UPSETS (150+ higher rated): {len(stats.get('high_rated_wins',[]))}")
    lines.append("""
Write coaching report with these 7 sections (** for headers):
**Player Overview** — 2 sentences
**Strengths** — 3 specific strengths with numbers
**Critical Weaknesses** — 3 weaknesses with numbers
**Opening Surgery** — what to keep, drop, and study instead
**Psychological Patterns** — colour gap, tilt, time-of-day
**Weekly Study Plan** — Mon–Sun, each day one specific task
**Study Resources** — 5 named resources matching weaknesses""")
    return "\n".join(lines)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ♟ Chess Dashboard")
    st.markdown("---")
    groq_key = st.text_input("Groq API Key", type="password",
        value=st.session_state.get("groq_key", GROQ_KEY),
        help="Free at console.groq.com")
    if groq_key: st.session_state["groq_key"] = groq_key
    st.markdown("---")
    st.markdown("""<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#444;line-height:2'>
        Data auto-updates every 2 hrs<br>
        via GitHub Actions → Supabase<br>
        App loads in &lt;2 seconds
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("⟳  Reload latest data"):
        st.cache_data.clear()
        for k in ["ai_report","study_plan"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#1f1f1f;font-family:JetBrains Mono,monospace;line-height:1.8'>DATA: LICHESS API<br>DB: SUPABASE FREE<br>AI: GROQ LLAMA 70B<br>AUTO-REFRESH: 2HRS</div>",unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials missing. Add SUPABASE_URL and SUPABASE_KEY to Streamlit Secrets.")
    st.stop()

with st.spinner("Loading your chess data..."):
    db_data = load_from_supabase()

if not db_data:
    st.markdown("""<div style='padding:3rem;text-align:center;font-family:JetBrains Mono,monospace;color:#555'>
        <div style='font-size:2rem;margin-bottom:1rem'>♟</div>
        <div style='font-size:13px;color:#c9a84c;margin-bottom:.5rem'>No data yet</div>
        <div style='font-size:12px'>The GitHub Actions job hasn't run yet.<br>
        Go to your GitHub repo → Actions tab → Run workflow manually to load data now.<br>
        After that it auto-refreshes every 2 hours.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

profile  = db_data.get("profile", {})
stats    = db_data.get("stats", {})
updated  = db_data.get("updated_at","")[:16].replace("T"," ") if db_data.get("updated_at") else "—"
perfs    = profile.get("perfs",{}) if profile else {}

# ── MASTHEAD ──────────────────────────────────────────────────────────────────
blitz_r  = perfs.get("blitz",{}).get("rating","—")
rapid_r  = perfs.get("rapid",{}).get("rating","—")
bullet_r = perfs.get("bullet",{}).get("rating","—")
title_b  = profile.get("title","") if profile else ""
title_h  = f"<span style='font-family:JetBrains Mono;font-size:1rem;color:#c9a84c'>{title_b} </span>" if title_b else ""
created  = profile.get("createdAt",0)
since    = datetime.fromtimestamp(created/1000,tz=timezone.utc).strftime("%B %Y") if created else "—"
total_lc = profile.get("count",{}).get("all",stats.get("total",0)) if profile else stats.get("total",0)

st.markdown(f"""<div class="masthead">
    <div class="masthead-eyebrow">Lichess · Personal Intelligence Dashboard</div>
    <div class="masthead-title">{title_h}<span>hritik</span>gupta</div>
    <div class="masthead-meta">Member since {since} &nbsp;·&nbsp; {total_lc:,} lifetime games &nbsp;·&nbsp; {stats.get('total',0):,} analysed &nbsp;·&nbsp; Blitz {blitz_r} &nbsp;·&nbsp; Rapid {rapid_r} &nbsp;·&nbsp; Bullet {bullet_r} &nbsp;·&nbsp; <span class="update-badge">Updated {updated} UTC</span></div>
</div>""", unsafe_allow_html=True)

# ── STAT STRIP ────────────────────────────────────────────────────────────────
all_w = sum(d["w"] for d in stats.get("by_format",{}).values())
all_l = sum(d["l"] for d in stats.get("by_format",{}).values())
all_d = sum(d["d"] for d in stats.get("by_format",{}).values())
total = stats.get("total",0)
wr    = round(all_w/total*100,1) if total else 0
best_streak = max((v["best"] for v in stats.get("streaks",{}).values()),default=0)
titled_w    = len(stats.get("titled_wins",[]))

st.markdown(f"""<div class="stat-strip">
    <div class="stat-cell"><div class="stat-val">{total:,}</div><div class="stat-lbl">Games analysed</div></div>
    <div class="stat-cell"><div class="stat-val">{all_w:,}</div><div class="stat-lbl">Total wins</div></div>
    <div class="stat-cell"><div class="stat-val">{wr}%</div><div class="stat-lbl">Win rate</div></div>
    <div class="stat-cell"><div class="stat-val">{best_streak}</div><div class="stat-lbl">Best streak</div></div>
    <div class="stat-cell"><div class="stat-val">{titled_w}</div><div class="stat-lbl">Titled scalps</div></div>
</div>""", unsafe_allow_html=True)

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
by_fmt = [(pf,d) for pf,d in sorted(stats.get("by_format",{}).items(),key=lambda x:x[1]["games"],reverse=True) if d["games"]>0]
if by_fmt:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Performance by Format</div><div class="section-pill">All time</div></div>',unsafe_allow_html=True)
    cols=st.columns(max(1,min(len(by_fmt),4)))
    for i,(pf,d) in enumerate(by_fmt[:8]):
        g=d["games"]; w=d["w"]; dr=d["d"]; l=d["l"]
        wr_p=round(w/g*100,1) if g else 0
        wp=round(w/g*100,1) if g else 0; dp=round(dr/g*100,1) if g else 0; lp=round(l/g*100,1) if g else 0
        with cols[i%4]:
            st.markdown(f"""<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:1rem;margin-bottom:.5rem">
                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#555;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem">{pf}</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:#c9a84c">{wr_p}%</div>
                <div style="margin:.4rem 0"><div class="wdl-bar"><div class="wdl-w" style="width:{wp}%"></div><div class="wdl-d" style="width:{dp}%"></div><div class="wdl-l" style="width:{lp}%"></div></div>
                <div class="wdl-labels"><span style="color:#4a8c3f">{w:,}W</span><span>{dr:,}D</span><span style="color:#8c3f3f">{l:,}L</span></div></div>
                <div style="font-family:'Inter',sans-serif;font-size:10px;color:#333">{g:,} games</div>
            </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── WHITE VS BLACK ────────────────────────────────────────────────────────────
cs = stats.get("color_stats",{})
if cs:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">White vs Black</div><div class="section-pill">Colour performance</div></div>',unsafe_allow_html=True)
    html='<div class="color-compare">'
    for color,piece in [("white","♔"),("black","♚")]:
        d=cs.get(color,{"w":0,"d":0,"l":0}); t=d["w"]+d["d"]+d["l"]
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
opp_buckets = stats.get("opp_buckets",{})
if opp_buckets:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Performance vs Rating Ranges</div><div class="section-pill">Where you win and lose</div></div>',unsafe_allow_html=True)
    buckets=sorted(opp_buckets.items(),key=lambda x:int(x[0].split("-")[0]))
    html=""
    for bkt,d in buckets:
        g=d["g"]
        if g<5: continue
        wr_b=round(d["w"]/g*100,1); bar_w=min(wr_b,100)
        col="#4a8c3f" if wr_b>=50 else "#c9a84c" if wr_b>=40 else "#8c3f3f"
        html+=f"""<div class="bucket-row">
            <div class="bucket-label">{bkt}</div>
            <div class="bucket-bar-wrap"><div class="bucket-bar" style="width:{bar_w}%;background:{col}"></div></div>
            <div class="bucket-wr" style="color:{col}">{wr_b}%</div>
            <div class="bucket-games">{g:,} games</div>
        </div>"""
    st.markdown(html,unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── TIME OF DAY ───────────────────────────────────────────────────────────────
hourly  = stats.get("hourly",{})
weekday = stats.get("weekday",{})
if hourly or weekday:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">When You Play Best</div><div class="section-pill">Hour · Day</div></div>',unsafe_allow_html=True)
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.8rem">Win rate by hour (UTC)</div>',unsafe_allow_html=True)
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
        st.markdown(html,unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.8rem">Win rate by day of week</div>',unsafe_allow_html=True)
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
        st.markdown(html,unsafe_allow_html=True)
        tilt=sum(1 for s in stats.get("session_data",[]) if len(s)>=6 and s[:3].count("w")>=2 and s[-3:].count("l")>=2)
        tc="#8c3f3f" if tilt>10 else "#c9a84c"
        st.markdown(f"""<div style="margin-top:1.5rem;background:#0d0d0d;border:1px solid #1a1a1a;border-left:3px solid {tc};padding:1rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#555;margin-bottom:.3rem">TILT SESSIONS DETECTED</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:{tc}">{tilt}</div>
            <div style="font-family:'Inter',sans-serif;font-size:11px;color:#555">Started well, ended badly</div>
        </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── BEST WINS + TITLED SCALPS ─────────────────────────────────────────────────
st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
col1,col2=st.columns(2)
with col1:
    st.markdown('<div class="section-head"><div class="section-title">Best Wins</div><div class="section-pill">Biggest upsets</div></div>',unsafe_allow_html=True)
    top=sorted(stats.get("high_rated_wins",[]),key=lambda x:x.get("opp_rating",0),reverse=True)[:10]
    if top:
        for i,hw in enumerate(top):
            rc="gold" if i==0 else ""; medal="🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else ""
            tb=f'<span class="win-title-badge">{hw.get("title","")}</span>' if hw.get("title") else ""
            lnk=f'<a class="win-link" href="https://lichess.org/{hw["id"]}" target="_blank">view ↗</a>' if hw.get("id") else ""
            st.markdown(f"""<div class="win-card">
                <div class="win-rank {rc}">{medal or i+1}</div>
                <div style="flex:1"><div class="win-opp">{hw['name']}{tb}</div><div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#444">{hw.get('perf','')} · +{hw.get('diff',0)} pts</div></div>
                <div><div class="win-rating">{hw.get('opp_rating','?')}</div>{lnk}</div>
            </div>""",unsafe_allow_html=True)
    else:
        st.markdown('<div class="no-data">No upsets yet</div>',unsafe_allow_html=True)
with col2:
    st.markdown('<div class="section-head"><div class="section-title">Titled Scalps</div><div class="section-pill">GM · IM · FM wins</div></div>',unsafe_allow_html=True)
    titled_wins = stats.get("titled_wins",[])
    if titled_wins:
        by_title=defaultdict(list)
        for tw in titled_wins: by_title[tw["title"]].append(tw)
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
        <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#8c3f3f">{len(stats.get('titled_losses',[]))}</div>
    </div>""",unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# ── STREAKS ───────────────────────────────────────────────────────────────────
streaks=sorted([(pf,v["best"]) for pf,v in stats.get("streaks",{}).items() if v["best"]>=2],key=lambda x:x[1],reverse=True)
if streaks:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Best Winning Streaks</div><div class="section-pill">Per format</div></div>',unsafe_allow_html=True)
    cols=st.columns(max(1,min(len(streaks),5)))
    for i,(pf,best) in enumerate(streaks[:5]):
        with cols[i]:
            st.markdown(f"""<div class="streak-box"><div class="streak-num">{best}</div>
                <div><div class="streak-format">{pf.upper()}</div><div class="streak-detail">best streak</div></div>
            </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── OPENINGS ──────────────────────────────────────────────────────────────────
wr_w = stats.get("wr_w",[]); wr_b = stats.get("wr_b",[])
if wr_w or wr_b:
    st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div class="section-title">Opening Analysis</div><div class="section-pill">Min 5 games</div></div>',unsafe_allow_html=True)
    def op_html(wr_list,top=True,limit=8):
        items=wr_list[:limit] if top else wr_list[-limit:]
        if not items: return '<div class="no-data">Not enough data</div>'
        html=""
        for row in items:
            op,wr,t = row[0],row[1],row[2]
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
        st.markdown(op_html(wr_w,True),unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin:1.2rem 0 .5rem">♔ Worst as White</div>',unsafe_allow_html=True)
        st.markdown(op_html(wr_w,False),unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.5rem">♚ Best as Black</div>',unsafe_allow_html=True)
        st.markdown(op_html(wr_b,True),unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#555;letter-spacing:.15em;text-transform:uppercase;margin:1.2rem 0 .5rem">♚ Worst as Black</div>',unsafe_allow_html=True)
        st.markdown(op_html(wr_b,False),unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ── AI COACHING ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-wrap">',unsafe_allow_html=True)
st.markdown('<div class="section-head"><div class="section-title">AI Coaching Report</div><div class="section-pill">Groq · Llama 70B · Free</div></div>',unsafe_allow_html=True)
groq_key=st.session_state.get("groq_key","")
if not groq_key:
    st.markdown("""<div class="ai-box"><div class="ai-eyebrow">Setup required</div>
        <div class="ai-body">Add your Groq API key in the sidebar.<br>
        Free at <strong style='color:#e8e4dc'>console.groq.com</strong> — no credit card. Takes 2 minutes.</div>
    </div>""",unsafe_allow_html=True)
else:
    col_a,col_b=st.columns(2)
    with col_a:
        if st.button("✦  Generate coaching report",key="gen_ai"):
            with st.spinner("Groq is analysing your game history..."):
                st.session_state["ai_report"] = call_groq(build_prompt(stats,profile), groq_key)
    with col_b:
        if st.button("📅  Generate weekly study plan",key="gen_plan"):
            with st.spinner("Building your personalised study plan..."):
                plan_p = build_prompt(stats,profile).replace(
                    "Write coaching report with these 7 sections",
                    "Write ONLY a detailed 7-day study plan. Monday through Sunday. "
                    "Each day: one specific task, 30-60 min, name exact Lichess puzzle themes, "
                    "opening variations, or endgame types. Start immediately with **Monday**.")
                st.session_state["study_plan"] = call_groq(plan_p, groq_key)

    def render_ai(text, eyebrow):
        sections=re.split(r'\*\*(.+?)\*\*',text)
        html=f'<div class="ai-box"><div class="ai-eyebrow">{eyebrow}</div>'
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

    if "ai_report" in st.session_state:
        render_ai(st.session_state["ai_report"], "♟ Groq Coach · Full Career Analysis")
    if "study_plan" in st.session_state:
        render_ai(st.session_state["study_plan"], "♟ Weekly Study Plan")
st.markdown('</div>',unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center;padding:2rem;border-top:1px solid #141414">
    <div style="font-family:'Playfair Display',serif;font-size:1rem;color:#2a2a2a">♟ hritikgupta · Chess Intelligence Dashboard</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#1f1f1f;margin-top:.3rem;letter-spacing:.1em">
        DATA: LICHESS API · DB: SUPABASE · AI: GROQ LLAMA 70B · AUTO-REFRESH: EVERY 2 HOURS
    </div>
</div>""",unsafe_allow_html=True)

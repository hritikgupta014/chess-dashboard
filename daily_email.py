"""
daily_email.py
Runs in GitHub Actions every day at 9:00 PM IST.
Fetches ALL games played today (IST day), analyses them,
gets an AI coaching summary from Groq, and emails an HTML
report to hritikgupta014@gmail.com via Gmail App Password.
"""
import requests
import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from collections import defaultdict

USERNAME  = "hritikgupta"
HEADERS   = {"User-Agent": "ChessDashboard/1.0 hritikgupta"}
EMAIL_TO  = "hritikgupta014@gmail.com"
IST       = timezone(timedelta(hours=5, minutes=30))

GMAIL_ADDRESS      = os.environ["GMAIL_ADDRESS"]        # your gmail
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]   # 16-char app password
GROQ_KEY           = os.environ.get("GROQ_API_KEY", "")
LICHESS_TOKEN      = os.environ.get("LICHESS_TOKEN", "")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── FETCH TODAY'S GAMES (IST day boundary) ────────────────────────────────────
def fetch_today_games():
    now_ist  = datetime.now(IST)
    midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    since_ms = int(midnight.timestamp() * 1000)
    hdrs = {**HEADERS, "Accept": "application/x-ndjson"}
    if LICHESS_TOKEN:
        hdrs["Authorization"] = f"Bearer {LICHESS_TOKEN}"
    games = []
    try:
        with requests.get(
            f"https://lichess.org/api/games/user/{USERNAME}",
            params={"since": since_ms, "opening": "true",
                    "moves": "false", "clocks": "false", "evals": "false"},
            headers=hdrs, stream=True, timeout=120
        ) as r:
            if r.status_code != 200:
                log(f"Lichess error: {r.status_code}"); return []
            for line in r.iter_lines():
                if line:
                    try: games.append(json.loads(line))
                    except: pass
    except Exception as e:
        log(f"Fetch error: {e}")
    games.sort(key=lambda g: g.get("createdAt", 0))
    log(f"Fetched {len(games)} games played today (IST)")
    return games

# ── PARSE ─────────────────────────────────────────────────────────────────────
def parse_game(g):
    uname   = USERNAME.lower()
    players = g.get("players",{})
    white   = players.get("white",{}); black = players.get("black",{})
    wu = (white.get("user",{}).get("name") or white.get("user",{}).get("id","")).lower()
    if wu == uname: my_side, my_data, opp_data = "white", white, black
    else:           my_side, my_data, opp_data = "black", black, white
    winner = g.get("winner"); status = g.get("status","")
    if   winner == my_side:                                result = "win"
    elif winner is None or status in ("draw","stalemate"): result = "draw"
    else:                                                  result = "loss"
    opp_user = opp_data.get("user",{})
    clock    = g.get("clock",{})
    tc = f"{clock.get('initial',0)//60}+{clock.get('increment',0)}" if clock else g.get("speed","")
    return {
        "id":         g.get("id",""),
        "side":       my_side,
        "result":     result,
        "status":     status,
        "perf":       g.get("perf",""),
        "tc":         tc,
        "opening":    g.get("opening",{}).get("name","Unknown"),
        "opp_name":   opp_user.get("name") or opp_user.get("id","?"),
        "opp_title":  opp_user.get("title",""),
        "opp_rating": opp_data.get("rating","?"),
        "diff":       my_data.get("ratingDiff", 0),
        "time_ist":   datetime.fromtimestamp(g.get("createdAt",0)/1000, tz=IST).strftime("%I:%M %p"),
    }

# ── GROQ COACHING SUMMARY ─────────────────────────────────────────────────────
def call_groq(prompt):
    if not GROQ_KEY: return ""
    models = ["llama-3.3-70b-versatile","llama3-70b-8192","llama3-8b-8192"]
    system = ("You are an expert chess coach writing a short end-of-day email review. "
              "Be direct, specific, cite actual numbers and game details. "
              "Use ** for section headers. Keep it under 400 words.")
    for model in models:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}",
                         "Content-Type": "application/json"},
                json={"model": model, "messages": [
                    {"role":"system","content":system},
                    {"role":"user","content":prompt}],
                    "max_tokens": 900, "temperature": 0.7},
                timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code in (400, 404, 429): continue
        except Exception as e:
            log(f"Groq error: {e}")
    return ""

# ── BUILD HTML EMAIL ──────────────────────────────────────────────────────────
GOLD="#c9a84c"; DARK="#0d0d0d"; BORDER="#2a2a2a"; TEXT="#e8e4dc"; MUTED="#888"
GREEN="#4a8c3f"; RED="#b05050"

def ai_to_html(text):
    """Convert **Header** style Groq output to simple email HTML."""
    import re as _re
    html = ""
    parts = _re.split(r'\*\*(.+?)\*\*', text)
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
        if i % 2 == 1:
            html += f'<h3 style="color:{GOLD};font-size:14px;margin:16px 0 6px;font-family:Georgia,serif;">— {part}</h3>'
        else:
            for line in part.split("\n"):
                l = line.strip()
                if l:
                    html += f'<p style="color:{MUTED};font-size:13px;line-height:1.7;margin:4px 0;">{l}</p>'
    return html

def build_email(today, ai_summary, date_str):
    if not today:
        body_core = f"""
        <div style="text-align:center;padding:40px 20px;">
            <div style="font-size:40px;">♟</div>
            <h2 style="color:{GOLD};font-family:Georgia,serif;">Rest Day</h2>
            <p style="color:{MUTED};font-size:14px;">No games played today. The board will be waiting tomorrow.</p>
        </div>"""
        return wrap_email(body_core, date_str)

    tw = sum(1 for g in today if g["result"]=="win")
    td = sum(1 for g in today if g["result"]=="draw")
    tl = sum(1 for g in today if g["result"]=="loss")
    net = sum(g["diff"] for g in today if isinstance(g["diff"], int))
    twr = round(tw/len(today)*100,1)
    net_c = GREEN if net >= 0 else RED
    net_s = f"+{net}" if net > 0 else str(net)

    # Summary strip
    body = f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {BORDER};margin-bottom:20px;">
      <tr>
        <td align="center" style="padding:14px;border-right:1px solid {BORDER};">
            <div style="font-size:22px;font-weight:bold;color:{GOLD};font-family:Georgia,serif;">{len(today)}</div>
            <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;">Games</div></td>
        <td align="center" style="padding:14px;border-right:1px solid {BORDER};">
            <div style="font-size:22px;font-weight:bold;color:{GREEN};font-family:Georgia,serif;">{tw}W</div>
            <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;">{td}D · {tl}L</div></td>
        <td align="center" style="padding:14px;border-right:1px solid {BORDER};">
            <div style="font-size:22px;font-weight:bold;color:{GOLD};font-family:Georgia,serif;">{twr}%</div>
            <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;">Win rate</div></td>
        <td align="center" style="padding:14px;">
            <div style="font-size:22px;font-weight:bold;color:{net_c};font-family:Georgia,serif;">{net_s}</div>
            <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;">Net rating</div></td>
      </tr>
    </table>"""

    # Game list
    body += f'<h3 style="color:{TEXT};font-family:Georgia,serif;font-size:15px;border-bottom:1px solid {BORDER};padding-bottom:6px;">Today\'s Games</h3>'
    for g in today:
        res = g["result"]
        rc  = GREEN if res=="win" else RED if res=="loss" else "#777"
        piece = "♔" if g["side"]=="white" else "♚"
        title = f" [{g['opp_title']}]" if g["opp_title"] else ""
        d  = g["diff"] if isinstance(g["diff"], int) else 0
        ds = f"+{d}" if d > 0 else str(d)
        dc = GREEN if d > 0 else RED if d < 0 else "#777"
        body += f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="border-left:3px solid {rc};background:#141414;margin-bottom:6px;">
          <tr>
            <td style="padding:10px 12px;">
                <span style="color:#666;font-size:11px;font-family:monospace;">{g['time_ist']}</span>
                &nbsp;<span style="background:{rc};color:#fff;font-size:10px;padding:2px 8px;font-family:monospace;letter-spacing:1px;">{res.upper()}</span>
                &nbsp;<span style="color:{TEXT};font-size:13px;">{piece} vs {g['opp_name']}{title} <span style="color:#666;">({g['opp_rating']})</span></span>
                <div style="color:#666;font-size:11px;margin-top:4px;font-family:monospace;">
                    {g['perf']} {g['tc']} · {g['opening'][:50]} · {g['status']}
                    &nbsp;·&nbsp; <span style="color:{dc};">{ds}</span>
                    &nbsp;·&nbsp; <a href="https://lichess.org/{g['id']}" style="color:{GOLD};text-decoration:none;">analyse ↗</a>
                </div>
            </td>
          </tr>
        </table>"""

    # AI summary
    if ai_summary:
        body += f"""
        <div style="border:1px solid {BORDER};border-top:2px solid {GOLD};padding:16px;margin-top:24px;background:#111;">
            <div style="color:{GOLD};font-size:10px;letter-spacing:2px;text-transform:uppercase;font-family:monospace;">♟ Coach's Evening Review</div>
            {ai_to_html(ai_summary)}
        </div>"""

    return wrap_email(body, date_str)

def wrap_email(body_core, date_str):
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#0a0a0a;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;">
<tr><td align="center" style="padding:24px 12px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:{DARK};border:1px solid {BORDER};">
  <tr><td style="padding:24px;border-bottom:2px solid {GOLD};">
      <div style="color:{GOLD};font-size:10px;letter-spacing:3px;text-transform:uppercase;font-family:monospace;">Daily Chess Coach · IST</div>
      <div style="color:{TEXT};font-size:24px;font-weight:bold;font-family:Georgia,serif;margin-top:4px;">
          <span style="color:{GOLD};">hritik</span>gupta</div>
      <div style="color:#666;font-size:12px;margin-top:4px;">{date_str}</div>
  </td></tr>
  <tr><td style="padding:24px;">{body_core}</td></tr>
  <tr><td style="padding:16px 24px;border-top:1px solid #1a1a1a;text-align:center;">
      <div style="color:#444;font-size:10px;font-family:monospace;letter-spacing:1px;">
          LICHESS · GROQ AI · SENT DAILY 9PM IST · GITHUB ACTIONS</div>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

# ── SEND ──────────────────────────────────────────────────────────────────────
def send_email(html, subject):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Daily Chess Coach <{GMAIL_ADDRESS}>"
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, EMAIL_TO, msg.as_string())
    log(f"Email sent to {EMAIL_TO}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    date_str = datetime.now(IST).strftime("%A, %d %B %Y")
    log(f"Daily coach run for {date_str}")

    raw   = fetch_today_games()
    today = [parse_game(g) for g in raw]

    ai_summary = ""
    if today:
        tw  = sum(1 for g in today if g["result"]=="win")
        td  = sum(1 for g in today if g["result"]=="draw")
        tl  = sum(1 for g in today if g["result"]=="loss")
        net = sum(g["diff"] for g in today if isinstance(g["diff"], int))
        seq = "".join(g["result"][0] for g in today)
        lines = []
        for i, g in enumerate(today, 1):
            d = g["diff"] if isinstance(g["diff"], int) else 0
            lines.append(f"{i}. [{g['time_ist']}] {g['perf']} {g['tc']} as {g['side']}: "
                         f"{g['result'].upper()} vs {g['opp_name']} ({g['opp_rating']}) — "
                         f"{g['opening']} — ended by {g['status']} — rating {d:+d}")
        prompt = f"""End-of-day chess review for {USERNAME}, {date_str} (all times IST).
SESSION: {len(today)} games — {tw}W {td}D {tl}L — net rating {net:+d}
Result sequence (chronological): {seq}
GAMES:
{chr(10).join(lines)}

Write the evening email review with sections (use ** headers):
**Session Verdict** — honest one-paragraph assessment with the numbers.
**Key Moment** — the single most important game today (cite game number) and why.
**Pattern Watch** — any tilt (losses clustering after early results), opening repeats, or time-control issues in the sequence.
**Tomorrow** — 2 concrete focuses for the next session."""
        ai_summary = call_groq(prompt)

    # Subject line
    if today:
        tw  = sum(1 for g in today if g["result"]=="win")
        tl  = sum(1 for g in today if g["result"]=="loss")
        td  = len(today) - tw - tl
        net = sum(g["diff"] for g in today if isinstance(g["diff"], int))
        subject = f"♟ Today: {tw}W-{td}D-{tl}L · {net:+d} rating · {datetime.now(IST).strftime('%d %b')}"
    else:
        subject = f"♟ Rest day · {datetime.now(IST).strftime('%d %b')}"

    html = build_email(today, ai_summary, date_str)
    send_email(html, subject)
    log("All done.")

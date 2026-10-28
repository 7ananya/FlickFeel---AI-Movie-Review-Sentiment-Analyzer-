import os, random, re
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="FlickFeel", page_icon="🎬", layout="wide")

# ── Try loading torch / transformers (optional) ──
try:
    import torch
    import torch.nn.functional as F
    from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ── Query param navigation ──
qp = st.query_params
if "page" in qp:
    val = qp["page"].replace("+", " ")
    st.session_state["page"] = val
    if "genre" in qp:
        st.session_state["selected_genre"] = qp["genre"]
    elif val != "Genre":
        st.session_state["selected_genre"] = None
    st.query_params.clear()

# ── Session state ──
for k, v in {
    "logged_in": False, "username": "", "page": "Home",
    "home_review": "", "users_db": {"admin": "admin123"},
    "feedbacks": [], "selected_genre": None, "genre_review": "",
    "dark_mode": False, "review_history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

cur_page = st.session_state.page
dark = st.session_state.dark_mode

if cur_page == "__logout__":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "Home"
    st.rerun()

if cur_page == "__toggle__":
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.session_state.page = "Home"
    st.rerun()

# ── Color tokens ──
if dark:
    BG="#07080f"; BG2="#0b0d18"; BG3="#10131f"; BG4="#161926"
    CARD_BDR="rgba(255,255,255,0.07)"; TEXT="#f0f2ff"; TEXT2="rgba(220,225,255,0.65)"
    TEXT3="rgba(180,190,255,0.38)"; TEXT4="rgba(180,190,255,0.2)"
    INP_BG="#10131f"; INP_CLR="#f0f2ff"; INP_BDR="rgba(100,120,255,0.22)"
    NAV_BG="rgba(7,8,15,0.97)"; FILM_BG="#0b0d18"
    HERO_BG="linear-gradient(135deg,#07080f 0%,#0f0a1e 40%,#07101a 100%)"
    ABOUT_BG="#0b0d18"; GRAIN_OP="0.02"
    ACC1="#e8294c"; ACC2="#f97316"; ACC3="#facc15"; ACC4="#22d3a5"; ACC5="#818cf8"
else:
    BG="#ffffff"; BG2="#f5f5f7"; BG3="#ffffff"; BG4="#ebebed"
    CARD_BDR="rgba(0,0,0,0.08)"; TEXT="#111111"; TEXT2="rgba(17,17,17,0.6)"
    TEXT3="rgba(17,17,17,0.38)"; TEXT4="rgba(17,17,17,0.18)"
    INP_BG="#ffffff"; INP_CLR="#111111"; INP_BDR="rgba(0,0,0,0.15)"
    NAV_BG="rgba(255,255,255,0.97)"; FILM_BG="#f0f0f2"
    HERO_BG="linear-gradient(135deg,#ffffff 0%,#f7f5ff 40%,#f0f7ff 100%)"
    ABOUT_BG="#f5f5f7"; GRAIN_OP="0"
    ACC1="#e8294c"; ACC2="#f97316"; ACC3="#d97706"; ACC4="#059669"; ACC5="#4f46e5"

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@300;400;500;600;700;800;900&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
*,html,body,[class*="css"]{{font-family:'Montserrat',sans-serif;box-sizing:border-box;margin:0;padding:0;}}
#MainMenu,footer,header{{visibility:hidden;}}
.stApp>header,.stDeployButton{{display:none!important;}}
.stApp{{background:{BG}!important;}}
.block-container{{padding:0!important;margin:0!important;max-width:100%!important;}}
section[data-testid="stMain"]>div:first-child{{padding:0!important;}}
/* Kill ALL Streamlit spacing */
.stMainBlockContainer,
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockSeparator"]{{padding:0!important;margin:0!important;gap:0!important;min-height:0!important;}}
[data-testid="stVerticalBlock"]>div,
[data-testid="stVerticalBlock"]>div>div{{padding:0!important;margin:0!important;gap:0!important;}}
.element-container,[data-testid="element-container"]{{margin:0!important;padding:0!important;min-height:0!important;}}
.stMarkdown{{margin:0!important;padding:0!important;}}
/* Ensure filmstrip iframe/block not clipped */
[data-testid="stMarkdownContainer"]{{overflow:visible!important;}}

/* Toggle button in navbar */
.nb-toggle{{background:transparent;border:1px solid {CARD_BDR};border-radius:2px;padding:6px 12px;font-size:14px;cursor:pointer;color:{TEXT};margin-left:8px;transition:all 0.2s;flex-shrink:0;line-height:1;}}
.nb-toggle:hover{{border-color:{ACC1};background:rgba(232,41,76,0.06);}}

/* === NAVBAR === */
.nb{{width:100%;background:{NAV_BG};border-bottom:1px solid rgba(0,0,0,0.08);display:flex;align-items:center;padding:0 56px;height:64px;position:relative;z-index:1000;backdrop-filter:blur(20px);}}
.nb-logo{{font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:4px;background:linear-gradient(90deg,{ACC1},{ACC2});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-decoration:none;margin-right:44px;flex-shrink:0;transition:opacity 0.2s;}}
.nb-logo:hover{{opacity:0.75;text-decoration:none;}}
.nb-links{{display:flex;align-items:center;flex:1;gap:0;}}
.nb-link{{color:{TEXT3};font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:8px 14px;white-space:nowrap;text-decoration:none;transition:color 0.2s;flex-shrink:0;}}
.nb-link:hover{{color:{TEXT};text-decoration:none;}}
.nb-link.act{{color:{ACC1};border-bottom:2px solid {ACC1};}}
.dd{{position:relative;display:inline-block;flex-shrink:0;}}
.dd-btn{{color:{TEXT3};font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:8px 14px;cursor:default;display:flex;align-items:center;gap:4px;transition:color 0.2s;user-select:none;}}
.dd:hover .dd-btn{{color:{TEXT};}}
.dd-arrow{{font-size:8px;transition:transform 0.2s;}}
.dd:hover .dd-arrow{{transform:rotate(180deg);}}
.dd-panel{{display:none;position:absolute;top:100%;left:0;padding-top:6px;z-index:9999;min-width:200px;}}
.dd-panel-inner{{background:{BG3};border:1px solid {CARD_BDR};border-top:2px solid {ACC1};border-radius:0 0 8px 8px;box-shadow:0 12px 32px rgba(0,0,0,0.1);padding:4px 0;}}
.dd:hover .dd-panel{{display:block;}}
.dd-item{{display:flex;align-items:center;gap:10px;padding:10px 16px;color:{TEXT2};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;text-decoration:none;transition:background 0.15s;}}
.dd-item:hover{{background:rgba(232,41,76,0.08);color:{TEXT};text-decoration:none;}}
.dd-ico{{font-size:14px;width:20px;text-align:center;flex-shrink:0;}}
.nb-auth{{display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:12px;}}
.nb-login{{color:{TEXT3};font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;padding:7px 18px;border-radius:2px;border:1px solid {CARD_BDR};background:transparent;text-decoration:none;transition:all 0.2s;}}
.nb-login:hover{{border-color:{TEXT3};color:{TEXT};text-decoration:none;}}
.nb-signup{{color:#fff;font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;padding:8px 20px;border-radius:2px;background:{ACC1};text-decoration:none;transition:all 0.2s;}}
.nb-signup:hover{{background:#c91f3a;text-decoration:none;}}
.nb-badge{{background:rgba(232,41,76,0.1);border:1px solid rgba(232,41,76,0.3);border-radius:2px;padding:7px 14px;color:{ACC1};font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;white-space:nowrap;flex-shrink:0;}}

/* === FILMSTRIP === */
.filmstrip{{background:{FILM_BG};border-top:2px solid {ACC1};border-bottom:2px solid {ACC1};overflow:hidden;height:36px;position:relative;}}
.filmstrip-track{{display:flex;align-items:center;height:100%;animation:filmscroll 32s linear infinite;white-space:nowrap;}}
@keyframes filmscroll{{0%{{transform:translateX(0)}}100%{{transform:translateX(-50%)}}}}
.filmstrip-item{{font-family:'Bebas Neue',sans-serif;font-size:13px;letter-spacing:4px;padding:0 20px;}}
.filmstrip-item:nth-child(5n+1){{color:{ACC1};}}
.filmstrip-item:nth-child(5n+2){{color:{ACC2};}}
.filmstrip-item:nth-child(5n+3){{color:{ACC3};}}
.filmstrip-item:nth-child(5n+4){{color:{ACC4};}}
.filmstrip-item:nth-child(5n+5){{color:{ACC5};}}
.filmstrip-dot{{color:{"rgba(255,255,255,0.2)" if dark else "rgba(0,0,0,0.2)"};font-size:8px;padding:0 6px;}}

/* === HERO === */
.hero-wrap{{position:relative;overflow:hidden;}}
.hero-video-frame{{position:relative;width:100%;background:{HERO_BG};min-height:560px;display:flex;align-items:center;overflow:hidden;}}
.hero-spotlight{{position:absolute;top:-10%;left:5%;width:700px;height:700px;background:radial-gradient(ellipse,rgba(232,41,76,{"0.1" if dark else "0.05"}) 0%,transparent 60%);animation:spotlight 7s ease-in-out infinite alternate;}}
.hero-spotlight2{{position:absolute;bottom:-10%;right:5%;width:500px;height:500px;background:radial-gradient(ellipse,rgba({"129,140,248" if dark else "79,70,229"},{"0.08" if dark else "0.04"}) 0%,transparent 60%);animation:spotlight2 9s ease-in-out infinite alternate;}}
@keyframes spotlight{{0%{{transform:translate(0,0)}}100%{{transform:translate(60px,30px)}}}}
@keyframes spotlight2{{0%{{transform:translate(0,0)}}100%{{transform:translate(-50px,-25px)}}}}
.hero-content{{position:relative;z-index:10;padding:64px 72px;flex:1;}}
.hero-eyebrow{{font-size:10px;letter-spacing:5px;text-transform:uppercase;color:{ACC1};margin-bottom:20px;font-weight:700;display:flex;align-items:center;gap:12px;}}
.hero-eyebrow::before{{content:'';display:block;width:24px;height:1px;background:{ACC1};}}
.hero-title{{font-family:'Bebas Neue',sans-serif;font-size:100px;line-height:0.88;letter-spacing:2px;color:{TEXT};margin-bottom:10px;}}
.hero-title .red{{background:linear-gradient(90deg,{ACC1},{ACC2});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hero-sub{{font-family:'Crimson Text',serif;font-size:21px;font-style:italic;color:{TEXT2};margin-bottom:32px;line-height:1.6;max-width:460px;}}
.hero-cta{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:48px;}}
.btn-primary{{background:{ACC1};color:#fff!important;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:13px 28px;border-radius:2px;text-decoration:none!important;transition:all 0.2s;border:none;cursor:pointer;display:inline-block;}}
.btn-primary:hover{{background:#c91f3a;transform:translateY(-1px);text-decoration:none!important;}}
.btn-secondary{{background:transparent;color:{TEXT2}!important;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:12px 28px;border-radius:2px;text-decoration:none!important;border:1px solid {CARD_BDR};transition:all 0.2s;display:inline-block;}}
.btn-secondary:hover{{border-color:{TEXT2};color:{TEXT}!important;}}
.hero-stats{{display:flex;gap:40px;}}
.hero-stat-val{{font-family:'Bebas Neue',sans-serif;font-size:38px;background:linear-gradient(90deg,{ACC3},{ACC2});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:1px;line-height:1;}}
.hero-stat-lbl{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};margin-top:3px;}}

/* === POSTERS === */
.posters-panel{{position:relative;width:520px;flex-shrink:0;min-height:560px;overflow:hidden;display:flex;align-items:center;justify-content:center;}}
.poster-grid{{position:relative;width:480px;height:520px;}}
.poster{{position:absolute;border-radius:6px;overflow:hidden;box-shadow:0 24px 64px rgba(0,0,0,0.6);transition:transform 0.35s ease,z-index 0s;background:{BG4};cursor:pointer;}}
.poster:hover{{z-index:100!important;transform:scale(1.06) rotate(0deg)!important;}}
.poster img{{width:100%;height:100%;object-fit:cover;display:block;}}
.poster-overlay{{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(0deg,rgba(0,0,0,0.75) 0%,transparent 100%);padding:16px 12px 10px;}}
.poster-title{{font-family:'Bebas Neue',sans-serif;font-size:13px;letter-spacing:1px;color:#fff;}}
.poster-year{{font-size:10px;color:rgba(255,255,255,0.45);letter-spacing:1px;}}
.poster-score{{position:absolute;top:8px;right:8px;background:{ACC1};color:#fff;font-size:10px;font-weight:800;padding:3px 6px;border-radius:2px;letter-spacing:0.5px;}}
.p1{{width:160px;height:240px;top:20px;left:20px;z-index:5;transform:rotate(-4deg);animation:float1 5s ease-in-out infinite;}}
.p2{{width:180px;height:268px;top:10px;left:160px;z-index:8;transform:rotate(2deg);animation:float2 6s ease-in-out infinite;}}
.p3{{width:150px;height:225px;top:40px;left:320px;z-index:4;transform:rotate(-2deg);animation:float3 7s ease-in-out infinite;}}
.p4{{width:175px;height:260px;top:250px;left:5px;z-index:6;transform:rotate(3deg);animation:float4 5.5s ease-in-out infinite;}}
.p5{{width:185px;height:275px;top:258px;left:165px;z-index:9;transform:rotate(-1deg);animation:float5 6.5s ease-in-out infinite;}}
.p6{{width:155px;height:232px;top:270px;left:330px;z-index:5;transform:rotate(4deg);animation:float6 5.8s ease-in-out infinite;}}
@keyframes float1{{0%,100%{{transform:rotate(-4deg) translateY(0)}}50%{{transform:rotate(-4deg) translateY(-10px)}}}}
@keyframes float2{{0%,100%{{transform:rotate(2deg) translateY(0)}}50%{{transform:rotate(2deg) translateY(-14px)}}}}
@keyframes float3{{0%,100%{{transform:rotate(-2deg) translateY(0)}}50%{{transform:rotate(-2deg) translateY(-9px)}}}}
@keyframes float4{{0%,100%{{transform:rotate(3deg) translateY(0)}}50%{{transform:rotate(3deg) translateY(-12px)}}}}
@keyframes float5{{0%,100%{{transform:rotate(-1deg) translateY(0)}}50%{{transform:rotate(-1deg) translateY(-16px)}}}}
@keyframes float6{{0%,100%{{transform:rotate(4deg) translateY(0)}}50%{{transform:rotate(4deg) translateY(-10px)}}}}

/* === SECTION LABELS === */
.section-label{{font-size:10px;letter-spacing:5px;text-transform:uppercase;color:{ACC1};margin-bottom:10px;font-weight:700;display:flex;align-items:center;gap:10px;}}
.section-label::after{{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(232,41,76,0.4),transparent);}}
.section-title{{font-family:'Bebas Neue',sans-serif;font-size:48px;color:{TEXT};letter-spacing:2px;margin-bottom:28px;line-height:1;}}

/* === TRAILERS === */
.trailers-section{{background:{BG2};padding:56px 72px;border-top:1px solid {CARD_BDR};}}
.trailers-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}}
.trailer-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;overflow:hidden;transition:all 0.25s;cursor:pointer;}}
.trailer-card:hover{{border-color:rgba(232,41,76,0.35);transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,0.25);}}
.trailer-thumb{{position:relative;width:100%;padding-top:56.25%;overflow:hidden;}}
.trailer-thumb iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}}
.trailer-info{{padding:14px 16px;}}
.trailer-title{{font-family:'Bebas Neue',sans-serif;font-size:17px;color:{TEXT};letter-spacing:1px;margin-bottom:3px;}}
.trailer-meta{{font-size:10px;color:{TEXT3};letter-spacing:1px;text-transform:uppercase;}}
.trailer-genre{{display:inline-block;border:1px solid rgba(232,41,76,0.35);border-radius:2px;color:{ACC1};font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;padding:2px 8px;margin-top:6px;}}

/* === ANALYZER === */
.analyzer-section{{background:{BG2};padding:56px 72px;border-top:1px solid {CARD_BDR};}}
.analyzer-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:36px;position:relative;overflow:hidden;}}
.analyzer-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{ACC1},{ACC2},{ACC3},{ACC4},{ACC5});}}

/* === GENRE GRID — pure HTML, no Streamlit columns === */
.genre-section{{background:{BG2};padding:0 72px 56px;}}
.genre-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:0;}}
.genre-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:22px 18px;text-align:center;transition:all 0.25s;cursor:pointer;text-decoration:none!important;display:block;position:relative;overflow:hidden;}}
.genre-card:hover{{transform:translateY(-4px);text-decoration:none!important;}}
.genre-card:nth-child(1){{border-top:2px solid {ACC1};}}
.genre-card:nth-child(1):hover{{box-shadow:0 12px 32px rgba(232,41,76,0.18);}}
.genre-card:nth-child(2){{border-top:2px solid #ec4899;}}
.genre-card:nth-child(2):hover{{box-shadow:0 12px 32px rgba(236,72,153,0.18);}}
.genre-card:nth-child(3){{border-top:2px solid {ACC2};}}
.genre-card:nth-child(3):hover{{box-shadow:0 12px 32px rgba(249,115,22,0.18);}}
.genre-card:nth-child(4){{border-top:2px solid {ACC1};}}
.genre-card:nth-child(4):hover{{box-shadow:0 12px 32px rgba(232,41,76,0.18);}}
.genre-card:nth-child(5){{border-top:2px solid {ACC5};}}
.genre-card:nth-child(5):hover{{box-shadow:0 12px 32px rgba(129,140,248,0.18);}}
.genre-card:nth-child(6){{border-top:2px solid {ACC4};}}
.genre-card:nth-child(6):hover{{box-shadow:0 12px 32px rgba(34,211,165,0.18);}}
.genre-card:nth-child(7){{border-top:2px solid {ACC5};}}
.genre-card:nth-child(7):hover{{box-shadow:0 12px 32px rgba(129,140,248,0.18);}}
.genre-card:nth-child(8){{border-top:2px solid {ACC3};}}
.genre-card:nth-child(8):hover{{box-shadow:0 12px 32px rgba(250,204,21,0.18);}}
.genre-ico{{font-size:28px;margin-bottom:10px;line-height:1;}}
.genre-name{{font-family:'Bebas Neue',sans-serif;font-size:17px;letter-spacing:1.5px;color:{TEXT};margin-bottom:3px;}}
.genre-count{{font-size:10px;letter-spacing:2px;color:{TEXT3};text-transform:uppercase;}}

/* === RESULT === */
.result-wrap{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:28px;margin-top:20px;position:relative;overflow:hidden;}}
.result-pos::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{ACC4},#6ee7b7);}}
.result-neg::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{ACC1},{ACC2});}}
.result-emoji{{font-size:48px;text-align:center;margin-bottom:10px;}}
.result-label{{font-family:'Bebas Neue',sans-serif;font-size:40px;text-align:center;letter-spacing:3px;margin-bottom:8px;}}
.result-pos .result-label{{color:{ACC4};}}
.result-neg .result-label{{color:{ACC1};}}
.result-bar-wrap{{background:{BG4};border-radius:2px;height:6px;margin:12px 0;overflow:hidden;}}
.result-bar{{height:100%;border-radius:2px;transition:width 0.8s ease;}}
.result-pos .result-bar{{background:linear-gradient(90deg,{ACC4},#6ee7b7);}}
.result-neg .result-bar{{background:linear-gradient(90deg,{ACC1},{ACC2});}}
.conf-label{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};text-align:center;margin-top:6px;}}
.result-detail{{margin-top:14px;padding-top:14px;border-top:1px solid {CARD_BDR};font-size:13px;color:{TEXT2};line-height:1.8;}}
.result-keywords{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}}
.kw-pos{{background:rgba(34,211,165,0.1);border:1px solid rgba(34,211,165,0.3);border-radius:2px;color:{ACC4};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:3px 8px;}}
.kw-neg{{background:rgba(232,41,76,0.1);border:1px solid rgba(232,41,76,0.3);border-radius:2px;color:{ACC1};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:3px 8px;}}

/* === REVIEW / HISTORY CARDS === */
.review-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:18px;margin-bottom:12px;transition:border-color 0.2s;}}
.review-card:hover{{border-color:rgba(232,41,76,0.3);}}
.history-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:14px 18px;margin-bottom:8px;border-left:3px solid transparent;}}
.history-pos{{border-left-color:{ACC4};}}
.history-neg{{border-left-color:{ACC1};}}

/* === STATS === */
.stats-panel{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;}}
.stat-box{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:14px 18px;flex:1;min-width:110px;text-align:center;}}
.stat-val{{font-family:'Bebas Neue',sans-serif;font-size:30px;color:{ACC3};letter-spacing:1px;}}
.stat-lbl{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};margin-top:2px;}}

/* === ABOUT / TEAM === */
.about-section{{background:{ABOUT_BG};padding:40px 72px 8px 72px;}}
.team-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:24px 18px;text-align:center;transition:all 0.25s;}}
.team-card:hover{{border-color:rgba(232,41,76,0.3);transform:translateY(-3px);}}
.team-avatar{{width:64px;height:64px;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:24px;color:#fff;letter-spacing:1px;}}
.team-name{{font-family:'Bebas Neue',sans-serif;font-size:18px;letter-spacing:1px;color:{TEXT};margin-bottom:3px;}}
.team-role{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};}}
.tech-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:20px 14px;text-align:center;transition:all 0.25s;}}
.tech-card:hover{{border-color:rgba(129,140,248,0.35);transform:translateY(-3px);}}

/* === FEEDBACK / CONTACT === */
.fb-item{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:16px;margin-bottom:12px;transition:border-color 0.2s;}}
.fb-item:hover{{border-color:rgba(232,41,76,0.25);}}
.contact-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:28px;}}

/* === STREAMLIT INPUTS === */
.stTextInput input,.stTextArea textarea{{background:{INP_BG}!important;color:{INP_CLR}!important;border:1px solid {INP_BDR}!important;border-radius:4px!important;font-family:'Montserrat',sans-serif!important;font-size:14px!important;}}
.stTextInput input:focus,.stTextArea textarea:focus{{border-color:{ACC1}!important;box-shadow:0 0 0 2px rgba(232,41,76,0.15)!important;}}
.stTextInput label,.stTextArea label,.stSelectbox label,.stSelectSlider label{{color:{TEXT3}!important;font-size:10px!important;letter-spacing:2px!important;text-transform:uppercase!important;font-weight:700!important;}}
.stButton button{{background:{ACC1}!important;color:#fff!important;font-family:'Montserrat',sans-serif!important;font-weight:700!important;font-size:11px!important;letter-spacing:2px!important;text-transform:uppercase!important;border:none!important;border-radius:2px!important;transition:all 0.2s!important;padding:11px 22px!important;}}
.stButton button:hover{{background:#c91f3a!important;transform:translateY(-1px)!important;}}
.stSelectbox>div>div{{background:{INP_BG}!important;border:1px solid {INP_BDR}!important;color:{INP_CLR}!important;border-radius:4px!important;}}
[data-baseweb="select"]>div{{background:{INP_BG}!important;border-color:{INP_BDR}!important;}}
[data-baseweb="select"] *{{color:{INP_CLR}!important;}}
[role="listbox"]{{background:{BG3}!important;}}
[role="option"]{{background:{BG3}!important;color:{INP_CLR}!important;}}
[role="option"]:hover{{background:rgba(232,41,76,0.08)!important;}}

/* === PAGE SHELL === */
.page-wrap{{padding:40px 72px 8px 72px;background:{BG};}}
.page-content{{padding:0 72px 48px 72px;background:{BG};}}
.sec-title{{font-family:'Bebas Neue',sans-serif;font-size:52px;letter-spacing:2px;color:{TEXT};margin-bottom:8px;line-height:1;}}
.sec-sub{{font-family:'Crimson Text',serif;font-size:18px;font-style:italic;color:{TEXT3};margin-bottom:16px;}}
.char-counter{{text-align:right;color:{TEXT3};font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-top:3px;}}
.stars{{color:{ACC3};font-size:17px;letter-spacing:2px;}}
.pill{{display:inline-block;border:1px solid {CARD_BDR};border-radius:2px;color:{TEXT3};font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;padding:4px 10px;margin:2px 4px 2px 0;transition:all 0.2s;}}
.pill:hover{{border-color:{ACC1};color:{ACC1};}}

/* === AUTH === */
.auth-card{{background:{BG3};border:1px solid {CARD_BDR};border-radius:6px;padding:40px;position:relative;overflow:hidden;}}
.auth-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{ACC1},{ACC2},{ACC3});}}

/* === FOOTER === */
.footer{{background:{BG2};border-top:1px solid {CARD_BDR};padding:36px 72px;}}
.footer-top{{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:24px;margin-bottom:24px;}}
.footer-logo{{font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:4px;background:linear-gradient(90deg,{ACC1},{ACC2});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.footer-sub{{color:{TEXT3};font-size:10px;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;}}
.footer-genres{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;}}
.footer-credit{{color:{TEXT3};font-size:10px;letter-spacing:1.5px;text-transform:uppercase;border-top:1px solid {CARD_BDR};padding-top:18px;text-align:center;}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# MODEL + RULE-BASED FALLBACK

# ──────────────────────────────────────────────────────────────────────────────
MODEL_DIR = "sentiment_model"

@st.cache_resource(show_spinner=False)
def load_model():
    if not TORCH_AVAILABLE or not os.path.exists(MODEL_DIR):
        return None, None
    try:
        tok = DistilBertTokenizer.from_pretrained(MODEL_DIR)
        mdl = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
        mdl.eval()
        return tok, mdl
    except Exception:
        return None, None

POSITIVE_WORDS = [
    "amazing","brilliant","excellent","outstanding","superb","fantastic","wonderful",
    "great","good","beautiful","masterpiece","breathtaking","stunning","incredible",
    "love","loved","enjoy","enjoyed","perfect","best","top","recommend","awesome",
    "exceptional","remarkable","moving","touching","emotional","powerful","riveting",
    "captivating","compelling","engaging","entertaining","thrilling","exciting",
    "hilarious","funny","heartwarming","uplifting","inspiring","genius","innovative",
    "fresh","original","unique","memorable","classic","timeless","epic","spectacular",
    "impressive","flawless","terrific","magnificent","delightful","charming",
    "enchanting","mesmerizing","gripping","must watch","5 star","five star","10/10",
    "worth it","solid","decent","nice","well done","beautifully","extraordinary",
    "fascinating","thought provoking","thought-provoking","visually","stunning",
]
NEGATIVE_WORDS = [
    "terrible","awful","horrible","dreadful","boring","waste","bad","worst",
    "disappointing","disappoints","disappointed","mediocre","poor","weak","slow",
    "predictable","cliche","generic","forgettable","unwatchable","nonsense",
    "ridiculous","laughable","pathetic","atrocious","abysmal","trash","garbage",
    "rubbish","flop","fail","failed","failure","hollow","shallow","incoherent",
    "confusing","mess","disaster","disastrous","overlong","tedious","dull","flat",
    "bland","lifeless","unconvincing","unrealistic","forced","contrived","sloppy",
    "amateurish","cringe","skip","avoid","overhyped","overrated","1 star","one star",
    "0/10","not worth","waste of time","bored","terrible acting","bad script",
    "poor writing","no plot","makes no sense","doesn't make sense","fell asleep",
]

def rule_based_sentiment(text: str):
    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    total = pos + neg
    if total == 0:
        return "POSITIVE", 57.0
    pos_ratio = pos / total
    if pos_ratio >= 0.5:
        conf = 55 + min(pos_ratio * 42, 42)
        return "POSITIVE", round(conf, 1)
    else:
        neg_ratio = 1 - pos_ratio
        conf = 55 + min(neg_ratio * 42, 42)
        return "NEGATIVE", round(conf, 1)

def extract_keywords(text: str, label: str):
    lower = text.lower()
    if label == "POSITIVE":
        return [w for w in POSITIVE_WORDS if w in lower][:6], []
    else:
        return [], [w for w in NEGATIVE_WORDS if w in lower][:6]

def analyze(text: str):
    tok, mdl = load_model()
    if tok and mdl:
        try:
            inputs = tok(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            with torch.no_grad():
                logits = mdl(**inputs).logits
            probs = F.softmax(logits, dim=1)[0]
            label = "POSITIVE" if probs[1] > probs[0] else "NEGATIVE"
            conf = float(probs[1]) if label == "POSITIVE" else float(probs[0])
            return label, round(conf * 100, 1)
        except Exception:
            pass
    return rule_based_sentiment(text)

def show_result(label, conf, text=""):
    is_pos = label == "POSITIVE"
    emoji = "🎉" if is_pos else "💔"
    color = "{ACC4}" if is_pos else "{ACC1}"
    cls = "result-pos" if is_pos else "result-neg"
    pos_kws, neg_kws = extract_keywords(text, label)
    kw_html = "".join(f'<span class="kw-pos">{kw}</span>' for kw in pos_kws)
    kw_html += "".join(f'<span class="kw-neg">{kw}</span>' for kw in neg_kws)
    words = len(text.split()); chars = len(text)
    detail_extra = f'<div class="result-keywords">{kw_html}</div>' if kw_html else ""
    st.markdown(f"""
    <div class="result-wrap {cls}">
      <div class="result-emoji">{emoji}</div>
      <div class="result-label" style="color:{color};">{label}</div>
      <div class="result-bar-wrap">
        <div class="result-bar" style="width:{conf}%;background:{color};"></div>
      </div>
      <div class="conf-label">Confidence: {conf}%</div>
      <div class="result-detail">
        📝 {words} words &nbsp;·&nbsp; {chars} characters
        {detail_extra}
      </div>
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# NAVBAR
# ──────────────────────────────────────────────────────────────────────────────
def nav_link(label, page):
    is_act = " act" if cur_page == page else ""
    return f'<a class="nb-link{is_act}" href="?page={page.replace(" ", "+")}">{label}</a>'

genres = [
    ("🔪","Thriller","Dark"),("❤️","Romance","Warm"),("😂","Comedy","Funny"),("👻","Horror","Scary"),
    ("🦸","Action","Intense"),("🚀","Sci-Fi","Futuristic"),("🎭","Drama","Deep"),("🧩","Mystery","Cryptic"),
]
genre_dd = "".join(
    f'<a class="dd-item" href="?page=Genre&genre={g[0]}{g[1]}"><span class="dd-ico">{g[0]}</span>{g[1]}</a>'
    for g in genres
)
toggle_icon = "🌙" if not st.session_state.dark_mode else "☀️"
auth_html = (
    f'<span class="nb-badge">🎬 {st.session_state.username}</span><a class="nb-login" href="?page=__logout__">Sign Out</a>'
    if st.session_state.logged_in else
    f'<a class="nb-login" href="?page=Login">Sign In</a><a class="nb-signup" href="?page=Signup">Join Now</a>'
)
films = ["THE GODFATHER","INCEPTION","PARASITE","INTERSTELLAR","PULP FICTION",
         "DARK KNIGHT","SCHINDLER'S LIST","CITY OF GOD","SPIRITED AWAY","GOODFELLAS",
         "WHIPLASH","BLADE RUNNER 2049","ARRIVAL","THE REVENANT","MAD MAX: FURY ROAD"]
ticker = "".join(f'<span class="filmstrip-item">{f}</span><span class="filmstrip-dot">◆</span>' for f in films*4)

st.markdown(f"""
<nav class="nb">
  <a class="nb-logo" href="?page=Home">🎬 FLICKFEEL</a>
  <div class="nb-links">
    {nav_link("HOME","Home")}
    {nav_link("ANALYZE","Analyze")}
    {nav_link("HISTORY","History")}
    <div class="dd">
      <div class="dd-btn {'act' if cur_page=='Genre' else ''}">GENRES <span class="dd-arrow">▾</span></div>
      <div class="dd-panel"><div class="dd-panel-inner">{genre_dd}</div></div>
    </div>
    {nav_link("ABOUT","About")}
    {nav_link("FEEDBACK","Feedback")}
    {nav_link("CONTACT","Contact Us")}
  </div>
  <div class="nb-auth">
    <a class="nb-toggle" href="?page=__toggle__" title="Toggle theme">{toggle_icon}</a>
    {auth_html}
  </div>
</nav>
<div class="filmstrip"><div class="filmstrip-track">{ticker}</div></div>
<script>
(function(){{
  function killGaps(){{
    var all = document.querySelectorAll(
      '[data-testid="stVerticalBlock"], [data-testid="stVerticalBlockSeparator"], ' +
      '.stMainBlockContainer, .block-container, ' +
      '[data-testid="stAppViewBlockContainer"], section[data-testid="stMain"] > div'
    );
    all.forEach(function(el){{
      el.style.setProperty('padding','0','important');
      el.style.setProperty('margin','0','important');
      el.style.setProperty('gap','0','important');
    }});
    document.querySelectorAll('.element-container, [data-testid="element-container"]').forEach(function(el){{
      el.style.setProperty('margin','0','important');
      el.style.setProperty('padding','0','important');
    }});
  }}
  killGaps();
  new MutationObserver(killGaps).observe(document.body,{{childList:true,subtree:true}});
}})();
</script>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HOME
# ──────────────────────────────────────────────────────────────────────────────
if cur_page == "Home":
    poster_data = [
        ("https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg","The Godfather","1972","9.2","p1"),
        ("https://image.tmdb.org/t/p/w342/ljsZTbVsrQSqZgWeep2B1QiDKuh.jpg","Inception","2010","8.8","p2"),
        ("https://image.tmdb.org/t/p/w342/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg","Parasite","2019","8.5","p3"),
        ("https://image.tmdb.org/t/p/w342/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg","Interstellar","2014","8.6","p4"),
        ("https://image.tmdb.org/t/p/w342/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg","Pulp Fiction","1994","8.9","p5"),
        ("https://image.tmdb.org/t/p/w342/qJ2tW6WMUDux911r6m7haRef0WH.jpg","The Dark Knight","2008","9.0","p6"),
    ]
    posters_html = "".join(f"""<div class="poster {cls}"><img src="{img}" alt="{title}" onerror="this.style.background='#333'"/>
        <div class="poster-score">{score}</div><div class="poster-overlay"><div class="poster-title">{title}</div><div class="poster-year">{year}</div></div></div>"""
        for img,title,year,score,cls in poster_data)

    st.markdown(f"""
    <div class="hero-wrap"><div class="hero-video-frame">
      <div class="hero-spotlight"></div><div class="hero-spotlight2"></div>
      <div class="hero-content">
        <div class="hero-eyebrow">AI-POWERED SENTIMENT ENGINE</div>
        <div class="hero-title">FEEL THE<br><span class="red">FILM.</span></div>
        <div class="hero-sub">Decode the emotion behind every review. DistilBERT trained on 50,000 real IMDb reviews.</div>
        <div class="hero-cta">
          <a class="btn-primary" href="?page=Analyze">▶ ANALYZE A REVIEW</a>
          <a class="btn-secondary" href="?page=About">HOW IT WORKS →</a>
        </div>
        <div class="hero-stats">
          <div><div class="hero-stat-val">50K</div><div class="hero-stat-lbl">IMDb Reviews</div></div>
          <div><div class="hero-stat-val">93%</div><div class="hero-stat-lbl">Accuracy</div></div>
          <div><div class="hero-stat-val">8</div><div class="hero-stat-lbl">Genres</div></div>
        </div>
      </div>
      <div class="posters-panel"><div class="poster-grid">{posters_html}</div></div>
    </div></div>""", unsafe_allow_html=True)

    # Trailers
    trailers = [
        ("https://www.youtube.com/embed/UaVTIH8mujA","The Godfather","1972","Biography · Drama"),
        ("https://www.youtube.com/embed/d9MyW72ELq0","Avatar: The Way of Water","2022","Sci-Fi · Epic"),
        ("https://www.youtube.com/embed/JfVOs4VSpmA","Spider Man: No way home","2021","Action · Drama"),
    ]
    trailer_cards = "".join(f"""<div class="trailer-card">
      <div class="trailer-thumb"><iframe src="{url}?rel=0&modestbranding=1" allowfullscreen loading="lazy"></iframe></div>
      <div class="trailer-info"><div class="trailer-title">{title}</div><div class="trailer-meta">{year}</div><span class="trailer-genre">{genre}</span></div>
    </div>""" for url,title,year,genre in trailers)
    st.markdown(f'<div class="trailers-section"><div class="section-label">NOW PLAYING</div><div class="section-title">HOT TRAILERS</div><div class="trailers-grid">{trailer_cards}</div></div>', unsafe_allow_html=True)

    # Quick analyzer
    st.markdown(f'<div class="analyzer-section"><div class="section-label">TRY IT NOW</div><div class="section-title">ANALYZE A REVIEW</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="padding:0 72px 72px;background:{BG2};">', unsafe_allow_html=True)
    st.markdown('<div class="analyzer-card">', unsafe_allow_html=True)
    review_text = st.text_area("", placeholder="Paste any movie review here — the AI will instantly detect its sentiment...", height=130, key="home_ta", label_visibility="collapsed")
    if review_text:
        st.markdown(f'<div class="char-counter">{len(review_text)} chars · {len(review_text.split())} words</div>', unsafe_allow_html=True)
    col_b, _ = st.columns([1, 5])
    with col_b:
        analyze_clicked = st.button("⚡ ANALYZE", use_container_width=True, key="home_btn")
    st.markdown('</div>', unsafe_allow_html=True)
    if analyze_clicked:
        if review_text.strip():
            with st.spinner("🎬 Analyzing sentiment..."):
                label, conf = analyze(review_text)
            show_result(label, conf, review_text)
            st.session_state.review_history.append({"text": review_text[:120]+("..." if len(review_text)>120 else ""),"label":label,"conf":conf,"time":datetime.now().strftime("%b %d, %Y %I:%M %p")})
        else:
            st.warning("⚠️ Please enter a review to analyze.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Genre grid — one single HTML block so CSS grid works correctly
    genre_cards_html = "".join(
        f'<a class="genre-card" href="?page=Genre&genre={g[0]}{g[1]}">'  
        f'<div class="genre-ico">{g[0]}</div>'
        f'<div class="genre-name">{g[1]}</div>'
        f'<div class="genre-count">{g[2]} VIBES</div></a>'
        for g in genres
    )
    st.markdown(f"""
    <div class="genre-section">
      <div class="section-label">EXPLORE</div>
      <div class="section-title">BROWSE BY GENRE</div>
      <div class="genre-grid">{genre_cards_html}</div>
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Analyze":
    st.markdown(f"""<div class="page-wrap">
    <div class="section-label">SENTIMENT ANALYSIS</div>
    <div class="sec-title">DECODE THE REVIEW</div>
    <div class="sec-sub">AI-powered engine — always gives an answer, even without the model</div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")
    with col1:
        st.markdown('<div class="analyzer-card">', unsafe_allow_html=True)
        rev = st.text_area("YOUR REVIEW", placeholder="Paste a movie review to decode its sentiment...", height=200, key="analyze_ta")
        if rev:
            st.markdown(f'<div class="char-counter">{len(rev)} chars · {len(rev.split())} words</div>', unsafe_allow_html=True)
        ab = st.button("⚡ ANALYZE SENTIMENT", use_container_width=True, key="ab")
        st.markdown('</div>', unsafe_allow_html=True)
        if ab:
            if rev.strip():
                with st.spinner("🎬 Analyzing..."):
                    label, conf = analyze(rev)
                show_result(label, conf, rev)
                st.session_state.review_history.append({"text":rev[:120]+("..." if len(rev)>120 else ""),"label":label,"conf":conf,"time":datetime.now().strftime("%b %d, %Y %I:%M %p")})
                st.info("✅ Saved to History!")
            else:
                st.warning("⚠️ Please enter a review to analyze.")

    with col2:
        examples = [
            ("The cinematography was breathtaking — every frame felt like a painting. A masterpiece.","POSITIVE","Inception"),
            ("Boring, predictable plot with terrible acting. Complete waste of time.","NEGATIVE","Generic Flick"),
            ("An emotional rollercoaster that left me in tears. Brilliant storytelling!","POSITIVE","Schindler's List"),
            ("The CGI was laughable and the dialogue felt forced. Disappointing sequel.","NEGATIVE","Blockbuster"),
        ]
        st.markdown(f'<div style="color:{TEXT3};font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;">EXAMPLE REVIEWS</div>', unsafe_allow_html=True)
        for i, (text, expected, movie) in enumerate(examples):
            color = "{ACC4}" if expected == "POSITIVE" else "{ACC1}"
            st.markdown(f"""<div class="review-card">
              <div style="color:{color};font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:6px;">● {expected}</div>
              <div style="color:{TEXT2};font-size:13px;line-height:1.6;font-style:italic;">"{text[:80]}..."</div>
              <div style="color:{TEXT4};font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-top:8px;">{movie}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Try this →", key=f"ex_{i}"):
                st.session_state["analyze_ta_preset"] = text
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "History":
    st.markdown(f"""<div class="page-wrap">
    <div class="section-label">YOUR ANALYSES</div>
    <div class="sec-title">REVIEW HISTORY</div>
    <div class="sec-sub">All sentiment analyses from this session</div>
    </div>""", unsafe_allow_html=True)
    history = st.session_state.review_history
    if not history:
        st.markdown(f'<div style="color:{TEXT3};text-align:center;padding:60px 0;font-size:15px;">No analyses yet — <a href="?page=Analyze" style="color:{ACC1};text-decoration:none;">Analyze a review</a> to get started!</div>', unsafe_allow_html=True)
    else:
        total = len(history)
        pos_count = sum(1 for h in history if h["label"]=="POSITIVE")
        avg_conf = round(sum(h["conf"] for h in history)/total, 1)
        st.markdown(f"""<div class="stats-panel">
          <div class="stat-box"><div class="stat-val">{total}</div><div class="stat-lbl">Total</div></div>
          <div class="stat-box"><div class="stat-val" style="color:{ACC4};">{pos_count}</div><div class="stat-lbl">Positive</div></div>
          <div class="stat-box"><div class="stat-val" style="color:{ACC1};">{total-pos_count}</div><div class="stat-lbl">Negative</div></div>
          <div class="stat-box"><div class="stat-val">{avg_conf}%</div><div class="stat-lbl">Avg Confidence</div></div>
        </div>""", unsafe_allow_html=True)
        if st.button("🗑️ CLEAR HISTORY", key="clear_hist"):
            st.session_state.review_history = []
            st.rerun()
        for item in reversed(history):
            is_pos = item["label"]=="POSITIVE"
            color = "{ACC4}" if is_pos else "{ACC1}"
            cls = "history-pos" if is_pos else "history-neg"
            emoji = "🎉" if is_pos else "💔"
            st.markdown(f"""<div class="history-card {cls}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="color:{color};font-weight:700;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;">{emoji} {item['label']} · {item['conf']}%</span>
                <span style="color:{TEXT3};font-size:10px;letter-spacing:1px;">{item['time']}</span>
              </div>
              <div style="color:{TEXT2};font-size:13px;line-height:1.6;font-style:italic;">"{item['text']}"</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Genre":
    gen = st.session_state.get("selected_genre") or "🎬 All Genres"
    st.markdown(f"""<div class="page-wrap">
    <div class="section-label">GENRE ANALYSIS</div>
    <div class="sec-title">{gen}</div>
    <div class="sec-sub">Analyze how audiences feel about {gen} films</div>
    </div>""", unsafe_allow_html=True)
    g1, g2 = st.columns([3, 2], gap="large")
    with g1:
        st.markdown('<div class="analyzer-card">', unsafe_allow_html=True)
        rev2 = st.text_area(f"Paste a {gen} review", placeholder=f"Drop a {gen} movie review here...", height=180, key="genre_ta")
        if rev2:
            st.markdown(f'<div class="char-counter">{len(rev2)} chars · {len(rev2.split())} words</div>', unsafe_allow_html=True)
        gb = st.button("⚡ ANALYZE", use_container_width=True, key="genre_btn")
        st.markdown('</div>', unsafe_allow_html=True)
        if gb:
            if rev2.strip():
                with st.spinner("🎬 Decoding..."):
                    label2, conf2 = analyze(rev2)
                show_result(label2, conf2, rev2)
                st.session_state.review_history.append({"text":rev2[:120]+("..." if len(rev2)>120 else ""),"label":label2,"conf":conf2,"time":datetime.now().strftime("%b %d, %Y %I:%M %p")})
            else:
                st.warning("⚠️ Please enter a review to analyze.")
    with g2:
        st.markdown(f'<div style="color:{TEXT3};font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;">OTHER GENRES</div>', unsafe_allow_html=True)
        for g in genres:
            active = "border-color:{ACC1};" if f"{g[0]}{g[1]}" == gen else ""
            st.markdown(f'<a class="genre-card" href="?page=Genre&genre={g[0]}{g[1]}" style="text-decoration:none;display:block;margin-bottom:10px;padding:12px 16px;{active}"><span style="font-size:20px;">{g[0]}</span> <span class="genre-name" style="font-size:14px;vertical-align:middle;">{g[1]}</span></a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "About":
    st.markdown(f"""<div class="about-section">
    <div class="section-label">THE STORY</div>
    <div class="sec-title">BEHIND FLICKFEEL</div>
    </div>""", unsafe_allow_html=True)
    ac1, ac2 = st.columns([3, 2], gap="large")
    with ac1:
        st.markdown(f"""<div style="color:{TEXT2};font-size:15px;line-height:2;margin-bottom:28px;">
          FlickFeel is an AI-powered movie sentiment analysis platform trained on <strong style="color:{ACC3};">50,000 IMDb reviews</strong>.
          Using a fine-tuned <strong style="color:{ACC3};">DistilBERT</strong> model, it decodes the emotional fingerprint of any movie review in real time.
          When the model isn't available, a smart rule-based engine kicks in automatically so you always get an answer.
        </div>
        <div style="display:flex;gap:24px;margin-bottom:36px;flex-wrap:wrap;">
          <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:48px;color:{ACC1};letter-spacing:1px;">93%</div><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};">Accuracy</div></div>
          <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:48px;color:{ACC3};letter-spacing:1px;">50K</div><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};">Reviews Trained</div></div>
          <div style="text-align:center;"><div style="font-family:'Bebas Neue',sans-serif;font-size:48px;color:{ACC5};letter-spacing:1px;">&lt;1s</div><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};">Inference Time</div></div>
        </div>""", unsafe_allow_html=True)
    with ac2:
        for ico,name,sub in [("🤗","HuggingFace","DistilBERT Model"),("🔥","PyTorch","Deep Learning"),("🌊","Streamlit","Web Interface"),("📚","IMDb Dataset","50K Reviews")]:
            st.markdown(f'<div class="tech-card" style="margin-bottom:12px;"><div style="font-size:28px;margin-bottom:8px;">{ico}</div><div style="font-family:\'Bebas Neue\',sans-serif;font-size:18px;letter-spacing:1px;color:{TEXT};">{name}</div><div style="font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-top:3px;">{sub}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="margin-top:48px;"><div class="section-label">THE CREW</div><div class="sec-title">MEET THE TEAM</div></div>', unsafe_allow_html=True)
    team_cols = st.columns(4)
    for i,(init,name,role) in enumerate([("A","Ananya","ML Engineer"),("S","Saptshrungi","Backend Dev"),("Ak","Akanksha","UI Designer"),("P","Priyanka","Data Scientist")]):
        with team_cols[i]:
            st.markdown(f'<div class="team-card"><div class="team-avatar">{init}</div><div class="team-name">{name}</div><div class="team-role">{role}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Contact Us":
    st.markdown(f"""<div class="page-wrap">
    <div class="section-label">GET IN TOUCH</div>
    <div class="sec-title">CONTACT US</div>
    <div class="sec-sub">We'd love to hear from you</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    cf, ci = st.columns([3, 2], gap="large")
    with cf:
        st.markdown('<div class="contact-card">', unsafe_allow_html=True)
        n = st.text_input("YOUR NAME", placeholder="John Doe", key="cn")
        e = st.text_input("EMAIL", placeholder="you@example.com", key="ce")
        s = st.selectbox("SUBJECT", ["General Inquiry","Bug Report","Feature Request","Partnership","Other"], key="cs")
        m = st.text_area("MESSAGE", placeholder="Write your message here...", height=130, key="cm")
        if st.button("📨 SEND MESSAGE", use_container_width=True, key="send_msg"):
            if n.strip() and e.strip() and m.strip():
                st.success(f"Thanks {n}! We'll reply to {e} within 24 hours.")
            else:
                st.warning("Please fill all fields.")
        st.markdown('</div>', unsafe_allow_html=True)
    with ci:
        st.markdown(f"""<div class="contact-card" style="margin-bottom:16px;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:20px;letter-spacing:1px;color:{TEXT};margin-bottom:18px;">DETAILS</div>
          <div style="color:{TEXT2};font-size:14px;line-height:3;">
            📧 <strong style="color:{ACC3};">Email:</strong> flickfeel@team.com<br>
            📱 <strong style="color:{ACC3};">Phone:</strong> +91 98765 43210<br>
            🌐 <strong style="color:{ACC3};">Web:</strong> www.flickfeel.ai<br>
            📍 <strong style="color:{ACC3};">Location:</strong> Pune, India<br>
            🕐 <strong style="color:{ACC3};">Hours:</strong> Mon–Fri, 9AM–6PM IST
          </div></div>
        <div class="contact-card"><div style="font-family:'Bebas Neue',sans-serif;font-size:20px;letter-spacing:1px;color:{TEXT};margin-bottom:14px;">FOLLOW US</div>
          <span class="pill">Twitter</span><span class="pill">LinkedIn</span><span class="pill">GitHub</span><span class="pill">Instagram</span>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Feedback":
    st.markdown(f"""<div class="page-wrap">
    <div class="section-label">YOUR VOICE</div>
    <div class="sec-title">AUDIENCE REVIEWS</div>
    <div class="sec-sub">Tell us what you think of FlickFeel</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    ff, fr = st.columns([2, 3], gap="large")
    with ff:
        st.markdown('<div class="contact-card">', unsafe_allow_html=True)
        fn = st.text_input("NAME", value=st.session_state.username if st.session_state.logged_in else "", key="fbn")
        fr2 = st.select_slider("RATING", options=["1★","2★","3★","4★","5★"], value="5★", key="fbr")
        fc = st.selectbox("CATEGORY", ["General","Model Accuracy","UI/UX","Performance","Feature Request"], key="fbc")
        ft = st.text_area("YOUR REVIEW", placeholder="Tell us what you think...", height=110, key="fbt")
        if st.button("🎬 SUBMIT REVIEW", use_container_width=True, key="submit_review"):
            if fn.strip() and ft.strip():
                st.session_state.feedbacks.append({"name":fn,"rating":fr2,"category":fc,"text":ft,"time":datetime.now().strftime("%b %d, %Y %I:%M %p")})
                st.success("Thank you for your feedback!")
                st.rerun()
            else:
                st.warning("Please fill in your name and feedback.")
        st.markdown('</div>', unsafe_allow_html=True)
    with fr:
        st.markdown(f'<div style="color:{TEXT3};font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:16px;">RECENT REVIEWS</div>', unsafe_allow_html=True)
        for fb in reversed([
            {"name":"Rahul M.","rating":"5★","category":"Model Accuracy","text":"Incredibly accurate! Really impressed by the analysis.","time":"Mar 10, 2025"},
            {"name":"Sneha P.","rating":"4★","category":"UI/UX","text":"Beautiful cinematic interface. Very professional.","time":"Mar 08, 2025"},
            {"name":"Arjun K.","rating":"5★","category":"General","text":"Best movie review analyzer I've tried!","time":"Mar 05, 2025"},
        ] + st.session_state.feedbacks):
            st.markdown(f"""<div class="fb-item">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-family:'Bebas Neue',sans-serif;font-size:17px;letter-spacing:1px;color:{TEXT};">👤 {fb['name']}</span>
                <span style="color:{ACC3};letter-spacing:2px;">{fb['rating']}</span>
              </div>
              <div style="color:{ACC1};font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin:4px 0;">{fb.get('category','')}</div>
              <div style="color:{TEXT2};font-size:13px;line-height:1.7;font-style:italic;">"{fb['text']}"</div>
              <div style="color:{TEXT4};font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-top:8px;">🕐 {fb['time']}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Login":
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;margin-bottom:28px;"><div style="font-family:\'Bebas Neue\',sans-serif;font-size:40px;letter-spacing:3px;color:{TEXT};">WELCOME BACK</div><div style="color:{TEXT3};font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-top:6px;">Sign in to your FlickFeel account</div></div>', unsafe_allow_html=True)
        u = st.text_input("USERNAME", placeholder="Enter username", key="lu")
        p = st.text_input("PASSWORD", type="password", placeholder="Enter password", key="lp")
        if st.button("🎬 SIGN IN", use_container_width=True, key="signin_btn"):
            if st.session_state.users_db.get(u) == p:
                st.session_state.logged_in = True; st.session_state.username = u
                st.session_state.page = "Home"; st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown(f'<div style="text-align:center;margin-top:16px;color:{TEXT3};font-size:12px;letter-spacing:1px;text-transform:uppercase;">No account yet?</div>', unsafe_allow_html=True)
        if st.button("CREATE ACCOUNT", use_container_width=True, key="to_signup"):
            st.session_state.page = "Signup"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
elif cur_page == "Signup":
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;margin-bottom:28px;"><div style="font-family:\'Bebas Neue\',sans-serif;font-size:40px;letter-spacing:3px;color:{TEXT};">JOIN FLICKFEEL</div><div style="color:{TEXT3};font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-top:6px;">Create your account today</div></div>', unsafe_allow_html=True)
        su = st.text_input("USERNAME", placeholder="e.g. moviefan123", key="su")
        se = st.text_input("EMAIL", placeholder="you@example.com", key="se")
        sp = st.text_input("PASSWORD", type="password", placeholder="Min 6 characters", key="sp")
        sc = st.text_input("CONFIRM PASSWORD", type="password", placeholder="Re-enter password", key="sc")
        if st.button("🎬 CREATE ACCOUNT", use_container_width=True, key="create_acct"):
            if not (su.strip() and se.strip() and sp.strip()):
                st.warning("Please fill in all fields.")
            elif len(sp)<6: st.error("Password must be at least 6 characters.")
            elif sp!=sc: st.error("Passwords do not match.")
            elif su in st.session_state.users_db: st.error("Username already exists.")
            else:
                st.session_state.users_db[su]=sp; st.session_state.logged_in=True
                st.session_state.username=su; st.session_state.page="Home"; st.rerun()
        st.markdown(f'<div style="text-align:center;margin-top:16px;color:{TEXT3};font-size:12px;letter-spacing:1px;text-transform:uppercase;">Already have an account?</div>', unsafe_allow_html=True)
        if st.button("BACK TO SIGN IN", use_container_width=True, key="to_login"):
            st.session_state.page = "Login"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER — genres in one horizontal row
# ──────────────────────────────────────────────────────────────────────────────
genre_footer_pills = "".join(
    f'<a href="?page=Genre&genre={g[0]}{g[1]}" class="pill" style="text-decoration:none;">{g[0]} {g[1]}</a>'
    for g in genres
)
st.markdown(f"""
<div class="footer">
  <div class="footer-top">
    <div>
      <div class="footer-logo">🎬 FLICKFEEL</div>
      <div class="footer-sub">DistilBERT Sentiment Engine · IMDb Dataset · 50K Reviews</div>
    </div>
    <div>
      <div style="color:{TEXT3};font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:10px;">BROWSE GENRES</div>
      <div class="footer-genres">{genre_footer_pills}</div>
    </div>
    <div>
      <div style="color:{TEXT3};font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:10px;">QUICK LINKS</div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <a href="?page=Analyze" style="color:{TEXT3};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;text-decoration:none;">⚡ Analyze</a>
        <a href="?page=History" style="color:{TEXT3};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;text-decoration:none;">📋 History</a>
        <a href="?page=About" style="color:{TEXT3};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;text-decoration:none;">🎬 About</a>
        <a href="?page=Contact+Us" style="color:{TEXT3};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;text-decoration:none;">📧 Contact</a>
      </div>
    </div>
  </div>
  <div class="footer-credit">Built with ❤️ by Ananya · Saptshrungi · Akanksha · Priyanka &nbsp;|&nbsp; © 2025 FlickFeel</div>
</div>
""", unsafe_allow_html=True)

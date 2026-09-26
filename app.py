#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULTI PRO MMC — Crypto-Exchange meets Next-Gen Logistics
=========================================================
Single-file production Flask application.

Company : MULTI PRO MMC (Director: Rövşən Heydərov)
Focus   : High-end chemical supply + logistics (B2B/B2C)
Phone   : +994 77 344 14 00
Email   : multi.r.pro111@gmail.com
Address : AZ5000, Sumqayıt ş. 21-ci MK/RN, ev 52

Routes
------
  GET /                      → Public freight & supply showcase
  GET /admin-panel           → Hidden control-tower (session protected)
  GET /product-image/<file>  → Public product images (uploads/products/)
  GET /partner-logo/<file>   → Partner logos (uploads/partners/)

Run (dev) ......... python app.py
Run (production) .. gunicorn -w 4 -b 0.0.0.0:8000 app:app
Requirements ...... pip install Flask

Database : sqlite3 file `multipro.db`
Uploads  : ./uploads/products/  (public product images)
           ./uploads/tenders/   (tender vault, admin-only download)
           ./uploads/partners/  (partner logos, public)
Admin password : "1234"  (override with env ADMIN_PASSWORD)
"""

import os
import re
import sqlite3
import datetime
from functools import wraps

from flask import (
    Flask, g, request, session, redirect, url_for,
    render_template_string, jsonify, send_from_directory, abort
)
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "multipro.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PRODUCT_IMAGE_DIR = os.path.join(UPLOAD_FOLDER, "products")
TENDER_DIR = os.path.join(UPLOAD_FOLDER, "tenders")
PARTNER_LOGO_DIR = os.path.join(UPLOAD_FOLDER, "partners")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")
SECRET_KEY = os.environ.get("SECRET_KEY", "multi-pro-mmc-ultra-secret-2026-CHANGE-IN-PROD")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB per product image

COMPANY = {
    "name": "MULTI PRO MMC",
    "director": "Rövşən Heydərov",
    "phone_display": "+994 77 344 14 00",
    "phone_href": "+994773441400",
    "phone_wa": "994773441400",
    "email": "multi.r.pro111@gmail.com",
    "address": "AZ5000, Sumqayıt ş. 21-ci MK/RN, ev 52",
}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    DATABASE=DATABASE,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50 MB
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)
os.makedirs(TENDER_DIR, exist_ok=True)
os.makedirs(PARTNER_LOGO_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS tender_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stored_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            size INTEGER NOT NULL DEFAULT 0,
            uploaded_at TEXT NOT NULL
        )
    """)
    db.commit()
    cur = db.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        now = datetime.datetime.now().isoformat(timespec="seconds")
        seed = [
            ("Epoksi Qətran və Sərtləşdiricilər",
             "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=900&auto=format&fit=crop"),
            ("Poliuretan Köpük Sistemləri",
             "https://images.unsplash.com/photo-1581094794329-c8112a89af12?q=80&w=900&auto=format&fit=crop"),
            ("Sənaye Boyaları və Kaplamalar",
             "https://images.unsplash.com/photo-1504307651254-35680f356dfd?q=80&w=900&auto=format&fit=crop"),
            ("Anbar Kimyası və Təmizlik",
             "https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=900&auto=format&fit=crop"),
            ("Elektrik İzolyasiya Materialları",
             "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?q=80&w=900&auto=format&fit=crop"),
            ("Sənaye İşıqlandırma Sistemləri",
             "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=900&auto=format&fit=crop"),
            ("Metal Borular və Profillər",
             "https://images.unsplash.com/photo-1531834685032-c34bf0d84c77?q=80&w=900&auto=format&fit=crop"),
            ("Laboratoriya Reaktivləri",
             "https://images.unsplash.com/photo-1504148455328-c376907d081c?q=80&w=900&auto=format&fit=crop"),
        ]
        db.executemany(
            "INSERT INTO products (name, image_url, created_at) VALUES (?, ?, ?)",
            [(n, u, now) for n, u in seed],
        )
        db.commit()
    db.close()


def format_size(num):
    try:
        num = int(num or 0)
    except Exception:
        num = 0
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0 or unit == "GB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{num} B"
        num /= 1024.0
    return f"{num:.1f} GB"


def is_admin():
    return bool(session.get("admin_logged_in") is True)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_admin():
            return jsonify({"ok": False, "error": "Giriş tələb olunur. Zəhmət olmasa /admin-panel vasitəsilə daxil olun."}), 403
        return fn(*args, **kwargs)
    return wrapper


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def local_product_file(image_value):
    """Return filesystem path if the product image is a locally uploaded file."""
    if image_value and image_value.startswith("/product-image/"):
        name = image_value.rsplit("/", 1)[-1]
        if name and os.path.basename(name) == name:
            return os.path.join(PRODUCT_IMAGE_DIR, name)
    return None


def file_ext(name):
    return (os.path.splitext(name or "")[1] or "").lstrip(".").upper()[:4] or "FILE"


# ---------------------------------------------------------------------------
# Design system — Crypto-Exchange meets Next-Gen Logistics
# Deep space black, glass cargo widgets, Binance gold. GPU-first:
# only transform/opacity are ever animated. No box-shadow/backdrop
# transitions anywhere. translateZ(0) forces hardware layers.
# ---------------------------------------------------------------------------
CSS = """
:root{
  --bg0:#090B0E; --bg1:#0D1117; --bg2:#181C24;
  --gold:#FCD535; --gold2:#D4AF37;
  --gold-soft:rgba(252,213,53,.08); --gold-border:rgba(252,213,53,.18);
  --text:#F4F6F8; --muted:#9AA3B2;
  --green:#2EBD85; --red:#F6465D;
  --card:rgba(255,255,255,0.03);
  --stroke:rgba(255,255,255,0.05);
  --radius:18px;
  --glow:0 0 0 1px var(--gold-border), 0 12px 44px rgba(252,213,53,.16);
  --font:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
  --disp:'Space Grotesk','Inter',-apple-system,'Segoe UI',Roboto,Arial,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg0);color:var(--text);font-family:var(--font);min-height:100vh;overflow-x:hidden;
  background-image:radial-gradient(1000px 520px at 10% -6%,rgba(252,213,53,.07),transparent 60%),
  radial-gradient(900px 560px at 90% 6%,rgba(212,175,55,.05),transparent 60%),
  radial-gradient(760px 640px at 50% 112%,rgba(252,213,53,.04),transparent 60%);}
a{color:inherit;text-decoration:none}
img{display:block;max-width:100%}
.mono{font-family:var(--mono)}
.wrap{max-width:1220px;margin:0 auto;padding:0 22px;position:relative;z-index:1}
/* ---------- SVG icon system (gold via currentColor) ---------- */
.svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
.btn .svg{width:17px;height:17px}
.tab-btn .svg{width:15px;height:15px;vertical-align:-2px;margin-right:6px}
.nav-cta .svg{width:16px;height:16px}
.hc-ico .svg,.ccard .ico .svg,.fico .svg.img{width:24px;height:24px}
.hc-ico,.ccard .ico{color:var(--gold)}
.searchbar .svg{width:17px;height:17px;color:var(--muted)}
.lock .svg{width:32px;height:32px;stroke:#090B0E;stroke-width:2}
.pw-wrap .svg{width:18px;height:18px}
.wa-float .svg{width:26px;height:26px}
.toast .t-ico .svg{width:20px;height:20px}
.toast.success .t-ico{color:var(--green)} .toast.error .t-ico{color:var(--red)} .toast.info .t-ico{color:var(--gold)}
/* ---------- Top nav ---------- */
.navbar{position:sticky;top:0;z-index:50;backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);
  background:rgba(9,11,14,.8);border-bottom:1px solid var(--stroke)}
.nav-inner{max-width:1220px;margin:0 auto;padding:13px 22px;display:flex;align-items:center;gap:14px}
.brand{display:flex;align-items:center;gap:12px;margin-right:auto}
.brand-mark{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;
  font-family:var(--disp);font-weight:700;font-size:20px;color:#090B0E;
  background:linear-gradient(135deg,var(--gold),var(--gold2))}
.brand-name{font-family:var(--disp);font-weight:700;letter-spacing:.05em;font-size:15px;line-height:1.15}
.brand-name small{display:block;font-family:var(--mono);font-weight:500;color:var(--muted);letter-spacing:.18em;font-size:9.5px}
.tabs{display:flex;gap:6px;background:rgba(255,255,255,0.03);border:1px solid var(--stroke);border-radius:999px;padding:5px}
.tab-btn{border:0;cursor:pointer;background:transparent;color:var(--muted);font-family:var(--font);
  font-weight:700;font-size:13px;padding:10px 18px;border-radius:999px;white-space:nowrap;
  transition:transform .25s ease,color .25s ease,background-color .25s ease}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{background:linear-gradient(135deg,var(--gold),var(--gold2));color:#090B0E}
.tab-btn.active .svg{stroke:#090B0E}
.nav-cta{display:flex;align-items:center;gap:9px;background:var(--gold-soft);border:1px solid var(--gold-border);
  color:var(--gold);font-weight:700;font-size:13px;padding:10px 15px;border-radius:11px;white-space:nowrap;
  transition:transform .25s ease}
.nav-cta:hover{transform:translateY(-2px)}
/* ---------- Buttons (transform-only motion) ---------- */
.btn{border:0;cursor:pointer;font-family:var(--font);font-weight:800;border-radius:13px;
  display:inline-flex;align-items:center;justify-content:center;gap:10px;
  transition:transform .25s ease,opacity .25s ease;transform:translateZ(0)}
.btn[disabled]{opacity:.55;pointer-events:none}
.btn-gold{background:linear-gradient(135deg,var(--gold),var(--gold2));color:#090B0E;padding:14px 22px;font-size:14px}
.btn-gold .svg{stroke:#090B0E}
.btn-gold:hover{transform:translateY(-3px)}
.btn-ghost{background:rgba(255,255,255,0.03);color:var(--text);border:1px solid var(--stroke);padding:13px 20px;font-size:14px}
.btn-ghost:hover{transform:translateY(-2px)}
.btn-danger{background:rgba(246,70,93,.1);border:1px solid rgba(246,70,93,.32);color:#ff8fa0;padding:10px 16px;font-size:13px}
.btn-danger:hover{transform:translateY(-2px)}
.btn-danger:hover .svg{stroke:#fff}
.btn-sm{padding:9px 14px;font-size:12.5px;border-radius:10px}
/* ---------- Cargo widgets (glass manifests, glow via opacity layer) ---------- */
.gcard{position:relative;background:var(--card);border:1px solid var(--stroke);border-radius:var(--radius);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  transform:translateZ(0);transition:transform .3s ease}
.gcard::after{content:'';position:absolute;inset:0;border-radius:inherit;box-shadow:var(--glow);
  opacity:0;transition:opacity .35s ease;pointer-events:none}
.lift:hover{transform:translateY(-5px)}
.lift:hover::after{opacity:1}
/* ---------- Hero ---------- */
.hero{padding:60px 0 26px;position:relative}
.hero-grid{display:grid;grid-template-columns:1.12fr .88fr;gap:34px;align-items:center}
.badge{display:inline-flex;align-items:center;gap:9px;font-size:11.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:var(--gold);background:var(--gold-soft);border:1px solid var(--gold-border);padding:9px 16px;border-radius:999px}
.badge .dot{width:8px;height:8px;border-radius:50%;background:var(--gold);animation:pulse 1.8s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.hero h1{font-family:var(--disp);font-size:clamp(38px,6vw,64px);font-weight:700;letter-spacing:-.02em;line-height:1.02;margin:22px 0 16px}
.hero h1 .gold{background:linear-gradient(120deg,#fff6c9,var(--gold) 45%,var(--gold2));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p.lead{color:var(--muted);font-size:16px;line-height:1.75;max-width:560px}
.hero p.lead b{color:var(--text)}
.hero p.lead b.g{color:var(--gold)}
.hero-actions{display:flex;gap:12px;margin-top:26px;flex-wrap:wrap}
/* Live stats bar */
.livebar{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:28px}
.lstat{background:var(--card);border:1px solid var(--stroke);border-radius:14px;padding:14px 16px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0)}
.lstat b{font-family:var(--mono);font-size:20px;display:block;color:var(--gold)}
.lstat span{color:var(--muted);font-size:11.5px;font-weight:600}
/* 3D container stage (pure CSS, transform-only) */
.stage{position:relative;padding:26px 10px 8px;perspective:1200px}
.float-wrap{animation:hover 6s ease-in-out infinite;will-change:transform}
@keyframes hover{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
.box3d{position:relative;width:280px;height:140px;margin:34px auto 0;transform-style:preserve-3d;transform:rotateX(-18deg) rotateY(28deg)}
.face{position:absolute;border:1px solid rgba(252,213,53,.4);overflow:hidden}
.face.front{left:0;top:0;width:280px;height:140px;transform:translateZ(75px);
  background:linear-gradient(135deg,#2a2210,#141007 60%,#0d0b06);}
.face.front::before{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent 0 16px,rgba(252,213,53,.13) 16px 19px)}
.face.back{left:0;top:0;width:280px;height:140px;transform:rotateY(180deg) translateZ(75px);background:#12100a}
.face.side{width:150px;height:140px;left:65px;top:0;background:linear-gradient(180deg,#241e0e,#100d06)}
.face.side.r{transform:rotateY(90deg) translateZ(140px)}
.face.side.l{transform:rotateY(-90deg) translateZ(140px)}
.face.top{width:280px;height:150px;left:0;top:-5px;transform:rotateX(90deg) translateZ(70px);background:#1c170b}
.face.bottom{width:280px;height:150px;left:0;top:-5px;transform:rotateX(-90deg) translateZ(70px);background:#0a0906}
.face .brand{position:absolute;left:18px;top:22px;font-family:var(--disp);font-weight:700;font-size:26px;letter-spacing:.04em;color:var(--gold)}
.face .sub{position:absolute;left:18px;top:56px;font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:#e8dfc0}
.face .spec{position:absolute;left:18px;bottom:16px;font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:#8f8468}
.face .stripe{position:absolute;left:0;right:0;bottom:0;height:10px;background:linear-gradient(90deg,var(--gold),var(--gold2))}
.ground{width:280px;height:44px;margin:6px auto 0;border-radius:50%;
  background:radial-gradient(closest-side,rgba(252,213,53,.28),transparent);animation:shade 6s ease-in-out infinite}
@keyframes shade{0%,100%{opacity:.8;transform:scaleX(1)}50%{opacity:.45;transform:scaleX(.86)}}
.node{position:absolute;width:10px;height:10px;border-radius:50%;background:var(--gold);animation:pulse 2.2s ease-in-out infinite;will-change:transform,opacity}
.node.n1{top:6%;left:8%} .node.n2{top:22%;right:6%;animation-delay:.7s} .node.n3{bottom:14%;left:14%;animation-delay:1.2s}
.packet{position:absolute;top:0;left:0;width:12px;height:12px;border-radius:50%;background:var(--gold);
  offset-path:path('M 20 130 C 120 40, 260 200, 420 60');animation:travel 7s linear infinite;will-change:offset-distance}
@keyframes travel{from{offset-distance:0%}to{offset-distance:100%}}
.route{position:absolute;inset:0;pointer-events:none;opacity:.5}
/* ---------- Sections ---------- */
.section{display:none}
.section.active{display:block;animation:fadeUp .4s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.sec-head{display:flex;align-items:end;justify-content:space-between;gap:14px;margin:32px 0 18px;flex-wrap:wrap}
.sec-head h2{font-family:var(--disp);font-size:clamp(23px,3.2vw,32px);font-weight:700;letter-spacing:-.01em}
.sec-head h2 span{color:var(--gold)}
.sec-head p{color:var(--muted);font-size:13.5px;margin-top:6px;max-width:560px;line-height:1.6}
.searchbar{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,0.03);border:1px solid var(--stroke);
  border-radius:13px;padding:12px 16px;min-width:min(340px,100%)}
.searchbar input{flex:1;background:transparent;border:0;outline:0;color:var(--text);font-family:var(--mono);font-size:13.5px}
/* ---------- Cargo catalog ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(258px,1fr));gap:18px;padding-bottom:8px}
.pcard{overflow:hidden}
.pcard .pimg{height:198px;overflow:hidden;position:relative;background:#101318}
.pcard .pimg img{width:100%;height:100%;object-fit:cover;transition:transform .5s ease;transform:translateZ(0)}
.pcard:hover .pimg img{transform:scale(1.06)}
.ptag{position:absolute;top:12px;left:12px;z-index:2;font-family:var(--mono);font-size:10.5px;font-weight:700;letter-spacing:.08em;
  background:rgba(9,11,14,.75);border:1px solid var(--gold-border);color:var(--gold);padding:6px 11px;border-radius:999px}
.pbody{padding:18px}
.sku{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--gold)}
.pbody h3{font-size:16px;font-weight:700;line-height:1.4;margin:8px 0;min-height:44px}
.pbody .meta{font-family:var(--mono);color:var(--muted);font-size:11.5px;margin:0 0 14px;display:flex;align-items:center;gap:8px}
.pbody .meta .ok{width:7px;height:7px;border-radius:50%;background:var(--green);display:inline-block}
.wa-btn{width:100%;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#090B0E;padding:13px;font-size:13.5px}
.wa-btn:hover{transform:translateY(-2px)}
.empty{background:var(--card);border:1px dashed var(--gold-border);border-radius:16px;padding:42px 24px;text-align:center;color:var(--muted)}
/* ---------- Tracking + cargo ops ---------- */
.track{display:grid;grid-template-columns:1.35fr .85fr;gap:16px}
.track-main{background:var(--card);border:1px solid var(--stroke);border-radius:var(--radius);padding:24px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0)}
.track-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.track-top small{color:var(--muted);font-size:10.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.track-top b{font-family:var(--mono);font-size:25px;letter-spacing:.02em}
.status{background:rgba(46,189,133,.14);color:var(--green);font-weight:800;font-size:12px;padding:8px 16px;border-radius:999px;
  display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(46,189,133,.3)}
.status::before{content:'';width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.8s ease-in-out infinite}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:20px 0 14px}
.step{display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--muted);font-size:12px;font-weight:700}
.step i{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;font-style:normal;font-family:var(--mono);font-weight:700;
  background:rgba(255,255,255,0.03);border:1px solid var(--stroke);color:var(--muted)}
.step.done{color:var(--gold)}
.step.done i{background:var(--gold);border-color:var(--gold);color:#090B0E}
.step.active{color:var(--text)}
.step.active i{background:transparent;border-color:var(--gold);color:var(--gold);animation:pulse 1.8s ease-in-out infinite}
.tbar{position:relative;height:10px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden}
.tbar i{position:relative;display:block;height:100%;width:68%;border-radius:99px;background:linear-gradient(90deg,var(--gold2),var(--gold));overflow:hidden}
.tbar i::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(9,11,14,.45),transparent);
  transform:translateX(-100%);animation:shine 2.4s linear infinite;will-change:transform}
@keyframes shine{to{transform:translateX(100%)}}
.track-route{display:flex;align-items:center;gap:10px;margin-top:14px;font-size:13px;font-weight:700}
.track-route .arr{color:var(--gold)}
.track-side{display:grid;gap:16px;grid-template-rows:repeat(3,1fr)}
.tstat{background:var(--card);border:1px solid var(--stroke);border-radius:var(--radius);padding:20px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0)}
.tstat b{font-family:var(--mono);font-size:27px;display:block;color:var(--gold)}
.tstat span{color:var(--muted);font-size:12.5px;font-weight:600}
.dash-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:14px}
.dstat{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--stroke);
  border-radius:15px;padding:15px 16px;transform:translateZ(0)}
.dstat .ico{width:44px;height:44px;flex:0 0 44px;border-radius:12px;display:grid;place-items:center;color:var(--gold);
  background:var(--gold-soft);border:1px solid var(--gold-border)}
.dstat .ico .svg{width:22px;height:22px}
.dstat b{font-family:var(--mono);font-size:21px;display:block;line-height:1.1}
.dstat span{font-size:12px;color:var(--muted);font-weight:600}
.uld-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(128px,1fr));gap:10px;margin-bottom:16px}
.uld{cursor:pointer;font-family:var(--font);text-align:left;background:var(--card);color:var(--text);
  border:1px solid var(--stroke);border-radius:14px;padding:12px 14px;transform:translateZ(0);
  transition:transform .25s ease,background-color .25s ease,border-color .25s ease}
.uld small{color:var(--muted);font-family:var(--mono);font-size:10.5px;font-weight:700}
.uld span{display:block;font-family:var(--mono);font-size:11px;color:var(--muted);font-weight:700;margin:4px 0}
.uld b{font-family:var(--mono);font-size:15px}
.uld:hover{transform:translateY(-3px)}
.uld.active{background:rgba(252,213,53,.1);border-color:var(--gold)}
.uld.active small,.uld.active span{color:var(--gold)}
.dash-detail{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}
.dd-card{background:var(--card);border:1px solid var(--stroke);border-radius:var(--radius);padding:24px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0)}
.dd-top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
.dd-top small{color:var(--muted);font-size:10.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.dd-top b{font-family:var(--mono);font-size:23px}
.kv{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px dashed rgba(255,255,255,.09);font-size:13.5px}
.kv span{color:var(--muted);font-weight:600}
.kv b{font-family:var(--mono)}
.dist{margin-bottom:14px}
.dist:last-child{margin-bottom:0}
.dist-top{display:flex;justify-content:space-between;font-family:var(--mono);font-size:12px;font-weight:700;margin-bottom:6px}
.dist-top span{color:var(--muted);font-weight:500}
.dbar{height:28px;border-radius:8px;background:rgba(255,255,255,.06);overflow:hidden}
.dbar i{display:block;height:100%;background-color:rgba(252,213,53,.14);
  background-image:radial-gradient(circle,rgba(252,213,53,.85) 1.6px,transparent 1.8px);background-size:9px 9px}
/* ---------- Partners marquee (transform-only loop) ---------- */
.marquee{overflow:hidden;position:relative;border:1px solid var(--stroke);border-radius:20px;background:rgba(255,255,255,0.02)}
.mtrack{display:flex;width:max-content;animation:mscroll 32s linear infinite;will-change:transform}
@keyframes mscroll{to{transform:translateX(-50%)}}
.partner{flex:0 0 auto;display:flex;align-items:center;gap:14px;min-width:272px;margin:18px 8px;
  background:var(--card);border:1px solid var(--stroke);border-radius:16px;padding:16px 20px;transform:translateZ(0)}
.partner b{font-size:15.5px;display:block}
.partner .ptxt{min-width:0}
.partner .psub{font-size:12px;color:var(--muted);font-weight:600;display:block}
.plogo{width:66px;height:52px;flex:0 0 66px;border-radius:12px;background:#fff;display:flex;align-items:center;justify-content:center;
  overflow:hidden;padding:6px}
.plogo img{max-width:100%;max-height:100%;object-fit:contain;display:block}
.plogo .mono{display:none;width:100%;height:100%;border-radius:8px;font-family:var(--disp);font-weight:700;font-size:16px;
  align-items:center;justify-content:center;color:#090B0E;background:linear-gradient(135deg,var(--gold),var(--gold2))}
.plogo.noimg{background:linear-gradient(135deg,var(--gold),var(--gold2));padding:0}
.plogo.noimg .mono{display:grid}
.plogo.dark{padding:0;background:#0a1e4a}
.plogo.dark img{width:100%;height:100%;object-fit:cover}
/* ---------- Contact ---------- */
.cgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:8px}
.ccard{background:var(--card);border:1px solid var(--stroke);border-radius:16px;padding:24px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0);transition:transform .3s ease;position:relative}
.ccard .ico{width:52px;height:52px;border-radius:14px;display:grid;place-items:center;margin-bottom:14px;
  background:var(--gold-soft);border:1px solid var(--gold-border)}
.ccard small{color:var(--muted);font-weight:700;font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.ccard strong{display:block;margin:8px 0 6px;font-size:15.5px;line-height:1.5;word-break:break-word}
.ccard a.link{color:var(--gold);font-weight:700;font-size:13.5px}
/* ---------- Footer / floating ---------- */
footer{margin-top:54px;border-top:1px solid var(--stroke);background:rgba(9,11,14,.75);position:relative;z-index:1}
.foot{max-width:1220px;margin:0 auto;padding:24px 22px;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;color:var(--muted);font-size:13px}
.foot b{color:var(--gold)}
.wa-float{position:fixed;right:20px;bottom:20px;z-index:60;width:58px;height:58px;border-radius:50%;display:grid;place-items:center;
  background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;transition:transform .25s ease;transform:translateZ(0)}
.wa-float:hover{transform:translateY(-4px)}
/* ---------- Toast ---------- */
#toasts{position:fixed;top:18px;right:18px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:min(360px,calc(100vw - 36px))}
.toast{background:rgba(16,19,24,.94);border:1px solid var(--stroke);border-left:4px solid var(--gold);border-radius:13px;
  padding:14px 16px;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);display:flex;gap:12px;align-items:flex-start;
  animation:slideIn .35s ease}
.toast.success{border-left-color:var(--green)} .toast.error{border-left-color:var(--red)}
.toast b{font-size:13.5px;display:block} .toast span{font-size:12.5px;color:var(--muted);line-height:1.5}
.toast .t-ico{margin-top:1px}
.toast.out{animation:slideOut .3s ease forwards}
@keyframes slideIn{from{opacity:0;transform:translateX(60px)}to{opacity:1;transform:none}}
@keyframes slideOut{to{opacity:0;transform:translateX(60px)}}
/* ---------- Modal ---------- */
.overlay{position:fixed;inset:0;z-index:9000;background:rgba(4,6,8,.72);display:none;align-items:center;justify-content:center;padding:20px}
.overlay.open{display:flex;animation:fadeUp .25s ease}
.modal{width:min(520px,100%);background:linear-gradient(180deg,#141821,#0c0e12);border:1px solid var(--gold-border);
  border-radius:20px;padding:28px;position:relative;max-height:90vh;overflow:auto;transform:translateZ(0)}
.modal h3{font-family:var(--disp);font-size:20px;font-weight:700}
.modal p.sub{color:var(--muted);font-size:13px;margin:6px 0 18px;line-height:1.6}
.modal .x{position:absolute;top:16px;right:16px;width:34px;height:34px;border-radius:10px;border:1px solid var(--stroke);
  background:rgba(255,255,255,0.03);color:var(--muted);cursor:pointer;display:grid;place-items:center}
.modal .x .svg{width:15px;height:15px}
.field{margin-bottom:14px}
.field label{display:block;font-size:11.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.field input[type=text]{width:100%;background:rgba(9,11,14,.7);border:1px solid var(--stroke);border-radius:11px;color:var(--text);
  padding:13px 14px;font-family:var(--font);font-size:14px;outline:0}
.img-preview{min-height:170px;border-radius:13px;border:1px dashed var(--gold-border);overflow:hidden;background:#0d1013;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:var(--muted);font-size:13px;margin-bottom:14px;padding:18px;text-align:center}
.img-preview img{width:100%;height:200px;object-fit:cover;border-radius:9px}
.img-preview .fname{font-family:var(--mono);font-size:12px;color:var(--gold);font-weight:700;word-break:break-all}
.file-drop{display:flex;align-items:center;gap:14px;border:1px dashed rgba(252,213,53,.4);border-radius:13px;
  background:rgba(252,213,53,.04);padding:18px;cursor:pointer;transition:transform .25s ease}
.file-drop:hover{transform:translateY(-2px)}
.file-drop .svg{width:26px;height:26px;color:var(--gold)}
.file-drop .fd-txt b{display:block;font-size:14px}
.file-drop .fd-txt span{font-size:12px;color:var(--muted)}
.confirm-actions{display:flex;gap:10px;margin-top:20px}
.confirm-actions .btn{flex:1;padding:13px}
/* ---------- Admin control tower ---------- */
.admin-top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:26px 0 6px}
.pill{display:inline-flex;align-items:center;gap:8px;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);
  background:var(--gold-soft);border:1px solid var(--gold-border);padding:7px 13px;border-radius:999px}
.pill .svg{width:13px;height:13px}
.pill .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.6s ease-in-out infinite}
.radar{width:44px;height:44px;border-radius:50%;position:relative;flex:0 0 44px;overflow:hidden;
  border:1px solid var(--gold-border);background:radial-gradient(circle,rgba(252,213,53,.12),rgba(252,213,53,.02))}
.radar::before{content:'';position:absolute;inset:0;border-radius:50%;
  background:conic-gradient(from 0deg,rgba(252,213,53,.9),transparent 26%);animation:sweep 2.6s linear infinite;will-change:transform}
.radar::after{content:'';position:absolute;inset:16px;border-radius:50%;background:var(--gold)}
@keyframes sweep{to{transform:rotate(360deg)}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:var(--card);border:1px solid var(--stroke);border-radius:15px;padding:18px;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);transform:translateZ(0)}
.kpi .k-top{display:flex;align-items:center;gap:10px;color:var(--gold);margin-bottom:8px}
.kpi b{font-family:var(--mono);font-size:25px}
.kpi span.lbl{color:var(--muted);font-size:12.5px;font-weight:600}
.dropzone{border:1px dashed rgba(252,213,53,.4);border-radius:18px;background:rgba(252,213,53,.04);
  padding:36px 22px;text-align:center;cursor:pointer;margin-top:14px;display:flex;flex-direction:column;align-items:center;gap:6px;
  transform:translateZ(0);transition:transform .25s ease}
.dropzone:hover{transform:translateY(-2px)}
.dropzone .svg.big{width:50px;height:50px;color:var(--gold)}
.dropzone h4{margin:10px 0 4px;font-size:16px} .dropzone p{color:var(--muted);font-size:13px}
.progress{height:8px;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden;margin-top:14px;display:none;width:100%}
.progress i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--gold),var(--gold2))}
.file-list{display:flex;flex-direction:column;gap:10px;margin-top:16px}
.frow{display:flex;align-items:center;gap:14px;background:var(--card);border:1px solid var(--stroke);border-radius:14px;
  padding:14px 16px;transform:translateZ(0);transition:transform .25s ease}
.frow:hover{transform:translateY(-2px)}
.fico{width:52px;flex:0 0 52px;border-radius:11px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px 4px;
  background:var(--gold-soft);border:1px solid var(--gold-border);color:var(--gold)}
.fico .svg.img{width:22px;height:22px}
.fext{font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.06em;color:var(--gold);margin-top:2px}
.frow .meta{flex:1;min-width:0} .frow .meta b{font-size:14px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.frow .meta span{font-family:var(--mono);color:var(--muted);font-size:12px}
.factions{display:flex;gap:8px;flex-shrink:0}
.login-wrap{min-height:100vh;display:grid;place-items:center;padding:24px;position:relative;z-index:1}
.login-card{width:min(430px,100%);background:linear-gradient(180deg,rgba(24,28,36,.94),rgba(12,14,18,.95));
  border:1px solid var(--gold-border);border-radius:24px;padding:38px 34px;text-align:center;
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);transform:translateZ(0)}
.lock{width:70px;height:70px;margin:0 auto 16px;border-radius:19px;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--gold),var(--gold2))}
.pw-wrap{position:relative}
.pw-wrap input{width:100%;background:rgba(9,11,14,.7);border:1px solid var(--stroke);border-radius:11px;color:var(--text);
  padding:13px 44px 13px 14px;font-family:var(--mono);font-size:14px;outline:0}
.pw-wrap button{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:0;cursor:pointer;color:var(--muted);
  width:32px;height:32px;display:grid;place-items:center;border-radius:8px}
.reveal{opacity:0;transform:translateY(22px);transition:opacity .55s ease,transform .55s ease;will-change:transform,opacity}
.reveal.vis{opacity:1;transform:none}
@media(max-width:920px){.hero-grid{grid-template-columns:1fr}.track{grid-template-columns:1fr}.track-side{grid-template-columns:repeat(3,1fr)}
  .dash-detail{grid-template-columns:1fr}.nav-inner{flex-wrap:wrap}.tabs{order:3;width:100%;overflow-x:auto}.tab-btn{flex:1}}
@media(max-width:560px){.hero{padding-top:38px}.livebar{grid-template-columns:1fr 1fr}.steps{grid-template-columns:repeat(2,1fr)}
  .track-side{grid-template-columns:1fr}.factions{flex-wrap:wrap}.nav-cta span.t{display:none}.box3d{transform:rotateX(-18deg) rotateY(28deg) scale(.82)}}
@media (prefers-reduced-motion: reduce){.float-wrap,.ground,.node,.packet,.radar::before,.mtrack,.tbar i::after,.status::before,.step.active i,.badge .dot,.pill .dot{animation:none !important}}
"""

# ---------------------------------------------------------------------------
# Inline SVG icon set (stroke style, gold via currentColor — zero emojis)
# ---------------------------------------------------------------------------
SVG_PHONE = '<svg class="svg" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
SVG_MAIL = '<svg class="svg" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/></svg>'
SVG_PIN = '<svg class="svg" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'
SVG_SEARCH = '<svg class="svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
SVG_CHECK = '<svg class="svg" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>'
SVG_TRUCK = '<svg class="svg" viewBox="0 0 24 24"><rect x="1" y="6" width="13" height="10" rx="1"/><path d="M14 9h4l4 4v3h-8z"/><circle cx="6" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/></svg>'
SVG_CHAT = '<svg class="svg" viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>'
SVG_BRIEFCASE = '<svg class="svg" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
SVG_BOLT = '<svg class="svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
SVG_GEM = '<svg class="svg" viewBox="0 0 24 24"><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M2 9h20M9 3l3 6 3-6M12 15l0 7"/></svg>'
SVG_SHIELD = '<svg class="svg" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>'
SVG_CLOCK = '<svg class="svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
SVG_BOX = '<svg class="svg" viewBox="0 0 24 24"><path d="M16.5 9.4 7.5 4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>'
SVG_FOLDER = '<svg class="svg" viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>'
SVG_GLOBE = '<svg class="svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
SVG_LOGOUT = '<svg class="svg" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
SVG_LOCK = '<svg class="svg" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
SVG_EYE = '<svg class="svg" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
SVG_UPLOAD = '<svg class="svg big" viewBox="0 0 24 24"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>'
SVG_DOWNLOAD = '<svg class="svg" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
SVG_TRASH = '<svg class="svg" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>'
SVG_IMAGE = '<svg class="svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'
SVG_DOC = '<svg class="svg img" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
SVG_PLUS = '<svg class="svg" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
SVG_ARROW = '<svg class="svg" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>'
SVG_X = '<svg class="svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
SVG_DB = '<svg class="svg" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
SVG_SEND = '<svg class="svg" viewBox="0 0 24 24"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/></svg>'

JS_ICONS = """const ICONS={
success:'<svg class="svg" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
error:'<svg class="svg" viewBox="0 0 24 24"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
info:'<svg class="svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'};
function toastIcon(t){return '<div class="t-ico">'+(ICONS[t]||ICONS.info)+'</div>';}
function showToast(title,msg,type){
  type=type||'info';
  const box=document.getElementById('toasts');
  const t=document.createElement('div'); t.className='toast '+type;
  t.innerHTML=toastIcon(type)+'<div><b></b><span></span></div>';
  t.querySelector('b').textContent=title||'Bildiriş'; t.querySelector('span').textContent=msg||'';
  box.appendChild(t);
  setTimeout(()=>{t.classList.add('out');setTimeout(()=>t.remove(),320);},3600);
}
function askConfirm(title,msg,okLabel){
  return new Promise(resolve=>{
    const ov=document.getElementById('confirmOverlay');
    document.getElementById('confirmTitle').textContent=title||'Əminsiniz?';
    document.getElementById('confirmMsg').textContent=msg||'Bu əməliyyat geri alına bilməz.';
    document.getElementById('confirmOk').textContent=okLabel||'Bəli, təsdiqlə';
    ov.classList.add('open');
    const ok=document.getElementById('confirmOk'), no=document.getElementById('confirmNo');
    const done=v=>{ov.classList.remove('open');ok.onclick=no.onclick=null;ov.onclick=null;resolve(v);};
    ok.onclick=()=>done(true); no.onclick=()=>done(false);
    ov.onclick=e=>{if(e.target===ov)done(false);};
  });
}"""

CONFIRM_MODAL_HTML = """
<div class="overlay" id="confirmOverlay">
  <div class="modal" style="width:min(420px,100%)">
    <h3 id="confirmTitle">Əminsiniz?</h3>
    <p class="sub" id="confirmMsg">Bu əməliyyat geri alına bilməz.</p>
    <div class="confirm-actions">
      <button class="btn btn-ghost" id="confirmNo">Ləğv et</button>
      <button class="btn btn-danger" id="confirmOk">Bəli, təsdiqlə</button>
    </div>
  </div>
</div>"""

# ---------------------------------------------------------------------------
# PUBLIC TEMPLATE — Freight & Supply front
# ---------------------------------------------------------------------------
PUBLIC_PAGE = """<!DOCTYPE html>
<html lang="az">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MULTI PRO MMC — Freight &amp; Chemical Supply</title>
<meta name="description" content="MULTI PRO MMC — premium kimyəvi təchizat və logistika. Sumqayıt, Azərbaycan.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
<!-- internal route: /admin-panel (hidden, session protected) -->
</head>
<body>
<div id="toasts"></div>

<header class="navbar">
  <div class="nav-inner">
    <div class="brand">
      <div class="brand-mark">M</div>
      <div class="brand-name">MULTI PRO MMC<small>FREIGHT &amp; SUPPLY</small></div>
    </div>
    <nav class="tabs" role="tablist">
      <button class="tab-btn active" data-tab="about" onclick="switchTab('about',this)">Haqqımızda</button>
      <button class="tab-btn" data-tab="products" onclick="switchTab('products',this)">Məhsullarımız</button>
      <button class="tab-btn" data-tab="cargo" onclick="switchTab('cargo',this);initCargo()">Yük İzləmə</button>
      <button class="tab-btn" data-tab="contact" onclick="switchTab('contact',this)">Əlaqə</button>
    </nav>
    <a class="nav-cta" href="tel:{{ c.phone_href }}">""" + SVG_PHONE + """<span class="t">{{ c.phone_display }}</span></a>
  </div>
</header>

<main class="wrap">

  <!-- TAB 1 : ABOUT -->
  <section id="tab-about" class="section active">
    <div class="hero">
      <div class="hero-grid">
        <div>
          <span class="badge"><span class="dot"></span> Canlı • Freight Network</span>
          <h1>MULTI PRO <span class="gold">MMC</span></h1>
          <p class="lead">Xoş gəlmisiniz! <b>MULTI PRO MMC</b> — yüksək keyfiyyətli <b class="g">kimyəvi təchizat</b> və
          qlobal <b class="g">logistika</b> üzrə ixtisaslaşmış B2B/B2C tərəfdaşınızdır. Hər yük manifestlə,
          hər sifariş şəffaf izləmə ilə idarə olunur.</p>
          <div class="hero-actions">
            <button class="btn btn-gold" onclick="switchTab('products')">Kataloqa Bax """ + SVG_ARROW + """</button>
            <button class="btn btn-ghost" onclick="switchTab('cargo');initCargo()">""" + SVG_SEND + """ Yük İzlə</button>
          </div>
          <div class="livebar">
            <div class="lstat"><b data-count="100" data-suffix="%">0</b><span>Etibarlılıq</span></div>
            <div class="lstat"><b>24/7</b><span>Dispetçer</span></div>
            <div class="lstat"><b data-count="{{ products|length }}" data-suffix="+">0</b><span>Kataloq yükü</span></div>
            <div class="lstat"><b data-count="5" data-suffix="">0</b><span>Böyük tərəfdaş</span></div>
          </div>
        </div>
        <div class="stage" aria-hidden="true">
          <span class="node n1"></span><span class="node n2"></span><span class="node n3"></span>
          <svg class="route" viewBox="0 0 440 260" preserveAspectRatio="none">
            <path id="routepath" d="M 20 210 C 120 120, 260 220, 420 70" fill="none" stroke="rgba(252,213,53,.35)"
              stroke-width="1.5" stroke-dasharray="6 7"/>
          </svg>
          <span class="packet"></span>
          <div class="float-wrap">
            <div class="box3d">
              <div class="face back"></div>
              <div class="face side l"></div>
              <div class="face bottom"></div>
              <div class="face top"></div>
              <div class="face side r"></div>
              <div class="face front">
                <span class="brand">MULTI PRO</span>
                <span class="sub">FREIGHT • MMC-2480</span>
                <span class="spec">MAX GROSS 30480 KG</span>
                <span class="stripe"></span>
              </div>
            </div>
          </div>
          <div class="ground"></div>
        </div>
      </div>
    </div>

    <div class="sec-head reveal">
      <div><h2>Canlı <span>Daşınma Paneli</span></h2><p>Sifarişinizin hər mərhələsini şəffaf izləyin — hər yük nəzarətimizdədir.</p></div>
      <span class="pill"><span class="dot"></span> Sistem aktivdir</span>
    </div>
    <div class="track reveal">
      <div class="track-main gcard">
        <div class="track-top"><div><small>İzləmə kodu</small><b>{{ 'MP-%04d-AZ' % products|length }}</b></div><span class="status">Operational</span></div>
        <div class="steps">
          <div class="step done"><i>1</i><span>Qəbul</span></div>
          <div class="step done"><i>2</i><span>Hazırlıq</span></div>
          <div class="step active"><i>3</i><span>Yoldadır</span></div>
          <div class="step"><i>4</i><span>Təhvil</span></div>
        </div>
        <div class="tbar"><i></i></div>
        <div class="track-route"><span>Sumqayıt MK-21</span><span class="arr">→</span><span>Bakı terminalı</span></div>
      </div>
      <div class="track-side">
        <div class="tstat gcard"><b data-count="{{ products|length }}" data-suffix="">0</b><span>Kataloq məhsulu</span></div>
        <div class="tstat gcard"><b>24/7</b><span>WhatsApp dəstəyi</span></div>
        <div class="tstat gcard"><b data-count="100" data-suffix="%">0</b><span>Şəffaf izləmə</span></div>
      </div>
    </div>

    <div class="sec-head reveal">
      <div><h2>Niyə <span>MULTI PRO?</span></h2><p>Maliyyə səviyyəli dəqiqlik, aviasiya səviyyəli operativlik.</p></div>
    </div>
    <div class="cgrid">
      <div class="ccard lift gcard reveal"><div class="ico">""" + SVG_BOLT + """</div><small>Sürət</small><strong>WhatsApp ilə ani qiymət təklifi</strong><span style="color:var(--muted);font-size:13px">Orta cavab müddəti — bir neçə dəqiqə.</span></div>
      <div class="ccard lift gcard reveal"><div class="ico">""" + SVG_GEM + """</div><small>Keyfiyyət</small><strong>Seçilmiş, yoxlanılmış kimya</strong><span style="color:var(--muted);font-size:13px">Yalnız etibarlı mənbələrdən təchizat.</span></div>
      <div class="ccard lift gcard reveal"><div class="ico">""" + SVG_SHIELD + """</div><small>B2B Fokus</small><strong>Nəhəng qurumlarla əməkdaşlıq</strong><span style="color:var(--muted);font-size:13px">Həcm endirimləri və rəsmi sənədləşmə.</span></div>
    </div>

    <div class="sec-head reveal">
      <div><h2>Böyük <span>Tərəfdaşlarımız</span></h2><p>Azərbaycanın ən böyük dövlət və özəl qurumları ilə çalışırıq.</p></div>
    </div>
    <div class="marquee reveal">
      <div class="mtrack">
        <div class="partner"><span class="plogo"><img src="/partner-logo/socar.png" alt="SOCAR" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">S</span></span><span class="ptxt"><b>SOCAR</b><span class="psub">Dövlət Neft Şirkəti</span></span></div>
        <div class="partner"><span class="plogo"><img src="/partner-logo/azersu.png" alt="Azərsu" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AS</span></span><span class="ptxt"><b>Azərsu ASC</b><span class="psub">İçməli su təchizatı</span></span></div>
        <div class="partner"><span class="plogo dark"><img src="/partner-logo/azerenerji.png" alt="Azərenerji" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AE</span></span><span class="ptxt"><b>Azərenerji ASC</b><span class="psub">Elektroenergetika</span></span></div>
        <div class="partner"><span class="plogo"><img src="/partner-logo/azersun.svg" alt="Azərsun" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AP</span></span><span class="ptxt"><b>Azərsun Petrochem</b><span class="psub">Neft-kimya sənayesi</span></span></div>
        <div class="partner"><span class="plogo"><img src="/partner-logo/giltex.png" alt="Gilan Tekstil Park" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">G</span></span><span class="ptxt"><b>Gilan Tekstil Park</b><span class="psub">Tekstil sənayesi</span></span></div>
        <div class="partner" aria-hidden="true"><span class="plogo"><img src="/partner-logo/socar.png" alt="" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">S</span></span><span class="ptxt"><b>SOCAR</b><span class="psub">Dövlət Neft Şirkəti</span></span></div>
        <div class="partner" aria-hidden="true"><span class="plogo"><img src="/partner-logo/azersu.png" alt="" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AS</span></span><span class="ptxt"><b>Azərsu ASC</b><span class="psub">İçməli su təchizatı</span></span></div>
        <div class="partner" aria-hidden="true"><span class="plogo dark"><img src="/partner-logo/azerenerji.png" alt="" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AE</span></span><span class="ptxt"><b>Azərenerji ASC</b><span class="psub">Elektroenergetika</span></span></div>
        <div class="partner" aria-hidden="true"><span class="plogo"><img src="/partner-logo/azersun.svg" alt="" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">AP</span></span><span class="ptxt"><b>Azərsun Petrochem</b><span class="psub">Neft-kimya sənayesi</span></span></div>
        <div class="partner" aria-hidden="true"><span class="plogo"><img src="/partner-logo/giltex.png" alt="" loading="lazy" onerror="this.closest('.plogo').classList.add('noimg');this.remove();"><span class="mono">G</span></span><span class="ptxt"><b>Gilan Tekstil Park</b><span class="psub">Tekstil sənayesi</span></span></div>
      </div>
    </div>
  </section>

  <!-- TAB 2 : CARGO CATALOG -->
  <section id="tab-products" class="section">
    <div class="sec-head">
      <div><h2>Yük <span>Kataloqu</span></h2><p>Hər məhsul manifestlə qeydə alınır — qızılı düymə ilə WhatsApp-da qiymət alın.</p></div>
      <div class="searchbar">""" + SVG_SEARCH + """<input id="search" placeholder="SKU / ad ilə axtar..." oninput="filterProducts()"></div>
    </div>
    <div class="grid" id="productGrid">
      {% for p in products %}
      <article class="pcard gcard lift reveal" data-name="{{ p['name']|e|lower }} {{ 'sku-%04d' % (8400 + p['id']) }}">
        <div class="pimg">
          <span class="ptag">{{ 'SKU-%04d' % (8400 + p['id']) }}</span>
          <img src="{{ p['image_url']|e }}" alt="{{ p['name']|e }}" loading="lazy"
               onerror="this.onerror=null;this.src='https://picsum.photos/seed/mp{{ p['id'] }}/800/600';">
        </div>
        <div class="pbody">
          <div class="sku">{{ 'SKU-%04d' % (8400 + p['id']) }} • EXW</div>
          <h3>{{ p['name']|e }}</h3>
          <div class="meta"><span class="ok"></span> STOKDA • SÜRƏTLİ ÇATDIRILMA</div>
          <button class="btn wa-btn" data-product="{{ p['name']|e }}" onclick="askPrice(this)">""" + SVG_CHAT + """ WhatsApp'la Qiymət Al</button>
        </div>
      </article>
      {% else %}
      <div class="empty" style="grid-column:1/-1">Hələlik kataloq boşdur. Tezliklə yeni yüklər əlavə olunacaq.</div>
      {% endfor %}
    </div>
    <div class="empty" id="noResult" style="display:none;margin-top:16px">Axtarışa uyğun yük tapılmadı.</div>
  </section>

  <!-- TAB 3 : CARGO OPS -->
  <section id="tab-cargo" class="section">
    <div class="sec-head">
      <div><h2>Yük <span>İzləmə Paneli</span></h2><p>Konteyner seçin — çəki, yük tipi və marşrut dərhal yenilənir.</p></div>
      <span class="pill"><span class="dot"></span> Canlı əməliyyat</span>
    </div>
    <div class="dash-stats">
      <div class="dstat gcard"><div class="ico">""" + SVG_BOX + """</div><div><b data-count="{{ products|length }}">0</b><span>Aktiv yük</span></div></div>
      <div class="dstat gcard"><div class="ico">""" + SVG_TRUCK + """</div><div><b data-count="12">0</b><span>Yoldadır</span></div></div>
      <div class="dstat gcard"><div class="ico">""" + SVG_CHECK + """</div><div><b><span data-count="98">0</span>%</b><span>Təhvil nisbəti</span></div></div>
      <div class="dstat gcard"><div class="ico">""" + SVG_CLOCK + """</div><div><b data-count="0">0</b><span>Gecikmə</span></div></div>
    </div>
    <div class="uld-grid" id="uldGrid">
      <button class="uld" onclick="selectUld(0,this)"><small>01</small><span>MP-532-EK</span><b>375 kq</b></button>
      <button class="uld" onclick="selectUld(1,this)"><small>02</small><span>MP-389-BA</span><b>375 kq</b></button>
      <button class="uld active" onclick="selectUld(2,this)"><small>03</small><span>MP-248-CX</span><b>550 kq</b></button>
      <button class="uld" onclick="selectUld(3,this)"><small>04</small><span>MP-119-SQ</span><b>450 kq</b></button>
      <button class="uld" onclick="selectUld(4,this)"><small>05</small><span>MP-774-AF</span><b>375 kq</b></button>
      <button class="uld" onclick="selectUld(5,this)"><small>06</small><span>MP-905-QR</span><b>650 kq</b></button>
      <button class="uld" onclick="selectUld(6,this)"><small>07</small><span>MP-667-TK</span><b>375 kq</b></button>
      <button class="uld" onclick="selectUld(7,this)"><small>08</small><span>MP-573-KL</span><b>550 kq</b></button>
    </div>
    <div class="dash-detail">
      <div class="dd-card gcard">
        <div class="dd-top"><div><small>Konteyner</small><b id="uldCode">MP-248-CX</b></div><span class="status">Operational</span></div>
        <div class="kv"><span>Yük tipi</span><b id="uldType">Elektronika</b></div>
        <div class="kv"><span>Çəki</span><b id="uldW">550 kq</b></div>
        <div class="kv"><span>Temperatur</span><b id="uldTemp">+18°C</b></div>
        <div class="track-route"><span id="uldFrom">Sumqayıt</span><span class="arr">→</span><span id="uldTo">Bakı</span></div>
      </div>
      <div class="dd-card gcard">
        <div class="dd-top"><div><small>Yük paylanması</small><b>Bu gün</b></div></div>
        <div class="dist"><div class="dist-top"><span>Orta bağlamalar</span><b>50%</b></div><div class="dbar"><i style="width:50%"></i></div></div>
        <div class="dist"><div class="dist-top"><span>Kiçik bağlamalar</span><b>30%</b></div><div class="dbar"><i style="width:30%"></i></div></div>
        <div class="dist"><div class="dist-top"><span>Böyük bağlamalar</span><b>20%</b></div><div class="dbar"><i style="width:20%"></i></div></div>
      </div>
    </div>
  </section>

  <!-- TAB 4 : CONTACT -->
  <section id="tab-contact" class="section">
    <div class="sec-head">
      <div><h2>Əlaqə <span>✦</span></h2><p>Zəng edin, yazın və ya ofisimizə yaxınlaşın — dispetçerlərimiz 24/7 aktivdir.</p></div>
    </div>
    <div class="cgrid">
      <div class="ccard lift gcard"><div class="ico">""" + SVG_PHONE + """</div><small>Telefon / WhatsApp</small><strong>{{ c.phone_display }}</strong><a class="link" href="tel:{{ c.phone_href }}">Zəng et →</a> &nbsp;•&nbsp; <a class="link" href="https://wa.me/{{ c.phone_wa }}" target="_blank" rel="noopener">WhatsApp →</a></div>
      <div class="ccard lift gcard"><div class="ico">""" + SVG_MAIL + """</div><small>E-poçt</small><strong style="font-size:14px">{{ c.email }}</strong><a class="link" href="mailto:{{ c.email }}">Məktub yaz →</a></div>
      <div class="ccard lift gcard"><div class="ico">""" + SVG_PIN + """</div><small>Terminal / Ünvan</small><strong>{{ c.address }}</strong><a class="link" href="https://maps.google.com/?q=Sumqayit+21+MK" target="_blank" rel="noopener">Xəritədə bax →</a></div>
      <div class="ccard lift gcard"><div class="ico">""" + SVG_BRIEFCASE + """</div><small>Direktor</small><strong>{{ c.director }}</strong><span style="color:var(--muted);font-size:13px">MULTI PRO MMC rəhbərliyi</span></div>
      <div class="ccard lift gcard"><div class="ico">""" + SVG_CLOCK + """</div><small>Dispetçer</small><strong>B.e — Ş. 09:00 – 18:00</strong><span style="color:var(--muted);font-size:13px">WhatsApp 24/7 aktivdir.</span></div>
      <div class="ccard lift gcard" style="border-color:var(--gold-border)"><div class="ico">""" + SVG_CHAT + """</div><small>Sürətli təklif</small><strong>Qiyməti dərhal öyrənin</strong><br><button class="btn btn-gold btn-sm" onclick="switchTab('products')">Kataloqa keç """ + SVG_ARROW + """</button></div>
    </div>
  </section>

</main>

<footer>
  <div class="foot">
    <div>© 2026 <b>MULTI PRO MMC</b> — Direktor: {{ c.director }}. Bütün hüquqlar qorunur.</div>
    <div class="mono" style="font-size:12px">{{ c.phone_display }} • {{ c.email }}</div>
  </div>
</footer>

<a class="wa-float" href="https://wa.me/{{ c.phone_wa }}?text=Salam%2C%20MULTI%20PRO%20MMC!%20M%C9%99lumat%20almaq%20ist%C9%99yir%C9%99m." target="_blank" rel="noopener" title="WhatsApp">""" + SVG_CHAT + """</a>

<script>
const WA_NUMBER = "{{ c.phone_wa }}";
""" + JS_ICONS + """
function switchTab(name, btn){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  const el = document.getElementById('tab-'+name);
  if(el) el.classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  else document.querySelectorAll('.tab-btn').forEach(b=>{ if(b.dataset.tab===name) b.classList.add('active'); });
  observeReveals();
  window.scrollTo({top:0,behavior:'smooth'});
}
function askPrice(btn){
  const name = btn.getAttribute('data-product') || 'məhsul';
  const text = "Salam, " + name + " m\\u0259hsulu bar\\u0259d\\u0259 qiym\\u0259t v\\u0259 m\\u0259lumat almaq ist\\u0259yir\\u0259m.";
  const url = "https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(text);
  showToast('WhatsApp açılır', name + ' üzr\\u0259 sor\\u011funuz hazırlanır...', 'success');
  setTimeout(()=>window.open(url,'_blank'), 450);
}
function filterProducts(){
  const q = (document.getElementById('search').value||'').toLowerCase().trim();
  let visible = 0;
  document.querySelectorAll('#productGrid .pcard').forEach(card=>{
    const hit = (card.dataset.name||'').includes(q);
    card.style.display = hit ? '' : 'none';
    if(hit) visible++;
  });
  document.getElementById('noResult').style.display = visible ? 'none' : 'block';
}
/* Animated counters (mono logistics data) */
function countUp(el){
  const target = parseInt(el.getAttribute('data-count'),10)||0;
  const suffix = el.getAttribute('data-suffix')||'';
  const t0 = performance.now(), dur = 1300;
  function tick(t){
    const p = Math.min(1,(t-t0)/dur), e = 1-Math.pow(1-p,3);
    el.textContent = Math.round(target*e) + suffix;
    if(p<1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function initCounters(scope){
  (scope||document).querySelectorAll('[data-count]:not([data-done])').forEach(el=>{
    el.setAttribute('data-done','1'); countUp(el);
  });
}
/* Cargo ops dashboard */
const ULDS=[
 {code:'MP-532-EK',w:'375 kq',type:'Sənaye avadanlığı',temp:'+18°C',from:'Sumqayıt',to:'Bakı'},
 {code:'MP-389-BA',w:'375 kq',type:'Tikinti materialı',temp:'+20°C',from:'Sumqayıt',to:'Bakı'},
 {code:'MP-248-CX',w:'550 kq',type:'Elektronika',temp:'+18°C',from:'Sumqayıt',to:'Bakı'},
 {code:'MP-119-SQ',w:'450 kq',type:'Tekstil',temp:'+22°C',from:'Bakı',to:'Sumqayıt'},
 {code:'MP-774-AF',w:'375 kq',type:'Ehtiyat hissələri',temp:'+20°C',from:'Sumqayıt',to:'Bakı'},
 {code:'MP-905-QR',w:'650 kq',type:'Metal konstruksiya',temp:'+15°C',from:'Bakı',to:'Sumqayıt'},
 {code:'MP-667-TK',w:'375 kq',type:'Kabel məhsulları',temp:'+18°C',from:'Sumqayıt',to:'Bakı'},
 {code:'MP-573-KL',w:'550 kq',type:'Qablaşdırma',temp:'+22°C',from:'Bakı',to:'Sumqayıt'}
];
function selectUld(i,el){
  const u=ULDS[i]; if(!u) return;
  document.querySelectorAll('#uldGrid .uld').forEach(c=>c.classList.remove('active'));
  if(el) el.classList.add('active');
  document.getElementById('uldCode').textContent=u.code;
  document.getElementById('uldType').textContent=u.type;
  document.getElementById('uldW').textContent=u.w;
  document.getElementById('uldTemp').textContent=u.temp;
  document.getElementById('uldFrom').textContent=u.from;
  document.getElementById('uldTo').textContent=u.to;
}
function initCargo(){
  const tab=document.getElementById('tab-cargo');
  if(!tab || tab.dataset.done) return;
  tab.dataset.done='1';
  initCounters(tab);
}
/* Scroll reveal (transform + opacity only) */
let _obs = null;
function observeReveals(){
  const els = document.querySelectorAll('.reveal:not(.vis)');
  if(!('IntersectionObserver' in window)){ els.forEach(e=>e.classList.add('vis')); return; }
  if(_obs) _obs.disconnect();
  _obs = new IntersectionObserver(entries=>{
    entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('vis'); _obs.unobserve(e.target); } });
  },{threshold:.12});
  els.forEach(e=>_obs.observe(e));
}
document.addEventListener('DOMContentLoaded', function(){ observeReveals(); initCounters(document); });
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# ADMIN LOGIN TEMPLATE — Control tower gate
# ---------------------------------------------------------------------------
ADMIN_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="az">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Control Tower — MULTI PRO MMC</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
</head>
<body>
<div id="toasts"></div>
<div class="login-wrap">
  <div class="login-card gcard">
    <div class="lock">""" + SVG_LOCK + """</div>
    <span class="pill">Control Tower • Məxfi giriş</span>
    <h2 style="margin:14px 0 6px;font-size:26px;font-weight:700;font-family:var(--disp)">MULTI PRO <span style="color:var(--gold)">MMC</span></h2>
    <p style="color:var(--muted);font-size:13.5px;margin-bottom:22px">Davam etmək üçün operator şifrəsini daxil edin.</p>
    <form id="loginForm" onsubmit="return doLogin(event)">
      <div class="field" style="text-align:left">
        <label>Operator şifrəsi</label>
        <div class="pw-wrap">
          <input id="pw" type="password" placeholder="••••" autocomplete="current-password" required>
          <button type="button" onclick="togglePw()" title="Göstər/Gizlət">""" + SVG_EYE + """</button>
        </div>
      </div>
      <button class="btn btn-gold" id="loginBtn" style="width:100%;padding:14px">Bağlan """ + SVG_ARROW + """</button>
    </form>
    <a href="/" style="display:inline-block;margin-top:18px;color:var(--muted);font-size:13px;font-weight:600">← Sayta qayıt</a>
  </div>
</div>
<script>
""" + JS_ICONS + """
function togglePw(){ const i=document.getElementById('pw'); i.type = i.type==='password'?'text':'password'; }
async function doLogin(e){
  e.preventDefault();
  const pw=document.getElementById('pw').value;
  const btn=document.getElementById('loginBtn');
  btn.disabled=true; btn.textContent='Yoxlanılır…';
  try{
    const r=await fetch('/admin-panel/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
    const d=await r.json();
    if(d.ok){ showToast('Xoş gəldiniz','Uğurlu giriş. Panel yüklənir...','success'); setTimeout(()=>location.reload(),700); }
    else{ showToast('Giriş rədd edildi', d.error||'Şifrə yanlışdır.','error'); btn.disabled=false; btn.textContent='Bağlan'; }
  }catch(err){ showToast('Xəta','Serverə qoşulmaq mümkün olmadı.','error'); btn.disabled=false; btn.textContent='Bağlan'; }
  return false;
}
document.getElementById('pw').focus();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# ADMIN DASHBOARD TEMPLATE — Control Tower
# ---------------------------------------------------------------------------
ADMIN_DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="az">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Control Tower — MULTI PRO MMC</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
</head>
<body>
<div id="toasts"></div>

<header class="navbar">
  <div class="nav-inner">
    <div class="brand">
      <div class="brand-mark">M</div>
      <div class="brand-name">MULTI PRO MMC<small>CONTROL TOWER</small></div>
    </div>
    <nav class="tabs">
      <button class="tab-btn active" onclick="switchA('products',this)">""" + SVG_BOX + """Məhsul İdarəetməsi</button>
      <button class="tab-btn" onclick="switchA('tenders',this)">""" + SVG_FOLDER + """Tender Arxivi</button>
    </nav>
    <a class="btn btn-ghost btn-sm" href="/" target="_blank">""" + SVG_GLOBE + """ Sayta bax</a>
    <a class="btn btn-danger btn-sm" href="/admin-panel/logout">""" + SVG_LOGOUT + """ Çıxış</a>
  </div>
</header>

<main class="wrap">
  <div class="admin-top">
    <span class="radar" aria-hidden="true"></span>
    <span class="pill"><span class="dot"></span> Tower aktiv • {{ c.director }}</span>
    <span style="color:var(--muted);font-size:13px">Bütün dəyişikliklər dərhal saytda görünür.</span>
  </div>

  <div class="kpis">
    <div class="kpi gcard"><div class="k-top">""" + SVG_BOX + """</div><b>{{ products|length }}</b><br><span class="lbl">Ümumi məhsul</span></div>
    <div class="kpi gcard"><div class="k-top">""" + SVG_FOLDER + """</div><b>{{ files|length }}</b><br><span class="lbl">Tender sənədi</span></div>
    <div class="kpi gcard"><div class="k-top">""" + SVG_DB + """</div><b>{{ total_size }}</b><br><span class="lbl">Arxiv həcmi</span></div>
  </div>

  <!-- TAB: PRODUCTS -->
  <section id="atab-products" class="section active">
    <div class="sec-head">
      <div><h2>Yük <span>Manifestləri</span></h2><p>Şəkli birbaşa cihazınızdan yükləyin — manifest dərhal kataloqa düşür.</p></div>
      <button class="btn btn-gold" onclick="openModal()">""" + SVG_PLUS + """ Yeni Məhsul</button>
    </div>
    <div class="grid" id="adminGrid">
      {% for p in products %}
      <article class="pcard gcard" id="prod-{{ p['id'] }}">
        <div class="pimg">
          <span class="ptag">{{ 'SKU-%04d' % (8400 + p['id']) }}</span>
          <img src="{{ p['image_url']|e }}" alt="{{ p['name']|e }}" loading="lazy"
               onerror="this.onerror=null;this.src='https://picsum.photos/seed/mp{{ p['id'] }}/800/600';">
        </div>
        <div class="pbody">
          <div class="sku">{{ 'SKU-%04d' % (8400 + p['id']) }} • EXW</div>
          <h3>{{ p['name']|e }}</h3>
          <div class="meta"><span class="ok"></span> KATALOQDA AKTİVDİR</div>
          <button class="btn btn-danger" style="width:100%" onclick="deleteProduct({{ p['id'] }}, this)">""" + SVG_TRASH + """ Sil</button>
        </div>
      </article>
      {% else %}
      <div class="empty" id="adminEmpty" style="grid-column:1/-1">Manifest yoxdur — ilk yükü əlavə edin.</div>
      {% endfor %}
    </div>
  </section>

  <!-- TAB: TENDERS -->
  <section id="atab-tenders" class="section">
    <div class="sec-head">
      <div><h2>Tender <span>Arxivi</span></h2><p>Təhlükəsiz korporativ məlumat anbarı — ictimai saytda <b>görünmür</b>.</p></div>
    </div>
    <div class="dropzone lift" id="dz" onclick="document.getElementById('fileInput').click()">
      """ + SVG_UPLOAD + """
      <h4>Faylı bura sürükləyin və ya klikləyib seçin</h4>
      <p>PDF, Word, Excel, ZIP, şəkil — maks. 50 MB</p>
      <input type="file" id="fileInput" style="display:none" onchange="uploadFiles(this.files)">
      <div class="progress" id="prog"><i id="progBar"></i></div>
    </div>
    <div class="file-list" id="fileList">
      {% for f in files %}
      <div class="frow" id="file-{{ f['id'] }}">
        <div class="fico">""" + SVG_DOC + """<span class="fext">{{ f['ext'] }}</span></div>
        <div class="meta"><b title="{{ f['original_name']|e }}">{{ f['original_name']|e }}</b><span>{{ f['size_h'] }} • {{ f['uploaded_at'] }}</span></div>
        <div class="factions">
          <a class="btn btn-ghost btn-sm" href="/admin-panel/download/{{ f['id'] }}">""" + SVG_DOWNLOAD + """ Yüklə</a>
          <button class="btn btn-danger btn-sm" onclick="deleteFile({{ f['id'] }})">""" + SVG_TRASH + """ Sil</button>
        </div>
      </div>
      {% else %}
      <div class="empty" id="fileEmpty">Anbar boşdur — ilk sənədi yükləyin.</div>
      {% endfor %}
    </div>
  </section>

  <div style="height:60px"></div>
</main>

<!-- ADD PRODUCT MODAL (real file upload) -->
<div class="overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <button class="x" onclick="closeModal()">""" + SVG_X + """</button>
    <h3>Yeni Yük Manifesti</h3>
    <p class="sub">Adı yazın və məhsul şəklini birbaşa cihazınızdan yükləyin. SKU avtomatik təyin olunur.</p>
    <div class="img-preview" id="imgPreview">""" + SVG_IMAGE + """<span>Şəkil önizləməsi burada görünəcək</span></div>
    <div class="field"><label>Məhsul adı *</label><input type="text" id="npName" placeholder="Məs: Epoksi Qətran A-200" maxlength="160"></div>
    <div class="field"><label>Məhsul şəkli * (PNG / JPG / WEBP, maks. 10 MB)</label>
      <label class="file-drop" id="fileDrop">
        """ + SVG_UPLOAD.replace(' big', '') + """
        <span class="fd-txt"><b>Şəkil seçin və ya bura sürükləyin</b><span id="fileHint">Hələ fayl seçilməyib</span></span>
        <input type="file" id="npFile" name="product_image" accept="image/*" required style="display:none">
      </label>
    </div>
    <button class="btn btn-gold" id="addBtn" style="width:100%;padding:14px" onclick="addProduct()">""" + SVG_CHECK + """ Manifesti Əlavə Et</button>
  </div>
</div>

""" + CONFIRM_MODAL_HTML + """

<script>
""" + JS_ICONS + """
function switchA(name,btn){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.getElementById('atab-'+name).classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
}
function openModal(){ document.getElementById('modalOverlay').classList.add('open'); setTimeout(()=>document.getElementById('npName').focus(),80); }
function closeModal(){ document.getElementById('modalOverlay').classList.remove('open'); }
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ closeModal(); } });
const npFile = document.getElementById('npFile');
const fileDrop = document.getElementById('fileDrop');
fileDrop.addEventListener('click', e=>{ if(e.target.tagName!=='INPUT') npFile.click(); });
fileDrop.addEventListener('dragover', e=>{ e.preventDefault(); });
fileDrop.addEventListener('drop', e=>{
  e.preventDefault();
  if(e.dataTransfer.files && e.dataTransfer.files.length){ npFile.files = e.dataTransfer.files; handleFileSelect(); }
});
npFile.addEventListener('change', handleFileSelect);
function handleFileSelect(){
  const box=document.getElementById('imgPreview'), hint=document.getElementById('fileHint');
  const f=npFile.files && npFile.files[0];
  if(!f){ hint.textContent='Hələ fayl seçilməyib'; return; }
  if(!f.type.startsWith('image/')){ showToast('Xəta','Yalnız şəkil faylı seçin (PNG, JPG, WEBP).','error'); npFile.value=''; return; }
  if(f.size > 10*1024*1024){ showToast('Xəta','Şəkil çox böyükdür (maks. 10 MB).','error'); npFile.value=''; return; }
  hint.textContent=f.name+' ('+(f.size/1024).toFixed(0)+' KB)';
  const rd=new FileReader();
  rd.onload=()=>{ box.innerHTML=''; const im=document.createElement('img'); im.src=rd.result; im.alt='Önizləmə'; box.appendChild(im);
    const s=document.createElement('span'); s.className='fname'; s.textContent=f.name; box.appendChild(s); };
  rd.readAsDataURL(f);
}
async function addProduct(){
  const name=document.getElementById('npName').value.trim();
  const f=npFile.files && npFile.files[0];
  if(name.length < 2){ showToast('Xəta','Məhsul adı minimum 2 simvol olmalıdır.','error'); return; }
  if(!f){ showToast('Xəta','Zəhmət olmasa məhsul şəkli seçin.','error'); return; }
  const fd=new FormData(); fd.append('name', name); fd.append('product_image', f);
  const btn=document.getElementById('addBtn'); btn.disabled=true; btn.textContent='Əlavə olunur…';
  try{
    const r=await fetch('/api/products/add',{method:'POST',body:fd});
    const d=await r.json();
    if(d.ok){
      showToast('Uğurlu','Manifest kataloqa əlavə edildi.','success');
      document.getElementById('npName').value=''; npFile.value='';
      document.getElementById('fileHint').textContent='Hələ fayl seçilməyib';
      closeModal(); setTimeout(()=>location.reload(),700);
    } else showToast('Xəta',d.error||'Əlavə etmək mümkün olmadı.','error');
  }catch(e){ showToast('Xəta','Server xətası.','error'); }
  btn.disabled=false; btn.textContent='Manifesti Əlavə Et';
}
async function deleteProduct(id, btn){
  const ok = await askConfirm('Manifest silinsin?','"'+id+'" nömrəli yük kataloqdan çıxarılacaq. Yüklənmiş şəkli də silinəcək.','Bəli, sil');
  if(!ok) return;
  btn.disabled=true; btn.textContent='Silinir…';
  try{
    const r=await fetch('/api/products/delete/'+id,{method:'POST'});
    const d=await r.json();
    if(d.ok){
      showToast('Silindi','Yük kataloqdan çıxarıldı.','success');
      const card=document.getElementById('prod-'+id);
      card.style.transition='transform .35s ease,opacity .35s ease'; card.style.opacity='0';
      setTimeout(()=>card.remove(),340);
    } else { showToast('Xəta',d.error||'Silinmədi.','error'); btn.disabled=false; }
  }catch(e){ showToast('Xəta','Server xətası.','error'); btn.disabled=false; }
}
const dz=document.getElementById('dz');
['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();}));
dz.addEventListener('drop',e=>{ e.preventDefault(); if(e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); });
function uploadFiles(files){
  if(!files || !files.length) return;
  const fd=new FormData(); fd.append('file', files[0]);
  const prog=document.getElementById('prog'), bar=document.getElementById('progBar');
  prog.style.display='block'; bar.style.width='15%';
  const xhr=new XMLHttpRequest();
  xhr.open('POST','/api/tender/upload',true);
  xhr.upload.onprogress=e=>{ if(e.lengthComputable) bar.style.width=Math.round(e.loaded/e.total*100)+'%'; };
  xhr.onload=()=>{
    bar.style.width='100%';
    setTimeout(()=>prog.style.display='none',500);
    try{
      const d=JSON.parse(xhr.responseText);
      if(xhr.status===200 && d.ok){ showToast('Yükləndi',d.file.original_name+' anbara əlavə edildi.','success'); setTimeout(()=>location.reload(),700); }
      else showToast('Xəta',(d&&d.error)||'Yükləmə uğursuz oldu.','error');
    }catch(e){ showToast('Xəta','Cavab oxunmadı.','error'); }
  };
  xhr.onerror=()=>{ prog.style.display='none'; showToast('Xəta','Şəbəkə xətası.','error'); };
  xhr.send(fd);
}
async function deleteFile(id){
  const ok = await askConfirm('Sənəd silinsin?','Bu sənəd tender arxivindən tamamilə çıxarılacaq.','Bəli, sil');
  if(!ok) return;
  try{
    const r=await fetch('/api/tender/delete/'+id,{method:'POST'});
    const d=await r.json();
    if(d.ok){ showToast('Silindi','Sənəd arxivdən çıxarıldı.','success'); document.getElementById('file-'+id).remove(); }
    else showToast('Xəta',d.error||'Silinmədi.','error');
  }catch(e){ showToast('Xəta','Server xətası.','error'); }
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes — Public
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template_string(PUBLIC_PAGE, products=products, c=COMPANY)


@app.route("/product-image/<path:filename>", methods=["GET"])
def product_image(filename):
    """Serve locally uploaded product images to the public catalog."""
    name = os.path.basename(filename or "")
    if not name or name != filename or name.startswith("."):
        abort(404)
    if not allowed_image(name):
        abort(404)
    path = os.path.join(PRODUCT_IMAGE_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    resp = send_from_directory(PRODUCT_IMAGE_DIR, name)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/partner-logo/<path:filename>", methods=["GET"])
def partner_logo(filename):
    """Serve locally stored partner logos (public)."""
    name = os.path.basename(filename or "")
    if not name or name != filename or name.startswith("."):
        abort(404)
    if not (allowed_image(name) or name.lower().endswith(".svg")):
        abort(404)
    path = os.path.join(PARTNER_LOGO_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    resp = send_from_directory(PARTNER_LOGO_DIR, name)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


# ---------------------------------------------------------------------------
# Routes — Hidden Admin (Control Tower)
# ---------------------------------------------------------------------------
@app.route("/admin-panel", methods=["GET"])
def admin_panel():
    if not is_admin():
        return render_template_string(ADMIN_LOGIN_PAGE, c=COMPANY)
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    rows = db.execute("SELECT * FROM tender_files ORDER BY id DESC").fetchall()
    files, total = [], 0
    for r in rows:
        d = dict(r)
        total += int(d.get("size") or 0)
        d["ext"] = file_ext(d.get("original_name"))
        d["size_h"] = format_size(d.get("size"))
        files.append(d)
    return render_template_string(
        ADMIN_DASHBOARD_PAGE, products=products, files=files,
        total_size=format_size(total), c=COMPANY,
    )


@app.route("/admin-panel/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    if not data:
        data = request.form.to_dict()
    password = (data.get("password") or "").strip()
    if password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        session.permanent = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Şifrə yanlışdır. Yenidən cəhd edin."}), 401


@app.route("/admin-panel/logout", methods=["GET"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_panel"))


@app.route("/admin-panel/download/<int:fid>", methods=["GET"])
def tender_download(fid):
    if not is_admin():
        abort(403)
    db = get_db()
    row = db.execute("SELECT * FROM tender_files WHERE id = ?", (fid,)).fetchone()
    if not row:
        abort(404)
    stored = row["stored_name"]
    if os.path.basename(stored) != stored:
        abort(400)
    directory = TENDER_DIR if os.path.isfile(os.path.join(TENDER_DIR, stored)) else UPLOAD_FOLDER
    if not os.path.isfile(os.path.join(directory, stored)):
        abort(404)
    try:
        return send_from_directory(
            directory, stored,
            as_attachment=True, download_name=row["original_name"],
        )
    except TypeError:
        return send_from_directory(
            directory, stored,
            as_attachment=True, attachment_filename=row["original_name"],
        )


# ---------------------------------------------------------------------------
# JSON APIs (admin only)
# ---------------------------------------------------------------------------
@app.route("/api/products/add", methods=["POST"])
@admin_required
def api_product_add():
    # Primary flow: multipart form with a real uploaded image file.
    # Legacy flow: JSON {name, image_url} (kept for backward compatibility).
    if request.is_json:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        image_url = (data.get("image_url") or "").strip()
        if len(name) < 2:
            return jsonify({"ok": False, "error": "Məhsul adı minimum 2 simvol olmalıdır."}), 400
        if len(name) > 160:
            return jsonify({"ok": False, "error": "Məhsul adı çox uzundur (maks. 160)."}), 400
        if not re.match(r"^(https?://|/product-image/)", image_url, re.I):
            return jsonify({"ok": False, "error": "Şəkil URL yanlışdır."}), 400
        stored_value = image_url
    else:
        name = (request.form.get("name") or "").strip()
        f = request.files.get("product_image")
        if len(name) < 2:
            return jsonify({"ok": False, "error": "Məhsul adı minimum 2 simvol olmalıdır."}), 400
        if len(name) > 160:
            return jsonify({"ok": False, "error": "Məhsul adı çox uzundur (maks. 160)."}), 400
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "Zəhmət olmasa məhsul şəkli seçin."}), 400
        safe = secure_filename(f.filename.strip())
        if not safe or not allowed_image(safe):
            return jsonify({"ok": False, "error": "Yalnız şəkil faylı icazəlidir (PNG, JPG, JPEG, WEBP, GIF)."}), 400
        stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        base, ext = os.path.splitext(safe)
        base = re.sub(r"[^A-Za-z0-9_\-]+", "_", base).strip("_")[:60] or "mehsul"
        stored = f"{stamp}_{base}{ext.lower()}"
        dest = os.path.join(PRODUCT_IMAGE_DIR, stored)
        try:
            f.save(dest)
        except Exception as exc:
            return jsonify({"ok": False, "error": f"Şəkil saxlanıla bilmədi: {exc}"}), 500
        if os.path.getsize(dest) > MAX_IMAGE_BYTES:
            try:
                os.remove(dest)
            except OSError:
                pass
            return jsonify({"ok": False, "error": "Şəkil çox böyükdür (maks. 10 MB)."}), 400
        stored_value = f"/product-image/{stored}"

    db = get_db()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    cur = db.execute(
        "INSERT INTO products (name, image_url, created_at) VALUES (?, ?, ?)",
        (name, stored_value, now),
    )
    db.commit()
    return jsonify({"ok": True, "product": {"id": cur.lastrowid, "name": name, "image_url": stored_value}})


@app.route("/api/products/delete/<int:pid>", methods=["POST", "DELETE"])
@admin_required
def api_product_delete(pid):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Məhsul tapılmadı."}), 404
    local = local_product_file(row["image_url"])
    if local:
        try:
            if os.path.isfile(local):
                os.remove(local)
        except OSError:
            pass
    db.execute("DELETE FROM products WHERE id = ?", (pid,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/tender/upload", methods=["POST"])
@admin_required
def api_tender_upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Fayl göndərilməyib."}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "Fayl seçilməyib."}), 400
    original = secure_filename(f.filename.strip())
    if not original:
        return jsonify({"ok": False, "error": "Fayl adı yanlışdır."}), 400
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    stored = f"{stamp}_{original}"
    stored = re.sub(r"[^A-Za-z0-9_.\-]", "_", stored)
    dest = os.path.join(TENDER_DIR, stored)
    try:
        f.save(dest)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Saxlanıla bilmədi: {exc}"}), 500
    size = os.path.getsize(dest) if os.path.isfile(dest) else 0
    now = datetime.datetime.now().isoformat(timespec="seconds")
    db = get_db()
    cur = db.execute(
        "INSERT INTO tender_files (stored_name, original_name, size, uploaded_at) VALUES (?, ?, ?, ?)",
        (stored, f.filename.strip(), size, now),
    )
    db.commit()
    return jsonify({"ok": True, "file": {
        "id": cur.lastrowid, "original_name": f.filename.strip(),
        "size": size, "size_h": format_size(size),
    }})


@app.route("/api/tender/delete/<int:fid>", methods=["POST", "DELETE"])
@admin_required
def api_tender_delete(fid):
    db = get_db()
    row = db.execute("SELECT * FROM tender_files WHERE id = ?", (fid,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Sənəd tapılmadı."}), 404
    stored = row["stored_name"]
    if os.path.basename(stored) == stored:
        for directory in (TENDER_DIR, UPLOAD_FOLDER):
            try:
                p = os.path.join(directory, stored)
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
    db.execute("DELETE FROM tender_files WHERE id = ?", (fid,))
    db.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
@app.errorhandler(413)
def too_large(_e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Fayl çox böyükdür (maks. 50 MB)."}), 413
    return "Fayl çox böyükdür (maks. 50 MB).", 413


@app.errorhandler(403)
def forbidden(_e):
    if request.path.startswith(("/api/", "/admin-panel/download")):
        return jsonify({"ok": False, "error": "Giriş qadağandır."}), 403
    return redirect(url_for("admin_panel"))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    # Production on Ubuntu:  gunicorn -w 4 -b 0.0.0.0:8000 app:app
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)

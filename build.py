#!/usr/bin/env python3
"""Parte Surf — junta modelos (Open-Meteo) + sitios web (web.json), descarta outliers y usa la MEDIANA.

Uso:  python3 -I build.py <template.html> <web.json | -> <salida.html>

web.json (opcional; lo llena la corrida programada leyendo Wisuki, Surf-forecast, Breakfinder, Lineup, Surfline):
  {"mat": [{"src": "Wisuki", "date": "2026-10-17", "slot": "AM", "sh": 1.4, "tp": 13, "sd": 240, "ws": 19, "wd": 190}],
   "pue": [...], "top": [...]}
  slot: "AM" = 06–11 h, "PM" = 12–19 h, "N" = 20–05 h.
  Unidades: sh m · tp s (período PICO) · sd/wd grados de donde viene · ws km/h. Cualquier campo puede faltar.

Método por hora y variable:
  1. Junta un valor por fuente (modelos + sitios web de esa franja).
  2. Mediana y MAD (desviación absoluta mediana × 1,4826).
  3. Límite = max(min(2,5·MAD, tope%·mediana), piso absoluto, piso%·mediana). Descarta lo que se aleja más que eso.
     Altura: piso 0,25 m / 22 %, tope 40 %. Período: piso 2,5 s, tope 30 %. Viento: piso 6 km/h / 30 %, tope 50 %.
  4. Mediana de lo que queda (si quedan ≥ 2). Direcciones: media circular de lo que queda a ≤ 45° (oleaje) / 60° (viento).

Historial: antes de escribir, lee el index.html anterior y guarda en DATA.hist las corridas de las últimas 30 h
(una cada ≥ 2 h, 72 horas de datos por spot) para que la página muestre cómo cambió el pronóstico.
"""
import json, sys, time, math, statistics, urllib.request, datetime

SPOTS = {"mat": (-33.96, -71.89), "pue": (-34.09, -71.97), "top": (-34.13, -72.01)}
DAYS = 10  # días 8 a 10 se muestran como tendencia (quedan pocos modelos)
TZ = "America/Santiago"
# best_match se excluye: en esta costa devuelve exactamente Météo-France y votaría dos veces.
# ecmwf_wam025 se excluye: no tiene celdas de mar en este tramo de costa.
WAVE_MODELS = ["ncep_gfswave025", "meteofrance_wave", "dwd_gwam"]
WIND_MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless", "meteofrance_seamless",
               "ukmo_seamless", "gem_seamless", "jma_seamless"]
LABEL = {"ncep_gfswave025": "NOAA GFS-Wave", "meteofrance_wave": "Météo-France ola", "dwd_gwam": "DWD GWAM",
         "ecmwf_ifs025": "ECMWF", "gfs_seamless": "NOAA GFS", "icon_seamless": "DWD ICON",
         "meteofrance_seamless": "Météo-France", "ukmo_seamless": "UK Met Office",
         "gem_seamless": "Canadá GEM", "jma_seamless": "Japón JMA"}
TP_FROM_MEAN = 1.25          # período pico ≈ 1,25 × período medio cuando el modelo no entrega pico
# (piso absoluto, piso relativo) para el corte de outliers
FLOORS = {"sh": (0.25, 0.22), "tp": (2.5, 0.0), "ws": (6.0, 0.30), "wg": (8.0, 0.30), "h2": (0.20, 0.30), "p2": (2.5, 0.0), "ww": (0.15, 0.30)}
# tope relativo: con pocas fuentes muy dispersas el MAD se infla; el límite nunca supera este % de la mediana
CAPS = {"sh": 0.40, "tp": 0.30, "ws": 0.50, "wg": 0.50, "h2": 0.60, "p2": 0.35, "ww": 0.60}


HEAD = """<!doctype html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1F45D6">
<meta name="apple-mobile-web-app-title" content="Según Vicho">
<link rel="icon" type="image/svg+xml" href="icons/icono.svg">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="icons/favicon-16.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<script data-goatcounter="https://segunvicho.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
<style>body{margin:0}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>
"""


def get(url, tries=4):
    err = None
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e
            time.sleep(3 + 4 * t)
    print("FALLÓ", url[:110], err, file=sys.stderr)
    return None


def valid(series, min_n=24):
    return series is not None and sum(x is not None for x in series) >= min_n


def dedupe(models, key):
    """Quita modelos cuya serie es idéntica a otra ya incluida (el mismo modelo con otro nombre)."""
    seen, out = [], {}
    for m, d in models.items():
        sig = tuple(d[key])
        if sig in seen:
            print("duplicado descartado:", m, file=sys.stderr)
            continue
        seen.append(sig); out[m] = d
    return out


def split_models(d, models, vars_):
    """Una respuesta multi-modelo trae columnas <var>_<modelo>; las separa en {modelo: {var: serie}}."""
    h = (d or {}).get("hourly", {})
    out = {}
    for m in models:
        cols = {v: h.get(f"{v}_{m}") if len(models) > 1 else h.get(v) for v in vars_}
        if valid(cols[vars_[0]]):
            out[m] = cols
    return out


def fetch_spot(lat, lon):
    bm = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&timezone={TZ}&forecast_days={DAYS}&cell_selection=sea"
    bw = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&timezone={TZ}&forecast_days={DAYS}&wind_speed_unit=kmh"
    wv = ["swell_wave_height", "swell_wave_period", "swell_wave_peak_period", "swell_wave_direction",
          "secondary_swell_wave_height", "secondary_swell_wave_period", "secondary_swell_wave_direction", "wind_wave_height"]
    vv = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"]
    # una llamada con todos los modelos; si falla, cae a una llamada por modelo
    wave = split_models(get(bm + "&models=" + ",".join(WAVE_MODELS) + "&hourly=" + ",".join(wv)), WAVE_MODELS, wv)
    for m in [m for m in WAVE_MODELS if m not in wave]:
        wave.update(split_models(get(bm + "&models=" + m + "&hourly=" + ",".join(wv), tries=2), [m], wv))
    wind = split_models(get(bw + "&models=" + ",".join(WIND_MODELS) + "&hourly=" + ",".join(vv)), WIND_MODELS, vv)
    for m in [m for m in WIND_MODELS if m not in wind]:
        wind.update(split_models(get(bw + "&models=" + m + "&hourly=" + ",".join(vv), tries=2), [m], vv))
    wave = {m: wave[m] for m in WAVE_MODELS if m in wave}; wind = {m: wind[m] for m in WIND_MODELS if m in wind}
    failed = [LABEL[m] for m in WAVE_MODELS + WIND_MODELS if m not in wave and m not in wind]
    extra = get(bm + "&hourly=sea_level_height_msl,sea_surface_temperature")
    wx = get(bw + "&hourly=temperature_2m,cloud_cover,precipitation&daily=sunrise,sunset")
    return dedupe(wave, "swell_wave_height"), dedupe(wind, "wind_speed_10m"), extra, wx, failed


def robust(vals, var, k=2.5):
    """vals: [(fuente, valor)] → (mediana, kept, cut)."""
    vals = [(s, float(v)) for s, v in vals if v is not None]
    if not vals:
        return None, [], []
    xs = [v for _, v in vals]
    med = statistics.median(xs)
    mad = statistics.median([abs(x - med) for x in xs]) * 1.4826
    fa, fr = FLOORS[var]
    lim = max(min(k * mad, CAPS[var] * abs(med)), fa, fr * abs(med))
    kept = [(s, v) for s, v in vals if abs(v - med) <= lim]
    cut = [(s, v) for s, v in vals if abs(v - med) > lim]
    if len(kept) >= 2:
        med = statistics.median([v for _, v in kept])
    return med, kept, cut


def circ_mean(degs):
    x = sum(math.cos(math.radians(d)) for d in degs); y = sum(math.sin(math.radians(d)) for d in degs)
    return None if not degs else (math.degrees(math.atan2(y, x)) + 360) % 360


def circ_robust(vals, lim):
    vals = [(s, float(v)) for s, v in vals if v is not None]
    if not vals:
        return None
    c = circ_mean([v for _, v in vals])
    diff = lambda a, b: abs((a - b + 540) % 360 - 180)
    kept = [v for _, v in vals if diff(v, c) <= lim]
    return circ_mean(kept) if kept else c


def slot_of(h):
    return "AM" if 6 <= h <= 11 else "PM" if 12 <= h <= 19 else "N"


def rnd(v, k=2):
    return None if v is None else round(v, k)


def build(web):
    now = datetime.datetime.now(datetime.timezone.utc)
    out = {"generated_utc": now.strftime("%Y-%m-%dT%H:%MZ"), "method": "mediana con corte de outliers", "spots": {}}
    for key, (lat, lon) in SPOTS.items():
        wave, wind, extra, wx, failed = fetch_spot(lat, lon)
        if not wave or not wind or not wx:
            raise SystemExit(f"Sin modelos suficientes para {key}: olas={list(wave)} viento={list(wind)}")
        times = wx["hourly"]["time"]; n = len(times)
        out.setdefault("tz_offset_s", wx.get("utc_offset_seconds", -10800))
        out.setdefault("start", times[0][:10])
        webs = web.get(key, [])
        H = {k: [] for k in ["sh", "sp", "sd", "h2", "p2", "d2", "ww", "ws", "wd", "wg", "shLo", "shHi", "wsLo", "wsHi", "nW", "nV"]}
        audit, srcSh, srcWs, cutSh, cutWs = {}, {}, {}, {}, {}

        def put(store, src, i, v, k):
            store.setdefault(src, [None] * n)[i] = rnd(v, k)

        for i in range(n):
            day, hr = times[i][:10], int(times[i][11:13])
            ws_ = [w for w in webs if w.get("date") == day and w.get("slot") == slot_of(hr)]
            g = lambda d, f: (d.get(f) or [None] * n)[i]
            # swell primario
            shv = [(LABEL[m], g(d, "swell_wave_height")) for m, d in wave.items()] + [(w["src"], w.get("sh")) for w in ws_]
            sh, ks, cs = robust(shv, "sh")
            tpv = []
            for m, d in wave.items():
                pk, mn = g(d, "swell_wave_peak_period"), g(d, "swell_wave_period")
                tpv.append((LABEL[m], pk if pk is not None else (mn * TP_FROM_MEAN if mn is not None else None)))
            tpv += [(w["src"], w.get("tp")) for w in ws_]
            tp, kt, ct = robust(tpv, "tp")
            sd = circ_robust([(LABEL[m], g(d, "swell_wave_direction")) for m, d in wave.items()] + [(w["src"], w.get("sd")) for w in ws_], 45)
            # swell secundario y mar de viento (solo modelos)
            h2, _, _ = robust([(LABEL[m], g(d, "secondary_swell_wave_height")) for m, d in wave.items()], "h2")
            p2, _, _ = robust([(LABEL[m], None if g(d, "secondary_swell_wave_period") is None else g(d, "secondary_swell_wave_period") * TP_FROM_MEAN) for m, d in wave.items()], "p2")
            d2 = circ_robust([(LABEL[m], g(d, "secondary_swell_wave_direction")) for m, d in wave.items()], 45)
            ww, _, _ = robust([(LABEL[m], g(d, "wind_wave_height")) for m, d in wave.items()], "ww")
            # viento
            wsv = [(LABEL[m], g(d, "wind_speed_10m")) for m, d in wind.items()] + [(w["src"], w.get("ws")) for w in ws_]
            ws, kw, cw = robust(wsv, "ws")
            wd = circ_robust([(LABEL[m], g(d, "wind_direction_10m")) for m, d in wind.items()] + [(w["src"], w.get("wd")) for w in ws_], 60)
            wg, _, _ = robust([(LABEL[m], g(d, "wind_gusts_10m")) for m, d in wind.items()], "wg")
            # auditoría y series por fuente
            for s, _ in ks + kt + kw:
                audit.setdefault(day, {}).setdefault(s, [0, 0])[0] += 1
            for s, _ in cs + ct + cw:
                audit.setdefault(day, {}).setdefault(s, [0, 0])[1] += 1
            for s, v in shv: put(srcSh, s, i, v, 2)
            for s, v in wsv: put(srcWs, s, i, v, 0)
            for s, _ in cs: cutSh.setdefault(s, []).append(i)
            for s, _ in cw: cutWs.setdefault(s, []).append(i)
            H["sh"].append(rnd(sh)); H["sp"].append(rnd(tp, 1)); H["sd"].append(rnd(sd, 0))
            H["h2"].append(rnd(h2)); H["p2"].append(rnd(p2, 1)); H["d2"].append(rnd(d2, 0)); H["ww"].append(rnd(ww))
            H["ws"].append(rnd(ws, 0)); H["wd"].append(rnd(wd, 0)); H["wg"].append(rnd(wg, 0))
            H["shLo"].append(rnd(min((v for _, v in ks), default=sh))); H["shHi"].append(rnd(max((v for _, v in ks), default=sh)))
            H["wsLo"].append(rnd(min((v for _, v in kw), default=ws), 0)); H["wsHi"].append(rnd(max((v for _, v in kw), default=ws), 0))
            H["nW"].append(len(ks)); H["nV"].append(len(kw))
        # mareas: extremos de la serie horaria refinados con una parábola
        sl = extra["hourly"]["sea_level_height_msl"] if extra else [None] * n
        tides = []
        for i in range(1, n - 1):
            a, b, c = sl[i - 1], sl[i], sl[i + 1]
            if None in (a, b, c) or not ((b > a and b >= c) or (b < a and b <= c)):
                continue
            den = a - 2 * b + c
            off = 0.5 * (a - c) / den if den else 0.0
            tides.append({"m": int(round((i + off) * 60)), "h": round(b - 0.25 * (a - c) * off, 2), "type": "alta" if b > a else "baja"})
        out["spots"][key] = dict(
            time=[t[5:16] for t in times], **H,
            tide=[rnd(x) for x in sl],
            sst=[rnd(x, 1) for x in (extra["hourly"]["sea_surface_temperature"] if extra else [None] * n)],
            ta=[rnd(x, 0) for x in wx["hourly"]["temperature_2m"]],
            cc=[rnd(x, 0) for x in wx["hourly"]["cloud_cover"]],
            pr=[rnd(x, 1) for x in wx["hourly"]["precipitation"]],
            tides=tides,
            audit={d: [{"src": s, "used": u, "cut": c} for s, (u, c) in sorted(v.items(), key=lambda x: -x[1][1])] for d, v in audit.items()},
            srcSh=srcSh, srcWs=srcWs, cutSh=cutSh, cutWs=cutWs,
            models={"wave": [LABEL[m] for m in wave], "wind": [LABEL[m] for m in wind], "web": sorted({w["src"] for w in webs}), "failed": failed},
            sun={d: [a[11:], b[11:]] for d, a, b in zip(wx["daily"]["time"], wx["daily"]["sunrise"], wx["daily"]["sunset"])})
    return out


# ——— historial: corridas anteriores para mostrar si el pronóstico mejoró o empeoró ———
HIST_FIELDS = ["sh", "sp", "sd", "h2", "p2", "d2", "ws", "wd", "ww", "tide"]
HIST_HOURS = 72     # cubre hoy y mañana aunque la corrida anterior sea del día previo
HIST_KEEP_H = 30    # guarda corridas de hasta 30 h atrás (alcanza para comparar con hace 24 h)


def read_data(path):
    """DATA embebido en un index.html ya construido, o None."""
    try:
        html = open(path).read()
        i = html.index("const DATA = ") + len("const DATA = ")
        return json.JSONDecoder().raw_decode(html[i:])[0]
    except Exception:
        return None


def snapshot(d):
    return {"t": d["generated_utc"], "start": d["start"],
            "spots": {k: {f: s[f][:HIST_HOURS] for f in HIST_FIELDS} for k, s in d["spots"].items()}}


def history(prev, now_utc):
    if not prev:
        return []
    runs = {h["t"]: h for h in prev.get("hist", [])}
    if "start" in prev:
        runs[prev["generated_utc"]] = snapshot(prev)
    t0 = datetime.datetime.strptime(now_utc, "%Y-%m-%dT%H:%MZ")
    keep = [h for t, h in runs.items()
            if t != now_utc and 0 < (t0 - datetime.datetime.strptime(t, "%Y-%m-%dT%H:%MZ")).total_seconds() <= HIST_KEEP_H * 3600]
    # una corrida cada ≥ 2 h basta (los push manuales generan corridas muy seguidas)
    out, last = [], None
    for h in sorted(keep, key=lambda h: h["t"], reverse=True):
        t = datetime.datetime.strptime(h["t"], "%Y-%m-%dT%H:%MZ")
        if last is None or (last - t).total_seconds() >= 2 * 3600:
            out.append(h); last = t
    return out[::-1]


if __name__ == "__main__":
    tpl, webp, outp = sys.argv[1:4]
    web = json.load(open(webp)) if webp != "-" else {}
    # datos de sitios web viejos no suman: si web.json tiene más de 36 h (o no dice cuándo se leyó), se ignora
    upd = (web.get("_meta") or {}).get("updated_utc")
    if not upd or (datetime.datetime.utcnow() - datetime.datetime.strptime(upd, "%Y-%m-%dT%H:%MZ")).total_seconds() > 36 * 3600:
        print("web.json sin fecha o con más de 36 h: se usan solo los modelos")
        web = {}
    data = build(web)
    data["hist"] = history(read_data(outp), data["generated_utc"])
    html = open(tpl).read().replace("__DATA__", json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    if outp.endswith("index.html"):  # página pública: documento completo con íconos y manifest
        html = HEAD + html + "\n</html>\n"
    open(outp, "w").write(html)
    for k, s in data["spots"].items():
        print(k, "| olas:", s["models"]["wave"], "| viento:", len(s["models"]["wind"]), "| web:", s["models"]["web"], "| fallaron:", s["models"]["failed"])

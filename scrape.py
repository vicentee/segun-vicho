#!/usr/bin/env python3
"""Lee los sitios web de pronóstico y escribe web.json para build.py.

Uso:  python3 -I scrape.py web.json

Fuentes (solo librería estándar, sin navegador):
  - Surf-forecast: tabla de 7 días, mañana / tarde / noche por día. Altura y período del swell, dirección, viento.
  - Wisuki: tabla cada 3 h. Se promedia por franja (AM 06–11, PM 12–19, N 20–05). Usa GFS, así que suma poco
    sobre los modelos, pero el corte de outliers lo maneja.
Si una fuente falla o cambia su HTML, se omite y el resto sigue. Si no se lee nada, web.json no se toca.
"""
import datetime, json, math, re, sys, time, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
SOURCES = {
    "mat": {"Surf-forecast": "https://www.surf-forecast.com/breaks/Matanzas/forecasts/latest/six_day",
            "Wisuki": "https://es.wisuki.com/forecast/4253/matanzas"},
    "pue": {"Surf-forecast": "https://www.surf-forecast.com/breaks/Puertecillo/forecasts/latest/six_day",
            "Wisuki": "https://es.wisuki.com/forecast/6652/puertecillo"},
    "top": {"Surf-forecast": "https://www.surf-forecast.com/breaks/Punta-Topocalma/forecasts/latest/six_day"},
}
KN = 1.852


def fetch(url):
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-CL,es;q=0.9,en;q=0.8"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(3)
    raise err


def row_html(html, name):
    i = html.find(f'data-row="{name}"')
    if i < 0:
        raise ValueError(f"fila {name} no encontrada")
    return html[i:html.find("</tr>", i)]


def circ(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    s = sum(math.sin(math.radians(v)) for v in vals); c = sum(math.cos(math.radians(v)) for v in vals)
    return round(math.degrees(math.atan2(s, c)) % 360)


def mean(vals, nd=1):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), nd) if vals else None


def parse_surf_forecast(html):
    days = []
    for span, date in re.findall(r'colspan="(\d+)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"', row_html(html, "days")):
        days += [date] * int(span)
    slots = re.findall(r"<span>(AM|PM|Night)</span>", row_html(html, "time"))
    cells = lambda n: re.findall(r"<td[^>]*>(.*?)</td>", row_html(html, n), re.S)
    swell, wind = cells("swell"), cells("wind")
    if not (len(days) == len(slots) == len(swell) == len(wind)) or not days:
        raise ValueError(f"columnas no calzan: {len(days)} {len(slots)} {len(swell)} {len(wind)}")
    out = []
    for date, slot, sw, wi in zip(days, slots, swell, wind):
        r = {"src": "Surf-forecast", "date": date, "slot": {"AM": "AM", "PM": "PM", "Night": "N"}[slot]}
        m = re.search(r'data-height="([\d.]+)"', sw)
        if m: r["sh"] = float(m.group(1))
        m = re.search(r'swell-period">\s*(\d+)', sw)
        if m: r["tp"] = int(m.group(1))
        m = re.search(r'swell-icon__arrow"[^>]*rotate\(([-\d.]+)\)', sw)
        if m: r["sd"] = round((float(m.group(1)) + 180) % 360)      # la flecha apunta hacia donde va; guardamos de dónde viene
        m = re.search(r'data-speed="([\d.]+)"', wi)
        if m: r["ws"] = round(float(m.group(1)), 1)                   # la tabla está en km/h
        m = re.search(r'wind-icon__arrow"[^>]*rotate\(([-\d.]+)\)', wi)
        if m: r["wd"] = round((float(m.group(1)) + 180) % 360)
        if "sh" in r or "ws" in r:
            out.append(r)
    return out


def parse_wisuki(html, today):
    t = html[html.find('<table class="forecast long">'):]
    t = t[:t.find("</table>")]
    if not t:
        raise ValueError("tabla no encontrada")
    # columnas: días (colspan) y horas
    days = []
    month, year, last = today.month, today.year, None
    for span, dom in re.findall(r'<th colspan="(\d+)"[^>]*id="day-(\d+)"', t):
        dom = int(dom)
        if last is not None and dom < last:          # cambio de mes
            month += 1
            if month == 13: month, year = 1, year + 1
        last = dom
        days += [datetime.date(year, month, dom).isoformat()] * int(span)
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)
    hours = [int(h) for h in re.findall(r">(\d{2})h<", trs[1])]
    rows = {}
    for tr in trs[2:]:
        th = re.search(r"<th[^>]*>(.*?)</th>", tr, re.S)
        if not th: continue
        name = re.sub(r"<[^>]+>|\s+", " ", th.group(1)).strip()
        rows.setdefault(name, []).append(re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S))
    num = lambda c: float(c) if re.fullmatch(r"\s*-?[\d.]+\s*", c or "") else None
    deg = lambda c: (lambda m: int(m.group(1)) if m else None)(re.search(r"\|\s*(\d+)&deg;", c or ""))
    media = next(v for k, v in rows.items() if k.startswith("Media"))[0]
    dirs = rows["Dirección"]            # [viento, olas]
    alt = next(v for k, v in rows.items() if k.startswith("Altura"))[0]
    per = next(v for k, v in rows.items() if k.startswith("Periodo"))[0]
    kn = "kn" in next(k for k in rows if k.startswith("Media"))
    n = min(len(days), len(hours), len(media), len(alt), len(per), len(dirs[0]), len(dirs[1]))
    if n < 8:
        raise ValueError(f"pocas columnas: {n}")
    slot = lambda h: "AM" if 6 <= h < 12 else "PM" if 12 <= h < 20 else "N"
    acc = {}
    for j in range(n):
        h, d = hours[j], days[j]    # mismo criterio que build.py: la franja N de un día son sus 00–05 h y 20–23 h
        key = (d, slot(h))
        a = acc.setdefault(key, {"sh": [], "tp": [], "sd": [], "ws": [], "wd": []})
        ws = num(media[j]); a["ws"].append(ws * KN if (ws is not None and kn) else ws)
        a["wd"].append(deg(dirs[0][j])); a["sh"].append(num(alt[j])); a["tp"].append(num(per[j])); a["sd"].append(deg(dirs[1][j]))
    out = []
    for (d, s), a in sorted(acc.items()):
        r = {"src": "Wisuki", "date": d, "slot": s, "sh": mean(a["sh"], 2), "tp": mean(a["tp"], 0), "sd": circ(a["sd"]), "ws": mean(a["ws"], 1), "wd": circ(a["wd"])}
        out.append({k: v for k, v in r.items() if v is not None})
    return out


def main(outp):
    today = (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(hours=3)).date()
    web, log = {}, []
    for key, srcs in SOURCES.items():
        rows = []
        for src, url in srcs.items():
            try:
                html = fetch(url)
                got = parse_surf_forecast(html) if src == "Surf-forecast" else parse_wisuki(html, today)
                got = [r for r in got if r["date"] >= today.isoformat()]
                rows += got
                log.append(f"{key} {src}: {len(got)} franjas")
            except Exception as e:
                log.append(f"{key} {src}: FALLÓ ({e})")
        web[key] = rows
    print("\n".join(log))
    if not any(web.values()):
        print("No se pudo leer ninguna fuente: web.json queda como estaba.")
        return
    web["_meta"] = {"updated_utc": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%MZ"), "log": log}
    json.dump(web, open(outp, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "web.json")

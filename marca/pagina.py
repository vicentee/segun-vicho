#!/usr/bin/env python3
"""Genera marca/index.html: la hoja del sistema del ícono. Uso: python3 marca/pagina.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from icono import icon, TOKENS

D = pathlib.Path(__file__).parent


def sized(svg, px):
    return svg.replace('width="64" height="64"', f'width="{px}" height="{px}"', 1)


def uniq(svg, tag):  # cada SVG inline necesita su propio id de recorte
    return svg.replace('id="t"', f'id="t{tag}"').replace("url(#t)", f"url(#t{tag})")


n = 0
def I(px, **kw):
    global n; n += 1
    return uniq(sized(icon(**kw), px), n)


# construcción: ícono grande + grilla de 8 unidades + anotaciones
grid = "".join(f'<line x1="{v}" y1="0" x2="{v}" y2="64" /><line x1="0" y1="{v}" x2="64" y2="{v}" />' for v in range(8, 64, 8))
construction = f'''<svg viewBox="-4 -7 92 76" width="100%" role="img" aria-label="Construcción del ícono sobre una grilla de 64 unidades">
  <g>{uniq(icon(level=3), "c").replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">', "").replace("</svg>", "")}</g>
  <g stroke="#FFFFFF" stroke-opacity=".28" stroke-width=".18">{grid}</g>
  <rect x="0" y="0" width="64" height="64" rx="14" fill="none" stroke="var(--accent)" stroke-width=".35" stroke-dasharray="1 1"/>
  <g fill="none" stroke="var(--accent)" stroke-width=".4"><line x1="0" y1="38" x2="64" y2="38"/></g>
  <g font-family="IBM Plex Mono, monospace" font-size="2.6" fill="var(--ink)">
    <text x="32" y="-2" text-anchor="middle">aguja · bloque · muesca</text>
    
    <text x="66" y="4" >r 14</text>
    <text x="66" y="42">agua</text><text x="66" y="51">espuma</text>
  </g>
</svg>'''

swatches = [("oceano", "Ultramar", "Fondo. Un solo campo de color plano, el mismo azul de los datos del reporte."),
            ("granito", "Papel", "La roca. Blanco cálido, como la piedra cubierta de guano."),
            ("agua", "Agua", "La línea de mar que corta la base de la roca."),
            ("espuma", "Espuma", "La reventazón delante de la roca."),
            ("oceano_noche", "Noche", "Fondo de la variante oscura.")]
sw = "".join(f'<div class="sw"><i style="background:{TOKENS[k]}"></i><b>{name}</b><code>{TOKENS[k]}</code><span>{desc}</span></div>' for k, name, desc in swatches)

levels = [(1, 16, "≤ 20 px · pestaña del navegador", "La roca y la línea de agua. A 16 píxeles basta la aguja para reconocerla."),
          (2, 32, "≤ 48 px · favoritos, barra de tareas", "Entra la espuma delante de la roca."),
          (3, 180, "> 48 px · pantalla de inicio", "Segunda línea de espuma, más tenue.")]
lv = "".join(f'''<div class="lv"><div class="lv-art"><div class="real">{I(px if px < 64 else 72, level=l)}</div>
  {"<div class='zoom'>" + I(112, level=l) + "</div>" if px < 64 else ""}</div>
  <b>Nivel {l}</b><span class="mono">{t}</span><p>{d}</p></div>''' for l, px, t, d in levels)

variants = [("mar", dict(level=3), "Mar", "La principal."), ("noche", dict(level=3, theme="noche"), "Noche", "Sobre fondos oscuros."),
            ("mono", dict(level=3, theme="mono"), "Una tinta", "Para máscaras e íconos del sistema."),
            ("mask", dict(level=3, rounded=False), "Adaptable", "Android recorta la forma: todo lo importante vive en el círculo central.")]
va = "".join(f'''<div class="va"><div class="va-art">{I(120, **kw)}{"<svg class='safe' viewBox='0 0 64 64'><circle cx='32' cy='32' r='25.6' fill='none' stroke='#F0913A' stroke-width='.6' stroke-dasharray='2 1.5'/></svg>" if k == "mask" else ""}</div>
  <b>{t}</b><span>{d}</span></div>''' for k, kw, t, d in variants)

html = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Ícono · Según Vicho</title>
<link rel="icon" type="image/svg+xml" href="../icons/icono.svg"><link rel="icon" type="image/png" sizes="32x32" href="../icons/favicon-32.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#FFFFFF;--panel:#F3F5F4;--ink:#0D1B26;--muted:#5E6B75;--grid:#E2E7EB;--accent:#F0913A;
  --f-head:"IBM Plex Sans Condensed","Arial Narrow",sans-serif;--f-body:"IBM Plex Sans",system-ui,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,monospace}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0C1117;--panel:#151C24;--ink:#E6EBEF;--muted:#8C99A4;--grid:#232D37;color-scheme:dark}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--f-body)}}
.wrap{{max-width:880px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-left)) 64px;display:flex;flex-direction:column;gap:44px}}
header{{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center;border-bottom:2px solid var(--ink);padding-bottom:20px}}
h1{{font:700 34px/1.05 var(--f-head);margin:0}} h2{{font:600 21px/1.2 var(--f-head);margin:0 0 6px}}
.lead{{margin:6px 0 0;color:var(--muted);max-width:56ch}} .sub{{margin:0 0 16px;color:var(--muted);max-width:62ch;font-size:14px}}
.mono,code{{font-family:var(--f-mono);font-size:12px}}
.src{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
.src div{{background:var(--panel);border-radius:8px;padding:14px}} .src b{{display:block;font:600 16px var(--f-head)}} .src span{{font-size:13.5px;color:var(--muted)}}
.cons{{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:24px;align-items:center}}
.cons ul{{margin:0;padding-left:18px;font-size:14px}} .cons li+li{{margin-top:6px}}
.lvs{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}
.lv-art{{height:132px;display:flex;align-items:flex-end;gap:14px;border-bottom:1px solid var(--grid);padding-bottom:12px;margin-bottom:10px}}
.zoom svg{{image-rendering:pixelated}} .lv b,.va b{{display:block;font:600 16px var(--f-head)}} .lv p{{margin:4px 0 0;font-size:13.5px;color:var(--muted)}} .lv .mono{{color:var(--muted)}}
.sws{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}}
.sw{{display:grid;grid-template-columns:40px 1fr;column-gap:10px;align-items:center}} .sw i{{grid-row:span 3;width:40px;height:40px;border-radius:8px;box-shadow:inset 0 0 0 1px rgba(127,127,127,.25)}}
.sw b{{font:600 14px var(--f-head)}} .sw code{{color:var(--muted)}} .sw span{{font-size:12.5px;color:var(--muted);line-height:1.35}}
.vas{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}} .va-art{{position:relative;width:120px;height:120px;margin-bottom:8px}} .va-art .safe{{position:absolute;inset:0;width:120px;height:120px}} .va span{{font-size:13px;color:var(--muted)}}
.ctx{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:18px}}
.tab{{background:var(--panel);border-radius:10px;padding:10px 10px 0}} .tab .bar{{display:flex;gap:6px}}
.tab .t{{display:flex;align-items:center;gap:8px;background:var(--bg);border-radius:8px 8px 0 0;padding:8px 12px;font-size:13px;max-width:240px}}
.tab .t.off{{background:transparent;color:var(--muted)}} .tab .url{{background:var(--bg);margin:0 -10px;padding:10px 14px;font:12px var(--f-mono);color:var(--muted);border-top:1px solid var(--grid)}}
.phone{{background:linear-gradient(165deg,#9CC2D6 0%,#5E8FA8 55%,#C9B88F 100%);border-radius:22px;padding:22px 18px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px 10px;justify-items:center}}
.app{{display:flex;flex-direction:column;align-items:center;gap:5px;font-size:11px;color:#fff}} .app i{{width:52px;height:52px;border-radius:13px;background:rgba(255,255,255,.14);display:block}} .app svg{{border-radius:13px}}
.files{{font:13px/1.8 var(--f-mono);columns:2;color:var(--muted)}}
@media (max-width:640px){{header{{grid-template-columns:1fr}} .src,.lvs,.cons,.ctx{{grid-template-columns:1fr}} .vas{{grid-template-columns:repeat(2,1fr)}} .files{{columns:1}}}}
</style></head><body><div class="wrap">
<header>{I(112, level=3)}<div><h1>Según Vicho · ícono</h1><p class="lead">La roca de Matanzas: un bloque anguloso, una muesca y la aguja. Una silueta que se reconoce incluso a 16 píxeles.</p></div></header>

<section><h2>De dónde viene</h2><p class="sub">Una sola referencia, reducida a su contorno.</p>
<div class="src"><div><b>El bloque</b><span>La masa baja e irregular que sube hacia la derecha.</span></div>
<div><b>La muesca</b><span>El corte que separa el bloque de la aguja: es lo que hace única la silueta.</span></div>
<div><b>La aguja</b><span>La columna vertical, la parte más alta. A tamaño chico, es lo último que se pierde.</span></div></div></section>

<section><h2>Construcción</h2><p class="sub">Grilla de 64 × 64 unidades. La roca se centra y se apoya en la línea de agua.</p>
<div class="cons">{construction}<ul>
<li><b>Esquinas</b> de 14 unidades, iguales a los íconos de app de iOS y Android.</li>
<li><b>La roca</b> es una sola silueta de 31 puntos, escalada según el nivel (70%, 68% y 68% del ancho) y centrada.</li>
<li><b>La línea de agua</b> corta la base de la roca y se extiende 6 unidades a cada lado.</li>
<li><b>La espuma</b> son trazos rectos y desplazados, nunca curvos: así no se lee como una cara.</li>
<li><b>Sin adornos:</b> colores planos, sin degradados ni sombras. Lo orgánico lo pone el contorno irregular de la roca.</li></ul></div></section>

<section><h2>Un ícono, tres niveles</h2><p class="sub">No se achica el mismo dibujo: se quita detalle según el tamaño, para que a 16 píxeles siga leyéndose la punta y las olas.</p>
<div class="lvs">{lv}</div></section>

<section><h2>Paleta</h2><p class="sub">Cinco tokens. Azul y papel hacen todo el trabajo; el resto son matices de los mismos dos.</p><div class="sws">{sw}</div></section>

<section><h2>Variantes</h2><div class="vas">{va}</div></section>

<section><h2>En contexto</h2><div class="ctx">
<div class="tab"><div class="bar"><div class="t">{I(16, level=1)}<span>Según Vicho</span></div><div class="t off">Windguru</div></div><div class="url">vicentee.github.io/segun-vicho</div></div>
<div class="phone">{"".join('<div class="app"><i></i>&nbsp;</div>' for _ in range(2))}<div class="app">{I(52, level=3)}<span>Según Vicho</span></div><div class="app"><i></i>&nbsp;</div></div>
</div></section>

<section><h2>Archivos</h2><div class="files">icons/icono.svg · favicon moderno<br>icons/favicon-32.png · favicon-16.png<br>icons/apple-touch-icon.png · 180 px<br>icons/icon-192.png · icon-512.png<br>icons/icon-maskable-512.png · Android<br>icons/icono-noche.svg · icono-mono.svg<br>marca/icono.py · genera todo desde la regla<br>manifest.webmanifest · instalar como app</div></section>
</div></body></html>'''
(D / "index.html").write_text(html)
print("marca/index.html listo")

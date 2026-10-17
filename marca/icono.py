#!/usr/bin/env python3
"""Sistema del ícono de Según Vicho: la roca de Matanzas.

La silueta de la roca (un bloque bajo e irregular que sube hacia la derecha, una muesca y la aguja vertical)
es la base de todo. Una sola regla genera los tamaños; a menor tamaño, menos detalle:

  nivel 1 (≤ 20 px)   roca + línea de agua
  nivel 2 (≤ 48 px)   + línea de ola
  nivel 3 (> 48 px)   + sol

Uso:  python3 marca/icono.py   (escribe los SVG en marca/ y el logo del encabezado en marca/logo.svg)
"""
import pathlib

TOKENS = {
    "oceano": "#123A47", "oceano_noche": "#0A1F26", "granito": "#ECE6D8", "agua": "#7FAEC2",
    "espuma": "#F4F1E6", "sol": "#F0913A", "tinta": "#0D1B26",
}

# silueta de la roca en unidades propias: 88 de ancho, base en y = 40; bloque anguloso, muesca y aguja hasta y = 6,5
ROCK = [(0, 40), (2, 37), (6, 35), (9, 35.5), (11, 32), (16, 30), (18, 27), (24, 26), (27, 23), (33, 22),
        (38, 20), (44, 20.5), (48, 19), (53, 20), (56, 22), (58, 24), (59, 30), (61, 34), (63, 33), (64, 28),
        (65, 20), (66, 14), (68, 9), (71, 6.5), (74, 7), (76, 10), (77, 16), (79, 24), (81, 32), (84, 37), (88, 40)]


def rock_path(scale, ox, base_y):
    pts = [(ox + x * scale, base_y - (40 - y) * scale) for x, y in ROCK]
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def icon(level=3, theme="mar", rounded=True):
    """theme: mar · noche · mono (una tinta, para máscaras)."""
    T = dict(TOKENS)
    if theme == "noche":
        T["oceano"] = T["oceano_noche"]
    mono = theme == "mono"
    c = lambda k: "#FFFFFF" if mono else T[k]
    bg = T["tinta"] if mono else T["oceano"]
    rr = 14 if rounded else 0
    scale = {1: 0.68, 2: 0.66, 3: 0.64}[level]
    width = 88 * scale
    ox, base = (64 - width) / 2, {1: 44, 2: 41, 3: 41}[level]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">',
           f'<defs><clipPath id="t"><rect width="64" height="64" rx="{rr}"/></clipPath></defs>',
           f'<g clip-path="url(#t)"><rect width="64" height="64" fill="{bg}"/>']
    if level >= 3:
        out.append(f'<circle cx="17" cy="17" r="4.4" fill="{c("sol")}"/>')
    out.append(f'<path d="{rock_path(scale, ox, base)}" fill="{c("granito")}" stroke="{c("granito")}" stroke-width=".6" stroke-linejoin="round"/>')
    # línea de agua: el mar que corta la base de la roca
    lw = {1: 3.2, 2: 2.2, 3: 2.0}[level]
    out.append(f'<line x1="{ox - 6:.1f}" y1="{base + lw / 2:.1f}" x2="{ox + width + 6:.1f}" y2="{base + lw / 2:.1f}" stroke="{c("agua")}" stroke-width="{lw}" stroke-linecap="round"/>')
    # espuma: trazos rectos y desplazados, como la reventazón delante de la roca
    if level >= 2:
        y = base + 9
        out.append(f'<line x1="12" y1="{y}" x2="{38 if level == 3 else 50}" y2="{y}" stroke="{c("espuma")}" stroke-width="{3.2 if level == 2 else 2.8}" stroke-linecap="round"/>')
        if level >= 3:
            out.append(f'<line x1="30" y1="{y + 6}" x2="52" y2="{y + 6}" stroke="{c("espuma")}" stroke-width="2.8" stroke-linecap="round" opacity=".6"/>')
    out.append("</g></svg>")
    return "".join(out)


def logo():
    """Logo del encabezado: sin recuadro, colores tomados del tema de la página (roca en tinta, mar en azul)."""
    return ('<svg viewBox="0 0 140 56" width="140" height="56" role="img" aria-label="Según Vicho">'
            '<defs><linearGradient id="lgf" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".18" stop-color="#fff"/><stop offset=".82" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<mask id="lmf" maskUnits="userSpaceOnUse" x="0" y="0" width="140" height="56"><rect width="140" height="56" fill="url(#lgf)"/></mask></defs>'
            '<circle cx="128" cy="12" r="4.5" fill="var(--sol)"/>'
            f'<path d="{rock_path(1.05, 14, 42)}" fill="var(--ink)" stroke="var(--ink)" stroke-width=".8" stroke-linejoin="round"/>'
            '<g mask="url(#lmf)" fill="none" stroke="var(--blue)" stroke-linecap="round">'
            '<line x1="2" y1="42.8" x2="138" y2="42.8" stroke-width="1.6"/>'
            '<line x1="16" y1="49" x2="72" y2="49" stroke-width="2.4" opacity=".6"/>'
            '<line x1="58" y1="54" x2="118" y2="54" stroke-width="2.4" opacity=".32"/></g></svg>')


if __name__ == "__main__":
    d = pathlib.Path(__file__).parent
    for name, kw in {"icono-16.svg": dict(level=1), "icono-32.svg": dict(level=2), "icono.svg": dict(level=3),
                     "icono-noche.svg": dict(level=3, theme="noche"), "icono-mono.svg": dict(level=3, theme="mono"),
                     "icono-maskable.svg": dict(level=3, rounded=False)}.items():
        (d / name).write_text(icon(**kw))
    (d / "logo.svg").write_text(logo())
    print("SVG listos en", d)

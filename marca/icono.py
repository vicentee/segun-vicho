#!/usr/bin/env python3
"""Sistema del ícono de Según Vicho.

Una sola regla genera todos los tamaños: la punta de Puertecillo (un promontorio con pinos que entra al mar)
y las líneas de ola que la rodean al doblar la punta, como una izquierda larga. A menor tamaño, menos detalle:

  nivel 1 (≤ 20 px)   promontorio + 2 olas gruesas
  nivel 2 (≤ 48 px)   + 3 olas + sol
  nivel 3 (> 48 px)   + 4 olas + pinos y roca en la punta + playa

Grilla de 64 × 64 unidades, esquinas de 14 unidades. Uso:  python3 marca/icono.py  (escribe los SVG en marca/)
"""
import pathlib

TOKENS = {  # paleta: océano y pino del club, arena y sol de la playa
    "oceano": "#0F3B45", "oceano_noche": "#0A1F26", "pino": "#5E8A55", "pino_sombra": "#3F6B40",
    "ola": "#F4F1E6", "arena": "#E3D3AE", "sol": "#F0913A", "tinta": "#0D1B26",
}


def icon(level=3, theme="mar", rounded=True):
    """theme: mar (fondo océano) · noche (fondo oscuro) · mono (una tinta, para máscaras)."""
    T = dict(TOKENS)
    if theme == "noche":
        T["oceano"] = T["oceano_noche"]
    mono = theme == "mono"
    bg = T["tinta"] if mono else T["oceano"]
    fg = lambda k: "#FFFFFF" if mono else T[k]
    stroke = {1: 5.0, 2: 3.6, 3: 3.0}[level]
    rr = 14 if rounded else 0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">',
           f'<defs><clipPath id="t"><rect width="64" height="64" rx="{rr}"/></clipPath></defs>',
           f'<g clip-path="url(#t)"><rect width="64" height="64" fill="{bg}"/>']
    # arena: franja curva abajo a la izquierda (la playa larga de Puertecillo)
    if level >= 3:
        out.append(f'<path d="M-2 47 Q14 50 28 66 L-2 66 Z" fill="{fg("arena")}" opacity="{0.9 if not mono else 0.35}"/>')
    # olas: líneas largas y paralelas que nacen en la punta y corren hacia la derecha, como una izquierda que pelea
    # la ola de adentro es la más blanca (espuma); las de afuera se apagan hacia mar adentro
    sets = {1: [0, 2], 2: [0, 1, 2], 3: [0, 1, 2, 3]}[level]
    gap = {1: 10.5, 2: 8.5, 3: 7.6}[level]
    for j, i in enumerate(sets):
        sx, sy = 21 + i * 1.5, 34 + i * gap          # nace pegada a la punta y se aleja
        ex, ey = 68, 30 + i * gap * 1.08             # sale por el borde derecho, levemente más alta
        cx, cy = 40, 27 + i * gap                     # curva convexa: la ola dobla la punta
        op = 1 - j * (0.18 if level >= 2 else 0.3)
        out.append(f'<path d="M{sx:.1f} {sy:.1f} Q{cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}" fill="none" stroke="{fg("ola")}" '
                   f'stroke-width="{stroke}" stroke-linecap="round" opacity="{op:.2f}"/>')
    # promontorio: cresta alta a la izquierda que baja hasta la punta rocosa
    land = "M-2 6 L6 6 Q14 5 18 12 Q21 18 24 26 Q25.5 30 22 31.5 Q14 34 6 36 L-2 38 Z"
    out.append(f'<path d="{land}" fill="{fg("pino")}"/>')
    if not mono:  # ladera en sombra hacia el mar
        out.append('<path d="M18 12 Q21 18 24 26 Q25.5 30 22 31.5 Q19 26 16 18 Z" fill="%s"/>' % T["pino_sombra"])
    if level >= 3:  # roca en la punta y pinos en la cresta
        out.append(f'<path d="M21 31 Q25 29.5 27 31.5 Q25 33.5 21.5 33 Z" fill="{fg("pino_sombra") if not mono else "#FFFFFF"}"/>')
        for x, h, y in [(4, 5.5, 7.2), (8.5, 6.5, 7.0), (13, 5.8, 7.6)]:
            out.append(f'<path d="M{x-2.6:.1f} {y} L{x:.1f} {y-h:.1f} L{x+2.6:.1f} {y} Z" fill="{fg("pino")}"/>')
    # sol: acento naranjo arriba a la derecha (la estrella del escudo, simplificada)
    if level >= 2:
        r = 5.2 if level == 2 else 4.6
        out.append(f'<circle cx="49" cy="15" r="{r}" fill="{fg("sol")}"/>')
    out.append("</g></svg>")
    return "".join(out)


if __name__ == "__main__":
    d = pathlib.Path(__file__).parent
    for name, kw in {"icono-16.svg": dict(level=1), "icono-32.svg": dict(level=2), "icono.svg": dict(level=3),
                     "icono-noche.svg": dict(level=3, theme="noche"), "icono-mono.svg": dict(level=3, theme="mono"),
                     "icono-maskable.svg": dict(level=3, rounded=False)}.items():
        (d / name).write_text(icon(**kw))
    print("SVG listos en", d)

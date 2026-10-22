# Según Vicho

Reporte de surf para **Matanzas, Puertecillo y Topocalma** (VI Región, Chile). Dice adónde ir, a qué hora y qué esperar, con la mediana de varias fuentes en vez de confiar en una sola.

**En línea:** https://vicentee.github.io/segun-vicho/

## Qué muestra

- **Veredicto:** spot, ventana y nivel (épico, bueno, igual sale, no pasa), con los cuatro datos que deciden: ola en la rompiente, período, energía (kJ, misma escala que Surf-Forecast) y viento, la tabla sugerida y el botón a la cámara cuando el spot tiene una.
- **Cómo cambió:** si el pronóstico de cada spot mejoró o empeoró respecto de la corrida de hace 6 y 24 horas, y por qué (ola, viento o período).
- **La semana:** un calendario de horas: cada día es una barra de 6 a 20 h coloreada según cómo está cada hora en el mejor spot, con la ventana en ámbar y el mejor día marcado. A la derecha, el puntaje de 0 a 10 de cada spot. Los días 8 a 10 son tendencia.
- **El día:** gráfico hora a hora de ola, swell, viento y marea, con un punto que marca la hora actual. Debajo, una tabla cada 3 horas (nivel, ola, período, energía, viento y marea) con las mismas columnas todos los días, y los otros spots.
- **Preguntar (?):** chat que responde con el mismo pronóstico: cómo viene la semana, qué día y spot conviene, y qué tabla usar (tipo, largo, ancho y litros) según estatura, peso, nivel y tablas que usas. Son reglas, sin servidor ni IA externa.
- **Por qué:** qué dijo cada fuente, cuáles se descartaron y la confianza de la recomendación.

## Cómo calcula

1. Trae modelos de oleaje (NOAA GFS-Wave, Météo-France, DWD GWAM) y de viento (ECMWF, NOAA GFS, DWD ICON, Météo-France, UK Met Office, Canadá GEM, Japón JMA) desde [Open-Meteo](https://open-meteo.com), más lo que se pueda leer de Wisuki, Surf-forecast, Breakfinder, Lineup y Surfline (`web.json`).
2. Por cada hora y variable calcula la mediana y la dispersión robusta (MAD), descarta lo que se aleja demasiado y usa la mediana de lo que queda.
3. Guarda las corridas de las últimas 30 horas (`hist` dentro de `index.html`) para comparar el pronóstico actual con el anterior.
4. Estima el tamaño en la rompiente y un puntaje por spot según tamaño, período, dirección del swell, viento respecto de la orientación de cada punta, mar de viento y marea.

| Archivo | Qué hace |
|---|---|
| `build.py` | Trae los datos, corta outliers, calcula medianas y escribe `index.html` |
| `template.html` | La página: diseño, puntaje y textos |
| `scrape.py` | Lee Surf-forecast y Wisuki y escribe `web.json` |
| `web.json` | Valores leídos de los sitios web en la última corrida |
| `marca/` | Sistema del ícono (la roca de Matanzas): `icono.py` genera los SVG, `index.html` es la hoja de marca |
| `icons/`, `manifest.webmanifest` | Íconos y datos para instalar la app en el celular |

## Actualización

A las 00:15, 06:15, 12:15 y 18:15 (hora de Chile) la GitHub Action `actualizar.yml` lee Surf-forecast y Wisuki (`scrape.py` → `web.json`), trae los modelos de Open-Meteo y reconstruye `index.html` (`build.py`). También corre cada vez que cambia `template.html`, `build.py` o `scrape.py`. Si `web.json` tiene más de 36 horas, se ignora y la mediana usa solo los modelos.

```bash
python3 -I scrape.py web.json
python3 -I build.py template.html web.json index.html
```

## Aviso

El tamaño en la rompiente, el nivel y la tabla sugerida son estimaciones propias.

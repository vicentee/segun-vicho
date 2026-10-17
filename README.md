# Según Vicho

Reporte de surf para **Matanzas, Puertecillo y Topocalma** (Chile central). Dice adónde ir, a qué hora y qué esperar, con la mediana de varias fuentes en vez de confiar en una sola.

## Qué muestra

- **Veredicto:** spot, ventana y nivel ("épico", "bueno", "igual sale", "no pasa"), con ola en metros, período, potencia y viento.
- **La semana:** puntaje, hora y tamaño por spot y día; el borde ámbar marca el mejor de cada día.
- **El día por tramos:** cómo evoluciona la ola y el viento hora a hora, cuándo se ensucia y si hay una segunda ventana.
- **Por qué:** qué dijo cada fuente, cuáles se descartaron y la confianza de la recomendación.

## Cómo calcula

1. Trae modelos de oleaje (NOAA GFS-Wave, Météo-France, DWD GWAM) y de viento (ECMWF, NOAA GFS, DWD ICON, Météo-France, UK Met Office, Canadá GEM, Japón JMA) desde [Open-Meteo](https://open-meteo.com), más lo que se pueda leer de Wisuki, Surf-forecast, Breakfinder, Lineup y Surfline (`web.json`).
2. Por cada hora y variable calcula la mediana y la dispersión robusta (MAD), descarta los valores que se alejan demasiado y usa la mediana de lo que queda.
3. Estima el tamaño en la rompiente y un puntaje por spot según tamaño, período, dirección del swell, viento respecto de la orientación de cada punta, mar de viento y marea.

Todo está en [`build.py`](build.py) (datos) y [`template.html`](template.html) (página).

## Actualización

Una GitHub Action reconstruye `index.html` a las 00:15 y 12:15 (hora de Chile) y cada vez que cambia `web.json`.

```bash
python3 -I build.py template.html web.json index.html
```

## Aviso

El tamaño en la rompiente, el puntaje y la tabla sugerida son estimaciones. Revisa la cámara o el reporte en vivo antes de manejar.

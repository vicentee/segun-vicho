# Según Vicho

Reporte de surf para **Matanzas, Puertecillo y Topocalma** (VI Región, Chile). Dice adónde ir, a qué hora y qué esperar, con la mediana de varias fuentes en vez de confiar en una sola.

**En línea:** https://vicentee.github.io/segun-vicho/

## Qué muestra

- **Veredicto:** spot, ventana y nivel (épico, bueno, igual sale, no pasa), con ola en la rompiente, swell, período, potencia y viento, la tabla sugerida y el botón a la cámara cuando el spot tiene una.
- **Cómo cambió:** si el pronóstico de cada spot mejoró o empeoró respecto de la corrida de hace 6 y 24 horas, y por qué (ola, viento o período).
- **La semana:** puntaje, hora y tamaño por spot y día. El borde ámbar marca el mejor de cada día. Los días 8 a 10 son tendencia.
- **El día:** gráfico hora a hora de ola, swell, viento y marea, con un punto que marca la hora actual. Debajo, los tramos del día y los otros spots.
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
| `web.json` | Valores leídos de los sitios web en la última corrida |
| `marca/` | Sistema del ícono (la roca de Matanzas): `icono.py` genera los SVG, `index.html` es la hoja de marca |
| `icons/`, `manifest.webmanifest` | Íconos y datos para instalar la app en el celular |

## Actualización

A las 00:00, 06:00, 12:00 y 18:00 (hora de Chile) una tarea programada lee los sitios web, actualiza `web.json` y reconstruye `index.html`. Como respaldo, la GitHub Action `actualizar.yml` reconstruye la página 15 minutos después de cada horario y cada vez que cambia `template.html`, `build.py` o `web.json`.

```bash
python3 -I build.py template.html web.json index.html
```

## Aviso

El tamaño en la rompiente, el nivel y la tabla sugerida son estimaciones propias.

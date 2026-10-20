# Tablero ENCC — Pantallas y Cultura Digital en Argentina

Tablero interactivo hecho en [Dash](https://dash.plotly.com/) que analiza los datos de la
**Encuesta Nacional de Consumos Culturales (ENCC 2022)**, con foco en actividades que
implican el uso de pantallas: cine, TV, videojuegos, redes sociales y noticias digitales.

Los resultados se muestran ponderados según el peso muestral (`peso`) de cada encuestado,
y pueden filtrarse por región, género, nivel socioeconómico y grupo etario.

## Estructura del proyecto

```
tablero_encc/
├── app.py                  # Layout principal: sidebar, filtros globales y routing de páginas
├── pages/
│   ├── home.py              # Página "Inicio": gráficos generales de consumo
│   ├── tv.py                 # Página "TV"
│   ├── cine.py                # Página "Cine"
│   ├── redes.py                # Página "Redes Sociales"
│   └── videojuegos.py           # Página "Videojuegos"
├── src/
│   ├── data.py               # Carga del CSV y aplicación de filtros
│   └── metrics.py            # Cálculo de indicadores (representatividad, perfiles únicos, etc.)
├── assets/
│   └── styles.css            # Estilos del tablero (cargados automáticamente por Dash)
├── data/
│   └── encc_looker_base.csv   # Dataset base
├── requirements.txt
└── .gitignore
```

## Cómo correrlo

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Por defecto levanta en `http://127.0.0.1:8051`.

## Datos

El dataset (`data/encc_looker_base.csv`) está en formato largo: una fila por combinación
de persona/actividad/dimensión/valor, con las siguientes columnas:

- `personaid`, `peso`: identificador de encuestado y su peso muestral
- `actividad`: Cine, TV, Videojuegos, Redes sociales, Noticias digitales
- `dimension` / `valor`: por ejemplo `dimension="Consume"` / `valor="Sí"`, o
  `dimension="Frecuencia"` / `valor="Semanal"`
- `region`, `provincia`, `genero`, `edad`, `grupos_edad`, `nse_3`: variables sociodemográficas

La variable `flag_consumo` (derivada en `src/data.py`) marca si esa persona consume esa
actividad, usada como base para la mayoría de los gráficos.


## Deploy con Docker

```bash
docker build -t tablero-encc .
docker run -p 8000:8000 tablero-encc
```

La app queda en `http://localhost:8000`. Para usar otro puerto: `docker run -e PORT=9000 -p 9000:9000 tablero-encc`.

Sin Docker: `pip install -r requirements.txt` y `gunicorn app:server --bind 0.0.0.0:8000 --timeout 120`
(siempre desde la raíz del proyecto, porque el CSV se lee por ruta relativa `data/encc_looker_base.csv`;
se puede cambiar con la variable `DATA_PATH`).

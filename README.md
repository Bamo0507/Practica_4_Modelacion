# **Simulador de Logística del Valle**

Aplicación local en Dash para comparar las rutas actuales con Dijkstra, A* y Hill Climbing. Permite seleccionar 8, 10 o 12 camiones y ejecutar cinco repeticiones emparejadas de cada configuración.

## **Preparación**

Desde la carpeta del proyecto, con Python 3.11 o posterior:

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt

## **Ejecutar la aplicación**

    .venv/bin/python -m flask --app src.app:server run --host 127.0.0.1 --port 8050

Abrir [la aplicación local](http://127.0.0.1:8050). El servidor se mantiene limitado al equipo local; se detiene con Ctrl+C. No se inicia al importar los módulos.

## **Pruebas**

    .venv/bin/python -m unittest discover -s tests -v

## **Organización**

- **data/matriz_logistica.csv**: matriz original, sin modificar.
- **src/graph**: objetos del grafo y lectura del CSV.
- **src/algorithms**: los tres algoritmos de rutas.
- **src/simulation**: llegadas, viajes, disponibilidad de vehículos y repeticiones.
- **src/ui**: controles, grafo, tablas y gráficas.
- **src/app.py**: conexión entre Dash y el motor.
- **assets/styles.css**: estilos de la interfaz.
- **media/**: capturas de la aplicación e imágenes del informe.
- **docs/informe.md**: informe académico.



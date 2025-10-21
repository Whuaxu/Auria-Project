# Simulador de vehículo (NATS producer/subscriber)

Resumen
-------
Pequeño proyecto docente que implementa un simulador de vehículo en un circuito marcado por "conos". Usa la arquitectura productor/subscriptor con NATS y serialización con msgspec.

Archivos principales 
- `simulator.py` — simula la física del vehículo, publica `simulator.state` y `simulator.cones`, y se suscribe a `vehicle.controls`.
- `controller.py` — recibe estado y conos y publica `vehicle.controls` (algoritmo de conducción, simple por defecto).
- `visualizer.py` — visualización en tiempo real (matplotlib) de posición, orientación y conos.
- `starting_pack.py` — mini-librería para facilitar NATS (decoradores `@subscribe`, `@timer`, `publish`, `start`).
- `messages.py` — definiciones de mensajes (msgspec.Struct) usados por los nodos.
- `nats_server.sh` — helper para arrancar un servidor NATS (Docker).
- `run.sh` — script que orquesta: NATS + simulador + controlador + visualizador.
- `requirements.txt` — dependencias Python necesarias.

Objetivo de la entrega
---------------------
- Implementar los tres componentes (simulador, controlador y visualizador) usando NATS y msgspec.
- Que el simulador publique estado y conos, que el controlador publique controles de vehículo y que el visualizador muestre resultados.
- Preparar el proyecto para ejecutarse en un entorno virtual (`requirements.txt`).
- Incluir `run.sh` para lanzar los componentes juntos.

Requisitos
----------
- Python 3.8+ (recomendado 3.10+)
- Docker (recomendado para levantar NATS) o acceso a un servidor NATS
- Instalar dependencias del `requirements.txt`

Instalación rápida (entorno virtual)
-----------------------------------
Unix / macOS (bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Levantar el servidor NATS
-------------------------
Con Docker:
```bash
docker run -it --rm -p 4222:4222 -p 8222:8222 nats:latest --addr=0.0.0.0 --http_port=8222
```
O usando el helper (si tienes bashm, es el que recomiendo):
```bash
./nats_server.sh
```

Ejecutar el sistema
-------------------
Con `run.sh` (bash/WSL/Git Bash):
```bash
./run.sh
```

O manualmente en 3 terminales (útil para depuración):
- Terminal A (simulador): `python simulator.py`
- Terminal B (controlador): `python controller.py`
- Terminal C (visualizador): `python visualizer.py`

Variables de entorno útiles
--------------------------
- `NATS_URL` — URL del servidor NATS (por defecto `nats://127.0.0.1:4222`)

Arquitectura y mensajes
-----------------------
- `starting_pack.py` expone `@subscribe(topic, MessageType)`, `@timer(interval)` y `publish(topic, msg)`.
- `messages.py` define `Controls`, `VehicleState`, `Cone`, `Cones`.
- Topics usados por convención:
  - `simulator.state` — VehicleState (publicado por el simulador)
  - `simulator.cones` — Cones (publicado por el simulador)
  - `vehicle.controls` — Controls (publicado por el controlador)

Depuración rápida
-----------------
- Si obtienes `ConnectionRefusedError` al conectar a NATS: revisa que NATS esté corriendo y que el puerto 4222 esté escuchando (usa `netstat` o `Test-NetConnection`).
- Si `run.sh` falla en Windows con `--net=host`, lanza NATS con `-p 4222:4222 -p 8222:8222`.
- Problemas de finales de línea (LF/CRLF): normaliza los scripts `.sh` a LF si ejecutas en WSL/contenedores.

Consejos finales
----------------
- Empieza por levantar NATS y ejecutar el simulador; luego añade visualizador y finalmente el controlador autónomo.



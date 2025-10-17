import math
from typing import List, Optional
import numpy as np
from msgspec import Struct
from starting_pack import subscribe, start, timer
from messages import Controls, VehicleState, Cone, Cones
import matplotlib.pyplot as plt
import asyncio


# ============================
#   Variables globales
# ============================

latest_state: Optional[VehicleState] = None
latest_cones: Optional[Cones] = None


# ============================
#   Suscripciones NATS
# ============================

@subscribe("simulator.state", VehicleState)
async def state_callback(msg: VehicleState):
    global latest_state
    latest_state = msg


@subscribe("simulator.cones", Cones)
async def cones_callback(msg: Cones):
    global latest_cones
    latest_cones = msg


# ============================
#   Visualización
# ============================

@timer(0.05) # Actualiza  cada 50 ms
async def update_plot():

    global latest_state, latest_cones

    if not hasattr(update_plot, "initialized"):
        plt.ion()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect("equal", "box")
        ax.set_xlim(-30, 30)
        ax.set_ylim(-20, 20)
        ax.set_title(" Simulador NATS - Visualización en tiempo real")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")

        # Elementos gráficos
        update_plot.fig = fig
        update_plot.ax = ax
        update_plot.scat = ax.scatter([], [], color="orange", label="Conos")
        update_plot.car_plot, = ax.plot([], [], "-k", lw=2, label="Coche")
        update_plot.dir_plot, = ax.plot([], [], "-r", lw=1.5, label="Dirección")
        update_plot.txt = ax.text(-29, 18, "", fontsize=9, color="blue")
        ax.legend()
        update_plot.initialized = True

    if latest_cones is not None:
        xs = [c.x for c in latest_cones.cones]
        ys = [c.y for c in latest_cones.cones]
        update_plot.scat.set_offsets(np.c_[xs, ys])

    if latest_state is not None:
        s = latest_state
        # Coche como linea triangular
        L = 1.5
        W = 0.7
        pts = np.array([
            [L, 0],
            [-L * 0.6, W],
            [-L * 0.6, -W]
        ])
        R = np.array([
            [math.cos(s.yaw), -math.sin(s.yaw)],
            [math.sin(s.yaw),  math.cos(s.yaw)]
        ])
        trans = (R @ pts.T).T + np.array([s.x, s.y])
        # Cerrar el triángulo añadiendo el primer punto al final para que se dibuje correctamente
        xs = np.append(trans[:, 0], trans[0, 0])
        ys = np.append(trans[:, 1], trans[0, 1])
        update_plot.car_plot.set_data(xs, ys)

        # Línea de dirección
        dir_line = np.array([
            [s.x, s.y],
            [s.x + math.cos(s.yaw) * 2.0, s.y + math.sin(s.yaw) * 2.0]
        ])
        update_plot.dir_plot.set_data(dir_line[:, 0], dir_line[:, 1])

        # Texto con estado
        update_plot.txt.set_text(
            f"Velocidad: {s.speed:.2f} m/s\n"
            f"Posición: ({s.x:.1f}, {s.y:.1f})"
        )

    # Redibujar
    update_plot.fig.canvas.draw()
    update_plot.fig.canvas.flush_events()


# ============================
#   Ejecución
# ============================

if __name__ == "__main__":
    
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("[LOG] Visualizador cerrado por el usuario.")

import math
from typing import List, Optional
from msgspec import Struct
from src.starting_pack import subscribe, publish, timer, start
import asyncio
from messages import VehicleState, Controls, Cone, Cones

# ============================
#   Variables globales
# ============================

latest_state: Optional[VehicleState] = None
latest_cones: Optional[Cones] = None

TARGET_SPEED = 6.0  # m/s


# ============================
#   Funciones auxiliares
# ============================

def angle_diff(a: float, b: float) -> float:
    """Devuelve la diferencia de ángulos en el rango [-pi, pi]."""
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return d


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
#   Control principal
# ============================

@timer(0.05)
async def control_loop():
    """Algoritmo de conducción autónoma básico."""
    global latest_state, latest_cones

    if latest_state is None or latest_cones is None:
        return  # Se espera a tener datos

    s = latest_state
    cones = latest_cones.cones

    # Buscar cono objetivo: el más cercano que esté delante del coche
    best_cone = None
    best_dist = float("inf")

    for c in cones:
        dx = c.x - s.x
        dy = c.y - s.y
        dist = math.hypot(dx, dy)
        angle_to = math.atan2(dy, dx)
        angle_diff_to = angle_diff(angle_to, s.yaw)

        # Filtrar conos "delante" (±120°)
        if abs(angle_diff_to) < math.radians(120) and dist > 1.0:
            if dist < best_dist:
                best_cone = c
                best_dist = dist

    if best_cone is None and cones:
        # Si no hay conos delante, ir al más cercano
        for c in cones:
            dx = c.x - s.x
            dy = c.y - s.y
            dist = math.hypot(dx, dy)
            if dist < best_dist:
                best_cone = c
                best_dist = dist

    # Calcular comandos de control
    if best_cone:
        angle_to_target = math.atan2(best_cone.y - s.y, best_cone.x - s.x)
        heading_error = angle_diff(angle_to_target, s.yaw)

        # Direccion de manera proporcional
        K_steer = 1.2
        steer_cmd = max(-1.0, min(1.0, K_steer * heading_error))
    else:
        steer_cmd = 0.0

    # Control proporcional de velocidad
    K_speed = 0.6
    speed_error = TARGET_SPEED - s.speed
    throttle_cmd = max(-1.0, min(1.0, K_speed * speed_error))

    # Enviar controles
    ctrl = Controls(throttle=throttle_cmd, steer=steer_cmd)
    await publish("vehicle.controls", ctrl)


# ============================
#   Ejecución
# ============================

if __name__ == "__main__":
    
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("[LOG] Controlador detenido por el usuario.")

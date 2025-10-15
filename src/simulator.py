import math
import time
from typing import List
import msgspec
from msgspec import Struct
from src.starting_pack import subscribe, publish, timer, start
import asyncio
from messages import VehicleState, Controls, Cone, Cones

# ============================
#   Parámetros simulador
# ============================

PUBLISH_RATE = 20.0  # Hz
DT = 1.0 / PUBLISH_RATE
MAX_ACCEL = 3.0
MAX_BRAKE = 6.0
MAX_SPEED = 10.0
MAX_STEER_ANGLE = math.radians(30)
WHEEL_BASE = 2.5

# Estado inicial del coche
state = VehicleState(x=18.0, y=0.0, yaw=math.pi, speed=0.0, timestamp=time.time())
current_controls = Controls()

# Generar conos en forma de óvalo
cones = Cones(cones=[
    Cone(x=20.0 * math.cos(a), y=8.0 * math.sin(a))
    for a in [i / 20.0 * 2 * math.pi for i in range(20)]
])


# ============================
#   Callbacks y simulación
# ============================

@subscribe("vehicle.controls", Controls)
async def controls_callback(msg: Controls):
    
    global current_controls
    current_controls = msg


@timer(1.0)
async def publish_cones():
    
    await publish("simulator.cones", cones)


@timer(DT)
async def simulate_step():
    
    global state, current_controls

    throttle = max(-1.0, min(1.0, current_controls.throttle))
    steer = max(-1.0, min(1.0, current_controls.steer))

    if throttle >= 0:
        accel = throttle * MAX_ACCEL
    else:
        accel = throttle * MAX_BRAKE  

    # Actualizar velocidad
    state.speed += accel * DT
    state.speed = max(0.0, min(MAX_SPEED, state.speed))

    # Calcular cambio de orientación (yaw rate )
    steer_angle = steer * MAX_STEER_ANGLE
    if abs(steer_angle) > 1e-3 and state.speed > 0.01:
        R = WHEEL_BASE / math.tan(steer_angle)
        yaw_rate = state.speed / R
    else:
        yaw_rate = 0.0

    # Integrar estado
    state.yaw += yaw_rate * DT
    state.x += state.speed * math.cos(state.yaw) * DT
    state.y += state.speed * math.sin(state.yaw) * DT
    state.timestamp = time.time()

    # Publicar estado actual
    await publish("simulator.state", state)


# ============================
#   Ejecución
# ============================

if __name__ == "__main__":
    
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("[LOG] Simulador detenido por el usuario.")

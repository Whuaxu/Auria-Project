import math
from typing import List, Optional
from msgspec import Struct
from starting_pack import subscribe, publish, timer, start
import asyncio
from messages import VehicleState, Controls, Cone, Cones

# ============================
#   Variables globales
# ============================

latest_state: Optional[VehicleState] = None
latest_cones: Optional[Cones] = None

TARGET_SPEED = 6.0  # m/s
# Estado para zigzag
last_target_side: Optional[str] = None  # 'left' or 'right'
last_target_proj: Optional[float] = None  # proyección (avance) del último objetivo


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

    # Buscar cono objetivo: zizaguear (lo que hace es ir por el interior del circuito xd)
    global last_target_side, last_target_proj
    left_candidates = []
    right_candidates = []

    for c in cones:
        dx = c.x - s.x
        dy = c.y - s.y
        dist = math.hypot(dx, dy)
        angle_to = math.atan2(dy, dx)
        angle_diff_to = angle_diff(angle_to, s.yaw)

        # Filtrar conos "delante" (±120°) y a una distancia mínima
        if abs(angle_diff_to) < math.radians(120) and dist > 0.5:
            # Coordenadas en el marco del coche
            x_rel = dx * math.cos(s.yaw) + dy * math.sin(s.yaw)  # adelante+
            y_rel = -(dx * math.sin(s.yaw)) + (dy * math.cos(s.yaw))  # izquierda+
            # Guardamos la proyección (avance) x_rel para medir progreso
            if y_rel < 0:
                right_candidates.append((x_rel, dist, c, y_rel))
            else:
                left_candidates.append((x_rel, dist, c, y_rel))

    # Ordenar por proyección hacia adelante (x_rel) en orden descendente (más adelante primero)
    left_candidates.sort(key=lambda x: x[0], reverse=True)
    right_candidates.sort(key=lambda x: x[0], reverse=True)

    best_cone = None
    best_dist = float("inf")

    # Alternar lado: tratar de elegir del lado opuesto al último objetivo para zigzag
    preferred_side = None
    if last_target_side == 'left':
        preferred_side = 'right'
    elif last_target_side == 'right':
        preferred_side = 'left'

    # Umbral mínimo de progreso para evitar quedarse entre dos conos
    MIN_PROGRESS = 1.0  # metros

    if preferred_side == 'right' and right_candidates:
        # buscar en candidatos de la derecha uno que avance respecto al último objetivo
        for proj, dist, c, y_rel in right_candidates:
            if last_target_proj is None or proj > (last_target_proj + MIN_PROGRESS):
                best_dist = dist
                best_cone = c
                last_target_side = 'right'
                selected_proj = proj
                break
        else:
            # si no hay avance suficiente, tomar el más avanzado igualmente
            proj, best_dist, best_cone, y_rel = right_candidates[0]
            selected_proj = proj
            last_target_side = 'right'
    elif preferred_side == 'left' and left_candidates:
        for proj, dist, c, y_rel in left_candidates:
            if last_target_proj is None or proj > (last_target_proj + MIN_PROGRESS):
                best_dist = dist
                best_cone = c
                last_target_side = 'left'
                selected_proj = proj
                break
        else:
            proj, best_dist, best_cone, y_rel = left_candidates[0]
            selected_proj = proj
    else:
        # Si no hay candidato del lado preferido, coger el más cercano entre ambos
        candidates = []
        if left_candidates:
            candidates.append(left_candidates[0])
        if right_candidates:
            candidates.append(right_candidates[0])
        if candidates:
            
            # elegir el que esté más adelante y que produzca progreso si es posible
            candidates.sort(key=lambda x: x[0], reverse=True)
            chosen = None
            for proj, dist, c, y_rel in candidates:
                if last_target_proj is None or proj > (last_target_proj + MIN_PROGRESS):
                    chosen = (proj, dist, c, y_rel)
                    break
            if chosen is None:
                chosen = candidates[0]
            best_proj, best_dist, best_cone, y_rel = chosen
            last_target_side = 'right' if y_rel < 0 else 'left'
            selected_proj = best_proj
        else:
            # fallback: si no hay ninguno en el frente, tomar el más cercano total
            if cones:
                best_cone = min(cones, key=lambda c: math.hypot(c.x - s.x, c.y - s.y))
                dx = best_cone.x - s.x
                dy = best_cone.y - s.y
                best_dist = math.hypot(dx, dy)
                x_rel = dx * math.cos(s.yaw) + dy * math.sin(s.yaw)
                y_rel = -(dx * math.sin(s.yaw)) + (dy * math.cos(s.yaw))
                last_target_side = 'right' if y_rel < 0 else 'left'
                selected_proj = x_rel

    # Calcular comandos de control
    if best_cone:
        angle_to_target = math.atan2(best_cone.y - s.y, best_cone.x - s.x)
        heading_error = angle_diff(angle_to_target, s.yaw)

        # Dirección proporcional (mantener respuesta agresiva para zigzag)
        K_steer = 1.2
        steer_cmd = max(-1.0, min(1.0, K_steer * heading_error))
    else:
        steer_cmd = 0.0

    # Control proporcional de velocidad + frenada si es necesario
    K_speed = 0.6
    speed_error = TARGET_SPEED - s.speed
    throttle_cmd = K_speed * speed_error

    # Frenado si estamos muy cerca del cono objetivo
    BRAKE_DISTANCE = 2.0  # m
    if best_cone is not None:
        if best_dist < BRAKE_DISTANCE:
            # Frenada proporcional a la proximidad (más cerca -> más frenada)
            brake_strength = (BRAKE_DISTANCE - best_dist) / BRAKE_DISTANCE
            # Aplicar brake (throttle negativo). Mezclamos con throttle_cmd para suavizar
            throttle_cmd = min(throttle_cmd, -min(1.0, brake_strength * 1.2))

        # Si el error de rumbo es grande y vamos rápido, reducir velocidad
        if abs(heading_error) > math.radians(45) and s.speed > 1.5:
            throttle_cmd = min(throttle_cmd, 0.0)

        # Actualizar la proyección objetivo elegido para el próximo paso
        try:
            last_target_proj = float(selected_proj)
        except Exception:
            # si no existe selected_proj, calcular la proyección actual
            dx = best_cone.x - s.x
            dy = best_cone.y - s.y
            last_target_proj = dx * math.cos(s.yaw) + dy * math.sin(s.yaw)

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

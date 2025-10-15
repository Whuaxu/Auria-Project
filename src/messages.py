from typing import List
from msgspec import Struct

# Comandos de control del vehículo (producidos por el controlador)
class Controls(Struct):

    """
    - throttle: aceleración [-1, 1]
    - steer: dirección [-1, 1]
    """

    throttle: float = 0.0
    steer: float = 0.0

# Estado actual del vehículo (publicado por el simulador)
class VehicleState(Struct):
    
    """
    - x, y: posición (m)
    - yaw: orientación (rad)
    - speed: velocidad (m/s)
    - timestamp: instante de tiempo (s)
    """

    x: float
    y: float
    yaw: float
    speed: float
    timestamp: float

# Representa un cono del circuito
class Cone(Struct):

    # x, y: posición (m)
    x: float
    y: float

# Lista de conos
class Cones(Struct):
   
    cones: List[Cone]

#!/bin/bash

set -e  # Detener en caso de error

# ================================================================
# 1. Lanzar servidor NATS
# ================================================================
if [[ -x ./nats_server.sh ]]; then

  echo "[LOG] Iniciando servidor NATS..."
  ./nats_server.sh &
  NATS_PID=$!
  sleep 2
  echo "[LOG] Servidor NATS iniciado (PID: $NATS_PID)"

else

  echo "[LOG]  No se encontró nats_server.sh o no es ejecutable."
  echo "[LOG] Por favor, inicia el servidor manualmente antes de continuar."
  exit 1
  
fi

# ================================================================
# 2. Lanzar simulador
# ================================================================
echo "[LOG] Iniciando simulador..."
python3 simulator.py &
SIM_PID=$!
sleep 1
echo "[LOG] Simulador iniciado (PID: $SIM_PID)"

# ================================================================
# 3. Lanzar controlador
# ================================================================
echo "[LOG] Iniciando controlador autónomo..."
python3 controller.py &
CTRL_PID=$!
sleep 1
echo "[LOG] Controlador iniciado (PID: $CTRL_PID)"

# ================================================================
# 4. Lanzar visualizador
# ================================================================
echo "[LOG]  Iniciando visualizador..."
python3 visualizer.py &
VIS_PID=$!
sleep 1
echo "[LOG] Visualizador iniciado (PID: $VIS_PID)"

# ================================================================
# 5. Información final
# ================================================================
echo ""
echo " [LOG] Todo iniciado correctamente."
echo ""
echo "Procesos en ejecución:"
echo "  NATS Server : PID $NATS_PID"
echo "  Simulador   : PID $SIM_PID"
echo "  Controlador : PID $CTRL_PID"
echo "  Visualizador: PID $VIS_PID"
echo ""
echo "[LOG] Las salidas no se están guardando en archivos (se pueden hacer logs pero no se pide)."
echo "[LOG] Para detener todo, ejecuta:"
echo ""
echo "   kill $NATS_PID $SIM_PID $CTRL_PID $VIS_PID"
echo ""
echo "O simplemente cierra esta terminal (los procesos se cerrarán automáticamente)."

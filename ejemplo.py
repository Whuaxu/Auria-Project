from msgspec import Struct
from starting_pack import encoder, subscribe, timer, publish, start
import asyncio

# así se definen los mensajes que se envian por los topics, lo más cómodo
# es definirlos en un archivo aparte para poder compartir las mismas definiciones entre varios programas
# hay que especificar el tipo de los datos obligatoriamente con anotaciones de tipos de python

class TipoMensaje(Struct):
	dato1 : int
	dato2 : float
	dato3 : str
	dato4 : list[int]
	
	
# para crear mensajes lo hacemos como cualquier otra clase
# mensaje_nuevo = TipoMensaje(dato1=1,dato2=2.2,dato3="asd",dato4=[])

# El estado lo guardamos en su propia clase
class NodeState(Struct):
	variable1 : int = 1
	variable2 : int = 2

# Creamos una instancia de esa clase
state = NodeState()

# para crear una subscripcion se usa @subscribe, en este ejemplo
# cada vez que llega un mensaje al topic "topic" se ejecuta subscriber_callback con ese mensaje,
# adicionalmente le indicamos que el mensaje es de tipo "TipoMensaje"
 
@subscribe("topic",TipoMensaje)
async def subscriber_callback(msg : TipoMensaje):
	# podemos acceder a las variables del mensajes como en cualquier otra clase
	print(msg.dato1)
	# podemos también crear otro mensaje fácilmente

	# republicamos el mensaje que nos acaba de llegar en "topic2"
	await publish("topic2",msg)
	
	
# el @timer ejecuta algo periodicamente, en este caso "timer_callback" se ejecutará 10 veces por segundo 
@timer(0.1)
async def timer_callback():
	state.variable1 += 1
	print(f"la variable de estado es {state.variable1}")

# IMPORTANTE: todas las funciones que tengan decoradores (@subscribe y @timer) deben ser async
# y cuando publiqueis mensajes con publish teneis que hacer await publish
# NO teneis que preocuparos de nada más con respecto a cosas asíncronas que esas dos cosas


# esto inicializa el starting_pack
if __name__ == "__main__":
	asyncio.run(start())

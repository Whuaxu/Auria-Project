"""starting pack for creating nodes.

use @subscribe like this:
```
@subscribe("cones",ConeArray)
def callback(msg : ConeArray):
...
```
you can also use `encoder` and `decoder` to encode and decode messages
before sending them and after receiving them
(though if you use @subscribe they are automatically decoded)

remember to call `start` in the main function
"""

import os
import nats
import asyncio
import msgspec
from types import FunctionType

TOPIC_NAME_ERROR = """
Error with topic name {topic} - NATS topics unlike ros do not use '/', they use '.',
also no leading '/', for example: '/can/state' would be 'can.state' in nats """

encoder = msgspec.json.Encoder()
# we create decoders for each type for faster decoding
decoders : dict[type[msgspec.Struct],msgspec.json.Decoder] = {}
nc = None # nats connection
subscriptions = []
timers = []

subscribe_setup : list[tuple[str,FunctionType,type[msgspec.Struct]]] = []

"""
Decorator to execute a task every `interval_s` seconds
example usage:
`@timer(0.1)
def printer():
    print uwu
`
"""
def timer(interval_s : float) -> FunctionType:
    def decorator(function : FunctionType) -> FunctionType:
        async def repeat(*args,**kwargs) -> None:
            while True:
                await asyncio.gather(
                    function(*args, **kwargs),
                    asyncio.sleep(interval_s),
                )
        timers.append(repeat) # append task so we can set it up on start()
        return function
    return decorator

"""
decorator to subscribe to a nats topic
example:
```
@subscribe("cones",ConeArray)
def callback(msg : ConeArray):
[...]
```
"""
def subscribe(topic : str, message_type : type[msgspec.Struct]) -> FunctionType:
    assert issubclass(message_type,msgspec.Struct)
    if "/" in topic:
        raise Exception(TOPIC_NAME_ERROR)
    def decorator(function : FunctionType) -> None:
        decoders[message_type] = msgspec.json.Decoder(type=message_type)
        subscribe_setup.append((topic,function,message_type))
    return decorator

"""
You should always call this at the start of your node, to:
1. Connect to nats
2. Setup the subscriptions
3. Keep async working until the program is terminated
"""
async def start() -> None:
    global nc  # noqa: PLW0603
    nats_url = os.environ.get("NATS_URL") or "nats://localhost:4222"
    try:
        nc = await nats.connect(nats_url)
    except ConnectionRefusedError:
        print(f"Couldn't connect to nats server at {nats_url}")

    for topic, function, message_type in subscribe_setup:
        async def callback(msg          : bytes,
                     function     : FunctionType = function,
                     message_type : type[msgspec.Struct] = message_type) -> None:
            msg = decoders[message_type].decode(msg.data)
            await function(msg)

        subscriptions.append(await nc.subscribe(topic, cb = callback))

    if timers:
        await asyncio.gather(*[timer() for timer in timers])
    else:
        # infinite wait
        await asyncio.Event().wait()

def nats_connection() -> nats.NATS:
    return nc

async def publish(topic : str, msg : msgspec.Struct) -> None:
    await nats_connection().publish(topic,encoder.encode(msg))

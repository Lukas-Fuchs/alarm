from hardware_state import *

# Listens for FIFO input
# As this will not terminate on its own this must be run in a different thread.
def fifo_listener(state):
    while True:
        for fifo in state.fifos.values():
            line = fifo.readline().decode("utf_8", "ignore")
            words = line.split()

            # skip invalid events
            if len(words) == 2:
                if words[0] not in state.encountered_sensors:
                    state.encountered_sensors.append(words[0])
                if words[0] in state.sensors:
                    state.sensors[words[0]].signal(words[1])

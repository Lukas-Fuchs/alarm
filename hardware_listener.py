from hardware_state import *
import time

# Listens for FIFO input
# As this will not terminate on its own this must be run in a different thread.
def fifo_listener(state):
    while True:
        time.sleep(0.1)
        with state.lock:
            for fifo in state.fifos.values():
                if fifo.closed:
                    continue
                maybe_data = fifo.read(-1)
                if not maybe_data:
                    continue    # Don't try to process what does not exist
                lines = maybe_data.decode("utf_8", "ignore").splitlines()

                for line in lines:
                    words = line.split()

                    print(line)

                    # skip invalid events
                    if len(words) == 2:
                        if words[0] not in state.encountered_sensors:
                            state.encountered_sensors.append(words[0])
                        if words[0] in state.sensors:
                            state.sensors[words[0]].signal(words[1])

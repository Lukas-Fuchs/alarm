import datetime
from datetime import datetime as dt
import threading
from threading import Lock

class alarm:
    time = dt.now()
    sensor = "alarm"
    mode = "daily"
    def __init__(self, time, sensor, mode):
        self.time = time
        self.sensor = sensor
        self.mode = mode

# contains all state related directly to alarms
class alarm_state:
    alarms = []

    # If this is true save() won't have any effect.
    # This can be helpful to prevent saving when replaying changes to the state
    block_saving = False

    lock = threading.Lock()

    def __init__(self):
        self.alarms = []

    def add_alarm(self, time, sensor, mode):
        now = dt.now()
        if time < now:
            # if the alarm would not trigger today add it for tomorrow
            time = dt.combine(now.date(), time.time())
            time += datetime.timedelta(days=1)
        self.alarms.append(alarm(time, sensor, mode))
        self.save()

    # Checks if an alarm is ready to be triggered
    def poll(self, hw_state):
        now = dt.now()
        for al in self.alarms:
            if al.time <= now:
                if al.mode == "single":
                    # single alarms expire after triggering
                    self.delete_alarm(al)
                elif al.mode == "daily":
                    # daily alarms will trigger at the same time the next day
                    al.time += datetime.timedelta(days=1)
                    hw_state.sensors[al.sensor] = 1
                return al
            hw_state.sensors[al.sensor] = 0
        return False

    # Removes an alarm from the list and saves the change
    def delete_alarm(self, al):
        self.alarms.remove(al)
        self.save()

    def clear(self):
        self.alarms = []

    # Saves the alarm state as a sequence of commands that would recreate that state
    def save(self):
        if self.block_saving:
            return

        out = open("alarm_state.dat", "w")
        for al in self.alarms:
            out.write("alarm add " + al.time.strftime("%H:%M") + " " + al.sensor + " " + al.mode + "\n")
        out.close()

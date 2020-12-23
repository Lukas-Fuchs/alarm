import datetime
from datetime import datetime as dt

class alarm:
    time = dt.now()
    mode = "daily"
    def __init__(self, time, mode):
        self.time = time
        self.mode = mode

# contains all state related directly to alarms
class alarm_state:
    alarms = []

    # If this is true save() won't have any effect.
    # This can be helpful to prevent saving when replaying changes to the state
    block_saving = False

    def add_alarm(self, time, mode):
        now = dt.now()
        if time < now:
            # if the alarm would not trigger today add it for tomorrow
            time = dt.combine(now.date(), time.time())
            time += datetime.timedelta(days=1)
        self.alarms.append(alarm(time, mode))
        self.save()

    # Checks if an alarm is ready to be triggered
    def poll(self):
        now = dt.now()
        for al in self.alarms:
            if al.time <= now:
                if al.mode == "single":
                    # single alarms expire after triggering
                    self.delete_alarm(al)
                elif al.mode == "daily":
                    # daily alarms will trigger at the same time the next day
                    al.time += datetime.timedelta(days=1)
                return True
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
            out.write("alarm add " + al.time.strftime("%H:%M") + " " + al.mode + "\n")
        out.close()

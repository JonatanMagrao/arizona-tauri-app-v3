import time

class EventTimer:
    def __init__(self):
        self.events = {}

    def start(self, name: str):
        self.events[name] = {
            "start": time.time(),
            "end": None,
            "duration": None
        }

    def end(self, name: str):
        if name not in self.events or self.events[name]["start"] is None:
            print(f"⚠️ Event '{name}' was not started.")
            return

        end_time = time.time()
        start_time = self.events[name]["start"]
        self.events[name]["end"] = end_time
        self.events[name]["duration"] = end_time - start_time

    def _format_duration(self, seconds: float) -> str:
        total_seconds = int(round(seconds))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def log(self):
        print("🕒 Event Summary:")
        total_duration = 0.0

        for name, data in self.events.items():
            if data["duration"] is not None:
                duration_str = self._format_duration(data["duration"])
                total_duration += data["duration"]
                print(f'🔹 {name:.<30} {duration_str}')
            else:
                print(f'🔸 {name:.<30} still running...')

        total_str = self._format_duration(total_duration)
        print(f'\n🧮 {"Total":.<30} {total_str}\n')

    def get_summary(self):
        return {
            name: {
                **data,
                "duration_str": self._format_duration(data["duration"])
            } for name, data in self.events.items()
            if data["duration"] is not None
        }
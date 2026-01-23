import threading
import time
from queue import Queue, Empty
from typing import Optional

from warsim.war_engine import WarEngine


class WarRuntime:
    def __init__(self):
        self.engine: Optional[WarEngine] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

        self.command_queue = Queue()
        self.event_queue = Queue()

    def start(self, seed=None, max_turns=50, delay=1.0):
        if self.running:
            return

        self.engine = WarEngine(
            logger=self._capture_event,
            seed=seed,
            max_turns=max_turns,
        )

        self.running = True

        def loop():
            while self.running and not self.engine.is_over():
                self._apply_commands()
                self.engine.step()
                time.sleep(delay)

            self.running = False

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _capture_event(self, msg: str):
        self.event_queue.put(msg)

    def _apply_commands(self):
        try:
            while True:
                cmd = self.command_queue.get_nowait()
                self._handle_command(cmd)
        except Empty:
            pass

    def _log(self, msg: str):
        if self.engine and hasattr(self.engine, "_log"):
            self.engine._log(msg)
        else:
            self._capture_event(msg)

    def _handle_command(self, cmd: dict):
        """
        Example cmd:
        {
          "god": "Shiva",
          "effect": "decay",
          "target": "Entity2",
          "magnitude": 0.3
        }
        """
        god = cmd.get("god")
        target_name = cmd.get("target")

        if not self.engine:
            return

        target = next((e for e in self.engine.entities if e.name == target_name), None)
        if not target:
            self._log(f"{god} tried to intervene, but the target was lost.")
            return

        effect = (cmd.get("effect") or "").lower()
        magnitude = float(cmd.get("magnitude", 0.2))

        if effect == "decay":
            dmg = target.max_health * magnitude
            target.health -= dmg
            self._log(
                f"{god} intervenes! {target.name} suffers divine decay ({dmg:.1f})."
            )
            return

        if effect == "heal":
            amt = target.max_health * magnitude
            target.health = min(target.max_health, target.health + amt)
            self._log(
                f"{god} intervenes! {target.name} is healed by {amt:.1f}."
            )
            return

    def get_events(self, limit=50):
        events = []
        try:
            while len(events) < limit:
                events.append(self.event_queue.get_nowait())
        except Empty:
            pass
        return events

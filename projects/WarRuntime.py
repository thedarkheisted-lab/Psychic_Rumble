import threading
import time
import re
import sys
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, TypedDict, Literal 
from collections import deque

from warsim.war_engine import WarEngine
from projects.BrahmaObserver import BrahmaObserver

sys.path.append(str(Path(__file__).resolve().parents[2]))

EventType = Literal["combat", "cosmic", "divine", "system", "status"]
VisibilityType = Literal["internal", "player", "lore"]

class WarEvent(TypedDict):
    turn: int
    timestamp: float

    type: EventType
    visibility: VisibilityType

    actor: str | None
    target: str | None
    value: float | None

    text: str


class WarRuntime:
    def __init__(self):
        self.engine: Optional[WarEngine] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

        self.command_queue = Queue()
        self.event_queue = Queue()

        self.history = deque(maxlen = 500)
        self.history_path = Path(".jarvis/war_history.jsonl")
        self.history_path.parent.mkdir(exist_ok = True)
        self.brahma = BrahmaObserver()
        self.brahma.attach_runtime(self)

        self.turn_gate = threading.Event()
        self.turn_gate.clear()


    def start(self, seed=None, max_turns=50, delay=1.0):
        if self.running:
            return

        self.command_queue = Queue()
        self.event_queue = Queue()
        self.engine = WarEngine(
            logger=self._capture_event,
            seed=seed,
            max_turns=max_turns,
        )

        self.running = True

        def loop():
            self.turn_gate.clear()

            while self.running and self.engine and not self.engine.is_over():

                self.turn_gate.wait()

                self.turn_gate.clear()

                self._apply_commands()

                self.engine.step()

                time.sleep(max(0.01,delay))

            self.running = False
            self.turn_gate.clear()

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _classify_event(self, msg: str) -> WarEvent:
        msg_lower = msg.lower()

        event_type: EventType = "system"
        visibility: VisibilityType = "internal"

        actor = None
        target = None
        value = None

        # ---- Cosmic events ----
        if msg_lower.startswith("*** cosmic event"):
            event_type = "cosmic"
            visibility = "player"

        # ---- Divine interventions ----
        elif "intervenes" in msg_lower:
            event_type = "divine"
            visibility = "player"

            # Example:
            # "Shiva intervenes! Entity2 suffers divine decay (12.4)."
            m = re.search(
                r"(?P<actor>\w+)\s+intervenes.*?(?P<target>[\w\s]+)\s+.*?\((?P<value>[\d.]+)\)",
                msg,
            )
            if m:
                actor = m.group("actor")
                target = m.group("target").strip()
                value = float(m.group("value"))

        # ---- Combat damage ----
        elif "takes" in msg_lower and "damage" in msg_lower:
            event_type = "combat"
            visibility = "player"

            # Example:
            # "Intern Greg: Intern Greg takes 18.7 damage (blocked 8.0)"
            m = re.search(
                r"(?P<target>[\w\s]+)\s+takes\s+(?P<value>[\d.]+)\s+damage",
                msg,
            )
            if m:
                target = m.group("target").strip()
                value = float(m.group("value"))

        # ---- Turn summary ----
        elif "turn" in msg_lower and "summary" in msg_lower:
            event_type = "status"
            visibility = "internal"

        # ---- Victory ----
        elif "wins after" in msg_lower:
            event_type = "system"
            visibility = "player"

        return {
            "turn": self.engine.turn if self.engine else -1,
            "timestamp": time.time(),

            "type": event_type,
            "visibility": visibility,

            "actor": actor,
            "target": target,
            "value": value,

            "text": msg,
        }


    def get_state_snapshot(self):
        return {
            "turn": self.engine.turn,
            "entities": [
                {
                    "name": e.name,
                    "health": e.health,
                    "max_health": e.max_health,
                    "karma": getattr(e, "karma", None)
                }
                for e in self.engine.entities
            ],
            "divine_energy": {
                # if gods are tracked here
            }
        }
    def _capture_event(self, msg: str):
        event: WarEvent = self._classify_event(msg)
        event.setdefault("timestamp", time.time())

        # Store full structured truth
        self.brahma.on_event(event)

        # Notify Brahma
        if hasattr(self, "brahma") and self.brahma:
            self.brahma.on_event(event)

        # UI only gets visible text
        if event["visibility"] == "player":
            self.event_queue.put(event["text"])

        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(event["text"] + "\n")

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
            self._log("A divine intervention was attempted, but no war is active.")
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

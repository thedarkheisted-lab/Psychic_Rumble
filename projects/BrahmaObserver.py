# # BrahmaObserver.py

# from collections import defaultdict
# from WarRuntime import WarEvent
# import time

# class BrahmaObserver:
#     def __init__(self):
#         self.events: list[WarEvent] = []              # full ordered history
#         self.turn_index = defaultdict(list)
#         self.last_review_turn = -1
#         self.last_assessment = None

#     def on_event(self, event: WarEvent):
#         turn = event.get("turn")

#         if not isinstance(turn, int) or turn < 0:
#             return  # ignore malformed events

#         self.events.append(event)
#         self.turn_index[turn].append(event)

#         if turn % 10 == 0 and turn != self.last_review_turn:
#             self.review(turn)
#             self.last_review_turn = turn

#     def review(self, turn: int):
#         """
#         High-level reflection. No commands. No IO.
#         """
#         window = []
#         for t in range(max(1, turn - 9), turn + 1):
#             window.extend(self.turn_index.get(t, []))

#         self.last_assessment = self._analyze(window, turn)

#     def _analyze(self, events: list[dict], turn: int):
#         """
#         Brahma understands causality, not just counts.
#         """
#         summary = {
#             "turn": turn,
#             "entity_states": {},
#             "damage_flow": defaultdict(float),
#             "interventions": [],
#             "cosmic_events": [],
#             "anomalies": [],
#         }

#         for e in events:
#             phase = e.get("phase")

#             if phase == "combat" and e.get("action") == "attack":
#                 summary["damage_flow"][e["target"]] += e.get("value", 0)

#             if phase == "divine":
#                 summary["interventions"].append({
#                     "god": e.get("actor"),
#                     "target": e.get("target"),
#                     "effect": e.get("action"),
#                     "value": e.get("value"),
#                 })

#             if phase == "cosmic":
#                 summary["cosmic_events"].append(e.get("action"))

#             # detect impossible states
#             before = e.get("before")
#             after = e.get("after")
#             if before and after:
#                 if "health" in before and "health" in after:
#                     if after["health"] > before["health"] and e.get("action") == "attack":
#                         summary["anomalies"].append(e)

#         return summary

# BrahmaObserver.py

from collections import defaultdict
from typing import List
import time
from pathlib import Path
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from projects.WarRuntime import WarEvent


class BrahmaObserver:
    """
    Brahma is a passive, omniscient observer.
    He never mutates state. He only understands causality over time.
    """

    def __init__(self):
        self.events: List["WarEvent"] = []
        self.turn_index = defaultdict(list)
        self.last_review_turn = -1
        self.last_assessment = None
        self.runtime = None
        self.storage_path = Path(".jarvis/war_structured.jsonl")
        self.storage_path.parent.mkdir(exist_ok = True)

    def attach_runtime(self, runtime):
        self.runtime = runtime

    def build_llm_context(self):
        return {
            "recent_events": list(self.events)[-20:],
            "analysis": self.last_assessment,
            "state": self.runtime.get_state_snapshot()
        }
    def on_event(self, event: "WarEvent"):
        turn = event.get("turn")

        if not isinstance(turn, int) or turn < 0:
            return  # defensive: ignore malformed events

        self.events.append(event)
        self.turn_index[turn].append(event)

        # Review every 10 turns
        if turn % 10 == 0 and turn != self.last_review_turn:
            self.review(turn)
            self.last_review_turn = turn
        
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def review(self, turn: int):
        """
        High-level reflection over last 10 turns.
        No IO. No commands. Pure analysis.
        """
        window = []
        for t in range(max(1, turn - 9), turn + 1):
            window.extend(self.turn_index.get(t, []))

        self.last_assessment = self._analyze(window, turn)

    def _analyze(self, events: List["WarEvent"], turn: int):
        """
        Stage-1 Brahma analysis:
        - understands damage flow
        - tracks divine & cosmic pressure
        - flags inconsistencies
        """

        summary = {
            "turn": turn,
            "damage_flow": defaultdict(float),
            "divine_actions": [],
            "cosmic_events": [],
            "anomalies": [],
            "event_count": len(events),
        }

        for e in events:
            etype = e["type"]

            # Combat damage aggregation
            if etype == "combat" and e.get("target") and e.get("value"):
                summary["damage_flow"][e["target"]] += e["value"]

            # Divine interventions
            elif etype == "divine":
                summary["divine_actions"].append({
                    "god": e.get("actor"),
                    "target": e.get("target"),
                    "value": e.get("value"),
                    "text": e["text"],
                })

            # Cosmic events
            elif etype == "cosmic":
                summary["cosmic_events"].append(e["text"])

            # Basic anomaly detection
            if etype == "combat" and e.get("value", 0) < 0:
                summary["anomalies"].append(e)

        return summary

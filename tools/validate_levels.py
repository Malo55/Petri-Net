#!/usr/bin/env python3
"""Valide hors-ligne que chaque solution passe structure + scénario."""
from __future__ import annotations

import json
from pathlib import Path

LEVELS = Path(__file__).resolve().parents[1] / "godot_project" / "data" / "levels"


class Net:
    def __init__(self, data: dict):
        self.places = {p["id"]: dict(p) for p in data.get("places", [])}
        self.transitions = {t["id"]: dict(t) for t in data.get("transitions", [])}
        self.arcs = {a["id"]: dict(a) for a in data.get("arcs", [])}

    def label_of(self, nid: str) -> str:
        if nid in self.places:
            return self.places[nid]["label"]
        return self.transitions[nid]["label"]

    def find_t(self, label: str) -> str | None:
        for tid, t in self.transitions.items():
            if t["label"] == label:
                return tid
        return None

    def marking(self) -> dict:
        return {p["label"]: p["tokens"] for p in self.places.values()}

    def input_arcs(self, tid: str):
        return [a for a in self.arcs.values() if a["to"] == tid and a["from"] in self.places]

    def output_arcs(self, tid: str):
        return [a for a in self.arcs.values() if a["from"] == tid and a["to"] in self.places]

    def enabled(self, tid: str) -> bool:
        for a in self.input_arcs(tid):
            tokens = self.places[a["from"]]["tokens"]
            if a.get("inhibitor"):
                if tokens >= a["weight"]:
                    return False
            else:
                if tokens < a["weight"]:
                    return False
        return True

    def fireable(self) -> list[str]:
        en = [tid for tid in self.transitions if self.enabled(tid)]
        if not en:
            return []
        mp = max(self.transitions[t].get("priority", 0) for t in en)
        return [t for t in en if self.transitions[t].get("priority", 0) == mp]

    def fire(self, tid: str) -> bool:
        if tid not in self.fireable():
            return False
        for a in self.input_arcs(tid):
            if a.get("inhibitor"):
                continue
            self.places[a["from"]]["tokens"] -= a["weight"]
        for a in self.output_arcs(tid):
            self.places[a["to"]]["tokens"] += a["weight"]
        return True

    def signature(self) -> str:
        pl = sorted(p["label"] for p in self.places.values())
        tr = sorted(f"{t['label']}@{t.get('priority', 0)}" for t in self.transitions.values())
        mk = [f"{lab}={self.places[[p for p in self.places.values() if p['label']==lab][0]['id']]['tokens']}" for lab in pl]
        arcs = []
        for a in self.arcs.values():
            arcs.append(f"{self.label_of(a['from'])}->{self.label_of(a['to'])}:w{a['weight']}:i{1 if a.get('inhibitor') else 0}")
        arcs.sort()
        return f"P[{','.join(pl)}]|T[{','.join(tr)}]|M[{','.join(mk)}]|A[{','.join(arcs)}]"


def run_seq(net: Net, seq: list[str]) -> bool:
    for lab in seq:
        tid = net.find_t(lab)
        if not tid or not net.fire(tid):
            return False
    return True


def main():
    failed = []
    for path in sorted(LEVELS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        sol = Net(data["solution_net"])
        ini = Net(data["initial_net"])
        if sol.signature() == ini.signature():
            failed.append((path.name, "initial==solution"))
            continue
        scen = data.get("scenario", {})
        seq = scen.get("firing_sequence", [])
        target = scen.get("target_marking", {})
        n = Net(data["solution_net"])
        if seq:
            if not run_seq(n, seq):
                failed.append((path.name, f"sequence blocked {seq}"))
                continue
        if target:
            mk = n.marking()
            for k, v in target.items():
                if mk.get(k) != v:
                    failed.append((path.name, f"marking {mk} != {target}"))
                    break
    if failed:
        print("FAILURES:")
        for f in failed:
            print(" -", f)
        raise SystemExit(1)
    print(f"OK: {len(list(LEVELS.glob('*.json')))} levels")


if __name__ == "__main__":
    main()

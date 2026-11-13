#!/usr/bin/env python3
"""Génère les 40 niveaux JSON du jeu pédagogique RdP."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "godot_project" / "data" / "levels"

ALL_TOOLS = [
    "select", "place", "transition", "arc", "inhibitor", "delete",
    "edit_tokens", "edit_weight", "edit_priority", "edit_label",
]
BASIC_TOOLS = [
    "select", "place", "transition", "arc", "delete",
    "edit_tokens", "edit_weight", "edit_label",
]
NO_INH = BASIC_TOOLS
WITH_INH = ALL_TOOLS


def place(pid, label, tokens, x, y):
    return {"id": pid, "label": label, "tokens": tokens, "x": x, "y": y}


def trans(tid, label, x, y, priority=0):
    return {"id": tid, "label": label, "priority": priority, "x": x, "y": y}


def arc(aid, frm, to, weight=1, inhibitor=False):
    return {"id": aid, "from": frm, "to": to, "weight": weight, "inhibitor": inhibitor}


def net(places, transitions, arcs):
    return {"places": places, "transitions": transitions, "arcs": arcs}


def level(order, diff, index, lid, title, statement, initial, solution, scenario, tools=None):
    return {
        "id": lid,
        "order": order,
        "index": index,
        "difficulty": diff,
        "title": title,
        "statement": statement,
        "tools": tools or ALL_TOOLS,
        "initial_net": initial,
        "solution_net": solution,
        "scenario": scenario,
    }


def chain_pt(tokens_p1=1, weight_in=1, weight_out=1, wrong_tokens=None, wrong_win=None, wrong_wout=None):
    """P1 -> T1 -> P2"""
    wt = tokens_p1 if wrong_tokens is None else wrong_tokens
    wi = weight_in if wrong_win is None else wrong_win
    wo = weight_out if wrong_wout is None else wrong_wout
    sol = net(
        [place("p1", "P1", tokens_p1, 180, 280), place("p2", "P2", 0, 520, 280)],
        [trans("t1", "T1", 350, 280)],
        [arc("a1", "p1", "t1", weight_in), arc("a2", "t1", "p2", weight_out)],
    )
    ini = net(
        [place("p1", "P1", wt, 180, 280), place("p2", "P2", 0, 520, 280)],
        [trans("t1", "T1", 350, 280)],
        [arc("a1", "p1", "t1", wi), arc("a2", "t1", "p2", wo)],
    )
    return ini, sol


levels = []
order = 1

# ========== FACILE 1-10 ==========
# 1: fix tokens
ini, sol = chain_pt(tokens_p1=1, wrong_tokens=0)
levels.append(level(
    order, "facile", 1, "facile_01", "Premier jeton",
    "La transition T1 doit pouvoir se franchir une fois. Placez le bon nombre de jetons dans P1, puis observez P2 recevoir un jeton.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 2: wrong weight in
ini, sol = chain_pt(tokens_p1=2, weight_in=2, wrong_win=1)
levels.append(level(
    order, "facile", 2, "facile_02", "Poids d'entrée",
    "P1 a 2 jetons. Pour vider P1 en un franchissement, le poids de l'arc P1→T1 doit être 2. Corrigez le poids.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 3: wrong weight out
ini, sol = chain_pt(tokens_p1=1, weight_out=2, wrong_wout=1)
levels.append(level(
    order, "facile", 3, "facile_03", "Poids de sortie",
    "Après franchissement de T1, P2 doit contenir 2 jetons. Ajustez le poids de l'arc T1→P2.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 2}}, NO_INH,
)); order += 1

# 4: two tokens consume one by one - need 2 tokens, fire twice conceptually via sequence T1,T1 - but after first fire only 1 left. Actually weight 1, tokens 2, sequence T1 T1
ini = net(
    [place("p1", "P1", 1, 180, 280), place("p2", "P2", 0, 520, 280)],
    [trans("t1", "T1", 350, 280)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
sol = net(
    [place("p1", "P1", 2, 180, 280), place("p2", "P2", 0, 520, 280)],
    [trans("t1", "T1", 350, 280)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
levels.append(level(
    order, "facile", 4, "facile_04", "Deux franchissements",
    "T1 doit pouvoir être franchie deux fois de suite. Corrigez le marquage initial de P1.",
    ini, sol, {"firing_sequence": ["T1", "T1"], "target_marking": {"P1": 0, "P2": 2}}, NO_INH,
)); order += 1

# 5: missing arc out
ini = net(
    [place("p1", "P1", 1, 180, 280), place("p2", "P2", 0, 520, 280)],
    [trans("t1", "T1", 350, 280)],
    [arc("a1", "p1", "t1", 1)],
)
sol = net(
    [place("p1", "P1", 1, 180, 280), place("p2", "P2", 0, 520, 280)],
    [trans("t1", "T1", 350, 280)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
levels.append(level(
    order, "facile", 5, "facile_05", "Arc manquant",
    "Ajoutez l'arc manquant de T1 vers P2 (poids 1) pour que le jeton apparaisse dans P2.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 6: extra token elsewhere
ini = net(
    [place("p1", "P1", 1, 160, 220), place("p2", "P2", 0, 520, 220), place("p3", "P3", 3, 340, 420)],
    [trans("t1", "T1", 340, 220)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
sol = net(
    [place("p1", "P1", 1, 160, 220), place("p2", "P2", 0, 520, 220), place("p3", "P3", 0, 340, 420)],
    [trans("t1", "T1", 340, 220)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
levels.append(level(
    order, "facile", 6, "facile_06", "Marquage parasite",
    "P3 ne doit pas contenir de jeton au départ. Corrigez le marquage, puis franchissez T1.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1, "P3": 0}}, NO_INH,
)); order += 1

# 7: simple fork P1->T1->[P2,P3]
ini = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 520, 200), place("p3", "P3", 0, 520, 400)],
    [trans("t1", "T1", 340, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
sol = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 520, 200), place("p3", "P3", 0, 520, 400)],
    [trans("t1", "T1", 340, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "t1", "p3", 1)],
)
levels.append(level(
    order, "facile", 7, "facile_07", "Production double",
    "T1 doit produire un jeton dans P2 et dans P3. Ajoutez l'arc manquant.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1, "P3": 1}}, NO_INH,
)); order += 1

# 8: join P1,P2 -> T1 -> P3
ini = net(
    [place("p1", "P1", 1, 160, 200), place("p2", "P2", 0, 160, 400), place("p3", "P3", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1), arc("a3", "t1", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 160, 200), place("p2", "P2", 1, 160, 400), place("p3", "P3", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1), arc("a3", "t1", "p3", 1)],
)
levels.append(level(
    order, "facile", 8, "facile_08", "Synchronisation",
    "T1 nécessite un jeton dans P1 et dans P2. Corrigez le marquage de P2.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, NO_INH,
)); order += 1

# 9: wrong direction conceptually - arc from P2 to T1 instead of T1 to P2... actually fix weight 3
ini, sol = chain_pt(tokens_p1=3, weight_in=3, wrong_tokens=3, wrong_win=1)
levels.append(level(
    order, "facile", 9, "facile_09", "Consommation totale",
    "Un seul franchissement de T1 doit consommer les 3 jetons de P1. Corrigez le poids de l'arc d'entrée.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 10: sequence P1-T1-P2-T2-P3, wrong tokens on P1
ini = net(
    [place("p1", "P1", 0, 120, 300), place("p2", "P2", 0, 360, 300), place("p3", "P3", 0, 600, 300)],
    [trans("t1", "T1", 240, 300), trans("t2", "T2", 480, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 120, 300), place("p2", "P2", 0, 360, 300), place("p3", "P3", 0, 600, 300)],
    [trans("t1", "T1", 240, 300), trans("t2", "T2", 480, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1)],
)
levels.append(level(
    order, "facile", 10, "facile_10", "Chaîne de transitions",
    "Le jeton doit aller de P1 à P3 via T1 puis T2. Placez un jeton dans P1.",
    ini, sol, {"firing_sequence": ["T1", "T2"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, NO_INH,
)); order += 1

# ========== MOYEN 1-10 ==========
# 11: missing place between two transitions
ini = net(
    [place("p1", "P1", 1, 120, 300), place("p3", "P3", 0, 620, 300)],
    [trans("t1", "T1", 260, 300), trans("t2", "T2", 480, 300)],
    [arc("a1", "p1", "t1", 1), arc("a4", "t2", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 120, 300), place("p2", "P2", 0, 370, 300), place("p3", "P3", 0, 620, 300)],
    [trans("t1", "T1", 260, 300), trans("t2", "T2", 480, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1)],
)
levels.append(level(
    order, "moyen", 1, "moyen_01", "Place intermédiaire",
    "Il manque la place P2 entre T1 et T2, ainsi que les arcs T1→P2 et P2→T2. Ajoutez-les (labels exacts P2).",
    ini, sol, {"firing_sequence": ["T1", "T2"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, NO_INH,
)); order += 1

# 12: missing transition between places
ini = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 560, 300)],
    [],
    [],
)
sol = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
levels.append(level(
    order, "moyen", 2, "moyen_02", "Transition manquante",
    "Ajoutez la transition T1 et les arcs pour transporter le jeton de P1 vers P2.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 13: conflict - shared place, need only one enabled path with correct marking
# P0 -> T1 -> P1 and P0 -> T2 -> P2, one token: conflict. Solution: 1 token, sequence chooses T1
ini = net(
    [place("p0", "P0", 0, 160, 300), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 360, 180), trans("t2", "T2", 360, 420)],
    [arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1), arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1)],
)
sol = net(
    [place("p0", "P0", 1, 160, 300), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 360, 180), trans("t2", "T2", 360, 420)],
    [arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1), arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1)],
)
levels.append(level(
    order, "moyen", 3, "moyen_03", "Situation de conflit",
    "P0 alimente T1 et T2 (conflit). Placez 1 jeton dans P0. La séquence attendue franchit T1 (le jeton va dans P1).",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P0": 0, "P1": 1, "P2": 0}}, NO_INH,
)); order += 1

# 14: complementary place capacity
# Resource place R with 1 token, machine M, process
ini = net(
    [place("p_libre", "Libre", 0, 160, 220), place("p_occupe", "Occupe", 0, 160, 420), place("p_fin", "Fin", 0, 560, 320)],
    [trans("t_start", "Start", 360, 220), trans("t_end", "End", 360, 420)],
    [
        arc("a1", "p_libre", "t_start", 1), arc("a2", "t_start", "p_occupe", 1),
        arc("a3", "p_occupe", "t_end", 1), arc("a4", "t_end", "p_libre", 1),
        arc("a5", "t_end", "p_fin", 1),
    ],
)
sol = net(
    [place("p_libre", "Libre", 1, 160, 220), place("p_occupe", "Occupe", 0, 160, 420), place("p_fin", "Fin", 0, 560, 320)],
    [trans("t_start", "Start", 360, 220), trans("t_end", "End", 360, 420)],
    [
        arc("a1", "p_libre", "t_start", 1), arc("a2", "t_start", "p_occupe", 1),
        arc("a3", "p_occupe", "t_end", 1), arc("a4", "t_end", "p_libre", 1),
        arc("a5", "t_end", "p_fin", 1),
    ],
)
levels.append(level(
    order, "moyen", 4, "moyen_04", "Place ressource",
    "La place Libre représente une ressource unique. Placez 1 jeton dans Libre pour permettre Start puis End.",
    ini, sol, {"firing_sequence": ["Start", "End"], "target_marking": {"Libre": 1, "Occupe": 0, "Fin": 1}}, NO_INH,
)); order += 1

# 15: wrong complementary arc (missing return)
ini = net(
    [place("p_libre", "Libre", 1, 160, 220), place("p_occupe", "Occupe", 0, 160, 420), place("p_fin", "Fin", 0, 560, 320)],
    [trans("t_start", "Start", 360, 220), trans("t_end", "End", 360, 420)],
    [
        arc("a1", "p_libre", "t_start", 1), arc("a2", "t_start", "p_occupe", 1),
        arc("a3", "p_occupe", "t_end", 1),
        arc("a5", "t_end", "p_fin", 1),
    ],
)
sol = net(
    [place("p_libre", "Libre", 1, 160, 220), place("p_occupe", "Occupe", 0, 160, 420), place("p_fin", "Fin", 0, 560, 320)],
    [trans("t_start", "Start", 360, 220), trans("t_end", "End", 360, 420)],
    [
        arc("a1", "p_libre", "t_start", 1), arc("a2", "t_start", "p_occupe", 1),
        arc("a3", "p_occupe", "t_end", 1), arc("a4", "t_end", "p_libre", 1),
        arc("a5", "t_end", "p_fin", 1),
    ],
)
levels.append(level(
    order, "moyen", 5, "moyen_05", "Arc de restitution",
    "Après End, la ressource doit revenir dans Libre. Ajoutez l'arc End→Libre.",
    ini, sol, {"firing_sequence": ["Start", "End"], "target_marking": {"Libre": 1, "Occupe": 0, "Fin": 1}}, NO_INH,
)); order += 1

# 16: parallel - two independent chains, need both start tokens
ini = net(
    [place("p1", "P1", 1, 120, 180), place("p2", "P2", 0, 400, 180), place("p3", "P3", 0, 120, 420), place("p4", "P4", 0, 400, 420)],
    [trans("t1", "T1", 260, 180), trans("t2", "T2", 260, 420)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p3", "t2", 1), arc("a4", "t2", "p4", 1)],
)
sol = net(
    [place("p1", "P1", 1, 120, 180), place("p2", "P2", 0, 400, 180), place("p3", "P3", 1, 120, 420), place("p4", "P4", 0, 400, 420)],
    [trans("t1", "T1", 260, 180), trans("t2", "T2", 260, 420)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p3", "t2", 1), arc("a4", "t2", "p4", 1)],
)
levels.append(level(
    order, "moyen", 6, "moyen_06", "Parallélisme",
    "Deux chaînes indépendantes. Corrigez P3 pour que T1 et T2 puissent toutes deux se franchir (ordre T1 puis T2).",
    ini, sol, {"firing_sequence": ["T1", "T2"], "target_marking": {"P1": 0, "P2": 1, "P3": 0, "P4": 1}}, NO_INH,
)); order += 1

# 17: delete extra arc that breaks things
ini = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p2", "t1", 1)],
)
sol = net(
    [place("p1", "P1", 1, 160, 300), place("p2", "P2", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1)],
)
levels.append(level(
    order, "moyen", 7, "moyen_07", "Arc en trop",
    "L'arc P2→T1 est incorrect et empêche le comportement attendu. Supprimez-le.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1}}, NO_INH,
)); order += 1

# 18: capacity 2 resource
ini = net(
    [place("p_buf", "Buffer", 0, 160, 300), place("p_out", "Out", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p_buf", "t1", 2), arc("a2", "t1", "p_out", 1)],
)
sol = net(
    [place("p_buf", "Buffer", 2, 160, 300), place("p_out", "Out", 0, 560, 300)],
    [trans("t1", "T1", 360, 300)],
    [arc("a1", "p_buf", "t1", 2), arc("a2", "t1", "p_out", 1)],
)
levels.append(level(
    order, "moyen", 8, "moyen_08", "Seuil de poids",
    "T1 consomme 2 jetons de Buffer. Placez exactement 2 jetons dans Buffer.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"Buffer": 0, "Out": 1}}, NO_INH,
)); order += 1

# 19: add complementary place
ini = net(
    [place("p_a", "A", 1, 140, 240), place("p_b", "B", 0, 140, 420)],
    [trans("t_ab", "Tab", 340, 240), trans("t_ba", "Tba", 340, 420)],
    [arc("a1", "p_a", "t_ab", 1), arc("a2", "t_ab", "p_b", 1), arc("a3", "p_b", "t_ba", 1), arc("a4", "t_ba", "p_a", 1)],
)
sol = net(
    [place("p_a", "A", 1, 140, 240), place("p_b", "B", 0, 140, 420), place("p_c", "C", 1, 560, 330)],
    [trans("t_ab", "Tab", 340, 240), trans("t_ba", "Tba", 340, 420)],
    [
        arc("a1", "p_a", "t_ab", 1), arc("a2", "t_ab", "p_b", 1), arc("a3", "p_b", "t_ba", 1), arc("a4", "t_ba", "p_a", 1),
        arc("a5", "p_c", "t_ab", 1), arc("a6", "t_ba", "p_c", 1),
    ],
)
levels.append(level(
    order, "moyen", 9, "moyen_09", "Place complémentaire",
    "Ajoutez la place complémentaire C (1 jeton) avec arcs C→Tab et Tba→C pour limiter A/B.",
    ini, sol, {"firing_sequence": ["Tab", "Tba"], "target_marking": {"A": 1, "B": 0, "C": 1}}, NO_INH,
)); order += 1

# 20: fix labels? better: reconnect wrong arc target
ini = net(
    [place("p1", "P1", 1, 140, 300), place("p2", "P2", 0, 400, 180), place("p3", "P3", 0, 400, 420), place("p4", "P4", 0, 660, 300)],
    [trans("t1", "T1", 270, 300), trans("t2", "T2", 530, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p3", "t2", 1), arc("a4", "t2", "p4", 1)],
)
sol = net(
    [place("p1", "P1", 1, 140, 300), place("p2", "P2", 0, 400, 180), place("p3", "P3", 0, 400, 420), place("p4", "P4", 0, 660, 300)],
    [trans("t1", "T1", 270, 300), trans("t2", "T2", 530, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1), arc("a3", "p2", "t2", 1), arc("a4", "t2", "p4", 1)],
)
levels.append(level(
    order, "moyen", 10, "moyen_10", "Mauvaise connexion",
    "L'arc d'entrée de T2 doit partir de P2 (pas P3). Supprimez P3→T2 et créez P2→T2. Vous pouvez supprimer P3 si elle devient inutile — la solution attend P3 sans jeton et sans arc.",
    ini, sol, {"firing_sequence": ["T1", "T2"], "target_marking": {"P1": 0, "P2": 0, "P3": 0, "P4": 1}}, NO_INH,
)); order += 1

# Wait - solution still has P3. Good. Player must remove arc a3 and add p2->t2. P3 stays with 0 tokens.

# ========== DIFFICILE ==========
# 21: deadlock - missing arc
ini = net(
    [place("p1", "P1", 1, 140, 220), place("p2", "P2", 1, 140, 420), place("p3", "P3", 0, 520, 320)],
    [trans("t1", "T1", 340, 220), trans("t2", "T2", 340, 420)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t2", 1), arc("a3", "t1", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 140, 220), place("p2", "P2", 1, 140, 420), place("p3", "P3", 0, 520, 320)],
    [trans("t1", "T1", 340, 220), trans("t2", "T2", 340, 420)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t2", 1), arc("a3", "t1", "p3", 1), arc("a4", "t2", "p3", 1)],
)
levels.append(level(
    order, "difficile", 1, "difficile_01", "Éviter le blocage partiel",
    "T1 et T2 doivent chacune déposer un jeton dans P3. Ajoutez l'arc T2→P3, puis enchaînez T1 puis T2.",
    ini, sol, {"firing_sequence": ["T1", "T2"], "target_marking": {"P1": 0, "P2": 0, "P3": 2}}, NO_INH,
)); order += 1

# 22: inhibitor intro
ini = net(
    [place("p1", "P1", 1, 160, 220), place("p2", "P2", 1, 160, 420), place("p3", "P3", 0, 560, 320)],
    [trans("t1", "T1", 360, 320)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 160, 220), place("p2", "P2", 0, 160, 420), place("p3", "P3", 0, 560, 320)],
    [trans("t1", "T1", 360, 320)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p3", 1), arc("a3", "p2", "t1", 1, True)],
)
levels.append(level(
    order, "difficile", 2, "difficile_02", "Arc inhibiteur",
    "T1 ne doit se franchir que si P2 est vide. Mettez P2 à 0 et ajoutez un arc inhibiteur P2→T1.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, WITH_INH,
)); order += 1

# 23: inhibitor blocks until cleared
ini = net(
    [place("p1", "P1", 1, 120, 200), place("p2", "P2", 1, 120, 400), place("p3", "P3", 0, 400, 200), place("p4", "P4", 0, 650, 300)],
    [trans("t_clear", "Clear", 280, 400), trans("t_go", "Go", 500, 200)],
    [
        arc("a1", "p2", "t_clear", 1),
        arc("a2", "p1", "t_go", 1), arc("a3", "t_go", "p4", 1),
        arc("a4", "p2", "t_go", 1, True),
    ],
)
sol = net(
    [place("p1", "P1", 1, 120, 200), place("p2", "P2", 1, 120, 400), place("p3", "P3", 0, 400, 400), place("p4", "P4", 0, 650, 300)],
    [trans("t_clear", "Clear", 280, 400), trans("t_go", "Go", 500, 200)],
    [
        arc("a1", "p2", "t_clear", 1), arc("a5", "t_clear", "p3", 1),
        arc("a2", "p1", "t_go", 1), arc("a3", "t_go", "p4", 1),
        arc("a4", "p2", "t_go", 1, True),
    ],
)
levels.append(level(
    order, "difficile", 3, "difficile_03", "Lever l'inhibition",
    "Go est inhibé par P2. Clear doit vider P2 vers P3. Ajoutez Clear→P3, puis séquence Clear, Go.",
    ini, sol, {"firing_sequence": ["Clear", "Go"], "target_marking": {"P1": 0, "P2": 0, "P3": 1, "P4": 1}}, WITH_INH,
)); order += 1

# 24: long sequence fix weight mid
ini = net(
    [place("p1", "P1", 2, 100, 300), place("p2", "P2", 0, 300, 300), place("p3", "P3", 0, 500, 300), place("p4", "P4", 0, 700, 300)],
    [trans("t1", "T1", 200, 300), trans("t2", "T2", 400, 300), trans("t3", "T3", 600, 300)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1),
        arc("a3", "p2", "t2", 2), arc("a4", "t2", "p3", 1),
        arc("a5", "p3", "t3", 1), arc("a6", "t3", "p4", 1),
    ],
)
sol = net(
    [place("p1", "P1", 2, 100, 300), place("p2", "P2", 0, 300, 300), place("p3", "P3", 0, 500, 300), place("p4", "P4", 0, 700, 300)],
    [trans("t1", "T1", 200, 300), trans("t2", "T2", 400, 300), trans("t3", "T3", 600, 300)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1),
        arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1),
        arc("a5", "p3", "t3", 1), arc("a6", "t3", "p4", 1),
    ],
)
levels.append(level(
    order, "difficile", 4, "difficile_04", "Séquence longue",
    "Le poids P2→T2 est trop élevé (2). Remettez-le à 1 pour enchaîner T1, T1, T2, T2, T3, T3 et remplir P4 de 2 jetons.",
    ini, sol, {"firing_sequence": ["T1", "T1", "T2", "T2", "T3", "T3"], "target_marking": {"P1": 0, "P2": 0, "P3": 0, "P4": 2}}, NO_INH,
)); order += 1

# 25: mutex with inhibitor
ini = net(
    [place("p_a", "A", 1, 120, 200), place("p_b", "B", 1, 120, 400), place("p_cs", "CS", 0, 520, 300), place("p_idle", "Idle", 1, 320, 500)],
    [trans("t_enter", "Enter", 320, 200), trans("t_leave", "Leave", 520, 420)],
    [
        arc("a1", "p_a", "t_enter", 1), arc("a2", "t_enter", "p_cs", 1),
        arc("a3", "p_cs", "t_leave", 1), arc("a4", "t_leave", "p_b", 1),
    ],
)
sol = net(
    [place("p_a", "A", 1, 120, 200), place("p_b", "B", 0, 120, 400), place("p_cs", "CS", 0, 520, 300), place("p_idle", "Idle", 1, 320, 500)],
    [trans("t_enter", "Enter", 320, 200), trans("t_leave", "Leave", 520, 420)],
    [
        arc("a1", "p_a", "t_enter", 1), arc("a2", "t_enter", "p_cs", 1),
        arc("a3", "p_cs", "t_leave", 1), arc("a4", "t_leave", "p_b", 1),
        arc("a5", "p_idle", "t_enter", 1), arc("a6", "t_leave", "p_idle", 1),
    ],
)
levels.append(level(
    order, "difficile", 5, "difficile_05", "Section critique",
    "Idle garde l'exclusion mutuelle. Mettez B à 0 et ajoutez Idle→Enter et Leave→Idle. Séquence Enter, Leave.",
    ini, sol, {"firing_sequence": ["Enter", "Leave"], "target_marking": {"A": 0, "B": 1, "CS": 0, "Idle": 1}}, NO_INH,
)); order += 1

# 26: producer consumer buffer size
ini = net(
    [place("p_empty", "Empty", 1, 120, 200), place("p_full", "Full", 0, 120, 400), place("p_item", "Item", 0, 400, 300), place("p_done", "Done", 0, 650, 300)],
    [trans("t_prod", "Prod", 260, 200), trans("t_cons", "Cons", 500, 400)],
    [
        arc("a1", "p_empty", "t_prod", 1), arc("a2", "t_prod", "p_full", 1), arc("a3", "t_prod", "p_item", 1),
        arc("a4", "p_full", "t_cons", 1), arc("a5", "p_item", "t_cons", 1), arc("a6", "t_cons", "p_empty", 1),
        arc("a7", "t_cons", "p_done", 1),
    ],
)
sol = net(
    [place("p_empty", "Empty", 2, 120, 200), place("p_full", "Full", 0, 120, 400), place("p_item", "Item", 0, 400, 300), place("p_done", "Done", 0, 650, 300)],
    [trans("t_prod", "Prod", 260, 200), trans("t_cons", "Cons", 500, 400)],
    [
        arc("a1", "p_empty", "t_prod", 1), arc("a2", "t_prod", "p_full", 1), arc("a3", "t_prod", "p_item", 1),
        arc("a4", "p_full", "t_cons", 1), arc("a5", "p_item", "t_cons", 1), arc("a6", "t_cons", "p_empty", 1),
        arc("a7", "t_cons", "p_done", 1),
    ],
)
levels.append(level(
    order, "difficile", 6, "difficile_06", "Producteur / consommateur",
    "Buffer de capacité 2 : Empty doit avoir 2 jetons. Enchaînez Prod, Prod, Cons, Cons.",
    ini, sol, {"firing_sequence": ["Prod", "Prod", "Cons", "Cons"], "target_marking": {"Empty": 2, "Full": 0, "Item": 0, "Done": 2}}, NO_INH,
)); order += 1

# 27: inhibitor weight
ini = net(
    [place("p1", "P1", 1, 160, 240), place("p2", "P2", 2, 160, 420), place("p3", "P3", 0, 560, 330)],
    [trans("t1", "T1", 360, 330)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p3", 1), arc("a3", "p2", "t1", 2, True)],
)
sol = net(
    [place("p1", "P1", 1, 160, 240), place("p2", "P2", 1, 160, 420), place("p3", "P3", 0, 560, 330)],
    [trans("t1", "T1", 360, 330)],
    [arc("a1", "p1", "t1", 1), arc("a2", "t1", "p3", 1), arc("a3", "p2", "t1", 2, True)],
)
levels.append(level(
    order, "difficile", 7, "difficile_07", "Seuil d'inhibition",
    "L'inhibiteur P2→T1 (poids 2) bloque si P2≥2. Réduisez P2 à 1 jeton pour autoriser T1.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 1, "P3": 1}}, WITH_INH,
)); order += 1

# 28: restore missing place in cycle
ini = net(
    [place("p1", "P1", 1, 200, 200), place("p2", "P2", 0, 500, 200), place("p3", "P3", 0, 500, 420)],
    [trans("t1", "T1", 350, 200), trans("t2", "T2", 500, 310), trans("t3", "T3", 350, 420)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1),
        arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1),
        arc("a5", "p3", "t3", 1),
    ],
)
sol = net(
    [place("p1", "P1", 1, 200, 200), place("p2", "P2", 0, 500, 200), place("p3", "P3", 0, 500, 420)],
    [trans("t1", "T1", 350, 200), trans("t2", "T2", 500, 310), trans("t3", "T3", 350, 420)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1),
        arc("a3", "p2", "t2", 1), arc("a4", "t2", "p3", 1),
        arc("a5", "p3", "t3", 1), arc("a6", "t3", "p1", 1),
    ],
)
levels.append(level(
    order, "difficile", 8, "difficile_08", "Cycle à refermer",
    "Ajoutez l'arc T3→P1 pour boucler. La séquence T1,T2,T3 doit ramener 1 jeton dans P1.",
    ini, sol, {"firing_sequence": ["T1", "T2", "T3"], "target_marking": {"P1": 1, "P2": 0, "P3": 0}}, NO_INH,
)); order += 1

# 29: remove deadlock-causing extra token
ini = net(
    [place("p1", "P1", 1, 140, 240), place("p2", "P2", 1, 140, 420), place("p3", "P3", 0, 560, 330)],
    [trans("t1", "T1", 340, 330)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1, True), arc("a3", "t1", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 1, 140, 240), place("p2", "P2", 0, 140, 420), place("p3", "P3", 0, 560, 330)],
    [trans("t1", "T1", 340, 330)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1, True), arc("a3", "t1", "p3", 1)],
)
levels.append(level(
    order, "difficile", 9, "difficile_09", "Jeton bloqueur",
    "P2 inhibe T1. Retirez le jeton de P2 pour débloquer le réseau.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, WITH_INH,
)); order += 1

# 30: complex join weights
ini = net(
    [place("p1", "P1", 2, 120, 180), place("p2", "P2", 3, 120, 420), place("p3", "P3", 0, 560, 300)],
    [trans("t1", "T1", 340, 300)],
    [arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1), arc("a3", "t1", "p3", 1)],
)
sol = net(
    [place("p1", "P1", 2, 120, 180), place("p2", "P2", 3, 120, 420), place("p3", "P3", 0, 560, 300)],
    [trans("t1", "T1", 340, 300)],
    [arc("a1", "p1", "t1", 2), arc("a2", "p2", "t1", 3), arc("a3", "t1", "p3", 1)],
)
levels.append(level(
    order, "difficile", 10, "difficile_10", "Jointure pondérée",
    "T1 doit consommer 2 jetons de P1 et 3 de P2 en un franchissement. Corrigez les poids d'entrée.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P1": 0, "P2": 0, "P3": 1}}, NO_INH,
)); order += 1

# ========== EXPERT ==========
# 31: priority basics
ini = net(
    [place("p0", "P0", 1, 160, 300), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 360, 180, 0), trans("t2", "T2", 360, 420, 0)],
    [arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1), arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1)],
)
sol = net(
    [place("p0", "P0", 1, 160, 300), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 360, 180, 0), trans("t2", "T2", 360, 420, 2)],
    [arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1), arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1)],
)
levels.append(level(
    order, "expert", 1, "expert_01", "Priorité simple",
    "T1 et T2 sont en conflit. Donnez à T2 la priorité 2 pour qu'elle soit choisie. Objectif : jeton dans P2.",
    ini, sol, {"firing_sequence": ["T2"], "target_marking": {"P0": 0, "P1": 0, "P2": 1}}, ALL_TOOLS,
)); order += 1

# 32: priority + inhibitor
ini = net(
    [place("p0", "P0", 1, 120, 300), place("p_block", "Block", 1, 120, 480), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 340, 180, 5), trans("t2", "T2", 340, 420, 0)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p_block", "t1", 1, True),
    ],
)
sol = net(
    [place("p0", "P0", 1, 120, 300), place("p_block", "Block", 0, 120, 480), place("p1", "P1", 0, 560, 180), place("p2", "P2", 0, 560, 420)],
    [trans("t1", "T1", 340, 180, 5), trans("t2", "T2", 340, 420, 0)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p_block", "t1", 1, True),
    ],
)
levels.append(level(
    order, "expert", 2, "expert_02", "Priorité inhibée",
    "T1 a une haute priorité mais est inhibée par Block. Videz Block pour que T1 gagne le conflit.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"P0": 0, "Block": 0, "P1": 1, "P2": 0}}, ALL_TOOLS,
)); order += 1

# 33: three-way priority
ini = net(
    [place("p0", "P0", 1, 140, 300), place("p1", "P1", 0, 560, 140), place("p2", "P2", 0, 560, 300), place("p3", "P3", 0, 560, 460)],
    [trans("t1", "T1", 340, 140, 1), trans("t2", "T2", 340, 300, 1), trans("t3", "T3", 340, 460, 1)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p0", "t3", 1), arc("a6", "t3", "p3", 1),
    ],
)
sol = net(
    [place("p0", "P0", 1, 140, 300), place("p1", "P1", 0, 560, 140), place("p2", "P2", 0, 560, 300), place("p3", "P3", 0, 560, 460)],
    [trans("t1", "T1", 340, 140, 1), trans("t2", "T2", 340, 300, 3), trans("t3", "T3", 340, 460, 1)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p0", "t3", 1), arc("a6", "t3", "p3", 1),
    ],
)
levels.append(level(
    order, "expert", 3, "expert_03", "Conflit à trois",
    "Trois transitions en conflit. Donnez la priorité 3 à T2 pour atteindre P2.",
    ini, sol, {"firing_sequence": ["T2"], "target_marking": {"P0": 0, "P1": 0, "P2": 1, "P3": 0}}, ALL_TOOLS,
)); order += 1

# 34: build small net from almost empty
ini = net(
    [place("p1", "P1", 1, 150, 300), place("p2", "P2", 0, 550, 300)],
    [],
    [],
)
sol = net(
    [place("p1", "P1", 1, 150, 300), place("p2", "P2", 0, 550, 300)],
    [trans("t1", "T1", 280, 300, 0), trans("t2", "T2", 420, 300, 1)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "t1", "p2", 1),
        arc("a3", "p1", "t2", 1), arc("a4", "t2", "p2", 2),
    ],
)
levels.append(level(
    order, "expert", 4, "expert_04", "Construire le choix",
    "Ajoutez T1 (prio 0) et T2 (prio 1) depuis P1 vers P2. T2 produit 2 jetons et doit être choisie grâce à sa priorité.",
    ini, sol, {"firing_sequence": ["T2"], "target_marking": {"P1": 0, "P2": 2}}, ALL_TOOLS,
)); order += 1

# 35: traffic light style
ini = net(
    [place("p_r", "Rouge", 1, 160, 160), place("p_o", "Orange", 0, 160, 320), place("p_v", "Vert", 0, 160, 480), place("p_tick", "Tick", 3, 520, 320)],
    [trans("t_ro", "RO", 340, 240), trans("t_ov", "OV", 340, 400), trans("t_vr", "VR", 340, 160)],
    [
        arc("a1", "p_r", "t_ro", 1), arc("a2", "t_ro", "p_o", 1), arc("a3", "p_tick", "t_ro", 1),
        arc("a4", "p_o", "t_ov", 1), arc("a5", "t_ov", "p_v", 1), arc("a6", "p_tick", "t_ov", 1),
        arc("a7", "p_v", "t_vr", 1), arc("a8", "t_vr", "p_r", 1), arc("a9", "p_tick", "t_vr", 1),
    ],
)
sol = net(
    [place("p_r", "Rouge", 1, 160, 160), place("p_o", "Orange", 0, 160, 320), place("p_v", "Vert", 0, 160, 480), place("p_tick", "Tick", 3, 520, 320)],
    [trans("t_ro", "RO", 340, 240), trans("t_ov", "OV", 340, 400), trans("t_vr", "VR", 340, 560)],
    [
        arc("a1", "p_r", "t_ro", 1), arc("a2", "t_ro", "p_o", 1), arc("a3", "p_tick", "t_ro", 1),
        arc("a4", "p_o", "t_ov", 1), arc("a5", "t_ov", "p_v", 1), arc("a6", "p_tick", "t_ov", 1),
        arc("a7", "p_v", "t_vr", 1), arc("a8", "t_vr", "p_r", 1),
    ],
)
levels.append(level(
    order, "expert", 5, "expert_05", "Feu tricolore",
    "Le retour Vert→Rouge (VR) ne doit pas consommer Tick. Supprimez l'arc Tick→VR. Séquence RO, OV, VR.",
    ini, sol, {"firing_sequence": ["RO", "OV", "VR"], "target_marking": {"Rouge": 1, "Orange": 0, "Vert": 0, "Tick": 1}}, ALL_TOOLS,
)); order += 1

# 36: dual resource
ini = net(
    [place("p_a", "A", 1, 100, 200), place("p_b", "B", 1, 100, 400), place("p_ra", "Ra", 0, 300, 140), place("p_rb", "Rb", 1, 300, 500), place("p_ok", "OK", 0, 620, 300)],
    [trans("t1", "T1", 420, 300)],
    [
        arc("a1", "p_a", "t1", 1), arc("a2", "p_b", "t1", 1),
        arc("a3", "p_ra", "t1", 1), arc("a4", "p_rb", "t1", 1),
        arc("a5", "t1", "p_ok", 1),
    ],
)
sol = net(
    [place("p_a", "A", 1, 100, 200), place("p_b", "B", 1, 100, 400), place("p_ra", "Ra", 1, 300, 140), place("p_rb", "Rb", 1, 300, 500), place("p_ok", "OK", 0, 620, 300)],
    [trans("t1", "T1", 420, 300)],
    [
        arc("a1", "p_a", "t1", 1), arc("a2", "p_b", "t1", 1),
        arc("a3", "p_ra", "t1", 1), arc("a4", "p_rb", "t1", 1),
        arc("a5", "t1", "p_ok", 1),
    ],
)
levels.append(level(
    order, "expert", 6, "expert_06", "Deux ressources",
    "T1 nécessite A, B, Ra et Rb. Placez aussi 1 jeton dans Ra.",
    ini, sol, {"firing_sequence": ["T1"], "target_marking": {"A": 0, "B": 0, "Ra": 0, "Rb": 0, "OK": 1}}, ALL_TOOLS,
)); order += 1

# 37: inhibitor unlock chain with priority
ini = net(
    [place("p_s", "Start", 1, 100, 300), place("p_g", "Gate", 1, 100, 480), place("p_m", "Mid", 0, 360, 300), place("p_e", "End", 0, 620, 300)],
    [trans("t_open", "Open", 240, 480, 0), trans("t_step", "Step", 240, 300, 2), trans("t_fin", "Fin", 500, 300, 0)],
    [
        arc("a1", "p_g", "t_open", 1),
        arc("a2", "p_s", "t_step", 1), arc("a3", "t_step", "p_m", 1), arc("a4", "p_g", "t_step", 1, True),
        arc("a5", "p_m", "t_fin", 1), arc("a6", "t_fin", "p_e", 1),
    ],
)
sol = net(
    [place("p_s", "Start", 1, 100, 300), place("p_g", "Gate", 1, 100, 480), place("p_m", "Mid", 0, 360, 300), place("p_e", "End", 0, 620, 300)],
    [trans("t_open", "Open", 240, 480, 0), trans("t_step", "Step", 240, 300, 2), trans("t_fin", "Fin", 500, 300, 0)],
    [
        arc("a1", "p_g", "t_open", 1),
        arc("a2", "p_s", "t_step", 1), arc("a3", "t_step", "p_m", 1), arc("a4", "p_g", "t_step", 1, True),
        arc("a5", "p_m", "t_fin", 1), arc("a6", "t_fin", "p_e", 1),
    ],
)
# Wait - initial == solution? Need a bug. Give Open wrong priority or missing - put Gate token wrong
# Actually make initial miss Fin arc weight or Open not connected - change initial Gate tokens to 0 and solution Gate 1... 
# Better: initial has Step priority 0 so if both enabled wrong - 
# Make initial missing Open entirely as wrong - player must ensure sequence Open, Step, Fin
# Put extra inhibitor wrongly on Fin from Gate
ini = net(
    [place("p_s", "Start", 1, 100, 300), place("p_g", "Gate", 1, 100, 480), place("p_m", "Mid", 0, 360, 300), place("p_e", "End", 0, 620, 300)],
    [trans("t_open", "Open", 240, 480, 0), trans("t_step", "Step", 240, 300, 2), trans("t_fin", "Fin", 500, 300, 0)],
    [
        arc("a1", "p_g", "t_open", 1),
        arc("a2", "p_s", "t_step", 1), arc("a3", "t_step", "p_m", 1), arc("a4", "p_g", "t_step", 1, True),
        arc("a5", "p_m", "t_fin", 1), arc("a6", "t_fin", "p_e", 1),
        arc("a7", "p_g", "t_fin", 1, True),
    ],
)
levels.append(level(
    order, "expert", 7, "expert_07", "Porte et priorité",
    "Fin est incorrectement inhibée par Gate. Supprimez l'arc inhibiteur Gate→Fin. Séquence Open, Step, Fin.",
    ini, sol, {"firing_sequence": ["Open", "Step", "Fin"], "target_marking": {"Start": 0, "Gate": 0, "Mid": 0, "End": 1}}, ALL_TOOLS,
)); order += 1

# 38: dense net fix one weight
ini = net(
    [
        place("p1", "P1", 1, 100, 160), place("p2", "P2", 1, 100, 320), place("p3", "P3", 1, 100, 480),
        place("p4", "P4", 0, 380, 240), place("p5", "P5", 0, 380, 400), place("p6", "P6", 0, 660, 320),
    ],
    [trans("t1", "T1", 240, 240), trans("t2", "T2", 240, 400), trans("t3", "T3", 520, 320)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1), arc("a3", "t1", "p4", 1),
        arc("a4", "p2", "t2", 1), arc("a5", "p3", "t2", 1), arc("a6", "t2", "p5", 1),
        arc("a7", "p4", "t3", 1), arc("a8", "p5", "t3", 1), arc("a9", "t3", "p6", 1),
    ],
)
sol = net(
    [
        place("p1", "P1", 1, 100, 160), place("p2", "P2", 2, 100, 320), place("p3", "P3", 1, 100, 480),
        place("p4", "P4", 0, 380, 240), place("p5", "P5", 0, 380, 400), place("p6", "P6", 0, 660, 320),
    ],
    [trans("t1", "T1", 240, 240), trans("t2", "T2", 240, 400), trans("t3", "T3", 520, 320)],
    [
        arc("a1", "p1", "t1", 1), arc("a2", "p2", "t1", 1), arc("a3", "t1", "p4", 1),
        arc("a4", "p2", "t2", 1), arc("a5", "p3", "t2", 1), arc("a6", "t2", "p5", 1),
        arc("a7", "p4", "t3", 1), arc("a8", "p5", "t3", 1), arc("a9", "t3", "p6", 1),
    ],
)
levels.append(level(
    order, "expert", 8, "expert_08", "Réseau dense",
    "P2 est partagée par T1 et T2 : il faut 2 jetons dans P2. Corrigez le marquage puis enchaînez T1, T2, T3.",
    ini, sol, {"firing_sequence": ["T1", "T2", "T3"], "target_marking": {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0, "P6": 1}}, ALL_TOOLS,
)); order += 1

# 39: priority cascade
ini = net(
    [place("p0", "P0", 2, 120, 300), place("p1", "P1", 0, 400, 160), place("p2", "P2", 0, 400, 300), place("p3", "P3", 0, 400, 440), place("p4", "P4", 0, 680, 300)],
    [trans("t1", "T1", 260, 160, 1), trans("t2", "T2", 260, 300, 1), trans("t3", "T3", 260, 440, 1), trans("t4", "T4", 540, 300, 0)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p0", "t3", 1), arc("a6", "t3", "p3", 1),
        arc("a7", "p1", "t4", 1), arc("a8", "p2", "t4", 1), arc("a9", "t4", "p4", 1),
    ],
)
sol = net(
    [place("p0", "P0", 2, 120, 300), place("p1", "P1", 0, 400, 160), place("p2", "P2", 0, 400, 300), place("p3", "P3", 0, 400, 440), place("p4", "P4", 0, 680, 300)],
    [trans("t1", "T1", 260, 160, 2), trans("t2", "T2", 260, 300, 2), trans("t3", "T3", 260, 440, 0), trans("t4", "T4", 540, 300, 0)],
    [
        arc("a1", "p0", "t1", 1), arc("a2", "t1", "p1", 1),
        arc("a3", "p0", "t2", 1), arc("a4", "t2", "p2", 1),
        arc("a5", "p0", "t3", 1), arc("a6", "t3", "p3", 1),
        arc("a7", "p1", "t4", 1), arc("a8", "p2", "t4", 1), arc("a9", "t4", "p4", 1),
    ],
)
levels.append(level(
    order, "expert", 9, "expert_09", "Priorités ciblées",
    "Avec 2 jetons dans P0, T1 et T2 doivent gagner contre T3. Mettez leur priorité à 2 (T3 à 0). Séquence T1, T2, T4.",
    ini, sol, {"firing_sequence": ["T1", "T2", "T4"], "target_marking": {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 1}}, ALL_TOOLS,
)); order += 1

# 40: final boss - mix
ini = net(
    [
        place("p_in", "In", 2, 80, 300), place("p_lock", "Lock", 1, 80, 480),
        place("p_a", "A", 0, 300, 200), place("p_b", "B", 0, 300, 400),
        place("p_out", "Out", 0, 700, 300),
    ],
    [trans("t_a", "Ta", 200, 200, 0), trans("t_b", "Tb", 200, 400, 0), trans("t_merge", "Merge", 500, 300, 0)],
    [
        arc("a1", "p_in", "t_a", 1), arc("a2", "t_a", "p_a", 1), arc("a3", "p_lock", "t_a", 1, True),
        arc("a4", "p_in", "t_b", 1), arc("a5", "t_b", "p_b", 1),
        arc("a6", "p_a", "t_merge", 1), arc("a7", "p_b", "t_merge", 1), arc("a8", "t_merge", "p_out", 1),
    ],
)
sol = net(
    [
        place("p_in", "In", 2, 80, 300), place("p_lock", "Lock", 0, 80, 480),
        place("p_a", "A", 0, 300, 200), place("p_b", "B", 0, 300, 400),
        place("p_out", "Out", 0, 700, 300),
    ],
    [trans("t_a", "Ta", 200, 200, 0), trans("t_b", "Tb", 200, 400, 0), trans("t_merge", "Merge", 500, 300, 0)],
    [
        arc("a1", "p_in", "t_a", 1), arc("a2", "t_a", "p_a", 1), arc("a3", "p_lock", "t_a", 1, True),
        arc("a4", "p_in", "t_b", 1), arc("a5", "t_b", "p_b", 1),
        arc("a6", "p_a", "t_merge", 1), arc("a7", "p_b", "t_merge", 1), arc("a8", "t_merge", "p_out", 1),
    ],
)
levels.append(level(
    order, "expert", 10, "expert_10", "Défi final",
    "Videz Lock (qui inhibe Ta). Ensuite la séquence Ta, Tb, Merge produit un jeton dans Out.",
    ini, sol, {"firing_sequence": ["Ta", "Tb", "Merge"], "target_marking": {"In": 0, "Lock": 0, "A": 0, "B": 0, "Out": 1}}, ALL_TOOLS,
)); order += 1


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    assert len(levels) == 40, len(levels)
    for lvl in levels:
        path = OUT / f"{lvl['id']}.json"
        path.write_text(json.dumps(lvl, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(levels)} levels to {OUT}")


if __name__ == "__main__":
    main()

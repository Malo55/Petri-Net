class_name PetriValidator
extends RefCounted

## Compare deux réseaux de façon canonique (par labels).


static func structures_equal(player: PetriNet, solution: PetriNet) -> bool:
	return canonical_signature(player) == canonical_signature(solution)


static func canonical_signature(net: PetriNet) -> String:
	var place_labels: Array[String] = []
	for pid in net.places:
		place_labels.append(str(net.places[pid]["label"]))
	place_labels.sort()

	var trans_parts: Array[String] = []
	for tid in net.transitions:
		var t: Dictionary = net.transitions[tid]
		trans_parts.append("%s@%d" % [t["label"], int(t.get("priority", 0))])
	trans_parts.sort()

	var marking_parts: Array[String] = []
	for label in place_labels:
		var pid := net.find_by_label(label)
		marking_parts.append("%s=%d" % [label, int(net.places[pid]["tokens"])])

	var arc_parts: Array[String] = []
	for aid in net.arcs:
		var a: Dictionary = net.arcs[aid]
		var from_label := _node_label(net, a["from"])
		var to_label := _node_label(net, a["to"])
		if from_label == "" or to_label == "":
			continue
		var inh: int = 1 if a.get("inhibitor", false) else 0
		arc_parts.append("%s->%s:w%d:i%d" % [from_label, to_label, int(a["weight"]), inh])
	arc_parts.sort()

	return "P[%s]|T[%s]|M[%s]|A[%s]" % [
		",".join(place_labels),
		",".join(trans_parts),
		",".join(marking_parts),
		",".join(arc_parts),
	]


static func _node_label(net: PetriNet, node_id: String) -> String:
	if net.places.has(node_id):
		return str(net.places[node_id]["label"])
	if net.transitions.has(node_id):
		return str(net.transitions[node_id]["label"])
	return ""


## Vérifie structure puis scénario comportemental sur un clone.
## scenario: {firing_sequence?: Array, target_marking?: Dictionary, max_steps?: int}
static func validate(player: PetriNet, solution: PetriNet, scenario: Dictionary) -> Dictionary:
	if not structures_equal(player, solution):
		return {
			"ok": false,
			"stage": "structure",
			"reason": "structure",
			"sim": {},
		}
	var clone := player.clone()
	## Remet le marquage initial de la solution pour la simulation pédagogique
	## (le marquage fait partie de la structure déjà validée).
	var sim: Dictionary = {}
	var seq: Array = scenario.get("firing_sequence", [])
	var target: Dictionary = scenario.get("target_marking", {})
	if not seq.is_empty() and target.is_empty():
		sim = PetriSimulator.run_sequence(clone, seq)
	elif not target.is_empty():
		sim = PetriSimulator.run_until_marking(
			clone,
			target,
			int(scenario.get("max_steps", 32)),
			seq
		)
	elif not seq.is_empty():
		sim = PetriSimulator.run_sequence(clone, seq)
		if sim.get("ok", false) and not target.is_empty():
			sim["ok"] = PetriSimulator._marking_matches(sim["marking"], target)
	else:
		## Pas de scénario : structure seule suffit, anim « idle » ok
		sim = {"ok": true, "steps_done": 0, "fired": [], "marking": clone.get_marking(), "blocked_at": "", "reason": ""}

	if not sim.get("ok", false):
		return {
			"ok": false,
			"stage": "behavior",
			"reason": sim.get("reason", "behavior"),
			"sim": sim,
		}
	if not target.is_empty() and not PetriSimulator._marking_matches(sim["marking"], target):
		return {
			"ok": false,
			"stage": "behavior",
			"reason": "mauvais_marquage",
			"sim": sim,
		}
	return {
		"ok": true,
		"stage": "done",
		"reason": "",
		"sim": sim,
	}

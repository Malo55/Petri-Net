class_name PetriNet
extends RefCounted

## Modèle de réseau de Petri place/transition avec arcs pondérés,
## arcs inhibiteurs et priorités de transitions.

var places: Dictionary = {} ## id -> {id, label, tokens, pos: Vector2}
var transitions: Dictionary = {} ## id -> {id, label, priority, pos: Vector2}
var arcs: Dictionary = {} ## id -> {id, from, to, weight, inhibitor}


func clear() -> void:
	places.clear()
	transitions.clear()
	arcs.clear()


func add_place(id: String, label: String, tokens: int = 0, pos: Vector2 = Vector2.ZERO) -> void:
	places[id] = {
		"id": id,
		"label": label,
		"tokens": tokens,
		"pos": pos,
	}


func add_transition(id: String, label: String, priority: int = 0, pos: Vector2 = Vector2.ZERO) -> void:
	transitions[id] = {
		"id": id,
		"label": label,
		"priority": priority,
		"pos": pos,
	}


func add_arc(id: String, from_id: String, to_id: String, weight: int = 1, inhibitor: bool = false) -> void:
	arcs[id] = {
		"id": id,
		"from": from_id,
		"to": to_id,
		"weight": max(1, weight) if not inhibitor else max(1, weight),
		"inhibitor": inhibitor,
	}


func remove_place(id: String) -> void:
	places.erase(id)
	_remove_arcs_touching(id)


func remove_transition(id: String) -> void:
	transitions.erase(id)
	_remove_arcs_touching(id)


func remove_arc(id: String) -> void:
	arcs.erase(id)


func _remove_arcs_touching(node_id: String) -> void:
	var to_remove: Array[String] = []
	for arc_id in arcs:
		var a: Dictionary = arcs[arc_id]
		if a["from"] == node_id or a["to"] == node_id:
			to_remove.append(arc_id)
	for arc_id in to_remove:
		arcs.erase(arc_id)


func get_input_arcs(transition_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for arc_id in arcs:
		var a: Dictionary = arcs[arc_id]
		if a["to"] == transition_id and places.has(a["from"]):
			result.append(a)
	return result


func get_output_arcs(transition_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for arc_id in arcs:
		var a: Dictionary = arcs[arc_id]
		if a["from"] == transition_id and places.has(a["to"]):
			result.append(a)
	return result


func is_enabled(transition_id: String) -> bool:
	if not transitions.has(transition_id):
		return false
	for a in get_input_arcs(transition_id):
		var place: Dictionary = places[a["from"]]
		if a.get("inhibitor", false):
			if place["tokens"] >= a["weight"]:
				return false
		else:
			if place["tokens"] < a["weight"]:
				return false
	return true


func get_enabled_transitions() -> Array[String]:
	var enabled: Array[String] = []
	for tid in transitions:
		if is_enabled(tid):
			enabled.append(tid)
	return enabled


## Retourne les transitions franchissables en respectant les priorités :
## seules celles de priorité maximale parmi les sensibilisées.
func get_fireable_transitions() -> Array[String]:
	var enabled := get_enabled_transitions()
	if enabled.is_empty():
		return enabled
	var max_prio := -999999
	for tid in enabled:
		max_prio = max(max_prio, int(transitions[tid].get("priority", 0)))
	var fireable: Array[String] = []
	for tid in enabled:
		if int(transitions[tid].get("priority", 0)) == max_prio:
			fireable.append(tid)
	return fireable


func fire(transition_id: String) -> bool:
	if not is_enabled(transition_id):
		return false
	## Priorité : si d'autres transitions sensibilisées ont une priorité plus haute, refuse.
	var fireable := get_fireable_transitions()
	if transition_id not in fireable:
		return false
	for a in get_input_arcs(transition_id):
		if a.get("inhibitor", false):
			continue
		places[a["from"]]["tokens"] -= a["weight"]
	for a in get_output_arcs(transition_id):
		places[a["to"]]["tokens"] += a["weight"]
	return true


func get_marking() -> Dictionary:
	var m: Dictionary = {}
	for pid in places:
		m[places[pid]["label"]] = places[pid]["tokens"]
	return m


func get_marking_by_id() -> Dictionary:
	var m: Dictionary = {}
	for pid in places:
		m[pid] = places[pid]["tokens"]
	return m


func set_tokens(place_id: String, tokens: int) -> void:
	if places.has(place_id):
		places[place_id]["tokens"] = max(0, tokens)


func clone() -> PetriNet:
	var n := PetriNet.new()
	for pid in places:
		var p: Dictionary = places[pid]
		n.add_place(p["id"], p["label"], p["tokens"], p["pos"])
	for tid in transitions:
		var t: Dictionary = transitions[tid]
		n.add_transition(t["id"], t["label"], t.get("priority", 0), t["pos"])
	for aid in arcs:
		var a: Dictionary = arcs[aid]
		n.add_arc(a["id"], a["from"], a["to"], a["weight"], a.get("inhibitor", false))
	return n


func to_dict() -> Dictionary:
	var places_arr: Array = []
	for pid in places:
		var p: Dictionary = places[pid]
		places_arr.append({
			"id": p["id"],
			"label": p["label"],
			"tokens": p["tokens"],
			"x": p["pos"].x,
			"y": p["pos"].y,
		})
	var transitions_arr: Array = []
	for tid in transitions:
		var t: Dictionary = transitions[tid]
		transitions_arr.append({
			"id": t["id"],
			"label": t["label"],
			"priority": t.get("priority", 0),
			"x": t["pos"].x,
			"y": t["pos"].y,
		})
	var arcs_arr: Array = []
	for aid in arcs:
		var a: Dictionary = arcs[aid]
		arcs_arr.append({
			"id": a["id"],
			"from": a["from"],
			"to": a["to"],
			"weight": a["weight"],
			"inhibitor": a.get("inhibitor", false),
		})
	return {
		"places": places_arr,
		"transitions": transitions_arr,
		"arcs": arcs_arr,
	}


static func from_dict(data: Dictionary) -> PetriNet:
	var n := PetriNet.new()
	for p in data.get("places", []):
		n.add_place(
			str(p["id"]),
			str(p.get("label", p["id"])),
			int(p.get("tokens", 0)),
			Vector2(float(p.get("x", 0)), float(p.get("y", 0)))
		)
	for t in data.get("transitions", []):
		n.add_transition(
			str(t["id"]),
			str(t.get("label", t["id"])),
			int(t.get("priority", 0)),
			Vector2(float(t.get("x", 0)), float(t.get("y", 0)))
		)
	for a in data.get("arcs", []):
		n.add_arc(
			str(a["id"]),
			str(a["from"]),
			str(a["to"]),
			int(a.get("weight", 1)),
			bool(a.get("inhibitor", false))
		)
	return n


func next_place_id() -> String:
	var i := 1
	while places.has("p%d" % i) or _label_taken("P%d" % i):
		i += 1
	return "p%d" % i


func next_transition_id() -> String:
	var i := 1
	while transitions.has("t%d" % i) or _label_taken("T%d" % i):
		i += 1
	return "t%d" % i


func next_arc_id() -> String:
	var i := 1
	while arcs.has("a%d" % i):
		i += 1
	return "a%d" % i


func next_place_label() -> String:
	var i := 1
	while _label_taken("P%d" % i):
		i += 1
	return "P%d" % i


func next_transition_label() -> String:
	var i := 1
	while _label_taken("T%d" % i):
		i += 1
	return "T%d" % i


func _label_taken(label: String) -> bool:
	for pid in places:
		if places[pid]["label"] == label:
			return true
	for tid in transitions:
		if transitions[tid]["label"] == label:
			return true
	return false


func find_by_label(label: String) -> String:
	for pid in places:
		if places[pid]["label"] == label:
			return pid
	for tid in transitions:
		if transitions[tid]["label"] == label:
			return tid
	return ""

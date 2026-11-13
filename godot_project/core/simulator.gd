class_name PetriSimulator
extends RefCounted

## Simule le franchissement de transitions et détecte les blocages.


static func can_fire(net: PetriNet, transition_id: String) -> bool:
	return transition_id in net.get_fireable_transitions()


static func fire(net: PetriNet, transition_id: String) -> bool:
	return net.fire(transition_id)


## Exécute une séquence de labels de transitions.
## Retourne {ok, steps_done, blocked_at, marking, fired}
static func run_sequence(net: PetriNet, sequence: Array) -> Dictionary:
	var fired: Array[String] = []
	for i in sequence.size():
		var label := str(sequence[i])
		var tid := _find_transition_by_label(net, label)
		if tid == "":
			return {
				"ok": false,
				"steps_done": i,
				"blocked_at": label,
				"marking": net.get_marking(),
				"fired": fired,
				"reason": "transition_introuvable",
			}
		if not net.fire(tid):
			return {
				"ok": false,
				"steps_done": i,
				"blocked_at": label,
				"marking": net.get_marking(),
				"fired": fired,
				"reason": "non_franchissable",
			}
		fired.append(label)
	return {
		"ok": true,
		"steps_done": sequence.size(),
		"blocked_at": "",
		"marking": net.get_marking(),
		"fired": fired,
		"reason": "",
	}


## Avance jusqu'à target_marking (par labels) ou max_steps.
## En cas de conflit (plusieurs fireables), suit preferred_sequence si fourni,
## sinon prend la première transition triée par label.
static func run_until_marking(
	net: PetriNet,
	target_marking: Dictionary,
	max_steps: int = 32,
	preferred_sequence: Array = []
) -> Dictionary:
	var fired: Array[String] = []
	var pref_idx := 0
	for step in max_steps:
		if _marking_matches(net.get_marking(), target_marking):
			return {
				"ok": true,
				"steps_done": step,
				"blocked_at": "",
				"marking": net.get_marking(),
				"fired": fired,
				"reason": "",
			}
		var fireable := net.get_fireable_transitions()
		if fireable.is_empty():
			return {
				"ok": false,
				"steps_done": step,
				"blocked_at": "",
				"marking": net.get_marking(),
				"fired": fired,
				"reason": "blocage",
			}
		var chosen := ""
		if pref_idx < preferred_sequence.size():
			var want := str(preferred_sequence[pref_idx])
			for tid in fireable:
				if net.transitions[tid]["label"] == want:
					chosen = tid
					break
		if chosen == "":
			fireable.sort_custom(func(a, b): return net.transitions[a]["label"] < net.transitions[b]["label"])
			chosen = fireable[0]
		else:
			pref_idx += 1
		var label: String = net.transitions[chosen]["label"]
		net.fire(chosen)
		fired.append(label)
	if _marking_matches(net.get_marking(), target_marking):
		return {
			"ok": true,
			"steps_done": max_steps,
			"blocked_at": "",
			"marking": net.get_marking(),
			"fired": fired,
			"reason": "",
		}
	return {
		"ok": false,
		"steps_done": max_steps,
		"blocked_at": "",
		"marking": net.get_marking(),
		"fired": fired,
		"reason": "max_steps",
	}


static func _find_transition_by_label(net: PetriNet, label: String) -> String:
	for tid in net.transitions:
		if net.transitions[tid]["label"] == label:
			return tid
	return ""


static func _marking_matches(current: Dictionary, target: Dictionary) -> bool:
	for key in target:
		var k := str(key)
		if int(current.get(k, -1)) != int(target[key]):
			return false
	return true

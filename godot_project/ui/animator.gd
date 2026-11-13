class_name NetAnimator
extends RefCounted

## Anime une séquence de franchissements sur un NetCanvas.

signal step_started(label: String)
signal step_finished(label: String)
signal finished(success: bool, reason: String)
signal blocked(label: String)

var canvas: NetCanvas
var working_net: PetriNet
var _busy: bool = false


func setup(p_canvas: NetCanvas) -> void:
	canvas = p_canvas


func is_busy() -> bool:
	return _busy


func play_sequence(net: PetriNet, sequence: Array, step_duration: float = 0.75) -> bool:
	if _busy:
		return false
	_busy = true
	working_net = net.clone()
	canvas.animating = true
	canvas.set_net(working_net)
	var tree := canvas.get_tree()
	for label_v in sequence:
		var label := str(label_v)
		var tid := ""
		for id in working_net.transitions:
			if working_net.transitions[id]["label"] == label:
				tid = id
				break
		if tid == "" or not working_net.is_enabled(tid) or tid not in working_net.get_fireable_transitions():
			canvas.highlighted_transition = ""
			canvas.queue_redraw()
			blocked.emit(label)
			finished.emit(false, "blocage")
			_busy = false
			canvas.animating = false
			return false
		step_started.emit(label)
		await _animate_fire(tid, step_duration)
		step_finished.emit(label)
		await tree.create_timer(0.15).timeout
	canvas.highlighted_transition = ""
	canvas.queue_redraw()
	finished.emit(true, "")
	_busy = false
	canvas.animating = false
	return true


func play_until_marking(net: PetriNet, target: Dictionary, preferred: Array = [], max_steps: int = 32, step_duration: float = 0.75) -> bool:
	if _busy:
		return false
	_busy = true
	working_net = net.clone()
	canvas.animating = true
	canvas.set_net(working_net)
	var tree := canvas.get_tree()
	var pref_idx := 0
	for _i in max_steps:
		if PetriSimulator._marking_matches(working_net.get_marking(), target):
			canvas.highlighted_transition = ""
			canvas.queue_redraw()
			finished.emit(true, "")
			_busy = false
			canvas.animating = false
			return true
		var fireable := working_net.get_fireable_transitions()
		if fireable.is_empty():
			blocked.emit("")
			finished.emit(false, "blocage")
			_busy = false
			canvas.animating = false
			return false
		var chosen := ""
		if pref_idx < preferred.size():
			var want := str(preferred[pref_idx])
			for tid in fireable:
				if working_net.transitions[tid]["label"] == want:
					chosen = tid
					break
		if chosen == "":
			fireable.sort_custom(func(a, b): return working_net.transitions[a]["label"] < working_net.transitions[b]["label"])
			chosen = fireable[0]
		else:
			pref_idx += 1
		var label: String = working_net.transitions[chosen]["label"]
		step_started.emit(label)
		await _animate_fire(chosen, step_duration)
		step_finished.emit(label)
		await tree.create_timer(0.12).timeout
	var ok := PetriSimulator._marking_matches(working_net.get_marking(), target)
	finished.emit(ok, "" if ok else "max_steps")
	_busy = false
	canvas.animating = false
	return ok


func _animate_fire(tid: String, duration: float) -> void:
	canvas.highlighted_transition = tid
	canvas.queue_redraw()
	var tree := canvas.get_tree()
	var inputs := working_net.get_input_arcs(tid)
	var outputs := working_net.get_output_arcs(tid)
	var t_pos: Vector2 = working_net.transitions[tid]["pos"]

	## Phase 1 : jetons vers la transition
	canvas.flying_tokens.clear()
	for a in inputs:
		if a.get("inhibitor", false):
			continue
		var from_pos: Vector2 = working_net.places[a["from"]]["pos"]
		for _k in int(a["weight"]):
			canvas.flying_tokens.append({"from": from_pos, "to": t_pos, "t": 0.0})
	await _tween_tokens(duration * 0.45)
	## Appliquer consommation
	for a in inputs:
		if a.get("inhibitor", false):
			continue
		working_net.places[a["from"]]["tokens"] -= a["weight"]
	canvas.flying_tokens.clear()
	canvas.queue_redraw()
	await tree.create_timer(0.08).timeout

	## Phase 2 : jetons vers les places de sortie
	for a in outputs:
		var to_pos: Vector2 = working_net.places[a["to"]]["pos"]
		for _k in int(a["weight"]):
			canvas.flying_tokens.append({"from": t_pos, "to": to_pos, "t": 0.0})
	await _tween_tokens(duration * 0.45)
	for a in outputs:
		working_net.places[a["to"]]["tokens"] += a["weight"]
	canvas.flying_tokens.clear()
	canvas.highlighted_transition = ""
	canvas.queue_redraw()


func _tween_tokens(duration: float) -> void:
	if canvas.flying_tokens.is_empty():
		return
	var tree := canvas.get_tree()
	var elapsed := 0.0
	while elapsed < duration:
		var dt := tree.root.get_process_delta_time()
		elapsed += dt
		var t := clampf(elapsed / duration, 0.0, 1.0)
		for ft in canvas.flying_tokens:
			ft["t"] = t
		canvas.queue_redraw()
		await tree.process_frame

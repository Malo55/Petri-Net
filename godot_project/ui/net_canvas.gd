class_name NetCanvas
extends Control

signal net_changed
signal node_selected(node_id: String, kind: String)
signal arc_selected(arc_id: String)
signal blank_clicked(pos: Vector2)

enum Tool { SELECT, PLACE, TRANSITION, ARC, INHIBITOR, DELETE }

const PLACE_RADIUS := 28.0
const TRANS_SIZE := Vector2(22, 44)
const TOKEN_RADIUS := 5.0

var net: PetriNet = PetriNet.new()
var current_tool: Tool = Tool.SELECT
var selected_id: String = ""
var selected_kind: String = "" ## place | transition | arc
var arc_from_id: String = ""
var dragging: bool = false
var drag_offset: Vector2 = Vector2.ZERO
var animating: bool = false
var highlighted_transition: String = ""
var flying_tokens: Array[Dictionary] = [] ## {from, to, t, color}
var allowed_tools: Array = ["select", "place", "transition", "arc", "inhibitor", "delete", "edit_tokens", "edit_weight", "edit_priority"]

var _font: Font


func _ready() -> void:
	_font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_STOP
	resized.connect(queue_redraw)


func set_net(new_net: PetriNet) -> void:
	net = new_net
	selected_id = ""
	selected_kind = ""
	arc_from_id = ""
	queue_redraw()


func set_tool(tool: Tool) -> void:
	current_tool = tool
	arc_from_id = ""
	queue_redraw()


func tool_allowed(name: String) -> bool:
	return name in allowed_tools


func _draw() -> void:
	## Fond grille
	var grid := 32
	for x in range(0, int(size.x), grid):
		draw_line(Vector2(x, 0), Vector2(x, size.y), Color(1, 1, 1, 0.04))
	for y in range(0, int(size.y), grid):
		draw_line(Vector2(0, y), Vector2(size.x, y), Color(1, 1, 1, 0.04))

	for aid in net.arcs:
		_draw_arc_visual(net.arcs[aid])

	for pid in net.places:
		_draw_place(net.places[pid])

	for tid in net.transitions:
		_draw_transition(net.transitions[tid])

	for ft in flying_tokens:
		var p: Vector2 = ft["from"].lerp(ft["to"], ft["t"])
		draw_circle(p, TOKEN_RADIUS + 1.0, Color(0.95, 0.85, 0.3))

	if arc_from_id != "":
		var from_pos := _node_pos(arc_from_id)
		draw_line(from_pos, get_local_mouse_position(), Color(0.5, 0.8, 1.0, 0.7), 2.0)


func _draw_place(p: Dictionary) -> void:
	var pos: Vector2 = p["pos"]
	var selected: bool = selected_id == p["id"] and selected_kind == "place"
	var fill := Color(0.18, 0.45, 0.62) if not selected else Color(0.25, 0.65, 0.85)
	draw_circle(pos, PLACE_RADIUS, fill)
	draw_arc(pos, PLACE_RADIUS, 0, TAU, 48, Color(0.9, 0.95, 1.0), 2.5)
	_draw_label(str(p["label"]), pos + Vector2(0, -PLACE_RADIUS - 14))
	_draw_tokens(pos, int(p["tokens"]))


func _draw_transition(t: Dictionary) -> void:
	var pos: Vector2 = t["pos"]
	var rect := Rect2(pos - TRANS_SIZE / 2.0, TRANS_SIZE)
	var selected: bool = selected_id == t["id"] and selected_kind == "transition"
	var highlighted: bool = highlighted_transition == t["id"] or highlighted_transition == t["label"]
	var fill := Color(0.85, 0.7, 0.2)
	if selected:
		fill = Color(1.0, 0.85, 0.35)
	if highlighted:
		fill = Color(0.3, 0.9, 0.45)
	draw_rect(rect, fill)
	draw_rect(rect, Color(0.95, 0.95, 0.9), false, 2.0)
	_draw_label(str(t["label"]), pos + Vector2(0, -TRANS_SIZE.y / 2.0 - 14))
	var prio := int(t.get("priority", 0))
	if prio != 0:
		_draw_label("prio %d" % prio, pos + Vector2(0, TRANS_SIZE.y / 2.0 + 12), 12)


func _draw_tokens(center: Vector2, count: int) -> void:
	if count <= 0:
		return
	if count > 6:
		_draw_label(str(count), center, 16)
		return
	var angles: Array = []
	match count:
		1:
			angles = [0.0]
		2:
			angles = [-0.5, 0.5]
		3:
			angles = [0.0, 2.1, 4.2]
		_:
			for i in count:
				angles.append(TAU * float(i) / float(count))
	var r := 10.0 if count > 1 else 0.0
	for i in count:
		var a: float = angles[i] if i < angles.size() else TAU * float(i) / float(count)
		var offset := Vector2(cos(a), sin(a)) * r if count > 1 else Vector2.ZERO
		if count == 2:
			offset = Vector2(angles[i] * 16.0, 0)
		draw_circle(center + offset, TOKEN_RADIUS, Color(0.08, 0.1, 0.14))


func _draw_arc_visual(a: Dictionary) -> void:
	var from_pos := _node_pos(a["from"])
	var to_pos := _node_pos(a["to"])
	if from_pos == Vector2.INF or to_pos == Vector2.INF:
		return
	var dir := (to_pos - from_pos).normalized()
	var start := from_pos + dir * _node_radius(a["from"])
	var end := to_pos - dir * _node_radius(a["to"])
	var selected: bool = selected_id == a["id"] and selected_kind == "arc"
	var col := Color(0.75, 0.8, 0.9)
	if a.get("inhibitor", false):
		col = Color(0.95, 0.4, 0.45)
	if selected:
		col = Color(1, 1, 0.5)
	draw_line(start, end, col, 2.5 if selected else 2.0)
	## Flèche
	var tip := end
	var left := tip - dir.rotated(0.4) * 12.0
	var right := tip - dir.rotated(-0.4) * 12.0
	draw_colored_polygon(PackedVector2Array([tip, left, right]), col)
	if a.get("inhibitor", false):
		draw_circle(end - dir * 6.0, 6.0, Color(0.12, 0.14, 0.18))
		draw_arc(end - dir * 6.0, 6.0, 0, TAU, 24, col, 2.0)
	var w := int(a["weight"])
	if w != 1 or a.get("inhibitor", false):
		var mid := (start + end) / 2.0 + dir.orthogonal() * 12.0
		_draw_label(str(w), mid, 13)


func _draw_label(text: String, pos: Vector2, font_size: int = 14) -> void:
	if _font == null:
		return
	var sz := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	draw_string(_font, pos - Vector2(sz.x / 2.0, -sz.y / 4.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.92, 0.94, 0.98))


func _node_pos(id: String) -> Vector2:
	if net.places.has(id):
		return net.places[id]["pos"]
	if net.transitions.has(id):
		return net.transitions[id]["pos"]
	return Vector2.INF


func _node_radius(id: String) -> float:
	if net.places.has(id):
		return PLACE_RADIUS
	return max(TRANS_SIZE.x, TRANS_SIZE.y) / 2.0


func _gui_input(event: InputEvent) -> void:
	if animating:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_on_left_press(mb.position)
			else:
				dragging = false
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			arc_from_id = ""
			_clear_selection()
			queue_redraw()
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if dragging and selected_kind in ["place", "transition"] and current_tool == Tool.SELECT:
			var pos := mm.position - drag_offset
			if selected_kind == "place":
				net.places[selected_id]["pos"] = pos
			else:
				net.transitions[selected_id]["pos"] = pos
			net_changed.emit()
			queue_redraw()
		elif arc_from_id != "":
			queue_redraw()


func _on_left_press(pos: Vector2) -> void:
	match current_tool:
		Tool.SELECT:
			_handle_select(pos)
		Tool.PLACE:
			if tool_allowed("place"):
				_add_place_at(pos)
		Tool.TRANSITION:
			if tool_allowed("transition"):
				_add_transition_at(pos)
		Tool.ARC, Tool.INHIBITOR:
			_handle_arc_tool(pos, current_tool == Tool.INHIBITOR)
		Tool.DELETE:
			if tool_allowed("delete"):
				_handle_delete(pos)


func _handle_select(pos: Vector2) -> void:
	var hit := _hit_test(pos)
	if hit["kind"] == "":
		_clear_selection()
		blank_clicked.emit(pos)
		queue_redraw()
		return
	selected_id = hit["id"]
	selected_kind = hit["kind"]
	if hit["kind"] == "arc":
		arc_selected.emit(hit["id"])
	else:
		node_selected.emit(hit["id"], hit["kind"])
		dragging = true
		drag_offset = pos - _node_pos(hit["id"])
	queue_redraw()


func _handle_arc_tool(pos: Vector2, inhibitor: bool) -> void:
	var tool_name: String = "inhibitor" if inhibitor else "arc"
	if not tool_allowed(tool_name):
		return
	var hit := _hit_test(pos)
	if hit["kind"] not in ["place", "transition"]:
		return
	if arc_from_id == "":
		arc_from_id = hit["id"]
		queue_redraw()
		return
	var from_id := arc_from_id
	var to_id: String = hit["id"]
	arc_from_id = ""
	if from_id == to_id:
		return
	## Arc valide place->transition ou transition->place ; inhibiteur seulement place->transition
	var from_is_place: bool = net.places.has(from_id)
	var to_is_place: bool = net.places.has(to_id)
	if from_is_place == to_is_place:
		return
	if inhibitor and not from_is_place:
		return
	var aid := net.next_arc_id()
	net.add_arc(aid, from_id, to_id, 1, inhibitor)
	net_changed.emit()
	queue_redraw()


func _handle_delete(pos: Vector2) -> void:
	var hit := _hit_test(pos)
	if hit["kind"] == "":
		return
	match hit["kind"]:
		"place":
			net.remove_place(hit["id"])
		"transition":
			net.remove_transition(hit["id"])
		"arc":
			net.remove_arc(hit["id"])
	_clear_selection()
	net_changed.emit()
	queue_redraw()


func _add_place_at(pos: Vector2) -> void:
	var id := net.next_place_id()
	var label := net.next_place_label()
	net.add_place(id, label, 0, pos)
	selected_id = id
	selected_kind = "place"
	net_changed.emit()
	node_selected.emit(id, "place")
	queue_redraw()


func _add_transition_at(pos: Vector2) -> void:
	var id := net.next_transition_id()
	var label := net.next_transition_label()
	net.add_transition(id, label, 0, pos)
	selected_id = id
	selected_kind = "transition"
	net_changed.emit()
	node_selected.emit(id, "transition")
	queue_redraw()


func _clear_selection() -> void:
	selected_id = ""
	selected_kind = ""


func _hit_test(pos: Vector2) -> Dictionary:
	## Priorité : places / transitions puis arcs
	for pid in net.places:
		if pos.distance_to(net.places[pid]["pos"]) <= PLACE_RADIUS + 4.0:
			return {"id": pid, "kind": "place"}
	for tid in net.transitions:
		var tpos: Vector2 = net.transitions[tid]["pos"]
		var rect := Rect2(tpos - TRANS_SIZE / 2.0 - Vector2(4, 4), TRANS_SIZE + Vector2(8, 8))
		if rect.has_point(pos):
			return {"id": tid, "kind": "transition"}
	for aid in net.arcs:
		if _hit_arc(net.arcs[aid], pos):
			return {"id": aid, "kind": "arc"}
	return {"id": "", "kind": ""}


func _hit_arc(a: Dictionary, pos: Vector2) -> bool:
	var from_pos := _node_pos(a["from"])
	var to_pos := _node_pos(a["to"])
	if from_pos == Vector2.INF or to_pos == Vector2.INF:
		return false
	var dist := _point_segment_distance(pos, from_pos, to_pos)
	return dist <= 8.0


func _point_segment_distance(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := 0.0 if ab.length_squared() == 0.0 else clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)


func edit_selected_tokens(delta: int) -> void:
	if not tool_allowed("edit_tokens"):
		return
	if selected_kind != "place" or selected_id == "":
		return
	net.set_tokens(selected_id, int(net.places[selected_id]["tokens"]) + delta)
	net_changed.emit()
	queue_redraw()


func set_selected_tokens(value: int) -> void:
	if not tool_allowed("edit_tokens"):
		return
	if selected_kind != "place" or selected_id == "":
		return
	net.set_tokens(selected_id, value)
	net_changed.emit()
	queue_redraw()


func set_selected_weight(value: int) -> void:
	if not tool_allowed("edit_weight"):
		return
	if selected_kind != "arc" or selected_id == "":
		return
	net.arcs[selected_id]["weight"] = max(1, value)
	net_changed.emit()
	queue_redraw()


func set_selected_priority(value: int) -> void:
	if not tool_allowed("edit_priority"):
		return
	if selected_kind != "transition" or selected_id == "":
		return
	net.transitions[selected_id]["priority"] = value
	net_changed.emit()
	queue_redraw()


func set_selected_label(label: String) -> void:
	if selected_id == "":
		return
	if selected_kind == "place" and net.places.has(selected_id):
		net.places[selected_id]["label"] = label
	elif selected_kind == "transition" and net.transitions.has(selected_id):
		net.transitions[selected_id]["label"] = label
	net_changed.emit()
	queue_redraw()

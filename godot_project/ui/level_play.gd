extends Control

@onready var statement_label: RichTextLabel = %StatementLabel
@onready var title_label: Label = %TitleLabel
@onready var canvas: NetCanvas = %NetCanvas
@onready var result_overlay: ColorRect = %ResultOverlay
@onready var result_label: Label = %ResultLabel
@onready var result_message: Label = %ResultMessage
@onready var next_level_btn: Button = %NextLevelBtn
@onready var back_to_select_btn: Button = %BackToSelectBtn
@onready var dismiss_hint: Label = %DismissHint
@onready var tokens_spin: SpinBox = %TokensSpin
@onready var weight_spin: SpinBox = %WeightSpin
@onready var priority_spin: SpinBox = %PrioritySpin
@onready var label_edit: LineEdit = %LabelEdit
@onready var props_panel: VBoxContainer = %PropsPanel
@onready var tool_buttons: HBoxContainer = %ToolButtons
@onready var resolve_btn: Button = %ResolveBtn
@onready var reset_btn: Button = %ResetBtn
@onready var back_btn: Button = %BackBtn

var level: Dictionary = {}
var initial_net: PetriNet
var solution_net: PetriNet
var animator: NetAnimator = NetAnimator.new()
var resolving: bool = false
var _player_snapshot: PetriNet = null
var _group: ButtonGroup
var _next_level: Dictionary = {}


func _ready() -> void:
	result_overlay.visible = false
	animator.setup(canvas)
	canvas.node_selected.connect(_on_node_selected)
	canvas.arc_selected.connect(_on_arc_selected)
	canvas.blank_clicked.connect(func(_p): _update_props_visibility())
	tokens_spin.value_changed.connect(_on_tokens_changed)
	weight_spin.value_changed.connect(_on_weight_changed)
	priority_spin.value_changed.connect(_on_priority_changed)
	label_edit.text_submitted.connect(_on_label_submitted)
	label_edit.focus_exited.connect(func(): _on_label_submitted(label_edit.text))
	resolve_btn.pressed.connect(_on_resolve)
	reset_btn.pressed.connect(_on_reset)
	back_btn.pressed.connect(_on_back)
	next_level_btn.pressed.connect(_on_next_level)
	back_to_select_btn.pressed.connect(_on_back)
	result_overlay.gui_input.connect(_on_overlay_input)

	if GameState.pending_level_id != "":
		var lvl := LevelDB.get_level(GameState.pending_level_id)
		GameState.pending_level_id = ""
		if not lvl.is_empty():
			setup_level(lvl)
			return
	if LevelDB.levels.size() > 0:
		setup_level(LevelDB.levels[0])


func setup_level(lvl: Dictionary) -> void:
	level = lvl
	_next_level = {}
	title_label.text = "%s — %s" % [
		LevelDB.difficulty_label(str(lvl.get("difficulty", ""))),
		str(lvl.get("title", lvl.get("id", "")))
	]
	statement_label.text = str(lvl.get("statement", ""))
	var tools: Array = lvl.get("tools", [
		"select", "place", "transition", "arc", "inhibitor", "delete",
		"edit_tokens", "edit_weight", "edit_priority", "edit_label"
	])
	canvas.allowed_tools = tools
	_rebuild_tools(tools)
	initial_net = PetriNet.from_dict(lvl.get("initial_net", {}))
	solution_net = PetriNet.from_dict(lvl.get("solution_net", {}))
	canvas.set_net(initial_net.clone())
	_hide_result_overlay()
	resolving = false
	_update_props_visibility()


func _rebuild_tools(tools: Array) -> void:
	for c in tool_buttons.get_children():
		c.queue_free()
	_group = ButtonGroup.new()
	var defs := [
		["select", "Sélection", NetCanvas.Tool.SELECT],
		["place", "Place", NetCanvas.Tool.PLACE],
		["transition", "Transition", NetCanvas.Tool.TRANSITION],
		["arc", "Arc", NetCanvas.Tool.ARC],
		["inhibitor", "Inhibiteur", NetCanvas.Tool.INHIBITOR],
		["delete", "Supprimer", NetCanvas.Tool.DELETE],
	]
	for d in defs:
		if d[0] not in tools:
			continue
		var b := Button.new()
		b.text = str(d[1])
		b.toggle_mode = true
		b.button_group = _group
		var tool_val: int = d[2]
		b.pressed.connect(func(): canvas.set_tool(tool_val as NetCanvas.Tool))
		tool_buttons.add_child(b)
		if d[0] == "select":
			b.button_pressed = true
			canvas.set_tool(NetCanvas.Tool.SELECT)


func _on_node_selected(node_id: String, kind: String) -> void:
	_update_props_visibility()
	if kind == "place":
		tokens_spin.value = canvas.net.places[node_id]["tokens"]
		label_edit.text = canvas.net.places[node_id]["label"]
	elif kind == "transition":
		priority_spin.value = canvas.net.transitions[node_id].get("priority", 0)
		label_edit.text = canvas.net.transitions[node_id]["label"]


func _on_arc_selected(arc_id: String) -> void:
	_update_props_visibility()
	weight_spin.value = canvas.net.arcs[arc_id]["weight"]


func _update_props_visibility() -> void:
	var kind := canvas.selected_kind
	%TokensRow.visible = kind == "place" and "edit_tokens" in canvas.allowed_tools
	%WeightRow.visible = kind == "arc" and "edit_weight" in canvas.allowed_tools
	%PriorityRow.visible = kind == "transition" and "edit_priority" in canvas.allowed_tools
	%LabelRow.visible = kind in ["place", "transition"]
	props_panel.visible = %TokensRow.visible or %WeightRow.visible or %PriorityRow.visible or %LabelRow.visible


func _on_tokens_changed(v: float) -> void:
	canvas.set_selected_tokens(int(v))


func _on_weight_changed(v: float) -> void:
	canvas.set_selected_weight(int(v))


func _on_priority_changed(v: float) -> void:
	canvas.set_selected_priority(int(v))


func _on_label_submitted(text: String) -> void:
	var cleaned := text.strip_edges()
	if cleaned != "":
		canvas.set_selected_label(cleaned)


func _on_reset() -> void:
	if resolving:
		return
	canvas.set_net(initial_net.clone())
	_hide_result_overlay()
	_update_props_visibility()


func _on_back() -> void:
	if resolving:
		return
	get_tree().change_scene_to_file("res://ui/level_select.tscn")


func _on_next_level() -> void:
	if resolving or _next_level.is_empty():
		return
	setup_level(_next_level)


func _on_resolve() -> void:
	if resolving or animator.is_busy():
		return
	resolving = true
	resolve_btn.disabled = true
	reset_btn.disabled = true
	back_btn.disabled = true

	_player_snapshot = canvas.net.clone()
	var scenario: Dictionary = level.get("scenario", {})
	var result := PetriValidator.validate(_player_snapshot, solution_net, scenario)

	if not result["ok"] and result["stage"] == "structure":
		_show_result(false)
		_finish_resolve()
		return

	var seq: Array = scenario.get("firing_sequence", [])
	var target: Dictionary = scenario.get("target_marking", {})
	var anim_ok := true

	if not seq.is_empty() and target.is_empty():
		anim_ok = await animator.play_sequence(_player_snapshot, seq)
	elif not target.is_empty():
		anim_ok = await animator.play_until_marking(
			_player_snapshot, target, seq, int(scenario.get("max_steps", 32))
		)
	else:
		anim_ok = true

	## Structure déjà OK ici ; le résultat final suit l'animation / scénario.
	if result["ok"] == false and result["stage"] == "behavior":
		## On anime quand même jusqu'au blocage si une séquence est définie.
		anim_ok = false

	_show_result(anim_ok)

	if _player_snapshot != null:
		canvas.set_net(_player_snapshot.clone())
	_finish_resolve()


func _finish_resolve() -> void:
	resolving = false
	resolve_btn.disabled = false
	reset_btn.disabled = false
	back_btn.disabled = false


func _show_result(ok: bool) -> void:
	result_overlay.visible = true
	_next_level = {}
	next_level_btn.visible = false
	back_to_select_btn.visible = false
	result_message.visible = false
	dismiss_hint.text = "Cliquez ailleurs pour rejouer"
	if ok:
		result_label.text = "Validé"
		result_label.modulate = Color(0.45, 0.95, 0.55)
		Progress.mark_completed(str(level.get("id", "")))
		_next_level = LevelDB.get_next_level(str(level.get("id", "")))
		if not _next_level.is_empty():
			next_level_btn.visible = true
			next_level_btn.disabled = false
		else:
			result_message.text = "Tous les niveaux sont terminés."
			result_message.visible = true
			back_to_select_btn.visible = true
	else:
		result_label.text = "Erreur"
		result_label.modulate = Color(0.95, 0.4, 0.4)


func _hide_result_overlay() -> void:
	result_overlay.visible = false
	next_level_btn.visible = false
	back_to_select_btn.visible = false
	result_message.visible = false
	_next_level = {}


func _on_overlay_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		_hide_result_overlay()

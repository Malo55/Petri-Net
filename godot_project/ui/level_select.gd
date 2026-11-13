extends Control

@onready var tabs: TabContainer = %Tabs
@onready var back_btn: Button = %BackBtn


func _ready() -> void:
	back_btn.pressed.connect(func(): get_tree().change_scene_to_file("res://ui/main_menu.tscn"))
	_build_tabs()


func _build_tabs() -> void:
	for c in tabs.get_children():
		c.queue_free()
	for diff in LevelDB.difficulties():
		var scroll := ScrollContainer.new()
		scroll.name = LevelDB.difficulty_label(diff)
		scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
		var grid := GridContainer.new()
		grid.columns = 5
		grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_theme_constant_override("h_separation", 12)
		grid.add_theme_constant_override("v_separation", 12)
		scroll.add_child(grid)
		tabs.add_child(scroll)

		var list := LevelDB.get_by_difficulty(diff)
		for lvl in list:
			var id := str(lvl.get("id", ""))
			var btn := Button.new()
			btn.custom_minimum_size = Vector2(180, 72)
			var done: bool = Progress.is_completed(id)
			var mark: String = " ✓" if done else ""
			btn.text = "%s%s\n%s" % [str(lvl.get("index", "")), mark, str(lvl.get("title", id))]
			if done:
				btn.modulate = Color(0.7, 1.0, 0.75)
			else:
				btn.modulate = Color(0.9, 0.92, 0.98)
			btn.pressed.connect(_open_level.bind(id))
			grid.add_child(btn)


func _open_level(level_id: String) -> void:
	GameState.pending_level_id = level_id
	get_tree().change_scene_to_file("res://ui/level_play.tscn")

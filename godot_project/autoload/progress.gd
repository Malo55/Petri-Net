extends Node

const SAVE_PATH := "user://progress.cfg"

var completed: Dictionary = {} ## level_id -> true


func _ready() -> void:
	load_progress()


func is_completed(level_id: String) -> bool:
	return completed.get(level_id, false)


func mark_completed(level_id: String) -> void:
	completed[level_id] = true
	save_progress()


func save_progress() -> void:
	var cfg := ConfigFile.new()
	for level_id in completed:
		if completed[level_id]:
			cfg.set_value("completed", level_id, true)
	cfg.save(SAVE_PATH)


func load_progress() -> void:
	completed.clear()
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	if cfg.has_section("completed"):
		for key in cfg.get_section_keys("completed"):
			completed[key] = bool(cfg.get_value("completed", key, false))


func reset_all() -> void:
	completed.clear()
	save_progress()

extends Node

## Charge tous les niveaux depuis res://data/levels/

var levels: Array[Dictionary] = []
var by_id: Dictionary = {}


func _ready() -> void:
	reload()


func reload() -> void:
	levels.clear()
	by_id.clear()
	var dir := DirAccess.open("res://data/levels")
	if dir == null:
		push_error("Impossible d'ouvrir res://data/levels")
		return
	dir.list_dir_begin()
	var fname := dir.get_next()
	var files: Array[String] = []
	while fname != "":
		if not dir.current_is_dir() and fname.ends_with(".json"):
			files.append(fname)
		fname = dir.get_next()
	dir.list_dir_end()
	files.sort()
	for f in files:
		var path := "res://data/levels/%s" % f
		var data := _load_json(path)
		if data.is_empty():
			continue
		data["path"] = path
		levels.append(data)
		by_id[str(data.get("id", f))] = data
	levels.sort_custom(func(a, b): return int(a.get("order", 0)) < int(b.get("order", 0)))


func _load_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Lecture impossible: %s" % path)
		return {}
	var text := file.get_as_text()
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("JSON invalide: %s" % path)
		return {}
	return parsed


func get_level(level_id: String) -> Dictionary:
	return by_id.get(level_id, {})


func get_next_level(level_id: String) -> Dictionary:
	for i in range(levels.size()):
		if str(levels[i].get("id", "")) == level_id:
			if i + 1 < levels.size():
				return levels[i + 1]
			return {}
	return {}


func get_by_difficulty(diff: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for lvl in levels:
		if str(lvl.get("difficulty", "")) == diff:
			result.append(lvl)
	return result


func difficulties() -> Array[String]:
	return ["facile", "moyen", "difficile", "expert"]


func difficulty_label(diff: String) -> String:
	match diff:
		"facile":
			return "Facile"
		"moyen":
			return "Moyen"
		"difficile":
			return "Difficile"
		"expert":
			return "Expert"
		_:
			return diff.capitalize()

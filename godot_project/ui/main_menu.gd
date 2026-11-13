extends Control


func _ready() -> void:
	%PlayBtn.pressed.connect(_on_play)
	%QuitBtn.pressed.connect(_on_quit)


func _on_play() -> void:
	get_tree().change_scene_to_file("res://ui/level_select.tscn")


func _on_quit() -> void:
	get_tree().quit()

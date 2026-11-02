extends OmniLight3D
## A house's torch, candle, lantern or hearth (owner 2026-11-02: "it would be nice if torches placed and the ones that
## come in the house emitted light, it's dark in there"): a warm light that flickers a little. Housing.add_lights
## makes them where a model's flame / coal / lamp-glow textures are.

var base := 1.0
var flicker := 0.1
var flick_seed := 0.0


func _process(_delta: float) -> void:
	if flicker <= 0.0:
		return
	var t := Time.get_ticks_msec() * 0.001
	var n := sin(t * 7.3 + flick_seed) * 0.5 + sin(t * 13.7 + flick_seed * 1.7) * 0.3 + sin(t * 23.1 + flick_seed * 2.9) * 0.2
	light_energy = base * (1.0 + flicker * n)

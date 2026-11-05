extends Node
## Debug (claude 2026-11-05): the character remaster comparison (owner: "pretty blocky and hurts our lighting
## system") - one Briton in the game's own world light, drawn four ways: as now; A (textures upscaled with
## 4x-UltraSharp, skin and hair shaded as skin and hair); B (the meshes smoothed, pipeline/subdivide_figure.py); A+B.
## Shots: the face, the face from the side, a chain torso, a plate torso.
##   Godot --path new-client/godot -- --zone=0 --time=15 --probe=figure_compare --mute [--out=<dir>] [--sub=1|2]
var v: Node
var out := "E:/Offline DAOC 036c/claude-work/walk/cmp"


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


## A: skin as skin (light through it, a soft sheen), hair with its sheen; textures from cmp_ultrasharp
const SKIN_CODE := "SSS_STRENGTH = 0.05;\n\tROUGHNESS = 0.55;\n\tSPECULAR = 0.4;\n\t//CUTOUT"


func _skin_shader(cutout: bool) -> Shader:
	var s := Shader.new()
	var code: String = Fig3Figure.SHADER
	if cutout:
		code = code.replace("//CUTOUT", "ALPHA = c.a;\n\tALPHA_SCISSOR_THRESHOLD = 0.5;\n\t//CUTOUT")
	s.code = code.replace("//CUTOUT", SKIN_CODE)
	return s


func _remaster(fig: Fig3Figure) -> void:
	var skin := _skin_shader(false)
	for mi in fig.model.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).material_override as ShaderMaterial
		if m == null:
			continue
		var n := String(mi.name).to_lower()
		if n.contains("head"):
			var m2 := m.duplicate() as ShaderMaterial
			m2.shader = skin
			mi.material_override = m2


func _figure(prefix: String, texset: String, armor: Dictionary) -> Fig3Figure:
	var fig := Fig3Figure.new()
	v.add_child(fig)
	if not fig.load_figure(prefix, texset):
		print("[cmp] no figure ", prefix)
		return null
	fig.apply({"face": 0, "hair": 1, "hair_color": 1, "eyes": 2, "skin": 1})
	fig.set_armor(armor)
	return fig


func _ready() -> void:
	get_tree().create_timer(400.0).timeout.connect(func(): print("[cmp] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	out = String(args.get("out", out))
	var sub := String(args.get("sub", "1"))
	await _wait(10.0)
	get_window().size = Vector2i(1600, 900)
	if v.get("hud"):
		v.hud.visible = false
	if v.get("ui"):
		v.ui.visible = false
	v.player.visible = false
	var base: Vector3 = v.player.global_position
	if args.has("spot"):                                   # --spot=x,z (zone metres): out in the open
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	# the figure turned to the sun, a little aside (the light that shows a shape)
	var face_yaw := 0.0
	var suns := get_tree().root.find_children("*", "DirectionalLight3D", true, false)
	if suns.size() > 0:
		var to_sun: Vector3 = (suns[0] as DirectionalLight3D).global_transform.basis.z
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(float(args.get("sun_off", "35")))
		print("[cmp] sun ", to_sun)
	var cam := Camera3D.new()
	cam.fov = 30.0
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	var chain := {"body": [5, "chnbody05_02_m"], "legs": [1, "cthlegs01_chn02"], "arms": [1, "ctharms01_chn02"],
		"gloves": [1, "chngloves01_02"], "boots": [1, "chnboots01_02"]}
	var plate := {"body": [1, "pltbody01_epic_paladin_m"], "legs": [1, "cthlegs01_epic_paladin"],
		"arms": [1, "ctharms01_epic_paladin"], "gloves": [1, "pltgloves01_epic_paladin"], "boots": [1, "pltboots01_epic_paladin"]}
	var variants := [["now", "bri_m", "x4plus", false], ["A", "bri_m", "cmp_ultrasharp", true],
		["B", "bri_m_sub" + sub, "x4plus", false], ["AB", "bri_m_sub" + sub, "cmp_ultrasharp", true]]
	var shots := [["face", {}, 0.75, 0.0, "Bip01 Head"], ["side", {}, 0.75, 70.0, "Bip01 Head"],
		["chain", chain, 2.1, 25.0, "Bip01 Spine2"], ["plate", plate, 2.1, -25.0, "Bip01 Spine2"]]
	for sh in shots:
		for va in variants:
			var fig := _figure(va[1], va[2], sh[1])
			if fig == null:
				continue
			fig.global_position = base
			fig.rotation.y = face_yaw
			if va[3]:
				_remaster(fig)
			fig.play("idle")
			await _frames(4)
			fig.anim.seek(1.0, true)
			fig.anim.pause()
			var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
			var bi := sk.find_bone(sh[4])
			var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(bi).origin
			# the figure's front: its model faces +z in Godot (the client's way); the camera in front, turned by the angle
			var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
			var dir := fwd.rotated(Vector3.UP, deg_to_rad(float(sh[3])))
			cam.global_position = target + dir * float(sh[2]) + Vector3(0, 0.05, 0)
			cam.look_at(target + Vector3(0, 0.02, 0))
			await _frames(90)
			var path := "%s_%s_%s.png" % [out, sh[0], va[0]]
			get_viewport().get_texture().get_image().save_png(path)
			print("[cmp] saved ", path)
			fig.queue_free()
			await _frames(2)
	get_tree().quit()

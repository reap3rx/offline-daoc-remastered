extends Node
## Debug (claude 2026-11-05): the armour's relief and metal, four ways (owner: "the textures of the hair and armor kind
## of stand out" next to the remastered faces) - as now; half as deep; read from the broad shapes (a coarser mip) for
## both relief and shine; broad and a little shallower. Chain, plate, studded and scale, close on the chest and arm.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=armor_relief --mute --no-npcs --spot=450,600
var v: Node

const SETS := {"chain": [41, 42, 43, 44, 45], "plate": [693, 694, 695, 696, 697], "studded": [81, 82, 83, 84, 85],
	"scale": [348, 349, 350, 351, 352]}
# name, relief x, relief_bias, metal_bias
const WAYS := [["now", 1.0, 1.0, 0.0], ["half", 0.5, 1.0, 0.0], ["broad", 1.0, 3.0, 2.0], ["broad_soft", 0.6, 3.0, 2.0]]


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _ready() -> void:
	get_tree().create_timer(600.0).timeout.connect(func(): print("[arm] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/arm"))
	await get_tree().create_timer(10.0).timeout
	get_window().size = Vector2i(1600, 900)
	for n in ["hud", "ui"]:
		if v.get(n):
			v.get(n).visible = false
	v.player.visible = false
	var base: Vector3 = v.player.global_position
	if args.has("spot"):
		var xz := String(args["spot"]).split(",")
		base = Vector3(float(xz[0]), 0.0, float(xz[1]))
		base.y = v.zone.height_at(base.x, base.z)
	var face_yaw := 0.0
	var suns := get_tree().root.find_children("*", "DirectionalLight3D", true, false)
	if suns.size() > 0:
		var to_sun: Vector3 = (suns[0] as DirectionalLight3D).global_transform.basis.z
		face_yaw = atan2(to_sun.x, to_sun.z) + deg_to_rad(float(args.get("sun_off", "55")))
	var cam := Camera3D.new()
	cam.fov = 30.0
	cam.near = 0.05
	v.add_child(cam)
	cam.make_current()
	for set_name in SETS:
		var fig := Fig3Figure.new()
		v.add_child(fig)
		fig.load_figure(String(args.get("race", "bri_m")))
		fig.apply({"face": 0, "hair": 1, "hair_color": 1, "eyes": 2, "skin": 1})
		var parts := {}
		for mdl in SETS[set_name]:
			parts.merge(Fig3Figure.armor_parts(int(mdl), false), true)
		fig.set_armor(parts)
		fig.global_position = base
		fig.rotation.y = face_yaw
		fig.play("idle")
		await _frames(4)
		fig.anim.seek(1.0, true)
		fig.anim.pause()
		var mats := []                              # [material, its own relief]
		for mi in fig.model.find_children("*", "MeshInstance3D", true, false):
			var m := (mi as MeshInstance3D).material_override as ShaderMaterial
			if m == null or mats.any(func(x): return x[0] == m):
				continue
			var r = m.get_shader_parameter("relief")
			if r != null and float(r) > 0.0:
				mats.append([m, float(r)])
		var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
		var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("Bip01 Spine2")).origin
		var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
		cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(20.0)) * 1.25 + Vector3(0, 0.1, 0)
		cam.look_at(target + Vector3(0, 0.05, 0))
		for w in WAYS:
			for x in mats:
				x[0].set_shader_parameter("relief", x[1] * float(w[1]))
				x[0].set_shader_parameter("relief_bias", float(w[2]))
				x[0].set_shader_parameter("metal_bias", float(w[3]))
			await _frames(45)
			var path := "%s_%s_%s.png" % [out, set_name, w[0]]
			get_viewport().get_texture().get_image().save_png(path)
			print("[arm] saved ", path)
		fig.queue_free()
		await _frames(2)
	get_tree().quit()

extends Node
## Debug (claude 2026-11-05): the hair test (owner: "a test run on a hair replacement ... on one hair style to see if
## we just want to do that first, or just soften the hair") - one Briton, three ways: his hair as now; the same hair
## softened (its texture's grain eased, a softer sheen); a replacement - a MakeHuman hair made of strand cards (CC0,
## pipeline/hair_obj_to_gltf.py) fitted over the old hair's place on the head, in the same colour. Face, side, back.
##   Godot --path new-client/godot -- --zone=0 --time=16 --probe=hair_test --mute --no-npcs --spot=450,600
##       [--race=bri_m] [--hair=1] [--colour=1] [--new=short04] [--fit=1.04]
var v: Node

const NEW_HAIR_SHADER := """
shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;
uniform sampler2D strands : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 colour : source_color = vec3(0.5, 0.4, 0.3);
void fragment() {
	vec4 t = texture(strands, UV);
	ALBEDO = clamp(colour * t.rgb * 2.0, 0.0, 1.0);
	ALPHA = t.a;
	ALPHA_SCISSOR_THRESHOLD = 0.35;
	ALPHA_ANTIALIASING_EDGE = 0.25;
	ROUGHNESS = 0.55;
	SPECULAR = 0.42;
	BACKLIGHT = colour * 0.35;
}
"""


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _hair_meshes(fig: Fig3Figure) -> Array:
	var out := []
	var styles: Array = fig.meta.get("hair_styles", [])
	var si := int(fig.look.get("hair", 0))
	if si < styles.size() and styles[si].node != null:
		for mi in fig._parts(String(styles[si].node)):
			if (mi as MeshInstance3D).visible:
				out.append(mi)
	return out


## The hair's colour: its texture's average (where it isn't see-through), times the colour's tint.
func _hair_colour(mi: MeshInstance3D) -> Color:
	var m := mi.material_override as ShaderMaterial
	var tex: Texture2D = m.get_shader_parameter("albedo_tex")
	var img := tex.get_image()
	if img.is_compressed():
		img.decompress()
	img.resize(64, 64)
	var sum := Vector3.ZERO
	var w := 0.0
	for y in 64:
		for x in 64:
			var c := img.get_pixel(x, y)
			sum += Vector3(c.r, c.g, c.b) * c.a
			w += c.a
	var avg := sum / maxf(w, 1e-3)
	var col := Color(avg.x, avg.y, avg.z)
	if int(m.get_shader_parameter("tint_mode")) == 1:
		col *= m.get_shader_parameter("tint")
	return col


func _soften(mi: MeshInstance3D) -> void:
	var m := (mi.material_override as ShaderMaterial).duplicate() as ShaderMaterial
	var img: Image = (m.get_shader_parameter("albedo_tex") as Texture2D).get_image()
	if img.is_compressed():
		img.decompress()
	var w := img.get_width()
	var h := img.get_height()
	img.resize(w / 3, h / 3, Image.INTERPOLATE_LANCZOS)      # the grain eased: down and back up
	img.resize(w, h, Image.INTERPOLATE_CUBIC)
	img.generate_mipmaps()
	m.set_shader_parameter("albedo_tex", ImageTexture.create_from_image(img))
	m.set_shader_parameter("sheen", 1.0)
	mi.material_override = m


func _replace(fig: Fig3Figure, olds: Array, new_name: String, fit: float) -> void:
	var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
	var colour := _hair_colour(olds[0])
	# the old hair's box, in the skeleton's space (its bind pose)
	var box := AABB()
	for i in olds.size():
		var b: AABB = (olds[i] as MeshInstance3D).get_aabb()
		box = b if i == 0 else box.merge(b)
	# the old hair mesh carries the beard too (Hair 2: moustache and goatee): only its part above the mouth goes
	var up0 := ((sk.global_transform.basis.inverse()) * Vector3.UP).normalized()
	var lo := up0.dot(box.get_center()) - 0.5 * (absf(up0.x) * box.size.x + absf(up0.y) * box.size.y + absf(up0.z) * box.size.z)
	var hi := lo + (absf(up0.x) * box.size.x + absf(up0.y) * box.size.y + absf(up0.z) * box.size.z)
	var cut := lo + (hi - lo) * float(get_parent().args.get("cut", "0.42"))
	for mi in olds:
		var m := (mi as MeshInstance3D).material_override as ShaderMaterial
		var m2 := m.duplicate() as ShaderMaterial
		var code := m.shader.code
		code = code.replace("varying vec2 logo_uv;", "varying vec2 logo_uv;\nvarying vec3 cut_lp;\nuniform vec3 cut_axis;\nuniform float cut_at;")
		code = code.replace("void vertex() {", "void vertex() {\n\tcut_lp = VERTEX;")
		code = code.replace("void fragment() {", "void fragment() {\n\tif (dot(cut_lp, cut_axis) > cut_at) discard;")
		var shd := Shader.new()
		shd.code = code
		m2.shader = shd
		m2.set_shader_parameter("cut_axis", up0)
		m2.set_shader_parameter("cut_at", cut)
		(mi as MeshInstance3D).material_override = m2
	colour *= float(get_parent().args.get("bright", "1.35"))
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var path := "res://content/characters/hair_test/%s.gltf" % new_name
	if doc.append_from_file(ProjectSettings.globalize_path(path), st) != OK:
		print("[hair] no ", path)
		return
	var scene: Node3D = doc.generate_scene(st)
	var hm: MeshInstance3D = scene.find_children("*", "MeshInstance3D", true, false)[0]
	var nb := hm.get_aabb()
	# the skeleton's own axes (the client's: z up): which way is up and forward for this figure; MakeHuman's are y up,
	# z forward, x to the figure's left
	var inv := sk.global_transform.basis.inverse()
	var up := (inv * Vector3.UP).normalized()
	var fwd := (inv * (fig.global_transform.basis * Vector3(0, 0, 1))).normalized()
	var lat := up.cross(fwd).normalized()
	var r := Basis(lat, up, fwd)
	var rb: AABB = Transform3D(r, Vector3.ZERO) * nb
	var along := func(b: AABB, ax: Vector3) -> float: return absf(ax.x) * b.size.x + absf(ax.y) * b.size.y + absf(ax.z) * b.size.z
	# fitted: as wide as the old hair (a little over, to sit on it), its top at the old top, centred
	var s: float = along.call(box, lat) / along.call(rb, lat) * fit
	var oc := box.get_center()
	var o := oc - r * nb.get_center() * s
	o += up * (0.5 * along.call(box, up) - 0.5 * along.call(rb, up) * s + 0.01 * along.call(box, up))
	var t_model := Transform3D(r * Basis.from_scale(Vector3.ONE * s), o)
	var head := sk.find_bone("Bip01 Head")
	var att := BoneAttachment3D.new()
	att.bone_name = "Bip01 Head"
	sk.add_child(att)
	att.add_child(scene)
	scene.transform = sk.get_bone_global_rest(head).affine_inverse() * t_model
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = NEW_HAIR_SHADER
	mat.shader = sh
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://content/characters/hair_test/%s_strands.png" % new_name))
	img.generate_mipmaps()
	mat.set_shader_parameter("strands", ImageTexture.create_from_image(img))
	mat.set_shader_parameter("colour", colour)
	hm.material_override = mat
	print("[hair] old box ", box, " up ", up, " fwd ", fwd, " scale ", s, " colour ", colour)


## B: the hair's own shape (and its beard), its texture redrawn as strands following the painting's flow
## (pipeline/hair_strands.py), and a few layers lifted off it whose strands are cut out - a soft, wispy surface
## instead of a painted shell.
func _strand_hair(fig: Fig3Figure, olds: Array, layers: int, depth: float) -> void:
	var m0 := (olds[0] as MeshInstance3D).material_override as ShaderMaterial
	var key := String((m0.get_shader_parameter("albedo_tex") as Texture2D).resource_path.get_file().get_basename())
	if key == "":
		key = String(get_parent().args.get("hairtex", "bri_m_hair02_blonde"))
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://content/characters/hair_test/%s_strands.png" % key))
	if img == null:
		print("[hair] no strands for ", key)
		return
	img.generate_mipmaps()
	var tex := ImageTexture.create_from_image(img)
	var mimg := Image.load_from_file(ProjectSettings.globalize_path("res://content/characters/hair_test/%s_strands_mask.png" % key))
	mimg.generate_mipmaps()
	var mask := ImageTexture.create_from_image(mimg)
	var code: String = m0.shader.code
	code = code.replace("varying vec2 logo_uv;", "varying vec2 logo_uv;\nuniform float shell_off = 0.0;\nuniform float shell_cut = 0.0;\nuniform sampler2D shell_mask : filter_linear_mipmap;")
	code = code.replace("void vertex() {", "void vertex() {\n\tVERTEX += NORMAL * shell_off;")
	code = code.replace("//CUTOUT", "if (shell_cut > 0.0) {\n\t\tALPHA = c.a * smoothstep(shell_cut, shell_cut + 0.15, texture(shell_mask, UV).r);\n\t\tALPHA_SCISSOR_THRESHOLD = 0.5;\n\t\tALPHA_ANTIALIASING_EDGE = 0.3;\n\t}\n\t//CUTOUT")
	var shd := Shader.new()
	shd.code = code
	for mi in olds:
		var base_m := ((mi as MeshInstance3D).material_override as ShaderMaterial).duplicate() as ShaderMaterial
		base_m.shader = shd
		base_m.set_shader_parameter("albedo_tex", tex)
		base_m.set_shader_parameter("sheen", 1.0)
		print("[hair] relief was ", base_m.get_shader_parameter("relief"), " metal ", base_m.get_shader_parameter("metal"))
		base_m.set_shader_parameter("relief", float(get_parent().args.get("relief", "0.0")))
		base_m.set_shader_parameter("metal", 0.0)
		base_m.set_shader_parameter("shell_mask", mask)
		(mi as MeshInstance3D).material_override = base_m
		for i in layers:
			var shell := (mi as MeshInstance3D).duplicate() as MeshInstance3D
			mi.get_parent().add_child(shell)
			var sm := base_m.duplicate() as ShaderMaterial
			sm.set_shader_parameter("shell_off", depth * float(i + 1) / float(layers))
			sm.set_shader_parameter("shell_cut", 0.2 + 0.5 * float(i) / float(maxi(layers - 1, 1)))
			shell.material_override = sm
	print("[hair] strands ", key, " layers ", layers, " depth ", depth)


func _ready() -> void:
	get_tree().create_timer(600.0).timeout.connect(func(): print("[hair] timed out"); get_tree().quit())
	v = get_parent()
	var args: Dictionary = v.args
	var out := String(args.get("out", "E:/Offline DAOC 036c/claude-work/walk/hair"))
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
	var shots := [["face", 0.8, 0.0], ["side", 0.8, 75.0], ["back", 0.9, 150.0]]
	for way in String(args.get("ways", "now,new,b")).split(","):
		var fig := Fig3Figure.new()
		v.add_child(fig)
		fig.load_figure(String(args.get("race", "bri_m")))
		fig.apply({"face": 0, "hair": int(args.get("hair", "1")), "hair_color": int(args.get("colour", "1")), "eyes": 2, "skin": 1})
		fig.global_position = base
		fig.rotation.y = face_yaw
		var olds := _hair_meshes(fig)
		print("[hair] ", way, " hair meshes ", olds.map(func(m): return m.name))
		if way == "soft":
			for mi in olds:
				_soften(mi)
		elif way == "b":
			_strand_hair(fig, olds, int(args.get("layers", "3")), float(args.get("depth", "0.18")))
		elif way == "new":
			_replace(fig, olds, String(args.get("new", "short04")), float(args.get("fit", "1.04")))
		fig.play("idle")
		await _frames(4)
		fig.anim.seek(1.0, true)
		fig.anim.pause()
		var sk: Skeleton3D = fig.model.find_children("*", "Skeleton3D", true, false)[0]
		var target: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("Bip01 Head")).origin
		var fwd: Vector3 = (fig.global_transform.basis * Vector3(0, 0, 1)).normalized()
		for sh in shots:
			cam.global_position = target + fwd.rotated(Vector3.UP, deg_to_rad(float(sh[2]))) * float(sh[1]) * fig.scale.x + Vector3(0, 0.08, 0)
			cam.look_at(target + Vector3(0, 0.04, 0))
			await _frames(45)
			var path := "%s_%s_%s.png" % [out, way, sh[0]]
			get_viewport().get_texture().get_image().save_png(path)
			print("[hair] saved ", path)
		fig.queue_free()
		await _frames(2)
	get_tree().quit()

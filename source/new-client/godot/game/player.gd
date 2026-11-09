class_name Player
extends CharacterBody3D
## Player character with two movement modes, chosen in the (temporary) Esc menu and saved; player only, bots are
## decided separately (owner 2026-10-09):
##   modern (default, WoW-style): full-speed strafing, A/D strafe while the right mouse is held, 65% backpedal, body
##     leans into diagonals, strafing plays the run cycle turned toward the side
##   classic (DAoC): A/D always turn, Q/E side-step at the slow side-step speed with the client's side-step clips,
##     slow backward walk, no lean
## Controls (modern):
##   W forward, S backpedal (65% speed), A/D turn, Q/E strafe (A/D strafe while the right mouse button is held)
##   right mouse: steer (character turns with the mouse), left mouse: orbit the camera only, both: run forward
##   keys from Keybinds (the client's keyboard.dat presets): Space jump, NumLock run lock, ScrollLock walk, T torch;
##   wheel zoom. Swimming stays on the surface (1.65: no diving before Trials of Atlantis)
## Strafing is full run speed. Animations are the client's own clips at the client's rates (nif_character.py).
## Fly mode (set_flying, F6 in the viewer): free flight where the camera points, Space up, Ctrl down, Shift fast.

const Mounts := preload("res://game/world/mounts.gd")
const QUIVER_MODELS := {1: 4250, 2: 4251, 3: 4252}   # objects.csv Alb / Mid / Hib Quiver (behind a stowed bow)
const RUN_SPEED := 191.0 * 0.025       # DAoC base run speed (191 units/s) in metres per second
const BACK_SPEED := RUN_SPEED * 0.65   # backpedal, as in WoW
const WALK_SPEED := RUN_SPEED * 0.35
const SWIM_SPEED := RUN_SPEED * 0.65
const TURN_RATE := PI                  # keyboard turning, radians per second (180 degrees)
const MOUSE_TURN := 0.005
const JUMP_VELOCITY := 4.6
const GRAVITY := 18.0
const AIR_CONTROL := 0.1               # how much steering survives in the air
const SWIM_DEPTH := 1.25               # water deeper than this over the ground: you swim (shallower: you wade)
const SWIM_FLOAT := 0.3                # swimming, the feet hang this far under the surface: the swim pose is flat
									   # (head 0.47 m over the feet), so the head and upper back stay out of the water
									   # (owner 2026-10-10: at 1.25 m the swimmer was under the surface)
# classic DAoC side-step and backward speed: the figure's stride per side-step / back-walk cycle in gamedata
# monnifs.csv (75 units per 1 s clip), i.e. the speed at which the client's own clips play naturally (gap-fill reading)
const CLASSIC_SIDE_SPEED := 75.0 * 0.025
const CLASSIC_BACK_SPEED := 75.0 * 0.025
# Ground movement copies the client's player update (game.dll 0x4365b2, see WORLD IMPORT LESSONS.md):
#   1. move; 2. ground pick straight down from max(64 units, this frame's drop) above the feet: any floor found above
#   the feet lifts the player onto it (this is the client's step-up: anything up to 64 units = 1.6 m that the pick
#   sees); 3. walls: the collider is tested against collision geometry only, contact normals flattened (pure walls);
#   4. second pick: floor within 1 unit below -> stand on it, else airborne and gravity takes over (no step-down snap).
const PICK_LIFT := 64.0 * 0.025
const FLOOR_SNAP := 1.0 * 0.025
const FALL_HEIGHT := 16.0 * 0.025       # client: only more than 16 units above the floor counts as falling (fall flags at
                                       # game.dll 0x4369e0); smaller drops while walking (downhill, off a step) follow the
                                       # ground, so running down a slope never switches to the falling animation
# The client's wall collider bottom sits above the feet: entity+0x44 is 0 for players (it is the random hover height
# of floating monsters), so the lift comes from the figure's bounding volume, which isn't readable statically. Pinned by
# client data: at the Mag Mell platform the model's own COLLIDEE mesh (houtwall 'collider ext08') covers the 0.26 m
# edge and the client still walks up it, so the bottom is above 0.26 m. Raised 2026-10-09 by the next client case: the
# Lethantis Association tower's stairs (Campacorentin Forest) have 0.37 m and 0.40 m risers (16 units, measured with
# tests/steps_probe.gd) that a walking player climbs in the client, so the bottom is above 0.40 m. Raised 2026-10-11 by
# the owner's old-client video: Caer Gothwaite's doorway (Isle of Glass, 1098 / 1370) has a 0.59 m threshold the client
# walks through without jumping (tests/step_probe.gd stopped at it at 0.45), so the bottom is above 0.59 m. The bots use
# this same value (BotSim reads it from here - bots and players share rules, owner).
const COLLIDER_LIFT := 0.62
const STEP_LEAD := 0.25                 # the wall collider's radius: where the leading-edge floor pick looks
# Too steep to stand on (owner 2026-11-01: "I was able to run up the side of the walls" - a keep's battered walls are
# floors to the pick): ground steeper than this can't be walked up, and standing on it you slide down off it. Stairs
# are unaffected (their treads are flat; the step-up lifts you over the risers), and so is a short steep face - the
# owner's 2026-11-02 video: a hut's stone footing, 0.7 m of sloped stones, stopped you at the door. Only ground that
# stays steep for STEEP_RUN_M counts (a wall's face does; a footing, a sill or a bevel doesn't).
const MAX_SLOPE_DEG := 55.0
const SLIDE_MPS := 7.0                   # sliding down ground too steep to stand on
const STEEP_RUN_M := 1.2                 # how far up the slope it must keep rising that steeply
# Ladders (game.dll RE 2026-10-10): touching a 'climb' wall (ZoneLoader ClimbBodies) puts the client in move state 7
# ("You start climbing."): forward climbs at 85 units/s x min(1, speed / 100), back climbs down at the same rate
# (0x439d19); landing while climbing down, or a jump, ends it ("You are no longer climbing.", 0x436b20 / 0x438731).
const CLIMB_SPEED := 85.0 * 0.025
# camera distance, from the client (game.dll 0x4ac407 clamps "cameradistance" to 50..500 units; 1500 only while linked
# to a siege engine / mount, 0x43f60c): 1.25 m to 12.5 m. Test runs keep a free camera (free_camera).
const CAM_MIN := 50.0 * 0.025
const CAM_MAX := 500.0 * 0.025
const CAM_MAX_FREE := 40.0
const CAM_PITCH := deg_to_rad(50.0)     # client: camera pitch clamped to -50..50 degrees (game.dll 0x4ac471)
# The torch, from the client (game.dll 0x43e5a4 "torch on" -> 0x47d4f4): two white point lights on a node 128 units
# (3.2 m) above the figure. Light 1: dimmer 200 x 0.01 = 2.0; light 2 (lights only scene group 0x2459dbc, not drawn
# yet): 200 x 0.0025 = 0.5. Both fall off as 1 / (0.006 d + d^2 / 147456) (d in units): full at ~6.8 m, about 0.6 at
# 10 m, 0.2 at 20 m. On by default, saved ("torchmode" in the client's user.dat); T (or Shift+T) toggles it.
const TORCH_HEIGHT := 128.0 * 0.025
const TORCH_RANGE := 30.0
const TORCH_ENERGY := 3.0              # mine: client dimmer 2.0 against the zone lights' 1.5 -> 2.2 base in this engine
const FLY_SPEED := 18.0
const FLY_FAST := 70.0

var zone: ZoneLoader
var region: RegionWorld                  # seamless zones: the ground / water of whichever loaded zone you stand over
var edges: Node                          # the world's edge (world/edge_veil.gd): you stop short of it (allows)
var in_combat := false                 # attack mode: weapon drawn, combat idle (Combat)
var combat_stance := ""                 # "" one-hand, "2h", "staff", "pole" (WeaponModels.stance)
var dead := false
var sitting := false                   # /sit (Combat.sit): sit_down once, then sit_idle until standing up
var speed_mult := 1.0                  # sprint (x1.3, Abilities)
var cc := ""                           # "stun" / "mez" / "root" from monster spells (Casting): no moving
var snare_mult := 1.0                  # snares: the run speed's share left
var shade := false                       # a Necromancer with a servant up (Pets)
var riding := false                     # on a stable horse (HorseRoutes moves you; jump gets you off)
var mount: Node3D = null                # your own horse under you (the server's ControlledHorse: Mounts) - you still steer
var ride_clip := "ride_horse"          # the rider's pose: ride_horse, or a flight's ride_griffon / _amphitere / _dragonfly
var stealth_mult := 1.0                 # hidden: Abilities.toggle_stealth's speed share
var encumbrance := 1.0                  # PlayerData.encumbrance_mult (refreshed when the inventory changes)
var buff_speed := 1.0                  # speed buffs (Combat from Casting's buff sums): Value % of normal
var _death_played := false
var _action := ""                       # a one-shot clip playing over idle: a swing, a flinch
var _action_left := 0.0
var _gear: Array = []                   # weapon holders on the attach bones
var char_yaw := 0.0                    # where the character faces; forward = -Z rotated by this
var cam_yaw := 0.0                     # camera heading (differs from char_yaw while orbiting with the left mouse)
var cam_pitch := -0.22
var cam_distance := 5.5
var swimming := false
var climbing := false                    # on a ladder (state 7)
var _climb_vy := 0.0
signal landed(fall_speed_units: float)   # touched ground from a fall: the downward speed (units / s)
var flying := false
var autorun := false
# /follow, /stick, /face (patch notes 2001: /follow "until you break off by moving in another direction"; /stick to
# fight closely, "breaks if the target gets outside of a certain range"; /face auto-faces a target)
var track_target: Node3D = null
var track_mode := ""                    # "", "follow", "stick", "face"
var track_name := ""
const FOLLOW_GAP_M := 3.0
const STICK_GAP_M := 1.4
const TRACK_START_M := 1000 * 0.025     # "unless you are relatively close to them"
const STICK_BREAK_M := 1500 * 0.025
var walking := false
var force_clip := ""                   # tests: hold one animation regardless of movement
var movement_mode := "modern"          # "modern" or "classic" (Esc menu)
var input_enabled := true              # false while a menu is open
var mouse_sensitivity := 1.0           # Options: CONTROLS
var invert_mouse := false
var _lmb_world := false                # mouse buttons pressed on the world (not on an interface window)
var _rmb_world := false
var _cursor_at := Vector2.ZERO          # where the cursor was when a mouse-look drag began
# Action Combat (ActionCombatMode, owner 2026-10-26): the mouse always looks and steers (no button held), A/D strafe,
# the mouse buttons fight. action_cursor: the cursor is out for the interface (Alt held) - the mouse doesn't look.
var action_mode := false
const FREE_TURN_RATE := 12.0             # action combat free look: how fast the body turns to where you run
var action_cursor := false
var aiming := false                     # drawing a bow in action combat: you stand to shoot (turning still aims)
var _defend_clip := ""                  # the parry / block / evade you just tried (a blow landing cuts it off)
var _defend_slow_left := 0.0            # ... and while it plays you move at half speed
var cam_kick := 0.0                      # a landed blow's small camera jolt (decays)
var shoulder := Vector2.ZERO             # action combat's over-the-shoulder view: metres right / up (Camera3D offsets)
var _dash := Vector3.ZERO               # a dodge's burst (world velocity, decays)
const AC_BUTTONS := ["ac_attack", "ac_parry", "ac_position", "ac_reactive", "ac_chain", "ac_dodge", "ac_cursor", "ac_hud",
		"ac_interact", "ac_shot", "ac_crit_shot", "ac_parry_only", "ac_lock"]
var _charge_fx: Node3D = null            # the heavy attack's charge: a glow on the weapon (the game's weapon effects)
var _dash_left := 0.0
var grounded := false
var _air_time := 0.0                   # seconds off the ground (the falling pose waits a moment)
var hold_frames := 12                   # after a spawn / teleport: stand still until the floors are in the physics world
var _floor_n := Vector3.UP               # the last floor pick's surface normal (_floor_below)
var _last_footing := Vector3.ZERO       # the last spot stood on (a fall into the void comes back here)
var free_camera := false               # test runs only: zoom out past the client's limit
var torch: OmniLight3D
var torch_on := true
var _strides := {}                     # monnifs.csv strides (units per cycle) from the character's .json sidecar
var _clip_len := {}

var _model: Node3D
var sounds: CharacterSounds             # footsteps / swim strokes from the client's creature sound sheet
var _figure := ""
var _anim: AnimationPlayer
var _pivot: Node3D
var _arm: SpringArm3D
var _body_offset := 0.0                # model lean toward diagonal movement, like WoW's 45-degree run
var camera: Camera3D


func _ready() -> void:
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = STEP_LEAD                           # (0.35 caught the next riser of steep stairs before the lift)
	capsule.height = 1.8 - COLLIDER_LIFT
	shape.shape = capsule
	shape.position.y = COLLIDER_LIFT + capsule.height * 0.5
	add_child(shape)
	motion_mode = CharacterBody3D.MOTION_MODE_FLOATING   # every contact is a wall (the client flattens normals)
	collision_layer = 0
	collision_mask = ZoneLoader.LAYER_WALL
	# encumbrance follows the inventory and strength (buffs / debuffs change it too)
	# (the launcher's server game: the server decides your speed - its MaxSpeed packet, encumbrance included -
	# ServerWorld sets `encumbrance` from it; the game's own weight sums don't apply)
	if not Server.active:
		PlayerData.hook(self, PlayerData.inventory_changed, func(): encumbrance = PlayerData.encumbrance_mult())
		PlayerData.hook(self, PlayerData.effects_changed, func(): encumbrance = PlayerData.encumbrance_mult())
		encumbrance = PlayerData.encumbrance_mult()

	torch = OmniLight3D.new()
	torch.name = "Torch"
	torch.position.y = TORCH_HEIGHT
	torch.light_color = Color.WHITE
	torch.omni_range = TORCH_RANGE
	torch.omni_attenuation = 1.0
	torch.shadow_enabled = false                         # the client's fixed-function point lights cast no shadows
	torch.light_volumetric_fog_energy = 0.25             # (remastered fog: no bright ball of haze round you)
	add_child(torch)
	var cfg := ConfigFile.new()
	cfg.load("user://settings.cfg")
	set_torch(bool(cfg.get_value("player", "torch", true)))
	mouse_sensitivity = float(cfg.get_value("player", "mouse_sensitivity", 1.0))
	invert_mouse = bool(cfg.get_value("player", "invert_mouse", false))
	_register_torch.call_deferred()

	_pivot = Node3D.new()
	_pivot.position.y = 1.55
	add_child(_pivot)
	_arm = SpringArm3D.new()
	_arm.spring_length = cam_distance
	_arm.collision_mask = ZoneLoader.LAYER_WALL | ZoneLoader.LAYER_FLOOR | ZoneLoader.LAYER_SCENERY
	# a small sphere swept along the arm, not a thin ray (owner 2026-10-28: the camera clipped through walls and
	# terrain - a ray let the near plane cut into a wall it grazed); _process also keeps it above ground and water
	var cam_ball := SphereShape3D.new()
	cam_ball.radius = CAM_BALL
	_arm.shape = cam_ball
	_arm.margin = 0.05
	_arm.add_excluded_object(get_rid())
	_pivot.add_child(_arm)
	camera = Camera3D.new()
	camera.far = 1500.0
	camera.fov = 70.0
	_arm.add_child(camera)
	camera.make_current()


func set_model(path: String) -> void:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		push_warning("player model missing: " + path)
		return
	_model = doc.generate_scene(state) as Node3D
	add_child(_model)
	var meta_path := path.get_basename() + ".json"
	if FileAccess.file_exists(meta_path):
		var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(meta_path))
		_strides = meta.get("strides_units", {})
		_clip_len = meta.get("clip_seconds", {})
		_figure = String(meta.get("sound_figure", meta.get("figure", "")))   # Catacombs cel_m uses the Celt sound set
	var players := _model.find_children("*", "AnimationPlayer", true, false)
	if players.size() > 0:
		_anim = players[0] as AnimationPlayer
		_set_loops()
		Fig3Figure.add_rest_reset(_anim)                     # bones a clip doesn't key go back to rest
		_play("idle")
		var idx = JSON.parse_string(FileAccess.get_file_as_string("res://content/sounds/sounds.json"))
		var sound_set := int(idx.get("model_sound_sets", {}).get(_figure, 0)) if idx is Dictionary else 0
		if sound_set > 0:
			sounds = CharacterSounds.new()
			sounds.name = "Sounds"
			add_child(sounds)
			sounds.setup(_model, _anim, sound_set)
	for node in _model.find_children("*", "MeshInstance3D", true, false):
		var mesh := (node as MeshInstance3D).mesh
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i) as StandardMaterial3D
			if mat and mat.albedo_texture:
				var img := mat.albedo_texture.get_image()
				img.generate_mipmaps()
				mat.albedo_texture = ImageTexture.create_from_image(img)
				mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_apply_model_yaw()


## A Catacombs race figure made on the character screens (CharacterStore entry: prefix + look).
func set_figure(c: Dictionary) -> void:
	var fig := Fig3Figure.new()
	fig.name = "Figure"
	add_child(fig)
	if not fig.load_figure(String(c.get("prefix", "cel_m"))):
		fig.queue_free()
		return
	fig.apply(c.get("look", {}))
	_model = fig
	_anim = fig.anim
	_set_loops()
	_strides = fig.meta.get("strides_units", {})
	_clip_len = fig.meta.get("clip_seconds", {})
	var sound_set := int(fig.meta.get("sound_set", 0))
	if sound_set > 0 and _anim:
		sounds = CharacterSounds.new()
		sounds.name = "Sounds"
		add_child(sounds)
		sounds.setup(fig.model, _anim, sound_set)
	_play("idle")
	_apply_model_yaw()
	refresh_gear.call_deferred()                           # the worn weapons, sheathed


## The server changed your model (ModelChange): a necromancer's shade, a berserker's Vendo form, an illusion - drawn
## as that monster model (monsters.json entry with "gltf") with its own clips; your race model again (an entry
## without "gltf") puts your figure and gear back (owner 2026-10-11: necromancers didn't become shades).
var _morph: Node3D
var _morph_casts := {}                         # a morph model's casting clips (monsters.json cast_clips)
var _unmorphed := {}                     # your figure while morphed: model, anim, strides, clip lengths


func morph(info: Dictionary) -> void:
	if hidden_look:
		_apply_hidden_look.call_deferred()                 # (the new figure goes see-through too)
	if _morph and is_instance_valid(_morph):
		_morph.queue_free()
	_morph = null
	if not _unmorphed.is_empty():
		_model = _unmorphed.model
		_anim = _unmorphed.anim
		_strides = _unmorphed.strides
		_clip_len = _unmorphed.clip_len
		_unmorphed = {}
		_morph_casts = {}
		if _model:
			_model.visible = true
	var path := String(info.get("gltf", ""))
	if path == "" or _model == null:
		_apply_model_yaw()
		return
	# the glTF with its skin, as the NPC views load it (the packed .scn has its textures taken out - drawn untextured,
	# your shade was a plain solid figure)
	var m: Node3D = null
	var ps := NpcManager._pack_model(path)
	if ps:
		m = ps.instantiate() as Node3D
	if m == null:
		push_warning("morph model missing: " + path)
		return
	_unmorphed = {"model": _model, "anim": _anim, "strides": _strides, "clip_len": _clip_len}
	_model.visible = false                                 # your figure and the gear on its bones
	m.scale *= float(info.get("scale", 1.0))
	m.position.y += Npc.figure_look(m, info, get_instance_id())   # skin alpha + hover (the shade floats, see-through)
	add_child(m)
	_morph = m
	_model = m
	var players := m.find_children("*", "AnimationPlayer", true, false)
	_anim = players[0] as AnimationPlayer if players.size() > 0 else null
	_set_loops()
	if _anim:
		Fig3Figure.add_rest_reset(_anim)
	_strides = info.get("strides_units", {})
	_clip_len = info.get("clip_seconds", {})
	_morph_casts = info.get("cast_clips", {})            # (its anim set's own clip per casting style: Npc.clip_for)
	_apply_model_yaw()
	_play("idle")


## The client's clamp clips play once (jump, land, death, swings, flinch, parry, evade); the rest loop.
func _set_loops() -> void:
	if _anim == null:
		return
	for clip in _anim.get_animation_list():
		_anim.get_animation(clip).loop_mode = Animation.LOOP_LINEAR if Fig3Figure.loops(clip) else Animation.LOOP_NONE


func _play(clip: String, speed := 1.0) -> void:
	if _anim == null or not _anim.has_animation(clip):
		return
	var fig := _model as Fig3Figure
	if fig and fig.move_clip(clip):                 # (remastered: a stop's last step under way - Fig3Figure.move_clip)
		return
	if _anim.current_animation != clip:
		_anim.play(clip, 0.15)
	_anim.speed_scale = speed * (fig.pace_factor() if fig and (clip == "run" or clip == "walk") else 1.0)


## Wounded: the 1.65 client's own rule (game.dll 0x438b5c, after the run speed from the server's MaxSpeed percent): below
## 35% health the speed is scaled by health / 35, never under a tenth - the server slows only NPCs (MaxSpeedCalculator),
## so the new client ran at full speed at any health (owner 2026-10-16). Not while flying (the GM speed case).
func _wounded_mult() -> float:
	var pct := int(PlayerData.health * 100.0)
	if flying or pct >= 35:
		return 1.0
	return maxf(pct / 35.0, 0.1)


func set_flying(on: bool) -> void:
	flying = on
	collision_mask = 0 if on else ZoneLoader.LAYER_WALL   # fly through buildings and terrain
	_arm.collision_mask = 0 if on else ZoneLoader.LAYER_WALL | ZoneLoader.LAYER_FLOOR | ZoneLoader.LAYER_SCENERY
	velocity = Vector3.ZERO


# --- combat (game/combat/combat.gd drives these) ------------------------------------------------------------------

func facing() -> float:
	return char_yaw


## The stance's version of a combat clip: combat_idle -> combat_idle_2h / _staff / _pole; attack_med ->
## attack_2h_med ... (canims.csv columns, build_races.py), falling back to the one-hand clip.
func _combat_clip(base: String) -> String:
	return WeaponModels.stance_clip(_anim, combat_stance, base)


## The active weapon's stance (WeaponModels.STANCES; the ranged set: bow / xbow / throw): the clips its swings and
## combat idle use.
func weapon_stance() -> String:
	if PlayerData.active_weapon == "ranged":
		return WeaponModels.ranged_kind(int(PlayerData.item_at(13).get("model", 0)))
	return WeaponModels.stance(int(MeleeMath.weapon(PlayerData).get("model", 0)))


func set_combat(on: bool, stance: String) -> void:
	in_combat = on
	combat_stance = stance
	refresh_gear()


## One swing: a random high / medium / low attack clip for the weapon's stance; hand "left" / "dual" a dual
## wielder's off-hand / both-weapons blow (the server's OneDualWeaponHit / BothDualWeaponHit). Returns the clip played.
func swing(stance: String, hand := "") -> String:
	leave_mount()
	combat_stance = stance
	var clip := WeaponModels.attack_clip(_anim, combat_stance, hand)
	_one_shot(clip)
	WeaponModels.flex_swing(self, clip)                    # a flex weapon's chain swings with the blow
	return clip


## A defence (canims.csv Parry / Evade / Block columns): the clip for the weapon's stance - one-hand, two-hand or
## polearm / staff; parries and blocks pick the low or the high one.
func defend(kind: String) -> void:
	if dead or _action_left > 0.0:
		return
	var clip := WeaponModels.defend_clip(_anim, combat_stance, kind)
	if clip != "":
		_one_shot(clip)


## A style's own animation (styles.csv Animation -> canims.csv column, content/characters/style_clips.json); returns
## the clip played, or "" when this figure has none (the generic swing plays instead).
## An emote (the client's emotes.csv id; build_races.py clip 'emote_<id>'). False when the figure lacks it.
func play_emote(id: int) -> bool:
	var clip := "emote_%d" % id
	if _anim == null or not _anim.has_animation(clip):
		return false
	_one_shot(clip)
	return true


func play_style(animation: int) -> String:
	var clip := String(Player.style_clips().get(str(animation), ""))
	if clip == "" or _anim == null or not _anim.has_animation(clip):
		return ""
	_one_shot(clip)
	WeaponModels.flex_swing(self, clip, true)              # the chain's own style swing
	return clip


static var _style_clips := {}


static func style_clips() -> Dictionary:
	if _style_clips.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://content/characters/style_clips.json"))
		_style_clips = parsed if parsed is Dictionary else {"": ""}
	return _style_clips


## The bow (canims Bow Ready / Bow Aim / Bow Fire; a crossbow's Xbow, a thrown weapon's Throw clips): draw, hold the
## aim, loose.
func bow_draw() -> void:
	leave_mount()
	_one_shot(_ranged() + "_ready")
	_bow_hold = true


func bow_release(fired: bool) -> void:
	_bow_hold = false
	if fired:
		_one_shot(_ranged() + "_fire")
	else:
		_action_left = 0.0


var _bow_hold := false


func _ranged() -> String:
	if combat_stance in WeaponModels.RANGED:
		return combat_stance
	return WeaponModels.ranged_kind(int(PlayerData.item_at(13).get("model", 0)))


## Action Combat: the parry / block / evade you try plays at once, hit or miss (owner 2026-10-26) - whatever was
## playing gives way to it - and you move at half speed while it does. A blow that gets through cuts it off (flinch).
func action_defend(kind: String) -> void:
	leave_mount()
	if dead or _anim == null:
		return
	var clip := WeaponModels.defend_clip(_anim, combat_stance, kind)
	if clip == "" and kind == "block":
		clip = WeaponModels.defend_clip(_anim, combat_stance, "parry")
	if clip == "":
		return
	_action_left = 0.0
	_one_shot(clip)
	_defend_clip = clip
	_defend_slow_left = clip_seconds(clip)


## A fully charged heavy attack: the drawn weapon glows gold (the client's own weapon effects - spweapons.csv's
## gold glows, by the weapon's stance) until the blow goes.
const CHARGE_GLOW_SCALE := 0.6
const CHARGE_GLOW_FADE := 0.5
const CHARGE_GLOW := {"": 11, "2h": 32, "scy": 32, "pole": 78, "staff": 92, "h2h": 11}


func charge_glow(on: bool) -> void:
	if not on:
		if is_instance_valid(_charge_fx):
			_charge_fx.queue_free()
		_charge_fx = null
		return
	if is_instance_valid(_charge_fx) or _model == null or not in_combat:
		return
	var holder: Node3D = null
	for h in _model.find_children("Weapon_*", "", true, false):
		var at := (h as Node).get_parent()
		if at is BoneAttachment3D and String((at as BoneAttachment3D).bone_name) in ["Bip01 R Held", "Bip01 R Hand"]:
			holder = h
			break
	if holder == null:
		return
	_charge_fx = WeaponModels.add_effect(holder, int(CHARGE_GLOW.get(combat_stance, 11)))
	if _charge_fx == null:
		return
	# subtler (owner 2026-10-28: "a smaller one, or dimmer one?"): smaller, see-through, and a faint light
	_charge_fx.scale *= CHARGE_GLOW_SCALE
	NifParticles.fit_to_scale(_charge_fx)
	for g in _charge_fx.find_children("*", "GeometryInstance3D", true, false):
		(g as GeometryInstance3D).transparency = maxf((g as GeometryInstance3D).transparency, CHARGE_GLOW_FADE)
	for l in _charge_fx.find_children("FxLight*", "OmniLight3D", true, false):
		(l as OmniLight3D).light_energy *= 0.35


## Hidden (Stealth, the server's PlayerModelTypeChange 3): you are drawn see-through, as the old client showed you
## to yourself (and to your realm) while stealthed - your gear with you; refresh_gear keeps it on new gear.
var hidden_look := false


func set_hidden_look(on: bool) -> void:
	hidden_look = on
	_apply_hidden_look()


func _apply_hidden_look() -> void:
	# meshes only (particles hide themselves by their own transparency - NifScene), each one's own value kept to restore
	for g in find_children("*", "MeshInstance3D", true, false):
		var mi := g as MeshInstance3D
		# the figure's own parts dither (Fig3Figure SHADER "fade"): blended, the head and hair sorted against the body
		# and stayed solid or vanished with the camera (owner 2026-10-31)
		var fm := mi.material_override as ShaderMaterial
		if fm and fm.shader and fm.shader.code.contains("uniform float fade"):
			fm.set_shader_parameter("fade", 0.35 if hidden_look else 1.0)
			if mi.has_meta("_hid_t"):
				mi.transparency = float(mi.get_meta("_hid_t"))
				mi.remove_meta("_hid_t")
			continue
		if hidden_look:
			if not mi.has_meta("_hid_t"):
				mi.set_meta("_hid_t", mi.transparency)
			mi.transparency = maxf(float(mi.get_meta("_hid_t")), 0.72)
		elif mi.has_meta("_hid_t"):
			mi.transparency = float(mi.get_meta("_hid_t"))
			mi.remove_meta("_hid_t")


func flinch() -> void:
	var over_defense := _defend_clip != "" and _action == _defend_clip and _action_left > 0.0
	if (_action_left <= 0.0 or over_defense) and not dead:
		_defend_clip = ""
		_defend_slow_left = 0.0
		_one_shot("flinch")


func _one_shot(clip: String) -> void:
	clip = String(_morph_casts.get(clip, clip))             # (morphed: the form's own clip for a casting style)
	if _anim == null or not _anim.has_animation(clip):
		return
	_action = clip
	_action_left = clip_seconds(clip)
	_anim.play(clip, 0.1)
	_anim.seek(0.0, true)
	_anim.speed_scale = 1.0


## Casting (anims.csv Cast Start / Cast Mid / Cast End): the start once, the mid pose looping while the cast bar
## fills, the end once when the spell lands (an interrupted cast just drops back to idle).
## The spell's own casting style (spells.csv Anim1-3 via SpellFx: Crossed, 1H Circ, Upraised...): start / mid / end
## clip names; the plain cast_start / cast_mid / cast_end when the figure lacks them.
var _cast_clips := ["cast_start", "cast_mid", "cast_end"]


## seconds: the cast's time (the server's SpellCastAnimation); the pose then ends on its own CAST_GRACE after it
## if neither the spell nor an interruption ever comes (owner 2026-10-14: a heal on a companion that died mid-cast, or
## running off while casting, left the casting pose stuck - the server dropped the cast without a word).
const CAST_GRACE := 2.0
var _cast_left := INF


func cast_start(clips: Array = [], seconds := -1.0) -> void:
	casting_spell = true
	_cast_left = seconds if seconds >= 0.0 else INF
	_cast_clips = [String(_morph_casts.get("cast_start", "cast_start")), String(_morph_casts.get("cast_mid", "cast_mid")),
			String(_morph_casts.get("cast_end", "cast_end"))]
	for i in mini(clips.size(), 3):
		var c := String(_morph_casts.get(String(clips[i]), clips[i]))   # a shade / Vendo form: its own cast clips
		if c != "" and _anim and _anim.has_animation(c):
			_cast_clips[i] = c
	_one_shot(_cast_clips[0])


func cast_end(landed := false) -> void:
	casting_spell = false
	if landed:
		_one_shot(_cast_clips[2])
	else:
		_action_left = 0.0


var casting_spell := false


func clip_seconds(clip: String) -> float:
	return float(_clip_len.get(clip, 1.0))


## The figures' "Stand Up" clip (anims.csv) is the 8 s standing idle, not a rise (pelvis never leaves standing height),
## and playing it out slid a moving player along for 4-8 s (owner 2026-10-10): standing up is the sit-down played
## backwards (0.8-1.5 s), and moving cuts it short (_animate).
## Action combat: the character faces where the camera looks only with the weapon out, a spell being cast or a bow
## drawn (owner 2026-10-28) - otherwise the camera looks around freely.
func _faces_camera() -> bool:
	return action_mode and (in_combat or casting_spell or aiming)


## Action combat's lock-on target (ActionCombatMode sets it; null when nothing is locked). While locked, the character
## faces the target - standing still, weapon out, casting - and is snapped to it before any spell / ability goes to
## the server, so a caster never has to turn by hand (owner 2026-11-01).
var lock_target: Node3D = null
## The target of the spell / ability just used (ActionCombatMode.before_use): faced while the cast lasts, locked on or
## not - the server checks the heading at the start and the end of a cast (owner 2026-11-01).
var cast_target: Node3D = null
var cast_target_until := 0


func _lock_yaw() -> float:
	var t: Node3D = lock_target
	if t != null and (not is_instance_valid(t) or not t.is_inside_tree()):
		lock_target = null
		t = null
	if t == null and cast_target != null:
		if not is_instance_valid(cast_target) or not cast_target.is_inside_tree():
			cast_target = null
		elif casting_spell or Time.get_ticks_msec() < cast_target_until:
			t = cast_target
	if t == null:
		return NAN
	var d := t.global_position - global_position
	if Vector2(d.x, d.z).length() < 0.3:
		return NAN
	return atan2(-d.x, -d.z)


## Turn at once to the lock target - or `t`, the target of a spell / ability being used - before the request goes
## to the server (it checks the heading it is sent).
func face_lock(t: Node3D = null) -> void:
	if not action_mode or dead or sitting:
		return
	if t != null and t != self:
		cast_target = t
		cast_target_until = Time.get_ticks_msec() + 900
	var y := _lock_yaw()
	if not is_nan(y):
		char_yaw = y


func sit(on: bool) -> void:
	sitting = on
	if on:
		_one_shot("sit_down")
	elif _anim and _anim.has_animation("sit_down"):
		_action = "stand_up"
		_action_left = clip_seconds("sit_down")
		_anim.play_backwards("sit_down", 0.1)
		_anim.speed_scale = 1.0


func die() -> void:
	dead = true
	sitting = false
	in_combat = false
	refresh_gear()


func revive() -> void:
	dead = false
	_death_played = false
	_action_left = 0.0
	_play("idle")


## Draw the weapons where the client hangs them (objects.csv flags, owner rules): in attack mode the active set's
## main weapon in the right hand (a left-hand weapon in the left hand); sheathed, one-handers at the belt and
## two-handers / polearms / staffs on the back. Every set shows (owner 2026-11-02): the ones not in use are stowed -
## the shield on the back while the two-hander is out, a bow slung over the shoulder with its quiver - and only a
## weapon in hand carries its effect.
func refresh_gear() -> void:
	if in_combat:
		combat_stance = weapon_stance()                     # another weapon set drawn in attack mode: its stance
	for g in _gear:
		if is_instance_valid(g):
			g.queue_free()
	_gear.clear()
	var gear_opts: Dictionary = (PlayerData.character.get("gear", {}) if PlayerData.character.get("gear") is Dictionary else {}).duplicate()
	gear_opts["realm"] = {"alb": 1, "mid": 2, "hib": 3}.get(String(PlayerData.character.get("realm", "")), 0)
	_gear = dress(_model, PlayerData.item_at, PlayerData.active_weapon, in_combat, true, gear_opts)
	if hidden_look:
		_apply_hidden_look.call_deferred()


## A figure's worn gear, shared with the character select screen (owner 2026-10-10: the staff / armour didn't show
## there): armour parts on a Fig3Figure (pipeline/build_armor.py), and the active weapon set on its bones. item_at:
## slot -> item Dictionary ({} when empty). Returns the bone attachments made.
## gear: the server's look flags for this character - {"hood": bool, "cloak_hidden": bool, "helm_hidden": bool}.
static func dress(model: Node3D, item_at: Callable, active_weapon: String, combat: bool, armor := true, gear := {}) -> Array:
	var made: Array = []
	if armor and model is Fig3Figure:                               # worn armour on the figure (pipeline/build_armor.py)
		var fig := model as Fig3Figure
		var female := String(fig.meta.get("prefix", "")).ends_with("_f")
		var parts := {}
		var tints := {}
		for slot in [22, 23, 25, 27, 28]:
			var it: Dictionary = item_at.call(slot)
			if not it.is_empty():
				var p := Fig3Figure.armor_parts(int(it.get("model", 0)), female, int(it.get("extension", 0)))
				parts.merge(p, true)
				for k in p:                                         # its dye on the parts it draws
					tints[k] = Fig3Figure.dye(int(it.get("color", 0)))
		var cl: Dictionary = item_at.call(26)                  # the cloak (its hood: /hood)
		if not cl.is_empty():
			var cp := Fig3Figure.armor_parts(int(cl.get("model", 0)), female)
			if cp.has("cloak"):
				parts["cloak"] = cp.cloak
				tints["cloak"] = Fig3Figure.dye(int(cl.get("color", 0)))
		fig.cloak_emblem = int(cl.get("emblem", 0)) if not cl.is_empty() else 0   # its guild emblem
		fig.hood_up = bool(gear.get("hood", false))
		fig.cloak_hidden = bool(gear.get("cloak_hidden", false))
		fig.helm_hidden = bool(gear.get("helm_hidden", false))
		fig.set_armor(parts, tints)
		var hm: Dictionary = item_at.call(21)                  # the helm / hat
		fig.set_helm(int(hm.get("model", 0)) if not hm.is_empty() else 0, fig.helm_hidden, int(hm.get("color", 0)))
	var skel: Skeleton3D = null
	if model:
		var found := model.find_children("*", "Skeleton3D", true, false)
		skel = found[0] if found.size() > 0 else null
	if skel == null:
		return made
	var sets := {"standard": [10, 11], "twohand": [12], "ranged": [13]}
	var active_slots: Array = sets.get(active_weapon, [10, 11])
	# every weapon set shows (owner 2026-11-02: "sheathed weapons that you're not actually using ... should still
	# show up on your back"): the active one in hand in combat, the others stowed - one-handers at the belt, a
	# two-hander on the back, a bow or crossbow slung over the shoulder with a quiver behind it, a shield on the
	# back when the two-hander is out. Only a weapon in hand carries its effect (its glow, its flame).
	var back_taken := {}                                       # "Bip01 R Back" / "Bip01 L Back" -> true
	var frame := BodyFrame.of(skel, model)                     # the figure's own right / up / back (a monster: {})
	for slot in [12, 13, 10, 11]:                              # the two-hander claims the back first
		var it: Dictionary = item_at.call(slot)
		if it.is_empty():
			continue
		var model_id := int(it.get("model", 0))
		var is_active: bool = slot in active_slots
		# an NPC with a shield model in its right hand too (shield merchants' NPCEquipment lists it in both hands): the
		# client draws the right hand's one only (owner 2026-10-11: a shield in both hands; the old client: right arm)
		var shield_model := int(WeaponModels.info(model_id).get("shield", 0)) > 0
		var right: Dictionary = item_at.call(10)
		# (not the hand-to-hand greaves: objects.csv marks them Shield too, and a Savage wears one on each arm)
		if slot == 11 and shield_model and int(WeaponModels.info(model_id).get("stance", 0)) != 13 \
				and int(WeaponModels.info(int(right.get("model", 0))).get("shield", 0)) > 0:
			continue
		var shield: bool = int(it.get("object_type", 0)) == ItemDb.SHIELD_TYPE or (shield_model and slot == 11)
		var stance := WeaponModels.stance(model_id)
		var ranged: bool = slot == 13 or stance in ["bow", "xbow", "throw"]
		var on_back: bool = int(it.get("hand", 0)) == 1 or slot == 12 or ranged or stance in ["2h", "pole", "staff", "scy"]
		# objects.csv "On Belt": only weapons marked sheathable go to the belt / back outside attack mode; the rest -
		# every staff (stance 4, all 118 marked 0), most polearms - stay in the hand (owner 2026-10-10); a set that
		# isn't the active one is stowed whatever it says (a staff on the back behind a drawn sword)
		var sheathes := int(WeaponModels.info(model_id).get("belt", 1)) == 1
		var in_hand: bool = is_active and (combat or not sheathes)
		var bone := ""
		var slung := false
		if shield:
			if is_active:
				bone = "Bip01 L Shield"
			else:
				bone = "Bip01 L Back" if not back_taken.has("Bip01 L Back") else "Bip01 R Back"
		elif in_hand:
			# the skeleton's "Held" nodes under each hand match the weapon NIF's HELD frame (the client's grip point);
			# an item objects.csv marks Shield (the hand-to-hand greaves) on the forearm's Shield bone of its hand -
			# game.dll 0x422806 (owner 2026-10-17: the Savage's right claw floated off its Held bone)
			if shield_model and skel.find_bone("Bip01 R Shield") >= 0:
				bone = "Bip01 L Shield" if slot == 11 or slot == 13 else "Bip01 R Shield"
			else:
				bone = "Bip01 L Held" if slot == 11 or slot == 13 else "Bip01 R Held"
		elif ranged:
			bone = "Bip01 L Back" if not back_taken.has("Bip01 L Back") else "Bip01 R Back"
			slung = true
		elif on_back:
			bone = "Bip01 R Back" if not back_taken.has("Bip01 R Back") else "Bip01 L Back"
		else:
			bone = "Bip01 R Belt" if slot == 11 else "Bip01 L Belt"
		if bone.ends_with("Back"):
			if back_taken.has(bone):
				continue                                       # no third thing on the back
			back_taken[bone] = true
		var idx := skel.find_bone(bone)
		var w := WeaponModels.make(model_id, in_hand, bone == "Bip01 L Held" or bone == "Bip01 L Shield")
		if idx < 0 or w == null:
			push_warning("gear: no %s (bone %d) or no model %d" % [bone, idx, model_id])
			continue
		WeaponModels.dye(w, int(it.get("color", 0)))           # its luster / enamel
		WeaponModels.set_emblem(w, model_id, int(it.get("emblem", 0)))   # a shield's guild emblem
		if bone.ends_with("Back") and not shield:
			if slung and not frame.is_empty():
				BodyFrame.place_bow(skel, skel.find_bone(bone), w, frame)
			elif slung:
				_sling_on_back(w, bone == "Bip01 L Back")
			elif slot == 12 or stance in ["2h", "pole", "staff", "scy"]:
				_raise_on_back(w)
		var at := BoneAttachment3D.new()
		at.bone_name = bone
		at.set_meta("shield", shield)
		skel.add_child(at)
		at.add_child(w)
		if in_hand:
			WeaponModels.add_effect(w, int(it.get("effect", 0)))   # its glow / flame (an item's weapon effect) - in hand only
		made.append(at)
	# the quiver (owner 2026-11-03: "the quiver can always be there whether you're holding the bow or not and only goes
	# away when no bow is equipped"; crossbows none - "bolts ... stored on the hip"): the realm's quiver flat on the
	# back, its mouth up past the right shoulder (BodyFrame.place_quiver)
	var bow: Dictionary = item_at.call(13)
	var has_bow := not bow.is_empty() and WeaponModels.stance(int(bow.get("model", 0))) not in ["xbow", "throw"]
	var quiver_shown := false
	if has_bow and QUIVER_MODELS.has(int(gear.get("realm", 0))) and not frame.is_empty():
		var qbone := "Bip01 Spine2" if skel.find_bone("Bip01 Spine2") >= 0 else "Bip01 Spine1"
		var qi := skel.find_bone(qbone)
		var q := WeaponModels.make(int(QUIVER_MODELS[int(gear.get("realm", 0))]), false, false)
		if qi >= 0 and q != null:
			BodyFrame.place_quiver(skel, qi, q, frame)
			var qa := BoneAttachment3D.new()
			qa.bone_name = qbone
			skel.add_child(qa)
			qa.add_child(q)
			made.append(qa)
			quiver_shown = true
	# a shield on the back stands off the slung bow and the quiver (owner 2026-11-03: "a bit further back from the bow
	# so they don't clip")
	if has_bow and not frame.is_empty():
		for at in made:
			var a := at as BoneAttachment3D
			if a and String(a.bone_name).ends_with("Back") and a.get_child_count() > 0 and a.get_meta("shield", false):
				BodyFrame.push_back(skel, skel.find_bone(a.bone_name), a.get_child(0) as Node3D, frame, 0.07)
	# the cloak hangs still while something rides on the back (owner 2026-11-03: the shield / two-hander clipped through
	# the swinging cloak) - Fig3Figure.Sway
	if model is Fig3Figure:
		(model as Fig3Figure).back_gear = not back_taken.is_empty() or quiver_shown
	return made


## The figure's own directions in its skeleton's space, from the rest pose: right (the right upper arm from the left),
## up (pelvis to head), back (behind it - the figure faces +Z in its model's space), the torso's length (L) and the
## bones' rest positions; {} when the skeleton lacks them (a monster).
class BodyFrame:
	static func of(skel: Skeleton3D, model: Node3D) -> Dictionary:
		var at := func(n: String) -> Vector3:
			var i := skel.find_bone(n)
			return skel.get_bone_global_rest(i).origin if i >= 0 else Vector3.INF
		var ru: Vector3 = at.call("Bip01 R UpperArm")
		var lu: Vector3 = at.call("Bip01 L UpperArm")
		var head: Vector3 = at.call("Bip01 Head")
		var pelvis: Vector3 = at.call("Bip01 Pelvis")
		var spine: Vector3 = at.call("Bip01 Spine2")
		if spine == Vector3.INF:
			spine = at.call("Bip01 Spine1")
		if Vector3.INF in [ru, lu, head, pelvis, spine]:
			return {}
		var right := (ru - lu).normalized()
		var up0 := head - pelvis
		var up := (up0 - right * up0.dot(right)).normalized()
		# the model's +Z (its front) in the skeleton's space
		var b := Basis.IDENTITY
		var n: Node = skel
		while n != null and n != model:
			if n is Node3D:
				b = (n as Node3D).transform.basis * b
			n = n.get_parent()
		var fwd := (b.inverse() * Vector3(0, 0, 1)).normalized()
		var back := right.cross(up).normalized()
		if back.dot(fwd) > 0.0:
			back = -back
		return {"right": right, "up": up, "back": back, "L": up0.length(), "ru": ru, "spine": spine,
				"rback": at.call("Bip01 R Back")}

	## The quiver flat on the upper back, its mouth up and out past the right shoulder (owner 2026-11-03 picture: the
	## bow slung from the left shoulder to the right hip, the quiver the other way, arrows standing over the right
	## shoulder), its arrows a third of their length above the shoulders.
	static func place_quiver(skel: Skeleton3D, bone: int, q: Node3D, f: Dictionary) -> void:
		var box := Player._holder_box(q)
		if box.size == Vector3.ZERO:
			return
		var k := 0
		var thin := 0
		for i in 3:
			if box.size[i] > box.size[k]:
				k = i
			if box.size[i] < box.size[thin]:
				thin = i
		var a_k := Vector3.ZERO
		a_k[k] = 1.0 if absf(box.end[k]) >= absf(box.position[k]) else -1.0     # toward the mouth (the arrows)
		var a_t := Vector3.ZERO
		a_t[thin] = 1.0
		var a_m := a_k.cross(a_t)
		var right: Vector3 = f.right
		var up: Vector3 = f.up
		var back: Vector3 = f.back
		var L: float = f.L
		var tilt := deg_to_rad(float(_arg("quiver-tilt", "25")))
		var mouth := (up * cos(tilt) + right * sin(tilt)).normalized()
		var t_t := (back - mouth * back.dot(mouth)).normalized()
		var src := Basis(a_k, a_t, a_m)
		var dst := Basis(mouth, t_t, mouth.cross(t_t))
		var sc := q.transform.basis.get_scale()
		var r := dst * src.inverse()
		var bs := r * Basis.from_scale(sc)
		var lq := box.size[k] * sc[k]
		var spine: Vector3 = f.spine
		var rb: Vector3 = f.rback
		var depth := maxf(0.0, (rb - spine).dot(back)) if rb != Vector3.INF else 0.12 * L
		var shoulder_h := ((f.ru as Vector3) - spine).dot(up)
		var anchor := spine + up * shoulder_h + right * L * float(_arg("quiver-right", "0.16")) \
				+ back * (depth + box.size[thin] * sc[thin] * 0.5 + L * float(_arg("quiver-off", "0.02")))
		var centre := anchor - mouth * lq * float(_arg("quiver-down", "0.2"))
		var g := Transform3D(bs, centre - bs * box.get_center())
		q.transform = skel.get_bone_global_rest(bone).affine_inverse() * g

	## A bow or crossbow slung across the back (owner 2026-11-03 picture): its limbs from the left shoulder down to the
	## right hip, flat on the back, outside the quiver so the two cross.
	static func place_bow(skel: Skeleton3D, bone: int, w: Node3D, f: Dictionary) -> void:
		var box := Player._holder_box(w)
		if box.size == Vector3.ZERO or bone < 0:
			return
		var k := 0
		var thin := 0
		for i in 3:
			if box.size[i] > box.size[k]:
				k = i
			if box.size[i] < box.size[thin]:
				thin = i
		var a_k := Vector3.ZERO
		a_k[k] = 1.0
		var a_t := Vector3.ZERO
		a_t[thin] = 1.0
		var a_m := a_k.cross(a_t)
		var right: Vector3 = f.right
		var up: Vector3 = f.up
		var back: Vector3 = f.back
		var L: float = f.L
		var tilt := deg_to_rad(float(_arg("bow-tilt", "32")))
		var limbs := (up * cos(tilt) - right * sin(tilt)).normalized()     # the upper limb over the left shoulder
		var t_t := (back - limbs * back.dot(limbs)).normalized()
		var r := Basis(limbs, t_t, limbs.cross(t_t)) * Basis(a_k, a_t, a_m).inverse()
		var sc := w.transform.basis.get_scale()
		var bs := r * Basis.from_scale(sc)
		var spine: Vector3 = f.spine
		var rb: Vector3 = f.rback
		var depth := maxf(0.0, (rb - spine).dot(back)) if rb != Vector3.INF else 0.12 * L
		var shoulder_h := ((f.ru as Vector3) - spine).dot(up)
		var centre := spine + up * shoulder_h * float(_arg("bow-up", "0.15")) \
				+ back * (depth + box.size[thin] * sc[thin] * 0.5 + L * float(_arg("bow-off", "0.10")))
		var g := Transform3D(bs, centre - bs * box.get_center())
		w.transform = skel.get_bone_global_rest(bone).affine_inverse() * g

	## A gear piece on a back bone moved further out behind the figure by share x the torso's length.
	static func push_back(skel: Skeleton3D, bone: int, w: Node3D, f: Dictionary, share: float) -> void:
		if bone < 0 or w == null:
			return
		var local := skel.get_bone_global_rest(bone).basis.inverse() * ((f.back as Vector3) * float(f.L) * share)
		w.position += local

	static func _arg(k: String, d: String) -> String:
		for a in OS.get_cmdline_user_args():
			if a.begins_with("--%s=" % k):
				return a.get_slice("=", 1)
		return d


## A bow or crossbow slung over the shoulder (owner 2026-11-02: "so it looks like they're slung over your shoulder"):
## on its back bone it would hang like a sword, so it is tipped across the back - about 35 degrees over the shoulder
## it hangs from (the left bone: tipped one way, the right: the other) and pushed up so the upper limb stands over
## the shoulder.
static func _sling_on_back(holder: Node3D, left: bool) -> void:
	var box := _holder_box(holder)
	if box.size == Vector3.ZERO:
		return
	var k := 0
	for i in 3:
		if box.size[i] > box.size[k]:
			k = i
	var axis := Vector3.ZERO                                  # the limbs' axis in the holder's frame
	axis[k] = 1.0
	# the back bone's outward normal is whichever axis the weapon's thickness lies on
	var thin := 0
	for i in 3:
		if box.size[i] < box.size[thin]:
			thin = i
	var normal := Vector3.ZERO
	normal[thin] = 1.0
	# (owner 2026-11-03 picture: from the left shoulder down to the right hip, crossing the quiver - the first tilt ran
	# with the quiver, the two stacked)
	var tilt := float(BodyFrame._arg("bow-tilt", "35"))
	holder.rotate(normal, deg_to_rad(-tilt if left else tilt))
	holder.position += axis * clampf(box.size[k] * 0.18, 4.0, 12.0)


## The holder's meshes' box in its own frame (NIF units), the grip at the origin.
static func _holder_box(holder: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for mi in holder.find_children("*", "MeshInstance3D", true, false):
		var xf := Transform3D.IDENTITY
		var n: Node = mi
		while n != null and n != holder:
			if n is Node3D:
				xf = (n as Node3D).transform * xf
			n = n.get_parent()
		var b: AABB = xf * (mi as MeshInstance3D).get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box


## A two-hander slung on the back sits higher (owner 2026-10-31: "too low ... the hilt of the greatsword should sit
## around the shoulders"): the weapon slides along its own length toward its grip end - about a quarter of its length,
## 6 to 16 units (15-40 cm) - so the hilt comes up over the shoulder and the blade or head off the legs. Its length and
## which end is the blade come from its meshes' box in the holder's frame (NIF units), the grip at the origin.
static func _raise_on_back(holder: Node3D) -> void:
	if "--back-low" in OS.get_cmdline_user_args():       # (tests: the old hang, to compare)
		return
	var box := AABB()
	var first := true
	for mi in holder.find_children("*", "MeshInstance3D", true, false):
		var xf := Transform3D.IDENTITY
		var n: Node = mi
		while n != null and n != holder:
			if n is Node3D:
				xf = (n as Node3D).transform * xf
			n = n.get_parent()
		var b: AABB = xf * (mi as MeshInstance3D).get_aabb()
		box = b if first else box.merge(b)
		first = false
	if first:
		return
	var k := 0
	for i in 3:
		if box.size[i] > box.size[k]:
			k = i
	var lo := box.position[k]
	var hi := box.end[k]
	var toward_blade := Vector3.ZERO
	toward_blade[k] = 1.0 if absf(hi) >= absf(lo) else -1.0
	holder.position = -toward_blade * clampf(box.size[k] * 0.24, 6.0, 16.0)


## /follow /stick /face: false (and the reason in chat) when the target can't be tracked.
func start_track(mode: String, target: Node3D, target_name: String) -> bool:
	if target == null or not is_instance_valid(target):
		PlayerData.message.emit("You must select a target to %s!" % mode, "system")
		return false
	if target == self:
		PlayerData.message.emit("You can't %s yourself!" % mode, "system")
		return false
	if mode != "face" and global_position.distance_to(target.global_position) > TRACK_START_M:
		PlayerData.message.emit("%s is too far away to %s." % [target_name, mode], "system")
		return false
	stop_track(true)
	track_target = target
	track_mode = mode
	track_name = target_name
	autorun = false                                   # patch notes: stick / follow / face turns run lock off
	PlayerData.message.emit({"follow": "You are now following %s.", "stick": "You are now sticking to %s.",
			"face": "You are now facing %s."}[mode] % target_name, "system")
	return true


func stop_track(quiet := false) -> void:
	if track_mode != "" and not quiet:
		PlayerData.message.emit({"follow": "You are no longer following %s.", "stick": "You are no longer sticking to %s.",
				"face": "You are no longer facing %s."}[track_mode] % track_name, "system")
	track_mode = ""
	track_target = null


func face(yaw_radians: float) -> void:
	char_yaw = yaw_radians
	cam_yaw = yaw_radians
	_body_offset = 0.0
	_apply_model_yaw()


func _apply_model_yaw() -> void:
	if _model:
		_model.rotation.y = char_yaw + PI + _body_offset   # the converted model faces +Z
	if mount and is_instance_valid(mount):
		mount.rotation.y = char_yaw + PI + _body_offset    # (the horse model faces +Z too)


## A fight from the saddle gets you off it (as the server does on an attack - AttackComponent.StartAttack - and on a
## hostile cast): off at once here, so Action Combat's swing / dodge / parry / draw plays on foot, and the server told.
func leave_mount() -> void:
	if mount and is_instance_valid(mount):
		set_mount(null)
		PlayerData.dismount_requested.emit()


## Your own horse (mounts' first pass, owner 2026-11-02): the server says you are on it (ControlledHorse) and how fast
## you go (MaxSpeed); the movement - modern or classic, the keys, the mouse, jumping - stays yours. The horse walks
## under you and you sit in its saddle (the figure's ride_horse pose). null: off it.
func set_mount(n: Node3D) -> void:
	if mount and is_instance_valid(mount):
		mount.queue_free()
	mount = n
	if n:
		add_child(n)
		_body_offset = 0.0
		_apply_model_yaw()
	else:
		if _model:
			_model.position = Vector3.ZERO
		if _anim:
			_anim.speed_scale = 1.0
		_play("idle")


## The pointer is over an interface window (owner 2026-10-11: scrolling a long server menu also zoomed the camera -
## a list that reached its end let the wheel through).
func _over_window() -> bool:
	var c := get_viewport().gui_get_hovered_control()
	while c:
		if c is ClassicWindow:
			return c.is_visible_in_tree()
		c = c.get_parent() as Control
	return false


func _unhandled_input(event: InputEvent) -> void:
	if not input_enabled:
		return
	# only presses that reach the world steer / look; a click on an interface window is taken by the window
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_lmb_world = event.pressed
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
		_rmb_world = event.pressed
	var rmb := _rmb_world and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
	var lmb := _lmb_world and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	if action_mode and not action_cursor and not dead and event is InputEventMouseMotion:
		var ady: float = event.relative.y * (-1.0 if invert_mouse else 1.0) * mouse_sensitivity
		cam_yaw -= event.relative.x * MOUSE_TURN * mouse_sensitivity
		cam_pitch = clampf(cam_pitch - ady * 0.004, -CAM_PITCH, CAM_PITCH)
		if _faces_camera() and not sitting and is_nan(_lock_yaw()):
			char_yaw = cam_yaw                          # action combat, weapon out: you face where you look
		return
	if action_mode and not action_cursor and event is InputEventMouseButton \
			and event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
		return                                           # (the fight takes the buttons: ActionCombatMode)
	if event is InputEventMouseMotion and (rmb or lmb):
		var dy: float = event.relative.y * (-1.0 if invert_mouse else 1.0) * mouse_sensitivity
		cam_yaw -= event.relative.x * MOUSE_TURN * mouse_sensitivity
		if free_camera:
			cam_pitch = clampf(cam_pitch - dy * 0.004, -1.35, 0.6)
		else:
			cam_pitch = clampf(cam_pitch - dy * 0.004, -CAM_PITCH, CAM_PITCH)
		if rmb and not sitting:
			char_yaw = cam_yaw                          # steering: the character follows the camera (sitting: looking)
	elif event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			# hide the cursor while dragging, as WoW does, and put it back where the drag began (capturing the mouse
			# parks it in the middle of the window; the owner saw every click jump the cursor to the centre)
			if (rmb or lmb) and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
				_cursor_at = get_viewport().get_mouse_position()
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			elif not (rmb or lmb) and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
				get_viewport().warp_mouse(_cursor_at)
			if event.pressed and event.button_index == MOUSE_BUTTON_RIGHT and not sitting:
				char_yaw = cam_yaw                      # right-click snaps the character to the camera heading
		elif event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and _over_window():
			pass                                        # the wheel over a window scrolls it, never the camera
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam_distance = maxf(CAM_MIN, cam_distance * 0.88)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam_distance = minf(CAM_MAX_FREE if free_camera else CAM_MAX, cam_distance / 0.88)
	if (event is InputEventKey or event is InputEventMouseButton) and event.is_pressed() and not event.is_echo():
		# the client's bindable actions (Keybinds: keyboard.dat presets, rebindable incl. mouse buttons)
		if Keybinds.pressed(event, "run_lock"):
			autorun = not autorun
		elif Keybinds.pressed(event, "torch") or (event is InputEventKey and event.shift_pressed
				and Keybinds.pressed(_unshifted(event), "torch")):   # its key or Shift + its key, as the client
			set_torch(not torch_on)
			var cfg := ConfigFile.new()
			cfg.load("user://settings.cfg")
			cfg.set_value("player", "torch", torch_on)
			cfg.save("user://settings.cfg")
		elif Keybinds.pressed(event, "walk"):
			walking = not walking
		elif Keybinds.pressed(event, "move_forward") or Keybinds.pressed(event, "move_back"):
			autorun = false


func _unshifted(event: InputEventKey) -> InputEventKey:
	var e := event.duplicate() as InputEventKey
	e.shift_pressed = false
	return e


func _key(k: Key) -> bool:
	return input_enabled and not dead and Input.is_physical_key_pressed(k)


func _act(id: String) -> bool:
	return input_enabled and not dead and not _ui_typing() and Keybinds.held(id)


func _ui_typing() -> bool:
	var f := get_viewport().gui_get_focus_owner()       # typing in chat / a text box doesn't move the character
	return f is LineEdit or f is TextEdit


## A new place (spawn, teleport, zone entry): hold still a few physics frames - the floors' collision is only there
## after the physics world has stepped once, and a city or dungeon has no terrain grid to catch a fall.
func hold() -> void:
	hold_frames = 12
	velocity = Vector3.ZERO


## The camera stays out of the ground and the water (owner 2026-10-28: looking up from a riverbank put it under the
## river): the spring arm's sphere keeps it off walls and roofs; out in the open it also stays CAM_CLEAR above the
## terrain and any water surface where it is. After physics (the arm places it there), before the frame is drawn.
const CAM_BALL := 0.25
const CAM_CLEAR := 0.35


## How far (up to dist) the camera can slide along dir before a wall, a roof or the ground - its sphere swept there.
var _offset_query: PhysicsShapeQueryParameters3D


func _offset_room(dir: Vector3, dist: float) -> float:
	if camera == null or dist <= 0.001 or not is_inside_tree():
		return dist
	if _offset_query == null:
		_offset_query = PhysicsShapeQueryParameters3D.new()
		var ball := SphereShape3D.new()
		ball.radius = CAM_BALL
		_offset_query.shape = ball
		_offset_query.exclude = [get_rid()]
	_offset_query.collision_mask = _arm.collision_mask
	_offset_query.transform = Transform3D(Basis.IDENTITY, camera.global_position)
	_offset_query.motion = dir * dist
	var r := get_world_3d().direct_space_state.cast_motion(_offset_query)
	if r.size() < 2:
		return dist
	return maxf(0.0, dist * float(r[0]) - 0.05)


## The camera's height follows the body smoothly on the ground (owner 2026-10-31: the camera jittered up and down
## stairs - each step lifts the body a few centimetres at once, and the camera hung on it rigidly); in the air it
## keeps up closely (jumps and falls stay tight). Snaps after a teleport or a big drop.
var _cam_y := INF


func _smooth_camera_height(delta: float) -> void:
	var y := global_position.y
	if _cam_y == INF or absf(y - _cam_y) > 2.5:
		_cam_y = y
	else:
		var rate := 14.0 if grounded else 40.0
		_cam_y += (y - _cam_y) * minf(1.0, delta * rate)
	_pivot.position.y = 1.55 + (_cam_y - y) + (_model.position.y if mount and _model else 0.0)


func _process(_delta: float) -> void:
	if camera == null or (zone == null and region == null):
		return
	if flying or riding:
		_cam_y = INF
		_pivot.position.y = 1.55
		return
	_smooth_camera_height(_delta)
	var g := camera.global_position
	var lim := _water_h(g.x, g.z)
	if zone and not zone.city:
		lim = maxf(lim, _ground_h(g.x, g.z))
	if lim > -INF and g.y < lim + CAM_CLEAR:
		camera.global_position.y = lim + CAM_CLEAR


func _physics_process(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	_physics_step(delta)
	if lantern and torch:                                 # the belt lantern rides on your hip as you turn
		torch.position = LANTERN_AT.rotated(Vector3.UP, char_yaw + PI)
	Perf.phys_add("player", Time.get_ticks_usec() - t0)        # (Perf's live log: the physics tick by part)


func _physics_step(delta: float) -> void:
	if hold_frames > 0:
		hold_frames -= 1
		velocity = Vector3.ZERO
		return
	if not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_lmb_world = false
	if not Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		_rmb_world = false
	if not (_lmb_world or _rmb_world) and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and input_enabled \
			and not action_mode:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE              # a release the world never saw (over a window)
		get_viewport().warp_mouse(_cursor_at)
	var rmb := input_enabled and _rmb_world and not dead       # a dead character doesn't move (both buttons either)
	var lmb := input_enabled and _lmb_world and not dead
	if riding:                                        # the horse carries you; the camera still orbits
		velocity = Vector3.ZERO
		if input_enabled and _act("jump"):
			PlayerData.dismount_requested.emit()          # PlayerDismountRequestHandler
		var clip := ride_clip if _anim and _anim.has_animation(ride_clip) else "ride_horse"
		if _anim and _anim.has_animation(clip) and _anim.current_animation != clip:
			_anim.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
			_anim.play(clip, 0.2)
		_pivot.rotation = Vector3(cam_pitch, cam_yaw, 0.0)
		_arm.spring_length = lerpf(_arm.spring_length, cam_distance, minf(1.0, delta * 10.0))
		return
	if dead:
		autorun = false
	var classic := movement_mode == "classic"
	if rmb and lmb:
		autorun = false
	var fwd := _act("move_forward") or (rmb and lmb) or autorun
	var back := _act("move_back")
	var left := _act("turn_left")
	var right := _act("turn_right")
	if track_mode != "":
		var manual := fwd or back or _act("strafe_left") or _act("strafe_right") or (track_mode != "face" and (left or right))
		var gone: bool = track_target == null or not is_instance_valid(track_target) or not track_target.is_inside_tree() 				or (track_target.has_method("is_alive") and not track_target.is_alive())
		var far: bool = track_target != null and is_instance_valid(track_target) and track_mode == "stick" 				and global_position.distance_to(track_target.global_position) > STICK_BREAK_M
		if manual or gone or far or dead:
			stop_track()
		else:
			var d := track_target.global_position - global_position
			char_yaw = atan2(-d.x, -d.z)
			var gap := Vector2(d.x, d.z).length()
			if track_mode == "follow" and gap > FOLLOW_GAP_M or track_mode == "stick" and gap > STICK_GAP_M:
				fwd = true
	var strafe := 0.0
	var turn := 0.0
	if (rmb and not classic) or action_mode:          # modern: with the right mouse held, A/D strafe (action: always)
		strafe += (1.0 if right else 0.0) - (1.0 if left else 0.0)
	else:
		turn += (1.0 if left else 0.0) - (1.0 if right else 0.0)
	if not action_mode:
		strafe += (1.0 if _act("strafe_right") else 0.0) - (1.0 if _act("strafe_left") else 0.0)
	elif input_enabled and not dead and not _ui_typing():
		# action combat: the strafe keys still strafe, except those that are also its buttons (Q / E by default)
		strafe += (1.0 if Keybinds.held_unshared("strafe_right", AC_BUTTONS) else 0.0) \
				- (1.0 if Keybinds.held_unshared("strafe_left", AC_BUTTONS) else 0.0)
	strafe = clampf(strafe, -1.0, 1.0)
	var ahead := (1.0 if fwd else 0.0) - (1.0 if back else 0.0)

	if flying:
		_fly(delta, ahead, strafe, turn)
		return

	# Action combat with the weapon away and no spell being cast (owner 2026-10-28): the camera looks freely - you can
	# turn it to see your character's face - and the character turns to run where you steer, relative to the camera.
	# Weapon out, casting or aiming: you face where you look, as before. Sitting: you stay put either way.
	var free_dir := Vector3.ZERO
	var lock_yaw := _lock_yaw() if action_mode and not dead and cc == "" and not sitting else NAN
	if not is_nan(lock_yaw) and (_faces_camera() or (ahead == 0.0 and strafe == 0.0)):
		char_yaw = lerp_angle(char_yaw, lock_yaw, minf(1.0, delta * 18.0))   # locked on: face the target
	elif action_mode and not dead and cc == "":
		if not _faces_camera():
			if ahead != 0.0 or strafe != 0.0:
				free_dir = Vector3(strafe, 0.0, -ahead).normalized().rotated(Vector3.UP, cam_yaw)
				char_yaw = lerp_angle(char_yaw, atan2(-free_dir.x, -free_dir.z), minf(1.0, delta * FREE_TURN_RATE))
				ahead = 1.0                                # (the body runs forward, toward where it is going)
				strafe = 0.0
		elif not sitting:
			char_yaw = lerp_angle(char_yaw, cam_yaw, minf(1.0, delta * 18.0))   # (drawn: turn to the camera's heading)

	char_yaw += turn * TURN_RATE * delta
	var moving := absf(ahead) > 0.0 or absf(strafe) > 0.0
	if not lmb and not action_mode and (moving or absf(turn) > 0.0):
		cam_yaw = lerp_angle(cam_yaw, char_yaw, minf(1.0, delta * 8.0))   # camera swings back behind
	if not rmb and not lmb and absf(turn) > 0.0:
		cam_yaw = char_yaw

	var local := Vector3(strafe, 0.0, -ahead)
	if local.length() > 1.0:
		local = local.normalized()                    # diagonals are not faster
	var water := _water_h(global_position.x, global_position.z) if zone else -INF
	var bed := _ground_h(global_position.x, global_position.z, global_position.y) if zone else -INF
	swimming = water - bed > SWIM_DEPTH and global_position.y < water + 0.05     # deep enough, and in it (not above)
	if sounds:
		sounds.surface = "swim" if swimming else ("water" if water - global_position.y > 0.1 else "dirt")
	var speed := RUN_SPEED
	if swimming:
		speed = SWIM_SPEED
	elif ahead < 0.0:
		speed = CLASSIC_BACK_SPEED if classic else BACK_SPEED   # backpedalling, straight or diagonal
	elif classic and ahead == 0.0 and strafe != 0.0:
		speed = CLASSIC_SIDE_SPEED                    # DAoC's slow side-step
	elif walking or (_key(KEY_SHIFT) and not action_mode):   # (action combat: Shift sprints - ActionCombatMode)
		speed = WALK_SPEED
	var wish := local.rotated(Vector3.UP, char_yaw) * speed * speed_mult * buff_speed * snare_mult * encumbrance * stealth_mult \
			* _wounded_mult() * (0.5 if action_mode and _defend_slow_left > 0.0 else 1.0)
	if free_dir != Vector3.ZERO:
		wish = free_dir * wish.length()                 # free look: straight where you steer while the body turns to it
	_defend_slow_left = maxf(0.0, _defend_slow_left - delta)
	if aiming and action_mode:
		wish = Vector3.ZERO
	if _dash_left > 0.0:                              # a dodge: a short burst on top of the run (Action Combat)
		_dash_left -= delta
		wish += _dash * clampf(_dash_left / 0.22, 0.0, 1.0)
	if cc != "":
		wish = Vector3.ZERO                             # stunned / mesmerized / rooted: no moving

	if not climbing and not swimming and ahead > 0.0 and cc == "" and _climb_ahead():
		climbing = true
		PlayerData.message.emit("You start climbing.", "system")
	if climbing and (_act("jump") or swimming or cc != "" or dead):
		_stop_climbing()
	if climbing:
		# up while pressing forward (into the ladder: the climb wall holds you), down with back, still otherwise
		var rate := minf(1.0, speed_mult * buff_speed * snare_mult * encumbrance)
		_climb_vy = CLIMB_SPEED * rate * (1.0 if ahead > 0.0 else (-1.0 if ahead < 0.0 else 0.0))
		var push := wish if ahead > 0.0 else Vector3.ZERO
		velocity = Vector3(push.x, _climb_vy, push.z)
		grounded = false
		_client_move(delta)
		if ahead < 0.0 and grounded:
			_stop_climbing()                              # down at the bottom
		elif ahead > 0.0 and not _climb_ahead():
			_stop_climbing()                              # over the top: stepped off onto the floor
		_air_time = 0.0
		_animate(ahead, strafe, speed, delta)
		_pivot.rotation = Vector3(cam_pitch, cam_yaw, 0.0)
		_arm.spring_length = lerpf(_arm.spring_length, cam_distance, minf(1.0, delta * 10.0))
		return
	if swimming:
		velocity.x = wish.x
		velocity.z = wish.z
		# 1.65: surface swimming only (diving came with Trials of Atlantis, 1.70) - held at the surface
		velocity.y = clampf((water - SWIM_FLOAT - global_position.y) * 4.0, -3.0, 3.0)
	elif grounded:
		velocity.x = wish.x
		velocity.z = wish.z
		velocity.y = JUMP_VELOCITY if _act("jump") else 0.0
	else:
		# airborne: keep the take-off momentum, a little steering
		velocity.x = lerpf(velocity.x, wish.x, AIR_CONTROL * delta * 10.0)
		velocity.z = lerpf(velocity.z, wish.z, AIR_CONTROL * delta * 10.0)
		velocity.y -= GRAVITY * delta
	_client_move(delta)
	_air_time = 0.0 if grounded or swimming else _air_time + delta

	if zone and zone.city and grounded:
		_last_footing = global_position
	if zone and zone.city and _last_footing != Vector3.ZERO and global_position.y < _last_footing.y - 300.0:
		global_position = _last_footing + Vector3(0, 0.3, 0)   # fell out of a city / dungeon: back where you stood
		velocity = Vector3.ZERO
	if zone and not zone.city and global_position.y < _ground_h(global_position.x, global_position.z, global_position.y) - 2.0:
		global_position.y = _ground_h(global_position.x, global_position.z) + 0.5   # fell through: recover

	# the legs keep pace with how fast you really go - sprint, speed buffs, snares, wounds (owner 2026-10-31)
	_animate(ahead, strafe, Vector2(wish.x, wish.z).length() if not swimming else speed, delta)
	cam_kick = move_toward(cam_kick, 0.0, delta * 0.5)
	if camera:
		var want := shoulder if action_mode else Vector2.ZERO
		# the over-the-shoulder offset slides the view sideways past where the arm checked (owner 2026-10-28: in
		# Camelot's alleys the camera looked through the wall beside you): only as far as there is room
		if want != Vector2.ZERO and not flying:
			want.x = signf(want.x) * _offset_room(camera.global_basis.x * signf(want.x), absf(want.x))
			want.y = signf(want.y) * _offset_room(camera.global_basis.y * signf(want.y), absf(want.y))
		var rate := minf(1.0, delta * 6.0)
		camera.h_offset = want.x if absf(want.x) < absf(camera.h_offset) else lerpf(camera.h_offset, want.x, rate)
		camera.v_offset = want.y if absf(want.y) < absf(camera.v_offset) else lerpf(camera.v_offset, want.y, rate)
	_pivot.rotation = Vector3(cam_pitch + cam_kick, cam_yaw, 0.0)
	_arm.spring_length = lerpf(_arm.spring_length, cam_distance, minf(1.0, delta * 10.0))


## Action Combat's dodge: a quick hop toward `local_dir` (x right, z back, in the character's frame) - the server's
## evade window is what actually avoids the blow; this is the body getting out of the way.
func dodge(local_dir: Vector3) -> void:
	if dead or cc != "" or not grounded:
		return
	leave_mount()
	var d := local_dir
	d.y = 0.0
	if d.length() < 0.1:
		d = Vector3(0, 0, 1)                         # no direction held: a step back
	_dash = d.normalized().rotated(Vector3.UP, char_yaw) * RUN_SPEED * 2.6
	_dash_left = 0.22


func _animate(ahead: float, strafe: float, speed: float, delta: float) -> void:
	if mount and is_instance_valid(mount) and not dead:
		# on your horse: you sit (ride_horse) - no lean, no run cycle - and the horse's legs follow the ground speed
		_body_offset = 0.0
		_apply_model_yaw()
		var ground := Vector2(velocity.x, velocity.z).length()
		Mounts.animate(mount, ground)
		Mounts.rider_pose(_anim, mount, ground)
		if _model:
			_model.position = Mounts.seat_point(mount)
		return
	# diagonal movement leans the body toward the travel direction (WoW turns the legs 45 degrees)
	# pure strafing turns the body most of the way toward the side and keeps the run cycle going: the client's own
	# side-step clips are DAoC's slow shuffle, which looked frozen at full strafe speed (owner, 2026-10-09)
	var target_offset := 0.0
	var classic := movement_mode == "classic"
	if classic:
		pass                                          # classic: the body always faces forward
	elif ahead > 0.0 and strafe != 0.0:
		target_offset = -strafe * PI * 0.25
	elif ahead < 0.0 and strafe != 0.0:
		target_offset = strafe * PI * 0.25
	elif ahead == 0.0 and strafe != 0.0:
		target_offset = -strafe * PI * 0.4
	_body_offset = lerp_angle(_body_offset, target_offset, minf(1.0, delta * 10.0))
	_apply_model_yaw()
	_action_left -= delta
	var moving := ahead != 0.0 or strafe != 0.0
	if casting_spell:
		_cast_left -= delta
		# moving ends the casting pose at once (as the old client: moving interrupts a cast - the server says so a
		# moment later), and a cast nothing came back for ends after its time
		if (moving and Server.active) or _cast_left < -CAST_GRACE:
			cast_end(false)
	if moving and _action == "stand_up":
		_action_left = 0.0                            # walking off from a sit goes straight into the run
	if dead:
		if not _death_played:                         # once, then the last frame holds (the clip doesn't loop)
			_death_played = true
			_one_shot("death")
	elif force_clip != "":
		_play(force_clip)
	elif _action_left > 0.0 and (grounded or swimming):
		# a swing / flinch / cast end plays out even while moving (owner 2026-10-10: moving cut swings off, and
		# stopping mid-swing left the run clip playing): the 1.65 client has no upper / lower body blending, so a
		# started full-body action finishes, sliding along, and movement takes over after it. In the water too
		# (owner 2026-10-14: combat while swimming as the original) - the figures have no swimming swings or casts
		# (anims.csv / canims.csv), so the same full-body clips play at the surface
		pass
	elif climbing:
		# the figure's anims.csv Ladder clip (Cat_CL_H_up.kfa, "climb up"): run backwards going down, held still
		_play("ladder" if _anim and _anim.has_animation("ladder") else "idle", signf(_climb_vy))
	elif sitting and not moving:
		_play("sit_idle")
	elif swimming and not moving and casting_spell:
		_play(_cast_clips[1])                         # a cast held in the water (moving stops a cast)
	elif swimming and not moving and _bow_hold:
		_play(_ranged() + "_aim")
	elif swimming:
		_play("swim")
	elif not grounded and (velocity.y > 0.0 or _air_time > 0.15):
		_play("jump")                                 # a jump, or a real fall - not a short drop off a ledge
	elif ahead < 0.0:
		_play("walk_back", _sync("walk_back", "back", speed))
	elif classic and ahead == 0.0 and strafe != 0.0:
		var clip := "strafe_right" if strafe > 0.0 else "strafe_left"
		_play(clip, _sync(clip, "strafe", speed))
	elif ahead >= 0.0 and (ahead > 0.0 or strafe != 0.0):
		if speed == WALK_SPEED:
			_play("walk", _sync("walk", "walk", speed))
		else:
			_play("run", _sync("run", "run", speed))
	elif casting_spell:
		_play(_cast_clips[1])
	elif _bow_hold:
		_play(_ranged() + "_aim")
	else:
		_play(_combat_clip("combat_idle") if in_combat else "idle")


func _register_torch() -> void:
	if zone:
		zone.add_dynamic_light(torch, TORCH_ENERGY)


## REMASTERED LIGHTING (SkySystem._set_extras, owner 2026-10-28: "a softer, yellow light, maybe originating at the
## hip, could simulate a belt lantern"): the torch becomes a warm lantern on your belt - a soft pool of yellow light
## round your feet, flickering a little, casting your shadow and the trees' - instead of the client's white light
## 3.2 m overhead. Off: the client's torch again.
const LANTERN_AT := Vector3(0.3, 1.0, 0.15)          # hip height, at your side (turned with you)
# (owner 2026-10-28, after the first: "needs to spread a bit more or be a bit more powerful ... too weak to have much
# utility in truly dark areas" - 1.6 over 13 m was a pool round your feet; brighter alone barely helped - the
# reach is the falloff: 0.5, a near-linear fade, lights the clearing round you and the trunks at its edge)
const LANTERN_ENERGY := 3.4
const LANTERN_RANGE := 30.0
const LANTERN_FALLOFF := 0.5
var lantern := false


func set_lantern(on: bool) -> void:
	lantern = on
	if torch == null:
		return
	if on:
		torch.light_color = Color(1.0, 0.74, 0.42)
		torch.omni_range = SkySystem._t("lantern_range", LANTERN_RANGE)
		torch.omni_attenuation = SkySystem._t("lantern_falloff", LANTERN_FALLOFF)   # brightest near you, a long fade
		torch.shadow_blur = 2.0
		torch.light_volumetric_fog_energy = 0.04         # (no ball of glowing haze round you)
		torch.light_size = 0.12                          # a lamp's flame, not a point: soft shadow edges
		torch.set_meta("base_energy", SkySystem._t("lantern", LANTERN_ENERGY))
		torch.set_meta("flicker", 0.06)
		torch.set_meta("flicker_seed", 3.0)
		torch.position = LANTERN_AT.rotated(Vector3.UP, char_yaw + PI)
	else:
		torch.light_color = Color.WHITE
		torch.omni_range = TORCH_RANGE
		torch.omni_attenuation = 1.0
		torch.shadow_enabled = false
		torch.light_volumetric_fog_energy = 0.25
		torch.light_size = 0.0
		torch.set_meta("base_energy", TORCH_ENERGY)
		if torch.has_meta("flicker"):
			torch.remove_meta("flicker")
		torch.position = Vector3(0.0, TORCH_HEIGHT, 0.0)
	if zone:
		zone.set_light_level(zone.light_level())


func set_torch(on: bool) -> void:
	torch_on = on
	if torch:
		torch.visible = on


## The client's order (see PICK_LIFT): vertical integrate, floor pick at the new spot (lift onto anything within the
## pick range), slide along walls at that height, then stand on a floor within 1 unit or fall.
func _client_move(delta: float) -> void:
	var start_pos := global_position
	var feet_before := global_position.y
	var vy := velocity.y
	var y := feet_before + vy * delta
	var step := Vector3(velocity.x, 0.0, velocity.z) * delta
	var floor_y := _floor_below(Vector3(global_position.x + step.x, y, global_position.z + step.z), feet_before)
	var on_ladder := climbing and _climb_ahead()
	if floor_y > y and not on_ladder:
		y = floor_y                                     # 2. lifted onto the floor (the client's step-up)
	if step.length() > 0.0001 and grounded and not on_ladder:
		# ...and at the collider's leading edge: a step no taller than the collider's lift (one the walls would let
		# through anyway) lifts you as you reach it, so steep narrow stairs (0.40 m risers on 0.25 m treads at the
		# Lethantis tower) don't catch the next riser before the centre is over the step
		var lead := global_position + step.normalized() * (STEP_LEAD + 0.02)
		var lead_y := _floor_below(Vector3(lead.x, y, lead.z), feet_before)
		if lead_y > y and lead_y - y <= COLLIDER_LIFT:
			y = lead_y
	global_position.y = y
	velocity = Vector3(velocity.x, 0.0, velocity.z)
	var was_at := global_position
	move_and_slide()                                    # 3. walls only, horizontal
	global_position.y = y                               # flattened normals: walls never push up or down
	if edges and not edges.allows(global_position):
		# the world's edge (EdgeVeil): no nearer - slide along it on whichever axis still may, else stay put
		var now := global_position
		if edges.allows(Vector3(now.x, y, was_at.z)):
			global_position = Vector3(now.x, y, was_at.z)
		elif edges.allows(Vector3(was_at.x, y, now.z)):
			global_position = Vector3(was_at.x, y, now.z)
		elif edges.allows(was_at) or not edges.allows(now):
			global_position = Vector3(was_at.x, y, was_at.z) if edges.allows(was_at) else now
	velocity.y = vy
	floor_y = _floor_below(global_position, feet_before)
	if not climbing and not swimming and not flying and global_position.y - floor_y <= FALL_HEIGHT + 0.025 \
			and _floor_n.y < cos(deg_to_rad(MAX_SLOPE_DEG)) and _steep_run(_floor_n, floor_y):
		# too steep: no further up it, and it lets you down - slide off along its fall line
		var down := Vector2(_floor_n.x, _floor_n.z).normalized()
		var moved := Vector2(global_position.x - start_pos.x, global_position.z - start_pos.z)
		if floor_y > feet_before + 0.005 and moved.dot(down) < 0.0:
			global_position = Vector3(start_pos.x, feet_before, start_pos.z)
		global_position.x += down.x * SLIDE_MPS * delta
		global_position.z += down.y * SLIDE_MPS * delta
		var under := _floor_below(global_position, global_position.y)
		if global_position.y - under <= 1.5:
			global_position.y = under               # held to it while sliding (not a fall: no fall damage on the way)
			grounded = true
			velocity.y = 0.0
			return
		floor_y = under
	var was_grounded := grounded
	# (+1 unit: the client's "more than 16 units" - a 16-unit stair riser measures 16.0x in floats and must not fall)
	if climbing and vy >= 0.0:
		grounded = false                                # on the ladder: held by it, not standing
	elif was_grounded and vy <= 0.0 and not swimming and global_position.y - floor_y <= FALL_HEIGHT + 0.025:
		global_position.y = floor_y                     # walking down: stay on the ground (not a fall in the client)
		grounded = true
		velocity.y = 0.0
		_last_footing = global_position
	elif global_position.y - floor_y <= FLOOR_SNAP and vy <= 0.0:
		global_position.y = maxf(global_position.y, floor_y) if swimming else floor_y
		if not was_grounded and not swimming and not flying and vy < 0.0:
			landed.emit(-vy / 0.025)                    # PlayerPositionUpdateHandler: fall damage on touching ground
		grounded = not swimming
		velocity.y = 0.0 if not swimming else velocity.y
	else:
		grounded = false
		if swimming and global_position.y < floor_y:
			global_position.y = floor_y                 # swimming along the lake bed


## Is the ground here (surface normal n, floor height y) the face of something tall - does it go on rising that steeply
## for STEEP_RUN_M uphill? (_floor_n is the last pick's: kept round the probe.)
func _steep_run(n: Vector3, y: float) -> bool:
	var keep := _floor_n
	var up := -Vector2(n.x, n.z).normalized()
	var p := global_position + Vector3(up.x, 0.0, up.y) * STEEP_RUN_M
	var ahead := _floor_below(Vector3(p.x, y, p.z), y + 1.9)   # (picked from 1.9 m up: under a doorway's lintel)
	_floor_n = keep
	return ahead - y > 1.4                                          # (1.2 m on: rising more than ~50 degrees)


## A ladder's climb wall right in front of the character (ZoneLoader's ClimbBodies), at the collider's bottom (0.5 m)
## or chest height: climbing lasts until the collider's bottom is over the top of the climb wall.
func _climb_ahead() -> bool:
	var fwd := Vector3(-sin(char_yaw), 0.0, -cos(char_yaw))
	var space := get_world_3d().direct_space_state
	for h in [0.5, 1.2]:
		var from := global_position + Vector3(0, h, 0)
		var q := PhysicsRayQueryParameters3D.create(from, from + fwd * (STEP_LEAD + 0.3), ZoneLoader.LAYER_WALL)
		q.hit_back_faces = true
		var hit := space.intersect_ray(q)
		if not hit.is_empty() and hit.collider is Node and (hit.collider as Node).name == "ClimbBodies":
			return true
	return false


func _stop_climbing() -> void:
	if climbing:
		climbing = false
		_climb_vy = 0.0
		PlayerData.message.emit("You are no longer climbing.", "system")


func _ground_h(x: float, z: float, near_y := INF) -> float:
	return region.height_at(x, z, near_y) if region else zone.height_at(x, z, near_y)


func _water_h(x: float, z: float) -> float:
	return region.water_level_at(x, z) if region else zone.water_level_at(x, z)


## Seamless zones: you crossed a border and the scene moved by -d.
func rebase(d: Vector3) -> void:
	if _last_footing != Vector3.ZERO:
		_last_footing -= d


## Height of the floor under p: a ray straight down from max(64 units, this frame's drop) above the feet against the
## floor layer (terrain + every visible face), like the client's pick (game.dll 0x467692). -INF when nothing is hit.
func _floor_below(p: Vector3, feet_before: float) -> float:
	var start := p.y + maxf(PICK_LIFT, feet_before - p.y)
	var best := -INF
	_floor_n = Vector3.UP
	if zone and not zone.city:
		# (a city's grid is the HIGHEST floor at each point - roofs, wall tops: as a floor its slopes between a street
		# and a wall lifted you up onto the wall, owner 2026-10-10 "an invisible bowl" in Camelot; cities use the pick)
		var t := _ground_h(p.x, p.z)
		if t <= start:
			best = t
			var e := 0.8
			_floor_n = Vector3(_ground_h(p.x - e, p.z) - _ground_h(p.x + e, p.z), 2.0 * e,
					_ground_h(p.x, p.z - e) - _ground_h(p.x, p.z + e)).normalized()
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, start, p.z), Vector3(p.x, start - 500.0, p.z),
			ZoneLoader.LAYER_FLOOR)
	q.hit_back_faces = false
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit and hit.position.y > best:
		best = hit.position.y
		_floor_n = hit.normal if hit.normal.y > 0.0 else -hit.normal
	return best


## Playback rate that makes a clip's feet match the ground: movement speed / (stride per cycle / cycle length).
func _sync(clip: String, stride_key: String, speed_mps: float) -> float:
	if _model is Fig3Figure and clip in ["run", "walk"]:      # a race figure: its own clip's measured pace
		var nat := (_model as Fig3Figure).natural_speed(clip)
		if nat > 0.0:
			return clampf(speed_mps / nat, 0.4, 3.0)
	var stride := float(_strides.get(stride_key, 0.0))
	var length := float(_clip_len.get(clip, 0.0))
	if stride <= 0.0 or length <= 0.0:
		return 1.0
	return clampf((speed_mps / 0.025) / (stride / length), 0.3, 3.0)


func _fly(delta: float, ahead: float, strafe: float, turn: float) -> void:
	# fly where the camera looks: forward/back along the view (pitch included), strafe sideways, Space up, Ctrl down
	cam_yaw += turn * TURN_RATE * delta
	char_yaw = cam_yaw
	var basis := Basis(Vector3.UP, cam_yaw) * Basis(Vector3.RIGHT, cam_pitch)
	var move := basis * Vector3(strafe, 0.0, -ahead)
	if _key(KEY_SPACE):
		move.y += 1.0
	if _key(KEY_CTRL):
		move.y -= 1.0
	var spd := FLY_FAST if _key(KEY_SHIFT) else FLY_SPEED
	if move.length() > 0.01:
		global_position += move.normalized() * spd * delta
	velocity = Vector3.ZERO
	_apply_model_yaw()
	_pivot.rotation = Vector3(cam_pitch, cam_yaw, 0.0)
	_arm.spring_length = lerpf(_arm.spring_length, cam_distance, minf(1.0, delta * 10.0))
	_play(force_clip if force_clip != "" else "idle")

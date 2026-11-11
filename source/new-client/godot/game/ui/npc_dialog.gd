class_name NpcDialog
extends ClassicWindow
## Talking to an NPC (owner 2026-11-11: "The old dialogue box ... needs a UI update, so it's easier to make choices"):
## what it says, and under it every [keyword] it offers as a button to pick - a teleporter's destinations, a trainer's
## or quest giver's answers. Picking one whispers it back, as clicking the bracketed word always did (the words in the
## text stay clickable too). The text and the choices scroll with the mouse wheel; the pad's d-pad walks the choices.
## NPCs with nothing to choose (a hastener's greeting) don't open it: their words float over them (server_world.gd).

signal keyword(npc_id: String, word: String)

const SIZE := Vector2(380, 340)
const BODY := Rect2(14, 30, 352, 150)
const CHOICES := Rect2(14, 190, 352, 136)

var npc_id := ""
var _title: Label
var _body: RichTextLabel
var _scroll: ScrollContainer
var _choices: VBoxContainer
var _words: Array = []


func build() -> void:
	closable = true
	_title = UiArt.label("", 11, UiArt.GOLD_HI)
	_title.position = Vector2(14, 7)
	_title.size = Vector2(SIZE.x - 50, 16)
	_title.clip_text = true
	add_child(_title)
	var x := UiArt.button("X", Vector2(16, 14), 8)
	x.position = Vector2(SIZE.x - 24, 6)
	x.pressed.connect(hide_window)
	add_child(x)
	_body = RichTextLabel.new()
	_body.position = BODY.position
	_body.size = BODY.size
	_body.bbcode_enabled = true
	_body.scroll_following = false
	_body.add_theme_font_override("normal_font", UiArt.font(false))
	_body.add_theme_font_size_override("normal_font_size", 10)
	_body.add_theme_color_override("default_color", UiArt.CREAM)
	_body.meta_clicked.connect(func(m): _pick(String(m)))
	UiArt.themed(_body)
	add_child(_body)
	_scroll = ScrollContainer.new()
	_scroll.position = CHOICES.position
	_scroll.size = CHOICES.size
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	UiArt.themed(_scroll)
	add_child(_scroll)
	_choices = VBoxContainer.new()
	_choices.custom_minimum_size = Vector2(CHOICES.size.x - 12, 0)
	_choices.add_theme_constant_override("separation", 3)
	_scroll.add_child(_choices)


## Show an NPC's words. "[word]" becomes a gold link and a choice button.
## Several things one NPC says at one moment stack (a trainer's greeting and the quests it offers you) instead of the
## last one replacing the rest (owner 2026-10-09: Magus Oreal's quest offer vanished under his training line).
var _frame := -1


func say(id: String, npc_name: String, text: String) -> void:
	var stack := Engine.get_process_frames() == _frame and id == npc_id and visible
	_frame = Engine.get_process_frames()
	npc_id = id
	_title.text = npc_name.to_upper()
	var re := RegEx.create_from_string("\\[([^\\]]+)\\]")
	var bb := re.sub(text.replace("\n", "\n\n"), "[url=$1][color=#f0c060]$1[/color][/url]", true)
	_body.text = (_body.text + "\n\n" + bb) if stack else bb
	if not stack:
		_words = []
	for m in re.search_all(text):
		var w := m.get_string(1).strip_edges()
		if w != "" and not _words.has(w):
			_words.append(w)
	_fill_choices()
	show_window()


## Words the NPC's text holds as [keywords] (the choices it offers).
static func keywords_in(text: String) -> Array:
	var out := []
	for m in RegEx.create_from_string("\\[([^\\]]+)\\]").search_all(text):
		out.append(m.get_string(1))
	return out


func _fill_choices() -> void:
	for c in _choices.get_children():
		c.queue_free()
	var has := not _words.is_empty()
	_scroll.visible = has
	_body.size = BODY.size if has else Vector2(BODY.size.x, SIZE.y - BODY.position.y - 14)
	for w in _words:
		var b := UiArt.button(String(w).to_upper(), Vector2(CHOICES.size.x - 12, 22), 9)
		b.custom_minimum_size = Vector2(CHOICES.size.x - 12, 22)
		b.pressed.connect(_pick.bind(String(w)))
		# the wheel over a button scrolls the choices (a button stops the mouse)
		b.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
				_scroll.scroll_vertical += 25 * (-1 if e.button_index == MOUSE_BUTTON_WHEEL_UP else 1)
				b.accept_event())
		b.mouse_entered.connect(func():
			if Pad.active:
				_scroll.ensure_control_visible(b))
		_choices.add_child(b)
	_scroll.scroll_vertical = 0


func _pick(word: String) -> void:
	keyword.emit(npc_id, word)

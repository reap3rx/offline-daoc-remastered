"""The HD head's face sliders (the character creator plan: ten features, ~73 sliders), each a MakeHuman (CC0) target
pair: the slider's left end is the 'decr' target, its right end the 'incr' one. '{s}' is a side (l / r): both sides
move together. 'carry': hair, beards, helms take the move too (the skull's sliders and those under a beard)."""

# feature key, label, [(slider key, label, minus target, plus target, carry)], presets [(label, {slider: value})]
FEATURES = [
    ('head', 'Head', [
        ('head_width', 'Width', 'head/head-scale-horiz-decr', 'head/head-scale-horiz-incr', 'hair'),
        ('head_depth', 'Length', 'head/head-scale-depth-decr', 'head/head-scale-depth-incr', 'hair'),
        ('head_height', 'Crown Height', 'head/head-scale-vert-decr', 'head/head-scale-vert-incr', 'hair'),
        ('head_back', 'Back of Skull', 'head/head-back-scale-depth-decr', 'head/head-back-scale-depth-incr', 'hair'),
        ('temples', 'Temples', 'forehead/forehead-temple-decr', 'forehead/forehead-temple-incr', 'hair'),
        ('face_length', 'Forehead Height', 'forehead/forehead-scale-vert-decr', 'forehead/forehead-scale-vert-incr', 'hair'),
    ], [('Round', {'head_width': 0.5, 'head_depth': -0.3, 'head_height': -0.3}),
        ('Long', {'head_width': -0.4, 'head_height': 0.5, 'face_length': 0.4}),
        ('Broad', {'head_width': 0.7, 'temples': 0.5})]),
    ('brow', 'Brow', [
        ('brow_height', 'Height', 'eyebrows/eyebrows-trans-down', 'eyebrows/eyebrows-trans-up', ''),
        ('brow_ridge', 'Ridge', 'eyebrows/eyebrows-trans-backward', 'eyebrows/eyebrows-trans-forward', ''),
        ('brow_angle', 'Angle', 'eyebrows/eyebrows-angle-down', 'eyebrows/eyebrows-angle-up', ''),
        ('forehead_slope', 'Forehead Slope', 'forehead/forehead-trans-backward', 'forehead/forehead-trans-forward', 'hair'),
        ('forehead_round', 'Forehead Shape', 'forehead/forehead-nubian-decr', 'forehead/forehead-nubian-incr', 'hair'),
    ], [('Heavy', {'brow_ridge': 0.8, 'brow_height': -0.4}), ('Arched', {'brow_angle': 0.7, 'brow_height': 0.3}),
        ('Flat', {'brow_ridge': -0.6, 'brow_angle': -0.3})]),
    ('eyes', 'Eyes', [
        ('eye_spacing', 'Spacing', 'eyes/{s}-eye-trans-in', 'eyes/{s}-eye-trans-out', ''),
        ('eye_height', 'Height', 'eyes/{s}-eye-trans-down', 'eyes/{s}-eye-trans-up', ''),
        ('eye_size', 'Size', 'eyes/{s}-eye-scale-decr', 'eyes/{s}-eye-scale-incr', ''),
        ('eye_depth', 'Depth', 'eyes/{s}-eye-push1-in', 'eyes/{s}-eye-push1-out', ''),
        ('eye_opening', 'Opening', 'eyes/{s}-eye-height2-decr', 'eyes/{s}-eye-height2-incr', ''),
        ('eye_inner_open', 'Inner Opening', 'eyes/{s}-eye-height1-decr', 'eyes/{s}-eye-height1-incr', ''),
        ('eye_outer_open', 'Outer Opening', 'eyes/{s}-eye-height3-decr', 'eyes/{s}-eye-height3-incr', ''),
        ('eye_inner_corner', 'Outer Corner (Slant)', 'eyes/{s}-eye-corner1-down', 'eyes/{s}-eye-corner1-up', ''),
        ('eye_outer_corner', 'Inner Corner', 'eyes/{s}-eye-corner2-down', 'eyes/{s}-eye-corner2-up', ''),
        ('eye_hood', 'Hooded Lid', 'eyes/{s}-eye-eyefold-up', 'eyes/{s}-eye-eyefold-down', ''),
        ('eye_crease', 'Lid Crease', 'eyes/{s}-eye-eyefold-convex', 'eyes/{s}-eye-eyefold-concave', ''),
        ('eye_fold_angle', 'Fold Angle', 'eyes/{s}-eye-eyefold-angle-down', 'eyes/{s}-eye-eyefold-angle-up', ''),
        ('epicanthic', 'Epicanthic Fold', 'eyes/{s}-eye-epicanthus-out', 'eyes/{s}-eye-epicanthus-in', ''),
        ('eye_bags', 'Bags', 'eyes/{s}-eye-bag-decr', 'eyes/{s}-eye-bag-incr', ''),
        ('eye_bag_height', 'Lower Lid', 'eyes/{s}-eye-bag-height-decr', 'eyes/{s}-eye-bag-height-incr', ''),
    ], [('Almond', {'eye_opening': -0.3, 'eye_outer_corner': 0.35, 'eye_inner_corner': -0.2}),
        ('Round', {'eye_opening': 0.6, 'eye_inner_open': 0.3, 'eye_outer_open': 0.3}),
        ('Hooded', {'eye_hood': 0.8, 'eye_crease': -0.3}),
        ('Monolid', {'eye_hood': 0.6, 'eye_crease': -0.8, 'epicanthic': 0.5}),
        ('Upturned', {'eye_outer_corner': 0.7, 'eye_fold_angle': 0.3}),
        ('Downturned', {'eye_outer_corner': -0.7, 'eye_fold_angle': -0.3}),
        ('Deep-set', {'eye_depth': -0.7, 'brow_ridge': 0.3}),
        ('Wide-set', {'eye_spacing': 0.6})]),
    ('nose', 'Nose', [
        ('nose_width', 'Width', 'nose/nose-scale-horiz-decr', 'nose/nose-scale-horiz-incr', ''),
        ('nose_length', 'Length', 'nose/nose-scale-vert-decr', 'nose/nose-scale-vert-incr', ''),
        ('nose_height', 'Height', 'nose/nose-trans-down', 'nose/nose-trans-up', ''),
        ('nose_projection', 'Projection', 'nose/nose-scale-depth-decr', 'nose/nose-scale-depth-incr', ''),
        ('nose_bridge_width', 'Bridge Width', 'nose/nose-width1-decr', 'nose/nose-width1-incr', ''),
        ('nose_curve', 'Bridge Curve', 'nose/nose-curve-concave', 'nose/nose-curve-convex', ''),
        ('nose_hump', 'Hump', 'nose/nose-hump-decr', 'nose/nose-hump-incr', ''),
        ('nose_tip_angle', 'Tip Angle', 'nose/nose-point-down', 'nose/nose-point-up', ''),
        ('nose_tip_size', 'Tip Size', 'nose/nose-point-width-decr', 'nose/nose-point-width-incr', ''),
        ('nostril_width', 'Nostril Width', 'nose/nose-nostrils-width-decr', 'nose/nose-nostrils-width-incr', ''),
        ('nostril_flare', 'Nostril Flare', 'nose/nose-flaring-decr', 'nose/nose-flaring-incr', ''),
        ('nostril_angle', 'Nostril Height', 'nose/nose-nostrils-angle-down', 'nose/nose-nostrils-angle-up', ''),
        ('septum', 'Septum', 'nose/nose-septumangle-decr', 'nose/nose-septumangle-incr', ''),
    ], [('Roman', {'nose_hump': 0.6, 'nose_curve': 0.5, 'nose_tip_angle': -0.3, 'nose_projection': 0.3}),
        ('Button', {'nose_length': -0.5, 'nose_tip_angle': 0.5, 'nose_tip_size': 0.3, 'nose_projection': -0.3}),
        ('Snub', {'nose_curve': -0.6, 'nose_tip_angle': 0.7}),
        ('Greek', {'nose_curve': 0.0, 'nose_hump': -0.5, 'nose_bridge_width': 0.3}),
        ('Broad', {'nose_width': 0.6, 'nostril_width': 0.6, 'nostril_flare': 0.5}),
        ('Narrow', {'nose_width': -0.6, 'nostril_width': -0.5, 'nose_bridge_width': -0.4})]),
    ('cheeks', 'Cheeks', [
        ('cheekbone_height', 'Cheekbone Height', 'cheek/{s}-cheek-trans-down', 'cheek/{s}-cheek-trans-up', 'beard'),
        ('cheekbone_width', 'Cheekbones', 'cheek/{s}-cheek-bones-decr', 'cheek/{s}-cheek-bones-incr', 'beard'),
        ('cheek_fullness', 'Fullness', 'cheek/{s}-cheek-volume-decr', 'cheek/{s}-cheek-volume-incr', 'beard'),
        ('cheek_hollow', 'Hollow', 'cheek/{s}-cheek-inner-incr', 'cheek/{s}-cheek-inner-decr', 'beard'),
        ('laugh_lines', 'Laugh Lines', 'mouth/mouth-laugh-lines-out', 'mouth/mouth-laugh-lines-in', 'beard'),
    ], [('High', {'cheekbone_height': 0.6, 'cheekbone_width': 0.5}), ('Gaunt', {'cheek_hollow': 0.8, 'cheek_fullness': -0.5}),
        ('Full', {'cheek_fullness': 0.7})]),
    ('mouth', 'Mouth', [
        ('mouth_width', 'Width', 'mouth/mouth-scale-horiz-decr', 'mouth/mouth-scale-horiz-incr', 'beard'),
        ('mouth_height', 'Height', 'mouth/mouth-trans-down', 'mouth/mouth-trans-up', 'beard'),
        ('mouth_depth', 'Protrusion', 'mouth/mouth-trans-backward', 'mouth/mouth-trans-forward', 'beard'),
        ('upper_lip', 'Upper Lip', 'mouth/mouth-upperlip-volume-decr', 'mouth/mouth-upperlip-volume-incr', 'beard'),
        ('lower_lip', 'Lower Lip', 'mouth/mouth-lowerlip-volume-decr', 'mouth/mouth-lowerlip-volume-incr', 'beard'),
        ('upper_lip_height', 'Upper Lip Height', 'mouth/mouth-upperlip-height-decr', 'mouth/mouth-upperlip-height-incr', 'beard'),
        ('lower_lip_height', 'Lower Lip Height', 'mouth/mouth-lowerlip-height-decr', 'mouth/mouth-lowerlip-height-incr', 'beard'),
        ('cupids_bow', "Cupid's Bow", 'mouth/mouth-cupidsbow-decr', 'mouth/mouth-cupidsbow-incr', 'beard'),
        ('bow_width', 'Bow Width', 'mouth/mouth-cupidsbow-width-decr', 'mouth/mouth-cupidsbow-width-incr', 'beard'),
        ('upper_lip_peak', 'Upper Lip Peak', 'mouth/mouth-upperlip-middle-down', 'mouth/mouth-upperlip-middle-up', 'beard'),
        ('philtrum', 'Philtrum', 'mouth/mouth-philtrum-volume-decr', 'mouth/mouth-philtrum-volume-incr', 'beard'),
        ('mouth_corners', 'Corners', 'mouth/mouth-angles-down', 'mouth/mouth-angles-up', 'beard'),
        ('lip_corners', 'Lip Ends', 'mouth/mouth-lowerlip-ext-down', 'mouth/mouth-lowerlip-ext-up', 'beard'),
        ('dimples', 'Dimples', 'mouth/mouth-dimples-out', 'mouth/mouth-dimples-in', 'beard'),
    ], [('Full', {'upper_lip': 0.6, 'lower_lip': 0.6}), ('Thin', {'upper_lip': -0.6, 'lower_lip': -0.5}),
        ('Bow', {'cupids_bow': 0.8, 'upper_lip_peak': 0.4}), ('Wide', {'mouth_width': 0.6}),
        ('Downturned', {'mouth_corners': -0.6}), ('Pouty', {'lower_lip': 0.6, 'mouth_depth': 0.4})]),
    ('jaw', 'Jaw', [
        ('jaw_width', 'Width', 'chin/chin-bones-decr', 'chin/chin-bones-incr', 'beard'),
        ('jaw_drop', 'Height', 'chin/chin-jaw-drop-decr', 'chin/chin-jaw-drop-incr', 'beard'),
        ('jaw_forward', 'Underbite', 'chin/chin-prognathism-decr', 'chin/chin-prognathism-incr', 'beard'),
        ('jowls', 'Jowls', 'neck/neck-double-decr', 'neck/neck-double-incr', 'beard'),
    ], [('Square', {'jaw_width': 0.7}), ('Soft', {'jaw_width': -0.5, 'jowls': 0.4})]),
    ('chin', 'Chin', [
        ('chin_length', 'Length', 'chin/chin-height-decr', 'chin/chin-height-incr', 'beard'),
        ('chin_depth', 'Depth', 'chin/chin-prominent-decr', 'chin/chin-prominent-incr', 'beard'),
        ('chin_width', 'Width', 'chin/chin-width-decr', 'chin/chin-width-incr', 'beard'),
        ('chin_cleft', 'Cleft', 'chin/chin-cleft-decr', 'chin/chin-cleft-incr', 'beard'),
    ], [('Strong', {'chin_depth': 0.6, 'chin_width': 0.4}), ('Pointed', {'chin_width': -0.6, 'chin_length': 0.3}),
        ('Cleft', {'chin_cleft': 0.8})]),
    ('ears', 'Ears', [
        ('ear_size', 'Size', 'ears/{s}-ear-scale-decr', 'ears/{s}-ear-scale-incr', 'hair'),
        ('ear_out', 'Out', 'ears/{s}-ear-wing-decr', 'ears/{s}-ear-wing-incr', 'hair'),
        ('ear_tilt', 'Tilt', 'ears/{s}-ear-rot-backward', 'ears/{s}-ear-rot-forward', 'hair'),
        ('ear_lobe', 'Lobe', 'ears/{s}-ear-lobe-decr', 'ears/{s}-ear-lobe-incr', 'hair'),
        ('ear_point', 'Point', 'ears/{s}-ear-shape-round', 'ears/{s}-ear-shape-pointed', 'hair'),
        ('ear_flare', 'Tip Flare', '', '', 'hair'),           # (owner 2026-11-25: the tips rotate out - made by hd_head)
    ], [('Pointed', {'ear_point': 0.8, 'ear_size': 0.2}), ('Small', {'ear_size': -0.5}), ('Flat', {'ear_out': -0.6})]),
    ('neck', 'Neck', [
        ('neck_thickness', 'Thickness', 'neck/neck-scale-horiz-decr', 'neck/neck-scale-horiz-incr', 'hair'),
    ], []),
]

SLIDERS = [s for f in FEATURES for s in f[2]]

# how far each end goes (owner, the plan: "as much flexibility as possible without getting into the grotesque or truly
# uncanny ... stopping a bit conservatively"): MakeHuman's targets at 1, unless a render showed an end too timid or
# too much. (slider, '-' or '+') -> gain; both ends: (slider, '')
GAIN = {
    ('nose_width', ''): 1.4, ('nose_height', ''): 1.3, ('nose_bridge_width', ''): 1.5, ('nostril_width', ''): 1.5,
    ('nostril_flare', ''): 1.5, ('nostril_angle', ''): 1.4, ('septum', ''): 1.5, ('nose_tip_size', ''): 1.4,
    ('nose_tip_angle', '-'): 0.7, ('nose_projection', '+'): 0.85,
    ('eye_hood', ''): 1.7, ('eye_crease', ''): 1.7, ('eye_fold_angle', ''): 1.7, ('epicanthic', ''): 1.7,
    ('eye_inner_corner', ''): 1.6, ('eye_outer_corner', ''): 1.6, ('eye_bags', ''): 1.6, ('eye_bag_height', ''): 1.2,
    ('mouth_height', ''): 0.75,
    ('eye_inner_open', ''): 1.4, ('eye_outer_open', ''): 1.4, ('eye_spacing', ''): 1.2,
}


def gain(key, sign):
    return GAIN.get((key, sign), GAIN.get((key, ''), 1.0))

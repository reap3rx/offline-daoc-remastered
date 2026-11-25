"""Midgard's reputation kin (claude 2026-11-25): the soldiers and the keepers of the old ways. rep_m1..rep_m4 share it."""
SOLDIERS = ["eiriks_huscarls", "steading_league", "huginfel_shieldwall", "galplen_woodwards", "khizil_forge", "wolfsbane_rangers",
            "vanern_wardens", "kings_host"]
LORE = ["haggerfel_volur", "nalliten_runecasters", "seidr_folk", "seithkona_circle", "volur_oath"]
def kin(k): return [x for x in (SOLDIERS if k in SOLDIERS else LORE) if x != k]

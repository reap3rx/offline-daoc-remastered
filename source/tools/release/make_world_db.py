"""A new player's world (Offline DAoC Remastered release, owner 2026-11-11: "I wouldn't want people using my DB save").

Copies the game database with SQLite's backup API (safe while the server runs) and takes every trace of a player out
of the copy: the account, its characters and their items, the bot roster with everything the bots earned, the
exchange's listings and sales, the local options (Make Me a GM). The world itself stays exactly as it is: monsters,
NPCs, merchants, quests, items, spells, keeps, the starting guilds, the server's settings. The roster is rolled fresh
by the launcher the first time it starts (PopulationRoster.Build) - every install gets its own living population.

    python make_world_db.py <the game database> <the new world database>

The original is only read. Prints what it removed and checks the copy's integrity.
"""
import os
import sqlite3
import sys

# whole tables whose rows are all someone's progress
CLEAR = [
    "Account", "AccountXCrafting", "AccountXCustomParam", "AccountXMoney",
    "DOLCharacters", "DOLCharactersXCustomParam", "DOLCharactersBackup", "DOLCharactersBackupXCustomParam",
    "CharacterXDataQuest", "CharacterXMasterLevel", "CharacterXOneTimeDrop", "PlayerXEffect", "PlayerInfo",
    "Inventory",                                  # every row belongs to a character or a bot (merchants use MerchantItem)
    "DBHouseCharsXPerms", "DBHousePermissions", "DBIndoorItem", "DBOutdoorItem", "HouseConsignmentMerchant",
    "househookpointitem",
    "Appeal", "AuditEntry", "BugReport", "Ban", "News", "serverstats", "KeepCaptureLog",
    "offline_world_bots", "offline_world_bot_guild", "offline_bot_commands", "bot_profiles",
    "offline_auction_listings", "offline_auction_escrow", "offline_auction_ledger", "realm_exchange_sales",
    "offline_runtime_status", "offline_local_options",
]


def tables(c):
    return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}


def main(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit("The new world must be written somewhere else than the game database.")
    if os.path.exists(dst):
        os.remove(dst)
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=30)
    target = sqlite3.connect(dst)
    source.backup(target)
    source.close()
    have = tables(target)
    removed = {}
    for t in CLEAR:
        if t in have:
            removed[t] = target.execute(f'delete from "{t}"').rowcount
    # houses: every lot back to the realm (none are owned in a fresh world)
    if "DBHouse" in have:
        removed["DBHouse (owners)"] = target.execute(
            "update DBHouse set OwnerID=NULL, Name=NULL, KeptMoney=0, LastPaid=NULL, GuildHouse=0, GuildName=NULL, "
            "HasConsignment=0 where OwnerID is not null and OwnerID<>''").rowcount
    # keeps and relics back with their first realm, unclaimed
    if "Keep" in have:
        removed["Keep (owners)"] = target.execute(
            "update Keep set Realm=OriginalRealm, ClaimedGuildName='' where Realm<>OriginalRealm "
            "or (ClaimedGuildName is not null and ClaimedGuildName<>'')").rowcount
    if "Relic" in have:
        removed["Relic (owners)"] = target.execute("update Relic set Realm=OriginalRealm where Realm<>OriginalRealm").rowcount
    # the starting guilds stay, without anyone's points or bank
    if "Guild" in have:
        target.execute("update Guild set RealmPoints=0, BountyPoints=0, Bank=0, MeritPoints=0, GuildLevel=0, "
                       "HaveGuildHouse=0, GuildHouseNumber=0")
    target.commit()
    target.execute("vacuum")
    ok = target.execute("pragma integrity_check").fetchone()[0]
    target.close()
    for k, v in removed.items():
        if v:
            print(f"  {k}: {v} rows")
    print(f"integrity: {ok}; {os.path.getsize(dst) / 1e6:.1f} MB -> {dst}")
    if ok != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

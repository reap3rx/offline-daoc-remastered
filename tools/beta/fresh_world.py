"""Offline DAoC Remastered Beta v0.1: turn a copy of the world database into a fresh world (claude 2026-11-03).
No player characters, no bots, every house lot for sale again, keeps back with their first realms, no news or
realm-exchange history. The account, the world itself (monsters, items, quests, NPCs, settings) stay.
Usage: python fresh_world.py <database copy>"""
import sqlite3, sys

db = sys.argv[1]
c = sqlite3.connect(db)
c.execute("PRAGMA foreign_keys=OFF")
q = lambda s, *a: c.execute(s, a).fetchall()
tables = {r[0] for r in q("select name from sqlite_master where type='table'")}
def run(sql, *a):
    t = sql.split()[2] if sql.upper().startswith("DELETE") else sql.split()[1]
    if t.strip('"[]`') not in tables:
        return
    n = c.execute(sql, a).rowcount
    print(f"  {n:6}  {sql[:110]}")

chars = [r[0] for r in q("select DOLCharacters_ID from DOLCharacters")]
print(f"player characters: {len(chars)}; bots: {q('select count(*) from offline_world_bots')[0][0]}")
c.execute("CREATE TEMP TABLE gone_chars(id TEXT PRIMARY KEY)")
c.executemany("INSERT INTO gone_chars VALUES (?)", [(x,) for x in chars])

# the bots (the launcher's own "delete all bots", server stopped)
run("DELETE FROM Inventory WHERE OwnerID LIKE 'offlinebot:%'")
run("DELETE FROM offline_auction_escrow")
run("DELETE FROM offline_auction_ledger")
run("DELETE FROM offline_auction_listings")
run("DELETE FROM offline_bot_commands")
run("DELETE FROM offline_world_bot_guild")
run("DELETE FROM offline_world_bots")
run("UPDATE offline_population_settings SET Value=CASE Key WHEN 'PopulationEnabled' THEN 'false' WHEN 'ActiveTarget' THEN '0' WHEN 'HardActiveCap' THEN '0' ELSE Value END WHERE Key IN ('PopulationEnabled','ActiveTarget','HardActiveCap')")
run("UPDATE ServerProperty SET Value=CASE `Key` WHEN 'population_enabled' THEN 'false' WHEN 'active_target' THEN '0' WHEN 'hard_active_cap' THEN '0' ELSE Value END WHERE `Key` IN ('population_enabled','active_target','hard_active_cap')")

# the houses: every owned lot for sale again
houses = [r[0] for r in q("select HouseNumber from DBHouse where OwnerID is not null and OwnerID<>''")]
c.execute("CREATE TEMP TABLE gone_houses(n INTEGER PRIMARY KEY)")
c.executemany("INSERT INTO gone_houses VALUES (?)", [(x,) for x in houses])
print(f"owned houses: {len(houses)}")
run("DELETE FROM DBHousePermissions WHERE HouseNumber IN (SELECT n FROM gone_houses)")
run("DELETE FROM DBHouseCharsXPerms WHERE HouseNumber IN (SELECT n FROM gone_houses)")
run("DELETE FROM DBIndoorItem WHERE HouseNumber IN (SELECT n FROM gone_houses)")
run("DELETE FROM DBOutdoorItem WHERE HouseNumber IN (SELECT n FROM gone_houses)")
run("DELETE FROM househookpointitem WHERE HouseNumber IN (SELECT n FROM gone_houses)")
run("DELETE FROM HouseConsignmentMerchant")
run("UPDATE DBHouse SET OwnerID='', Name='', Model=0, Porch=0, Emblem=0, GuildHouse=0, GuildName='', HasConsignment=0, KeptMoney=0, NoPurge=0, IndoorGuildBanner=0, IndoorGuildShield=0, OutdoorGuildBanner=0, OutdoorGuildShield=0 WHERE HouseNumber IN (SELECT n FROM gone_houses)")

# the player characters and everything that hangs on them
run("DELETE FROM Inventory WHERE OwnerID IN (SELECT id FROM gone_chars)")
run("DELETE FROM DOLCharactersXCustomParam")
run("DELETE FROM CharacterXDataQuest")
run("DELETE FROM CharacterXOneTimeDrop")
run("DELETE FROM PlayerXEffect")
run("DELETE FROM Quest")
run("DELETE FROM DOLCharactersBackup")
run("DELETE FROM DOLCharacters")
run("DELETE FROM AccountXMoney")
run("DELETE FROM AccountXCrafting")
# items left by characters deleted long ago (no owner any more), keeping anything an NPC, merchant, house or account owns
run("""DELETE FROM Inventory WHERE OwnerID NOT IN (SELECT Name FROM Account) AND OwnerID NOT IN (SELECT Account_ID FROM Account)
       AND OwnerID NOT IN (SELECT CAST(HouseNumber AS TEXT) FROM DBHouse) AND OwnerID NOT IN (SELECT DBHouse_ID FROM DBHouse)
       AND OwnerID GLOB '????????-????-????-????-????????????'""")

# the realm war and the world's history
run("UPDATE [Keep] SET Realm=OriginalRealm, ClaimedGuildName=''")
run("UPDATE Relic SET Realm=OriginalRealm, LastRealm=OriginalRealm")
run("DELETE FROM News")
run("DELETE FROM realm_exchange_sales")
c.commit()
c.execute("VACUUM")
print("integrity:", q("pragma integrity_check")[0][0])
print("left:", {t: q(f'select count(*) from "{t}"')[0][0] for t in ["DOLCharacters", "offline_world_bots", "Inventory", "Account"]})

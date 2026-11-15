# All server commands

Every command the server registers, by who may use it. Written by `tools/claude-version/list_server_commands.py` from the code; do not edit by hand. Many are inherited from the server the game is built on and are untested here. The everyday ones are in [QUICK-COMMANDS.md](../QUICK-COMMANDS.md).

## Player commands (218)

Anyone can use these.

| Command | Also | What it does | Usage |
| --- | --- | --- | --- |
| `/ac` |  | Action combat: click-to-swing melee with timed parry, block and dodge | `/ac on \| off \| toggle \| info`<br>`/ac swing \| style <anytime\|position\|reactive\|chain>`<br>`/ac parry \| guard <on\|off> \| dodge` |
| `/advice` |  | Lists all flagged Advisors, sends advisors questions, and sends messages to the Advice channel. |  |
| `/advisor` |  | Flags your character as a class or tradeskill Advisor (<ADV>) for new players' questions. |  |
| `/afk` |  | Enables/disables a flag that indicates you are "away from keyboard," and allows you to attach a message that will auto-send to any player that uses '/send' to you (e.g., '/afk Bio break'). |  |
| `/aggressive` |  | Restore normal companion assisting (default) | `/aggressive` |
| `/angry` |  | Look angrily around | `/angry` |
| `/anonymous` |  | Enables/disables anonymous mode, which hides you from player searches (e.g., '/who'). |  |
| `/api` |  | Toggles API options | `/api specs - toggle showing the specs of the player` |
| `/appea` |  | Use /appeal to file an appeal |  |
| `/appeal` |  | Usage: '/appeal <appeal type> <appeal text> |  |
| `/as` | `/asend` | Sends a message to the alliance chat | `/as <text>` |
| `/assist` |  | Assist your target | `/assist [playerName]` |
| `/autoloot` |  | automaticly pick up any loot that drops in your area | `/autoloot <on/off>` |
| `/autosplit` |  | Choose how the loot and money are split between members of group | `/autosplit on/off (Leader only: Toggles both coins and loot for entire group)`<br>`/autosplit coins (Leader only: When turned off, will send coins to the person who picked it up, instead of splitting it evenly across other members)`<br>`/autosplit loot (Leader only: When turned off, will send loot to the person who picked it up, instead of splitting it evenly across other members)`<br>`/autosplit self (Any group member: Choose not to receive autosplit loot items)` |
| `/backupstyle` |  | Modify automatic backup style. | `/backupstyle <set \| clear>` |
| `/bang` |  | Bang on your shield | `/bang` |
| `/battlechat` | `/bc` `/bchat` | Battle group command | `/bc <text>` |
| `/battlegroup` | `/bg` | Battle group command | `/bg <option>` |
| `/beckon` |  | Makes a beckoning gesture with character's hand | `/beckon` |
| `/beg` |  | Plea for items or money | `/beg` |
| `/bind` |  | Binds your soul to a bind location, you will start from there after you die and /release | `/bind` |
| `/blush` |  | Act in a shy manner | `/blush` |
| `/boat` | `/boatcommand` | Boat command (use /boat for options) | `/boat <option>` |
| `/book` |  | Your spellbook: everything your specializations teach, and when | `/book` |
| `/boot` |  | Kicks a player out of your house |  |
| `/bountylocation` |  | Show the location of your active bounty target. | `/bountylocation` |
| `/bountyrent` |  | Pay house rent with bountypoints |  |
| `/bow` |  | Give an honorable bow | `/bow` |
| `/brandish` |  | Brandish your weapon | `/brandish` |
| `/broadcast` | `/b` | Broadcast something to other players in the same zone | `/b <message>` |
| `/buff` |  | Buff your target (or yourself) with all your best buffs in one cast | `/buff  (all your best buffs on your target, or on you)`<br>`/buff <(buffList) \| all \| help> [playerName \| npcName]` |
| `/cancelstyle` |  | Toggle cancelstyle flag. | `/cancelstyle` |
| `/charge` |  | Onward! | `/charge` |
| `/chat` | `/c` | Chat group command | `/c <text>` |
| `/chatgroup` | `/cg` | Chat group command | `/cg <option>` |
| `/checkappeal` |  | Checks the status of your appeal or cancels it. | `/checkappeal view - View your appeal status.`<br>`/checkappeal cancel - Cancel your appeal and remove it from the queue.` |
| `/checkconcolor` |  | Check the target's con color server-side. | `/checkconcolor` |
| `/cheer` |  | Cheer with both hands in the air | `/cheer` |
| `/ck` |  | Displays who owns the CK while in a battleground. | `/ck` |
| `/clap` |  | Make a clapping gesture | `/clap` |
| `/classes` |  | Lists your realm's Classic + SI classes and party roles | `/classes` |
| `/classrog` |  | change the chance% of getting ROGs outside of your current class at level 50, | `/classrog <%chance>` |
| `/clientcfg` |  | The new client's settings kept on your character | `/clientcfg set <key> <value>` |
| `/cloak` |  | Show / hide your cloak. |  |
| `/cmdhelp` |  | Displays available commands | `'/cmdhelp' displays a list of all the commands and their descriptions`<br>`'/cmdhelp <cmd>' displays the usage for cmd` |
| `/combatstats` |  | Toggle detailed combat log | `/combatstats <on/off>` |
| `/companion` |  | Your companion: call, send home, gear, sell, role, how much they talk, ideas, a new name | `/companion [call \| home \| gear \| sell \| role \| ideas \| talk chatty\|normal\|quiet \| rename <name>]` |
| `/confuse` |  | Confused | `/confuse` |
| `/cower` |  | Cower | `/cower` |
| `/craftmacro` |  | Crafting macros and utilities | `'/craftmacro set <#>' to set how many items you want to craft`<br>`'/craftmacro clear' to reset to crafting once`<br>`'/craftmacro show' to show the current craft settings`<br>`'/craftmacro buy' to buy the necessary materials to craft one item`<br>`'/craftmacro buy <#>' to buy the necessary materials to craft <#> items`<br>`'/craftmacro buyto <#>' to buy only the missing materials to craft <#> items` |
| `/cry` |  | Sob pathetically | `/cry` |
| `/curtsey` |  | Give a low curtsey | `/curtsey` |
| `/dance` |  | Dance a little jig | `/dance` |
| `/deal` |  | Deal one card to a player in your group. Cards must first be prepared with /shuffle. | `/deal <name> <u/d>` |
| `/defensive` |  | Companions wait for enemies to approach you | `/defensive` |
| `/diabolical` |  | Sneer diabolically | `/diabolical` |
| `/disband` |  | Disband from a group | `/disband` |
| `/discard` |  | Discard card # from your hand, or discard all cards. | `/discard <#\|all>` |
| `/dismiss` |  | Make a dismissing gesture | `/dismiss` |
| `/dismisspet` |  | Dismiss the novelty pet | `/dismisspet` |
| `/dismount` |  | Dismount your steed | `/dismount` |
| `/doh` |  | doh | `/doh` |
| `/drink` |  | drink | `/drink` |
| `/dropmr` |  | Drops the Minotaurrelic. | `/dropmr` |
| `/duel` |  | Duel another player | `/duel` |
| `/email` |  | Set e-mail address for current account | `/email <address>` |
| `/emote` | `/em` `/e` | Roleplay an action or emotion | `/emote <text>` |
| `/events` |  | Dynamic events in your zone | `/events - the events window: this zone's events, to start, wake or stop (testing)`<br>`/events list - what's happening in this zone, in the chat`<br>`/events start <id> [stage] - start an event now, at a stage if given (testing)`<br>`/events stop <id> - end an event now (testing)`<br>`/events wake <id> - make it a disturbance now, waiting for someone to come near (testing)` |
| `/facegloc` |  | Turns and faces your character into the direction of the x, y coordinates provided (using DOL region global coordinates). | `/facegloc [x] [y]` |
| `/faceloc` |  | Turns and faces your character into the direction of the x, y coordinates provided (using Mythic zone coordinates). | `/faceloc [x] [y]` |
| `/faction` |  | Talk to players and active playerbots in your realm | `/faction <message>` |
| `/filter` |  | Turns off the bad word filter. | `/filter` |
| `/flex` |  | Makes a flexing gesture | `/flex` |
| `/formation` |  | Change the formation of your pets! | `/formation <type>` |
| `/freelevel` |  | Display state of FreeLevel | `/freelevel` |
| `/friend` |  | Adds/Removes a player to/from your friendlist! | `/friend <playerName>` |
| `/gc` | `/guildcommand` | Guild command (use /gc help for options) | `/gc <option>` |
| `/gloc` |  | Show the current coordinates | `/gloc` |
| `/grind` |  | Stationary automatic pulls with your temporary companions | `/grind`<br>`/grind stop` |
| `/groundassist` |  | Show the current coordinates | `/groundassist` |
| `/group` | `/g` | Say something to other chat group players | `/g <message>` |
| `/groupsort` |  | Sort players in the group | `'/groupsort switch <#> <#>' - switches two group members.` |
| `/gtrange` |  | Gives a range to a ground target | `/gtrange` |
| `/gu` | `/guild` | Guild Chat command | `/gu <text>` |
| `/hardcore` |  | Flags a player as Hardcore. Dying after activating Hardcore will result in the character deletion. | `/hardcore on` |
| `/held` |  | List the cards in your hand. Use 'held g' to display faceup cards held by group members. | `/held <g>` |
| `/helm` |  | Toggles the helm on and off when wearing an helm. | `/helm` |
| `/hood` |  | Toggles the hood on and off when wearing a hooded cloak. | `/hood` |
| `/horse` |  | Horse emotes | `/horse <emote>` |
| `/house` |  | Show various housing information |  |
| `/houseface` |  | Points to the specified guildhouse of the guild noted, or the lot number noted in the command. /houseface alone will point to one's personal home. |  |
| `/housefriend` |  | Invite a specified player to your house | `/housefriend all`<br>`/housefriend player <player>`<br>`/housefriend account <player>`<br>`/housefriend guild <guild> (If there are two or more words enclose them with " ")` |
| `/housepoints` |  | Toggles display of housepoints |  |
| `/howl` |  | Howl with rage | `/howl` |
| `/hug` |  | Makes a hugging gesture | `/hug` |
| `/ignore` |  | Adds/Removes a player to/from your Ignorelist! | `/ignore <playerName>` |
| `/induct` |  | Make a ceremonial induction gesture | `/induct` |
| `/invite` |  | Invite a specified or targeted player to join your group | `/invite <player>` |
| `/kiss` |  | Blow a kiss | `/kiss` |
| `/knock` |  | Knock on a house | `/knock` |
| `/language` |  | Change your language. |  |
| `/lastname` |  | Set/change your lastname. | `/lastname <name>` |
| `/laugh` |  | Makes a laughing gesture | `/bang` |
| `/level` |  | Allows you to level 20 instantly if you have a level 50 | `/level` |
| `/lfg` |  | Broadcast a LFG message to other players in the same region | `/lfg <message>` |
| `/loco` |  | Think this is crazy | `/loco` |
| `/lookfar` |  | Lets you look into the distance | `/lookfar` |
| `/makeleader` | `/m` | Set a new group leader (can be used by current leader). | `/m <playerName>` |
| `/mememe` |  | mememe | `/mememe` |
| `/military` |  | A military salute | `/military` |
| `/mobs` |  | Lists accessible monsters at an exact level | `/mobs <level> [page]`<br>`/mobs (your current level)` |
| `/monty` |  | Think Camelot is a silly place | `/monty` |
| `/namemount` |  | Name your hourse | `/namemount` |
| `/news` |  | Show news on social interface | `/news` |
| `/no` |  | Shake your head | `/no` |
| `/Noqueue` |  | Allows you to disable/enable queuing | `/Noqueue` |
| `/o` | `/osend` | Speak in officer chat (Must be a guild officer) | `/o <text>` |
| `/online` | `/on` | Shows all Players that are currently online |  |
| `/password` |  | Changes your account password | `/password <current_password> <new_password>` |
| `/played` |  | Returns the age of the character | `/played` |
| `/point` |  | Points to something in front of you | `/point` |
| `/ponder` |  | For when you just want to go "hmmmmmmm" | `/ponder` |
| `/pray` |  | You can pray on your gravestones to get some experience back | `/pray` |
| `/present` |  | To present someone with something | `/present` |
| `/pull` |  | Orders party bots and their pets to engage your target | `/pull` |
| `/quest` | `/quests` | Display a list of your ongoing and completed quests | `/quest` |
| `/questguide` |  | Read the period (2001-2004) Allakhazam walkthrough of a quest | `/questguide - next page of your active quests' guides`<br>`/questguide <quest name> [page]` |
| `/quit` | `/q` | Removes the player from the world | `/quit` |
| `/raid` |  | Open a level-50 companion raid (40 or 80 total) | `/raid 40`<br>`/raid 80` |
| `/raise` |  | Raise your hand, as in volunteering or getting attention | `/raise` |
| `/random` |  | prints out a random number between 1 and the number specified. | `/random [#] to get a random number between 1 and the number you specified.` |
| `/range` |  | Gives a range to a target | `/range` |
| `/realm` |  | Displays the current realm status. | `/realm` |
| `/realmtask` |  | Displays the current realm bonuses status. | `/realmtask` |
| `/realmtimer` |  | Displays the players current realmtimer Status | `/realmtimer` |
| `/rearrange` |  | Allows you to rearrange your character overview. | `/rearrange list - Shows a list with all to this account assigned characters and their slots.`<br>`/rearrange setslot [source slot] [target slot] - Sets the given source slot to the given target slot.` |
| `/region` | `/reg` | Broadcast something to other players in the same region | `/region <message>` |
| `/release` |  | When you are dead you can '/release'. This will bring you back to your bindpoint! | `/release` |
| `/relics` | `/relic` | Displays the current relic status. | `/relics` |
| `/rent` |  | Pay house rent |  |
| `/repair` |  | You can repair an item when you are a crafter | `/repair` |
| `/report` |  | 'Reports a bug |  |
| `/reportbug` |  | Use /appeal to file an appeal |  |
| `/reportharass` |  | Use /appeal to file an appeal |  |
| `/reportstuck` |  | Use /appeal to file an appeal |  |
| `/reporttos` |  | Use /appeal to file an appeal |  |
| `/respec` |  | Respecs the char | `/respec` |
| `/rofl` |  | rofl | `/rofl` |
| `/roleplay` |  | Flags a player with an  tag to indicate the player is a role player. | `/roleplay on/off` |
| `/roll` |  | simulates a dice roll. | `/roll [#] to throw with a specified number of dice` |
| `/rp` |  | toggle receiving realm points | `/rp <on/off>` |
| `/rude` |  | A rude gesture | `/rude` |
| `/safety` |  | Turns off PvP safety flag. | `/safety off` |
| `/salute` |  | Makes a stiff salute | `/salute` |
| `/salvage` |  | You can salvage one or multiple item(s) when you are a crafter | `/salvage`<br>`/salvage all`<br>`/salvage <bag>`<br>`/salvage <bag-bag>` |
| `/say` | `/s` | Say something to other players around you | `/say <message>` |
| `/search` |  | Search the current area. | `/search` |
| `/sell` |  | Sell items to a targeted merchant.  Specify a single bag, a range or all | `/sell 2-3 to sell all items in bags 2 and 3`<br>`/sell all to sell all items` |
| `/send` |  | Sends a private message to the target player. |  |
| `/serverinfo` |  | Shows information about the server | `/serverinfo` |
| `/servernews` | `/sn` | Shows the current Server News |  |
| `/settitle` |  | Sets the current player title | `/settitle <index> - to change current title using index in the list` |
| `/setwho` |  | Set your class or trade for /who output | `/setwho class \| trade` |
| `/shiver` |  | shiver | `/shiver` |
| `/show` |  | Show all your cards to the other players (all cards become 'up'). | `/show` |
| `/shrug` |  | Shrug your shoulders | `/shrug` |
| `/shuffle` |  | Shuffle # of decks, minimum 1. Must be used before /deal. | `/shuffle <#>` |
| `/sit` | `/rest` | Sit | `/sit` |
| `/slap` |  | Slap someone | `/slap` |
| `/slit` |  | Let your enemy know what you want to do to him | `/slit` |
| `/smile` |  | Make a big smile | `/smile` |
| `/socialmenu` |  | What you can do with your target (the controller's hold-Interact menu) | `/socialmenu [objectId]` |
| `/spacing` |  | Change the spacing of your pets! | `/spacing {normal, big, huge}` |
| `/sprint` |  | Toggles sprint mode | `/sprint [on\|off]` |
| `/stables` |  | Show your realm's Classic and Shrouded Isles stable connections | `/stables [page]`<br>`/stables classic`<br>`/stables si` |
| `/stagger` |  | stagger | `/stagger` |
| `/stand` |  | Stands up when sitting | `/stand` |
| `/startled` |  | Be startled | `/startled` |
| `/stats` |  | Displays player statistics |  |
| `/statsanon` |  | Hides your statistics | `/statsanon` |
| `/stench` |  | Wave away the local stench | `/stench` |
| `/storyquest` |  | Story quests: list yours; start / step / reset one (testing) | `/storyquest list \| start <id> [step] \| step <id> <step> \| done <id> \| reset <id> \| reload` |
| `/stuck` |  | Move the player to the last recorded safe position | `/stuck` |
| `/summon` | `/mount` | Summon your horse (or get off it) | `/summon`<br>`/mount` |
| `/surrender` |  | I give up! | `/surrender` |
| `/sweat` |  | sweat | `/sweat` |
| `/switch` |  | Equip Weapons from bag. (/switch 1h 1, will replace your mainhand weapon with the first slot in your backpack) | `/switch 1h <slot>`<br>`/switch offhand <slot>`<br>`/switch 2h <slot>`<br>`/switch range <slot>` |
| `/talk` |  | Talk | `/talk` |
| `/target` |  | target a player by name | `/target <playerName>` |
| `/targeteffects` |  | Display various combat related info about your target | `/targeteffects` |
| `/targetstats` |  | Display various combat related info about your target | `/targetstats` |
| `/task` |  | Ask for a Task from Guards or Merchants | `/task` |
| `/task` |  | Ask the targeted guard or merchant for a task, else open the Quest Guide | `/task (target a guard, merchant or crafter)`<br>`/task status`<br>`/task abort` |
| `/taunt` |  | A very mean gesture when you really want to insult someone | `/taunt` |
| `/tc` |  | Teleport to your capital's Realm Exchange | `/tc` |
| `/time` |  | time in game | `/time` |
| `/trade` |  | Broadcast a trade message to other players in the same region | `/trade <message>` |
| `/tradewith` |  | Open a trade with your target | `/tradewith` |
| `/train` |  | Trains a line by the specified amount | `/train <line> <level>` |
| `/transfercorpse` |  |  | `/tc`<br>`/transfercorpse <Keep name> ie: /transfercorpse dun crauchon` |
| `/vault` |  | Open the player's inventory. |  |
| `/version` |  | Get the version of the game server | `/version` |
| `/victory` |  | Make a victory cheer | `/victory` |
| `/viewreports` |  | Allows you to view submitted bug reports. | `/viewreports` |
| `/vote` |  | Displays the current poll or let you vote | `/vote  shows you the current voting`<br>`/vote 1\|2\|...\|x  vote for your choice with the given number` |
| `/wallet` |  | Your wallet: Marks of Valor, seals and the other currencies | `/wallet` |
| `/wave` |  | Makes a waving gesture | `/wave` |
| `/webdisplay` |  | Set informations displayed on the herald | `/webdisplay <position\|template\|equipment\|craft> [on\|off]` |
| `/where` |  | Ask where an NPC is from Guards | `/where <NPC Name>` |
| `/whisper` | `/whis` | Sends a private message to your target if it is close enough | `/whisper <message>` |
| `/who` |  | Shows who is online | `/who  Can be modified with [playername], [class], [#] level, [location], [##] [##] level range`<br>`/WHO ALL - lists all players online`<br>`/WHO NF lists all players online in New Frontiers`<br>`/WHO CSR lists all Customer Service Representatives currently online`<br>`/WHO DEV lists all Development Team Members currently online`<br>`/WHO QTA lists all Quest Team Assistants currently online` |
| `/worship` |  | worship | `/worship` |
| `/xfire` |  | Xfire support | `/xfire <on\|off>` |
| `/xp` |  | toggle receiving experience points | `/xp <on/off>` |
| `/xpstats` |  | Toggle showing XP statistics | `/xpstats <off\|on\|verbose>` |
| `/yawn` |  | yawn | `/yawn` |
| `/yell` | `/y` | Yell something to other players around you | `/yell <message>` |
| `/yes` |  | Nod your head | `/yes` |

## GM commands (66)

Need GM mode (the launcher's GM option, set while the server is stopped).

| Command | Also | What it does | Usage |
| --- | --- | --- | --- |
| `/addbind` |  |  |  |
| `/addhookpoint` |  |  |  |
| `/adviceteam` |  | Lists all flagged Advisors, sends advisors questions, and sends messages to the Advice channel as STAFF. |  |
| `/announce` |  |  |  |
| `/area` |  |  |  |
| `/ban` |  | #<ClientID> can be used in place of player name.  Use /clientlist to see playing clients. |  |
| `/blink` |  | Makes the specified UI Part of your target or yourself blinking. | `/blink <id>: type /blink for a list of possible IDs` |
| `/cast` |  |  | `/cast loadspell <spellid> Load a spell from the DB into the global spell cache` |
| `/clearinventory` |  |  | `/clearinventory - clears your entire inventory` |
| `/clientlist` |  | Usage: /clientlist [full] - full option includes IP's and accounts |  |
| `/crafting` |  |  | `/crafting salvageadd <SalvageYieldID (0 for next free)> <MaterialId_nb> <Count> [Realm] [PackageID]`<br>`/crafting salvageupdate <SalvageYieldID> <MaterialId_nb> <Count> <Realm> [PackageID]`<br>`/crafting salvageinfo <SalvageYieldID>` |
| `/debug` |  |  |  |
| `/diag` |  | Toggle server logging of performance diagnostics. | `/diag perf <on\|off> [duration] to toggle performance diagnostics logging on server with an optional duration (in minutes).`<br>`/diag notify <on\|off> <interval> to toggle GameEventMgr Notify profiling, where interval is the period of time in milliseconds during which to accumulate stats.`<br>`/diag object to count non-null service objects in ServiceObjectStore arrays.` |
| `/door` |  |  | `'/door show' toggle enable/disable add dialog when targeting doors`<br>`'/door sound <soundid>'` |
| `/fly` |  | Toggle invulnerable observer flight | `/fly — toggle observer flight; returns to your starting position when disabled` |
| `/genuniques` |  |  | `/genuniques ([TOA] \|\| [L51] \|\| [self] \|\| [suit] \|\| [objecttype]) [itemtype] : generate 8 unique items` |
| `/gmappeal` | `/gmhelp` | Commands for server staff to assist players with their Appeals. | `/gmappeal view <player name> - Views the appeal of a specific player.`<br>`/gmappeal list - Lists all the current Appeals from online players only, in a window.`<br>`/gmappeal listall - Will list Appeals of both offline and online players, in a window.`<br>`/gmappeal assist <player name> - Take ownership of the player's appeal and lets other staff know you are helping this player.`<br>`/gmappeal jumpto - Will jump you to the player you are currently assisting (must use /gmappeal assist first).`<br>`/gmappeal jumpback - Will jump you back to where you were after you've helped the player (must use /gmappeal jumpto first).` |
| `/GMinfo` |  | Various Information | `'/GMinfo (select a target or not)` |
| `/gmrelic` |  |  |  |
| `/gmrelicpad` |  |  |  |
| `/gmstealth` |  | Grants the ability to stealth to a gm/admin character | `/gmstealth on : turns the command on`<br>`/gmstealth off : turns the command off` |
| `/gmvote` |  | Various voting commands! | `/gmvote create ... creates a new empty voting`<br>`/gmvote add choice 1 ... adds 'choice 1' to the newly created voting`<br>`/gmvote desc use this several times ... adds the textline 'use this several times' to the newly created voting`<br>`/gmvote start ... starts the newly created voting`<br>`/gmvote start NAME ... loads and starts the voting saved with NAME`<br>`/gmvote cancel ... cancels the voting currently in progress` |
| `/harm` |  |  |  |
| `/heal` |  |  | `/heal me - heals self` |
| `/instance` |  | This command assists in the creation of instances. | `/instance key <instancekey> (this sets the id of the instance you want to work with)`<br>`/instance entry <ClassType> [<NpcTemplateID>] (add elements to the instance)`<br>`/instance remove (please target the element to remove)`<br>`/instance create <skin> (skin is the region id to copy)`<br>`/instance test (enter a created instance)`<br>`/instance close (delete the instance on the server)` |
| `/item` |  |  | `/item description <Description> <slot> - set the description of this item`<br>`/item procchance <chance>`<br>`/item classtype <ClassType> <slot> - Set this items ClassType`<br>`/item packageid <PackageID> <slot> - Set this items PackageID`<br>`/item levelrequired <level> <slot> - Set the required level needed to use spells and procs on this item`<br>`/item bonuslevel <level> <slot> - Set the level required for item bonuses to effect player` |
| `/jp` |  | Modify or use the jumppoint system | `/jp add <name>`<br>`/jp list`<br>`/jp port to <name>`<br>`/jp remove <name>` |
| `/jump` |  |  | `/jump to <#ClientID>`<br>`/jump to <myhouse \| house [#]>`<br>`/jump to region [#] - jump to same location in new region`<br>`/jump refresh - force a world refresh around you` |
| `/keep` |  |  | `/keep move {[x,y,z,h] [amount]} - admin only`<br>`/keep skintype [0 = any, 1 = old, 2 = new] - force keep to use old or new skins` |
| `/keepcomponent` |  |  | `/keepcomponent move - move to your position`<br>`/keepcomponent rotate [0 - 3]`<br>`/keepcomponent reload`<br>`'/keepcomponent save' to save the component in the DB` |
| `/keepguard` |  |  |  |
| `/merchant` |  |  | `'/merchant savelist <newname>' to saves this merchants items list under a new name` |
| `/minorelic` |  |  |  |
| `/mob` |  | Mob creation and modification commands. |  |
| `/mobfaction` |  |  |  |
| `/morph` |  | Temporarily changes the target player's model | `'/morph <modelID> [time]' to change into <modelID> for [time] minutes (default=10)` |
| `/mountgm` |  | Mount a steed | `/mountgm` |
| `/mute` |  | Command to mute annoying players.  Player mutes are temporary, allchars are set on an account and must be removed. | `/mute <playername or #ClientID> - example /mute #24  to mute player on client id 24`<br>`/mute <playername or #ClientID> allchars - this applies an account mute to this player`<br>`/mute <playername or #ClientID> remove - remove all mutes from this players account` |
| `/ngg` |  | NPC Gear Generator | `'/ngg random [color]' Create a completely random equipment template`<br>`'/ngg cloth [color]' Create a random set of cloth`<br>`'/ngg leather [color]' Create a random set of leather`<br>`'/ngg studded [color]' Create a random set of studded`<br>`'/ngg chain [color]' Create a random set of chain`<br>`'/ngg scale [color]' Create a random set of scale` |
| `/npc` |  | Various npc commands | `/npc say <text>`<br>`/npc yell <text>`<br>`/npc action <text>`<br>`/npc emote <emote>`<br>`/npc face <name>`<br>`/npc follow <name>` |
| `/object` |  | Various Object commands! | `'/object info' to get information about the object`<br>`'/object movehere' to move object to your location`<br>`'/object create [ObjectClassName]' to create a default object`<br>`'/object fastcreate [name] [modelID]' to create the specified object`<br>`'/object model <newModel>' to set the model to newModel`<br>`'/object modelinc' Increment the object model by 1` |
| `/offlinejump` |  |  |  |
| `/path` |  | There are several path functions | `/path create - creates a new temporary path, deleting any existing temporary path`<br>`/path load <pathname> - loads a path from db`<br>`/path add [speedlimit] [wait time in second] - adds a point at the end of the current path`<br>`/path save <pathname> - saves a path to db`<br>`/path travel - makes a target npc travel the current path`<br>`/path stop - clears the path for a targeted npc and tells npc to walk to spawn` |
| `/player` |  | Various Admin/GM commands to edit characters. | `/player name <newName>`<br>`/player lastname <change\|reset> <newLastName>`<br>`/player level <newLevel>`<br>`/player levelup`<br>`/player reset - Reset and re-level a player to their current level.`<br>`/player realm <newRealm>` |
| `/removehouse` |  | Remove House or you are | `/removehouse` |
| `/resetability` |  |  | `/resetability - <self\|target\|group\|cg\|bg>` |
| `/sameip` |  | Find the double logins | `/sameip` |
| `/setsalvage` |  |  | `/setsalvage - the item to modify have to be in lastbagpack slot (item saved and updated automatically)` |
| `/siegeweapon` |  | creates siege weapons | `/siegeweapon create miniram/lightram/mediumram/heavyram/catapult/ballista/cauldron/trebuchet` |
| `/spammob` |  | Mob creation and modification commands. | `/spammob create [amount] - creates [amount] mobs at the player's location`<br>`/spammob create [amount] [radius] - creates [amount] mobs in a [radius] around the player`<br>`/spammob clear [radius] - deletes all spam mobs in a [radius] around the player` |
| `/spawn` |  | Opens the companion class menu or creates a temporary helper | `/spawn [class name]` |
| `/speclock` |  | Set your SpecMod combat modifier to a designated value <0.01 min> | `/speclock <value> - where value is a decimal input like 1.10 or 0.85`<br>`/speclock reset - clear value and use normal combat calculations` |
| `/speed` |  | Change base speed of target (no parameter to see current speed) | `/speed [newSpeed]` |
| `/stop` |  | Stops the npc's movement! | `'/stop' to stop the target mob` |
| `/team` |  | Broadcasts a message to all server team members (i.e., plvl 2+). |  |
| `/tele` |  | Teleport to a playerbot or monster camp | `/tele <playerbot name>`<br>`/tele mob <monster name>` |
| `/teleport` |  | Manage teleport destinations | `'/teleport add <ID> <type>' add a teleport destination`<br>`'/teleport reload' reload all teleport locations from the db` |
| `/titlegm` |  | Changes target player's titles | `/titlegm <add> <class type> - add a title to the target player`<br>`/titlegm <remove> <class type> - remove a title from the target player`<br>`/titlegm <set> <class type> - sets current title of the target player`<br>`/titlegm <list> - lists all target player's titles` |
| `/translate` |  | Use '/translate add [Language] [TranslationId] [Text]' to add a new translation. |  |
| `/walk` |  | Commands a npc to walk! | `'/walk <xoff> <yoff> <zoff> <speed>' to make the npc walk to x+xoff, y+yoff, z+zoff` |
| `/weather` |  | Sets the weather for the current region | `'/weather info' for information about the current weather in this region`<br>`'/weather start <line> <duration> <speed> <diffusion> <intensity>' to start a storm in this region`<br>`'/weather start' to start a random storm in this region`<br>`'/weather restart' to restart the storm in this region`<br>`'/weather stop' to stop the storm in this region` |
| `/wf` |  | World feature tests: /wf chest [trap] \| /wf stone \| /wf die | `/wf chest [trap]`<br>`/wf stone`<br>`/wf die` |
| `/xmob` |  |  | `/xmob get <radius> (max5000)`<br>`/xmob view`<br>`/xmob spawn <radius> (max5000)`<br>`/xmob clear`<br>`/xmob copy <num> (max 20)`<br>`/xmob setlevels <radius> <value> or <min> <max> (max5000)` |
| `/zone` |  |  | `/zone info`<br>`/zone divingflag <0 = use region, 1 = on, 2 = off>`<br>`/zone waterlevel <#>`<br>`/zone bonus <zoneID\|current> <xpBonus> <rpBonus> <bpBonus> <coinBonus> <Save? (true/false)>` |
| `/zonebonus` | `/zb` | Picks a new bonus zone | `/zonebonus or /zb` |
| `/zonepoint` |  |  |  |

## Administrator commands (15)

Need an administrator account.

| Command | Also | What it does | Usage |
| --- | --- | --- | --- |
| `/account` |  | Creates new, manages existing, and controls character assignment for accounts. |  |
| `/benchmark` |  | Performs a system benchmark of the specified type. This is used to gauge overall system performance. |  |
| `/code` |  |  |  |
| `/dfowner` |  | Changes the Realm owning access to Darkness Falls |  |
| `/fixnpcspawn` |  | Fix NPC positions and spawn points using navmesh. | `/fixnpcspawn [target\|zone\|region\|world] <SnapDown> <SnapUp> <DryRun(true(default)/false)>`<br>`/fixnpcspawn goto <index> - Teleport to a fixed NPC from the last run`<br>`/fixnpcspawn result <page\|clear> - Print results (2k per page) or clear memory` |
| `/freeze` |  | Freeze The region timer you're in. (Test purpose only) | `/freeze {seconds}` |
| `/keepdoorteleport` |  | Manage keepdoor teleport destinations | `'/keepdoorteleport add <enter\|exit> <in\|out> add a teleport destination`<br>`'/keepdoorteleport reload' reload all teleport locations from the db` |
| `/plvl` |  | Alters an account's privilege level (plvl) and grants/revokes access to command types depending on the user's plvl. With these commands, accounts may be granted Admin, GM, and Player command access from in-game. |  |
| `/refresh` |  | Refresh some specific static data cache stored in scripts or other objects | `/refresh list \| ClassName 'dot' MethodName` |
| `/Reload` |  | Reload various elements | `/reload mob\|object\|specs\|spells\|teleports` |
| `/serverproperties` |  |  |  |
| `/shutdown` |  | Initiates a total shutdown of the server. |  |
| `/snoop` |  | Snoops | `/snoop <player>` |
| `/speedhack` |  | Change speed hack detection parameters (non-persistent). | `/speedhack <parameter> <value>` |
| `/unloadxmldb` |  | Unload your Database Tables to a local XML File Repository. |  |

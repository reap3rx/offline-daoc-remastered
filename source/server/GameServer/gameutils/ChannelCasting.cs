using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// Channelled casting (owner 2026-11-19: "hold the spell button down to channel it ... Quick ... Normal ... Powered
    /// ... cast bar"). A spell with ranks in its family (SpellFamilies), held on its key, is channelled instead of cast:
    ///   - let go before the first mark: it fizzles (owner 2026-11-19: "if the spell button isn't being held down, the
    ///     spell fizzles out (unless you get to one of the charge levels)");
    ///   - let go between the quick mark and the cast time: the rank before it (Quick);
    ///   - let go between the cast time and the powered mark: the current rank (Normal);
    ///   - let go past the powered mark: the next rank - learned or not yet (Powered).
    /// Nothing goes off until the key is let go ("it doesn't cast until you let go of the button even if you get to the
    /// maximum charge"): the gathering holds. The quick mark is the cast time times 0.6, down to 0.4 with dexterity; the
    /// powered mark the cast time times PoweredTimes. No rank before: no quick mark; no rank after: no powered mark.
    /// Moving or being interrupted breaks the channel; held past MaxHoldMs it fizzles. Each rank costs its own power; the
    /// one that goes off is cast with no cast time of its own (the channel was its cast).
    ///
    /// The client: "/channel hold" just before its UseSpell (the key is down) and "/channel release" when the key comes
    /// up; told "#CH|start|quickMs|normalMs|poweredMs|prev|cur|next|damageType" and "#CH|end|name|how" (how: quick /
    /// normal / powered, or fizzle with no name).
    /// </summary>
    public static class ChannelCasting
    {
        public const double PoweredTimes = 1.6;
        public const int MinQuickMs = 300;
        const int HoldPendingMs = 1500;
        public const int MaxHoldMs = 30000;

        sealed class State
        {
            public long HoldAt;                       // "/channel hold" came (its UseSpell next)
            public bool Active;
            public long Start;
            public int QuickMs, NormalMs, PoweredMs;
            public Spell Prev, Cur, Next;
            public SpellLine Line;
            public int X, Y;
            public int Serial;
        }

        static readonly ConditionalWeakTable<GamePlayer, State> _states = new();

        static State Of(GamePlayer p) => _states.GetValue(p, _ => new State());

        public static void Hold(GamePlayer p) => Of(p).HoldAt = GameLoop.GameLoopTime;

        public static bool IsChannelling(GamePlayer p) => p != null && _states.TryGetValue(p, out State s) && s.Active;

        /// <summary>The quick mark's share of the cast time: 0.6, less with dexterity (to 0.4 at 160).</summary>
        public static double QuickShare(int dex) => Math.Clamp(0.6 - (dex - 60) / 500.0, 0.4, 0.6);

        /// <summary>The ranks around a spell in its line: the one before (learned) and the one after (any).</summary>
        public static (Spell prev, Spell next) Ranks(Spell spell, SpellLine line)
        {
            if (spell == null || line == null)
                return (null, null);
            List<Spell> list = SkillBase.GetSpellList(line.KeyName);
            Spell prev = SpellFamilies.PreviousRank(spell, list);
            object k = SpellFamilies.Key(spell);
            Spell next = list.Where(s => s.ID != spell.ID && (s.Level > spell.Level || s.Level == spell.Level && s.ID > spell.ID) && Equals(SpellFamilies.Key(s), k))
                .OrderBy(s => s.Level).ThenBy(s => s.ID).FirstOrDefault();
            return (prev, next);
        }

        // only spells against foes - damage and crowd control (owner 2026-11-19: "the spell charging has also affected
        // buffs. I don't think it should work for those, only for offensive and crowd control spells")
        static bool Channelable(Spell s) =>
            s != null && CastTimeOf(s) > 0 && !s.NeedInstrument && s is not Song && !s.IsPulsing &&
            (IsPlaced(s) || s.IsHarmful && !SpellFamilies.IsPet(s));

        // A Necromancer's spells (owner 2026-11-24: "make the upgrades and spell casting work like others (since you can
        // cast some spells as a shade) with the charging"): the shade issues a PetSpell and the servant casts what it
        // carries, so the cast time to channel is the servant's; the rank that goes off reaches the servant instant
        // (ChannelledByShade - PetSpellHandler), the channel having been its cast.
        static bool IsServantSpell(Spell s) => s != null && s.SpellType == eSpellType.PetSpell && s.SubSpellID > 0;

        static Spell Carried(Spell s) => IsServantSpell(s) ? SkillBase.GetSpellByID(s.SubSpellID) : null;

        static int CastTimeOf(Spell s) => Math.Max(s.CastTime, Carried(s)?.CastTime ?? 0);

        static readonly ConditionalWeakTable<Spell, object> _channelled = new();

        /// <summary>PetSpellHandler: this PetSpell was channelled by the shade - its servant casts it at once.</summary>
        public static bool ChannelledByShade(Spell s) => s != null && _channelled.TryGetValue(s, out _);

        /// <summary>A spell set down at your ground target (an Animist's turrets): channelled too, the client showing where it
        /// will go - wherever the reticle points, within range - and setting the ground target there as the key comes up
        /// (owner 2026-11-21: "as soon as you release it, it will release where the action combat reticle is pointed").</summary>
        public static bool IsPlaced(Spell s) => s != null && s.SpellType is eSpellType.SummonAnimistFnF or eSpellType.SummonAnimistPet or eSpellType.SummonTheurgistPet;   // (a Theurgist's pets too - AlbionKits)

        /// <summary>UseSpellHandler: a held key's spell. True when it is channelled (the cast is the channel's).</summary>
        public static bool TryBegin(GamePlayer p, Spell spell, SpellLine line)
        {
            State st = Of(p);
            bool held = st.HoldAt > 0 && GameLoop.GameLoopTime - st.HoldAt <= HoldPendingMs;
            st.HoldAt = 0;
            if (st.Active)
                Cancel(p, st, null);                    // (another spell asked for: the channel gives way)
            if (!held || st.Active || !Channelable(spell) || line == null || !p.IsAlive)
                return false;
            if (p.IsCasting || p.IsMoving || p.IsStunned || p.IsMezzed || p.IsSilenced || ManaShield.IsWarding(p))
                return false;                          // (the ordinary cast says why not)
            if (p.GetSkillDisabledDuration(spell) > 0)
                return false;
            if (IsServantSpell(spell) && (p.ControlledBrain?.Body is not GameNPC servant || !servant.IsAlive))
                return false;                          // (no servant: PetSpellHandler says so)
            var (prev, next) = Ranks(spell, line);
            if (prev == null && next == null)
                return false;
            int normal;
            try
            {
                Spell timed = spell.CastTime > 0 ? spell : Carried(spell);
                normal = ScriptMgr.CreateSpellHandler(p, timed, line) is SpellHandler sh ? p.CalculateCastingTime(sh) : timed.CastTime;
            }
            catch (Exception)
            {
                normal = CastTimeOf(spell);
            }
            normal = Math.Max(500, normal);
            int dex = p.GetModified(eProperty.Dexterity);
            st.Active = true;
            st.Start = GameLoop.GameLoopTime;
            st.NormalMs = normal;
            st.QuickMs = prev != null ? Math.Max(MinQuickMs, (int) (normal * QuickShare(dex))) : 0;
            st.PoweredMs = next != null ? (int) (normal * PoweredTimes) : 0;
            st.Prev = prev;
            st.Cur = spell;
            st.Next = next;
            st.Line = line;
            st.X = p.X;
            st.Y = p.Y;
            int serial = ++st.Serial;
            p.Out.SendMessage($"You begin channelling {spell.Name}.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            // the gathering, held until the key comes up (its time: the longest a hold may last)
            foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellCastAnimation(p, spell.ClientEffect, (ushort) (MaxHoldMs / 100));
            NewClient.Send(p, $"#CH|start|{st.QuickMs}|{st.NormalMs}|{st.PoweredMs}|{Clean(prev?.Name)}|{Clean(spell.Name)}|{Clean(next?.Name)}|{(int) spell.DamageType}|{(IsPlaced(spell) ? spell.Range : 0)}");
            new ECSGameTimer(p, _ => Tick(p, st, serial), 100);
            return true;
        }

        static string Clean(string s) => (s ?? "").Replace("|", "/");

        static int Tick(GamePlayer p, State st, int serial)
        {
            if (!st.Active || st.Serial != serial)
                return 0;
            if (!p.IsAlive || p.ObjectState != GameObject.eObjectState.Active)
            {
                Cancel(p, st, null);
                return 0;
            }
            long dx = p.X - st.X, dy = p.Y - st.Y;
            if (IsServantSpell(st.Cur) && (p.ControlledBrain?.Body is not GameNPC servant || !servant.IsAlive))
            {
                Cancel(p, st, "Your servant is gone and your channel breaks!");
                return 0;
            }
            if (dx * dx + dy * dy > 24 * 24 || p.IsStunned || p.IsMezzed || p.IsSilenced)
            {
                Cancel(p, st, "You move and your channel breaks!");
                return 0;
            }
            if (p.IsBeingInterruptedByOther && p.InterruptTime > st.Start && p.LastInterrupter != p)
            {
                Cancel(p, st, $"{p.LastInterrupter?.GetName(0, true) ?? "Something"} breaks your channel!");
                return 0;
            }
            if (GameLoop.GameLoopTime - st.Start > MaxHoldMs)
            {
                Cancel(p, st, "You hold the spell too long and it fizzles out.");
                return 0;
            }
            return 100;
        }

        /// <summary>"/channel release": the key came up.</summary>
        public static void Release(GamePlayer p)
        {
            if (!_states.TryGetValue(p, out State st) || !st.Active)
                return;
            long el = GameLoop.GameLoopTime - st.Start;
            if (st.QuickMs > 0 ? el < st.QuickMs : el < st.NormalMs)
                Cancel(p, st, "Your spell fizzles out - hold it longer.");
            else if (el < st.NormalMs)
                Fire(p, st, st.Prev, "quick");
            else if (st.PoweredMs <= 0 || el < st.PoweredMs)
                Fire(p, st, st.Cur, "normal");
            else
                Fire(p, st, st.Next, "powered");
        }

        public static void Cancel(GamePlayer p)
        {
            if (_states.TryGetValue(p, out State st) && st.Active)
                Cancel(p, st, "You stop channelling.");
        }

        static void Cancel(GamePlayer p, State st, string why)
        {
            st.Active = false;
            st.Serial++;
            foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendInterruptAnimation(p);
            NewClient.Send(p, "#CH|end||fizzle");
            if (why != null)
                p.Out.SendMessage(why, eChatType.CT_SpellResisted, eChatLoc.CL_SystemWindow);
        }

        static void Fire(GamePlayer p, State st, Spell rank, string how)
        {
            st.Active = false;
            st.Serial++;
            rank ??= st.Cur;
            Spell instant = rank.Copy();
            instant.CastTime = 0;                       // (the channel was its cast)
            if (IsServantSpell(instant))
                _channelled.AddOrUpdate(instant, true);  // (and its servant's: PetSpellHandler)
            if (IsPlaced(rank))
                p.GroundTargetInView = true;            // (the client placed it on what the reticle sees)
            NewClient.Send(p, $"#CH|end|{Clean(rank.Name)}|{how}");
            if (!p.CastSpell(instant, st.Line))
            {
                foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendInterruptAnimation(p);
            }
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&channel", ePrivLevel.Player, "Channelled casting (the client's held spell keys)", "/channel hold | release | cancel")]
    public class ChannelCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null || args.Length < 2)
                return;
            switch (args[1].ToLowerInvariant())
            {
                case "hold": ChannelCasting.Hold(p); break;
                case "release": ChannelCasting.Release(p); break;
                case "cancel": ChannelCasting.Cancel(p); break;
            }
        }
    }
}

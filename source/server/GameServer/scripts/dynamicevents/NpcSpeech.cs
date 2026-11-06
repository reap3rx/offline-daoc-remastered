using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// An NPC speaking aloud without the NPC window (owner 2026-11-02: the window popping up mid-fight "messes with action
    /// combat" - "floating chat bubbles instead? Might be a useful system to have developed"). Every player within range
    /// gets "#SAY|&lt;object id&gt;|&lt;name&gt;|&lt;text&gt;": the new client floats the words over the NPC's head and
    /// puts them in the chat as a say line (game/ui/speech_bubbles.gd). The NPC window stays for talking to someone on
    /// purpose (a click: a greeting with [keywords] to answer).
    /// </summary>
    public static class NpcSpeech
    {
        public const int RANGE = 3000;                   // a shout across a battlefield: further than /say

        public static void Say(GameNPC npc, string text, int range = RANGE)
        {
            if (npc == null || string.IsNullOrEmpty(text) || npc.ObjectState != GameObject.eObjectState.Active)
                return;
            string line = $"#SAY|{npc.ObjectID}|{npc.Name}|{text.Replace('\n', ' ')}";
            foreach (GamePlayer p in npc.GetPlayersInRadius((ushort) range))
                NewClient.Send(p, line);
        }

        /// <summary>To one player only (a reply meant for them), still as a bubble.</summary>
        public static void SayTo(GameNPC npc, GamePlayer to, string text)
        {
            if (npc == null || to == null || string.IsNullOrEmpty(text))
                return;
            npc.TurnTo(to, 10000);
            NewClient.Send(to, $"#SAY|{npc.ObjectID}|{npc.Name}|{text.Replace('\n', ' ')}");
        }
    }
}

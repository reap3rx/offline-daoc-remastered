using DOL.GS.PlayerTitles;

namespace DOL.GS.Reputation
{
    /// <summary>
    /// The reputation title (owner 2026-11-22: "earning a title for Trusted, honored, and legend, and if it can, have that
    /// title auto apply when you're in that zone"): one entry in the titles list whose words follow where you are - your
    /// best title with this zone's factions, else your realm title - unless you locked one with /rep title.
    /// </summary>
    public class ReputationPlayerTitle : SimplePlayerTitle
    {
        public override string GetDescription(GamePlayer player)
        {
            string t = ReputationService.TitleFor(player);
            return string.IsNullOrEmpty(t) ? "your reputation title" : t;
        }

        public override string GetValue(GamePlayer source, GamePlayer player) => ReputationService.TitleFor(player);

        public override bool IsSuitable(GamePlayer player) => ReputationService.TitlesEarned(player).Count > 0;
    }
}

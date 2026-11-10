using DOL.GS.ServerProperties;

namespace DOL.GS
{
    /// <summary>
    /// Safety gates for the active-only autonomous population. Defaults guarantee
    /// that installing or starting the server cannot create a bot on its own.
    /// </summary>
    public static class AutonomousPopulationProperties
    {
        [ServerProperty("autonomous_population", "population_enabled", "Master switch. False means no autonomous profiles are created or spawned. Once enabled, live bot activity does not require a human player online.", false)]
        public static bool POPULATION_ENABLED;

        [ServerProperty("autonomous_population", "active_target", "Legacy dashboard mirror of the non-retired roster size. The server always targets the complete roster.", 0)]
        public static int ACTIVE_TARGET;

        [ServerProperty("autonomous_population", "hard_active_cap", "Legacy compatibility value only. It does not limit the autonomous population.", 0)]
        public static int HARD_ACTIVE_CAP;

        [ServerProperty("autonomous_population", "initial_cohort_size", "Recommended first observed cohort when population creation is explicitly enabled.", 3)]
        public static int INITIAL_COHORT_SIZE;

        [ServerProperty("autonomous_population", "active_only", "Reject time-skipped or offline simulated bot progression.", true)]
        public static bool ACTIVE_ONLY;

        [ServerProperty("autonomous_population", "startup_ramp_minutes", "Startup ramp duration. The first 33 percent stagger through five minutes and the remaining roster through the next ten minutes.", 15)]
        public static int STARTUP_RAMP_MINUTES;

        [ServerProperty("autonomous_population", "allow_character_deletion", "Owner-only destructive gate. Keep false so shutdowns, restarts, and population reductions can only park bot characters.", false)]
        public static bool ALLOW_CHARACTER_DELETION;

        [ServerProperty("autonomous_population", "ai_budget_ms", "Maximum autonomous decision work per game-loop slice. Work over budget is deferred, never simulated.", 4.0)]
        public static double AI_BUDGET_MS;

        [ServerProperty("autonomous_population", "world_actor_only", "Require every progressing bot to remain a real loaded world actor.", true)]
        public static bool WORLD_ACTOR_ONLY;

        // The living population's dials (owner 2026-11-10, "Living Bot Population - Plan"; OfflineDaoc.Population.PopulationKnobs
        // reads them, and the launcher's Population page writes them).
        [ServerProperty("autonomous_population", "population_max_online_per_realm", "Most bots online per realm at once.", 250)]
        public static int POPULATION_MAX_ONLINE_PER_REALM;

        [ServerProperty("autonomous_population", "population_curve_scale", "Multiplies every hour's online share of the roster (0.5 = a quiet server).", 1.0)]
        public static double POPULATION_CURVE_SCALE;

        [ServerProperty("autonomous_population", "population_prime_start_hour", "The local hour prime time starts (it lasts about four hours).", 19)]
        public static int POPULATION_PRIME_START_HOUR;

        [ServerProperty("autonomous_population", "population_new_arrivals", "New level-one arrivals online at a time per realm.", 30)]
        public static int POPULATION_NEW_ARRIVALS;

        [ServerProperty("autonomous_population", "population_session_scale", "Multiplies every bot session's length.", 1.0)]
        public static double POPULATION_SESSION_SCALE;

        [ServerProperty("autonomous_population", "population_persona_mix", "Casual / regular / tryhard percent for new personas.", "25/55/20")]
        public static string POPULATION_PERSONA_MIX;

        [ServerProperty("autonomous_population", "population_chat_level", "quiet, normal or lively.", "normal")]
        public static string POPULATION_CHAT_LEVEL;

        [ServerProperty("autonomous_population", "population_mistake_rate", "off, low, normal or high.", "normal")]
        public static string POPULATION_MISTAKE_RATE;

        [ServerProperty("autonomous_population", "population_fast_clock", "Testing: the population's day passes in an hour.", false)]
        public static bool POPULATION_FAST_CLOCK;

        [ServerProperty("autonomous_population", "population_launch_utc", "When the population's first arrivals began (stamped by the server; cleared when the launcher builds a fresh roster). The roster arrives over about 24 days from it.", "")]
        public static string POPULATION_LAUNCH_UTC;
    }
}

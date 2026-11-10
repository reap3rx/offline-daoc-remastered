#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace OfflineDaoc.Population;

// The living bot population (owner 2026-11-10, "Living Bot Population - Plan", with the online shares doubled): who is
// online and when. Pure rules, shared by the server (its login scheduler) and the launcher (roster building, the
// Population page) - no server types here, so the launcher links this file as it links BotGoalSettings.cs.

/// <summary>
/// A bot's player habits, rolled once when the roster is built and saved with it (offline_world_bots.PersonaJson), so
/// the same bot is recognisably the same player night after night. Every trait is a 0-100 slider.
///   Drive   casual .. tryhard (session length, how hard it pushes)
///   Focus   PvE .. RvR
///   Social  soloer .. grouper
///   Skill   makes mistakes .. clean play
///   Chat    quiet .. talkative
///   Sched   its usual play time: evening, weekend, night or day
/// </summary>
public sealed class BotPersona
{
    public int V { get; set; } = 1;
    public int Drive { get; set; } = 50;
    public int Focus { get; set; } = 40;
    public int Social { get; set; } = 50;
    public int Skill { get; set; } = 50;
    public int Chat { get; set; } = 45;
    public string Sched { get; set; } = "evening";

    public const string Casual = "casual", Regular = "regular", Tryhard = "tryhard";

    public string Tier => Drive < 34 ? Casual : Drive > 70 ? Tryhard : Regular;
    public string SocialKind => Social < 34 ? "solo" : Social > 66 ? "group" : "either";
    public string FocusKind => Focus < 34 ? "pve" : Focus > 66 ? "rvr" : "mixed";

    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

    public string ToJson() => JsonSerializer.Serialize(this, Json);

    public static BotPersona? Parse(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
            return null;
        try
        {
            return JsonSerializer.Deserialize<BotPersona>(json, Json);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    /// <summary>Its usual session length in minutes: casual 30-90, regular 60-180, tryhard 120-300.</summary>
    public (int Min, int Max) SessionMinutes => Tier switch
    {
        Casual => (30, 90),
        Tryhard => (120, 300),
        _ => (60, 180),
    };

    /// <summary>How likely it plays at this local time: 1 inside its usual window, less at its edges, rarely outside.</summary>
    public double ScheduleWeight(DateTime local)
    {
        double h = local.Hour + local.Minute / 60.0;
        bool weekend = local.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday;
        return Sched switch
        {
            "weekend" => weekend ? Window(h, 10, 24) : Window(h, 19.5, 22.5) * 0.45,
            "night" => Window(h, 21, 27),
            "day" => weekend ? Window(h, 9, 19) : Window(h, 8.5, 17),
            _ => weekend ? Window(h, 12, 24) : Window(h, 18, 23.5),        // evening
        };
    }

    // 1 inside [from, to) (hours, to may pass midnight: 27 = 3 am), 0.35 within 90 minutes of either end, else 0.08.
    private static double Window(double h, double from, double to)
    {
        for (int shift = -24; shift <= 24; shift += 24)
        {
            double x = h + shift;
            if (x >= from && x < to)
                return 1.0;
        }
        for (int shift = -24; shift <= 24; shift += 24)
        {
            double x = h + shift;
            if ((x >= from - 1.5 && x < from) || (x >= to && x < to + 1.5))
                return 0.35;
        }
        return 0.08;
    }

    // Classes that lean one way (owner's plan: "A healer leans grouper, an assassin leans soloer and RvR").
    public static readonly HashSet<int> Healers = [4, 6, 10, 24, 26, 28, 46, 47, 48];
    public static readonly HashSet<int> Assassins = [9, 23, 49];
    public static readonly HashSet<int> Loners = [3, 5, 12, 13, 25, 27, 30, 41, 50, 55, 63];

    /// <summary>
    /// A fresh persona: the drive mix (casual / regular / tryhard, percent) and the plan's other mixes - focus 45 / 35 /
    /// 20 PvE / mixed / RvR, social 30 / 40 / 30 solo / either / group, skill and chat on bell curves (chat a little
    /// quiet), schedule evening most, then weekend, then night owl and daytime - nudged by the class.
    /// </summary>
    public static BotPersona Roll(Random rng, int classId, int casualPct = 25, int tryhardPct = 20)
    {
        var p = new BotPersona();
        int d = rng.Next(100);
        p.Drive = d < casualPct ? rng.Next(5, 34) : d >= 100 - tryhardPct ? rng.Next(71, 98) : rng.Next(34, 71);
        int f = rng.Next(100);
        p.Focus = f < 45 ? rng.Next(3, 34) : f < 80 ? rng.Next(34, 67) : rng.Next(67, 98);
        int s = rng.Next(100);
        p.Social = s < 30 ? rng.Next(3, 34) : s < 70 ? rng.Next(34, 67) : rng.Next(67, 98);
        p.Skill = Bell(rng, 50, 16);
        p.Chat = Bell(rng, 42, 18);
        int sc = rng.Next(100);
        p.Sched = sc < 50 ? "evening" : sc < 75 ? "weekend" : sc < 88 ? "night" : "day";
        if (Healers.Contains(classId))
            p.Social = Math.Min(97, p.Social + 18);
        else if (Assassins.Contains(classId))
        {
            p.Social = Math.Max(3, p.Social - 18);
            p.Focus = Math.Min(97, p.Focus + 15);
        }
        else if (Loners.Contains(classId))
            p.Social = Math.Max(3, p.Social - 8);
        return p;
    }

    private static int Bell(Random rng, double mean, double sd)
    {
        double u1 = 1.0 - rng.NextDouble(), u2 = rng.NextDouble();
        double z = Math.Sqrt(-2.0 * Math.Log(u1)) * Math.Cos(2.0 * Math.PI * u2);
        return (int)Math.Clamp(Math.Round(mean + z * sd), 2, 98);
    }
}

/// <summary>The dials (ServerProperty rows the launcher's Population page edits), with the plan's defaults.</summary>
public sealed record PopulationKnobs(
    int MaxOnlinePerRealm = 250,
    double CurveScale = 1.0,
    int PrimeStartHour = 19,
    int NewArrivals = 30,
    double SessionScale = 1.0,
    int CasualPct = 25,
    int TryhardPct = 20,
    string ChatLevel = "normal",
    string MistakeRate = "normal",
    bool FastClock = false)
{
    public const string KeyMaxOnline = "population_max_online_per_realm";
    public const string KeyCurveScale = "population_curve_scale";
    public const string KeyPrimeStart = "population_prime_start_hour";
    public const string KeyNewArrivals = "population_new_arrivals";
    public const string KeySessionScale = "population_session_scale";
    public const string KeyPersonaMix = "population_persona_mix";
    public const string KeyChatLevel = "population_chat_level";
    public const string KeyMistakeRate = "population_mistake_rate";
    public const string KeyFastClock = "population_fast_clock";

    /// <summary>A day passes in an hour on the fast clock (the plan's test switch).</summary>
    public double ClockRate => FastClock ? 24.0 : 1.0;

    public static PopulationKnobs FromProperties(Func<string, string?> read)
    {
        var d = new PopulationKnobs();
        (int casual, int tryhard) = (d.CasualPct, d.TryhardPct);
        string? mix = read(KeyPersonaMix);
        if (!string.IsNullOrWhiteSpace(mix))
        {
            string[] f = mix.Split('/', ',', ' ').Where(x => x.Length > 0).ToArray();
            if (f.Length == 3 && int.TryParse(f[0], out int c) && int.TryParse(f[2], out int t))
                (casual, tryhard) = (Math.Clamp(c, 0, 100), Math.Clamp(t, 0, 100 - Math.Clamp(c, 0, 100)));
        }
        return d with
        {
            MaxOnlinePerRealm = Int(read(KeyMaxOnline), d.MaxOnlinePerRealm, 0, 5000),
            CurveScale = Dbl(read(KeyCurveScale), d.CurveScale, 0.0, 10.0),
            PrimeStartHour = Int(read(KeyPrimeStart), d.PrimeStartHour, 0, 23),
            NewArrivals = Int(read(KeyNewArrivals), d.NewArrivals, 0, 1000),
            SessionScale = Dbl(read(KeySessionScale), d.SessionScale, 0.05, 10.0),
            CasualPct = casual,
            TryhardPct = tryhard,
            ChatLevel = read(KeyChatLevel)?.Trim().ToLowerInvariant() is "quiet" or "lively" or "normal" ? read(KeyChatLevel)!.Trim().ToLowerInvariant() : d.ChatLevel,
            MistakeRate = read(KeyMistakeRate)?.Trim().ToLowerInvariant() is "off" or "low" or "normal" or "high" ? read(KeyMistakeRate)!.Trim().ToLowerInvariant() : d.MistakeRate,
            FastClock = bool.TryParse(read(KeyFastClock), out bool fast) && fast,
        };
    }

    private static int Int(string? s, int fallback, int lo, int hi) =>
        int.TryParse(s, out int v) ? Math.Clamp(v, lo, hi) : fallback;

    private static double Dbl(string? s, double fallback, double lo, double hi) =>
        double.TryParse(s, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double v)
            ? Math.Clamp(v, lo, hi) : fallback;
}

/// <summary>The daily curve and the level bands.</summary>
public static class PopulationCurve
{
    // (hour, share of the roster online) - the plan's table doubled (owner 2026-11-10: "I would bump up the percentages
    // for online by double"): 3-8 am about 6%, 8 am - 5 pm about 12%, rising to 20% by 7 pm, 20-24% in prime time
    // (7-11 pm), falling to about 8% by 3 am. Straight lines between the points.
    private static readonly (double Hour, double Share)[] Points =
    [
        (0, 0.17), (1, 0.13), (2, 0.10), (3, 0.075), (4, 0.06), (8, 0.06), (9, 0.12), (17, 0.12), (19, 0.20),
        (21, 0.24), (23, 0.22), (24, 0.17),
    ];

    /// <summary>The share of a realm's roster online at this local time (prime time moved to start at primeStart).</summary>
    public static double Share(DateTime local, int primeStart = 19, double scale = 1.0, bool drift = true)
    {
        double h = local.Hour + local.Minute / 60.0 + local.Second / 3600.0;
        h = ((h - (primeStart - 19)) % 24 + 24) % 24;
        double share = Points[^1].Share;
        for (int i = 1; i < Points.Length; i++)
        {
            if (h <= Points[i].Hour)
            {
                var (h0, s0) = Points[i - 1];
                var (h1, s1) = Points[i];
                share = s0 + (s1 - s0) * (h - h0) / (h1 - h0);
                break;
            }
        }
        return Math.Max(0.0, share * scale * (drift ? Drift(local) : 1.0));
    }

    /// <summary>A little day-to-day wobble (within 10%), smooth through the hours, so two evenings aren't identical.</summary>
    public static double Drift(DateTime local)
    {
        double hours = (local - DateTime.MinValue).TotalHours;
        long h0 = (long)Math.Floor(hours);
        double t = hours - h0;
        return 1.0 + 0.1 * (Noise(h0) * (1 - t) + Noise(h0 + 1) * t);
    }

    private static double Noise(long n)
    {
        unchecked
        {
            ulong x = (ulong)n * 0x9E3779B97F4A7C15UL;
            x ^= x >> 31;
            x *= 0xBF58476D1CE4E5B9UL;
            x ^= x >> 29;
            return (x % 2001) / 1000.0 - 1.0;                  // -1 .. 1
        }
    }

    /// <summary>The online target for a realm: roster size x the hour's share, under the ceiling.</summary>
    public static int Target(int rosterSize, DateTime local, PopulationKnobs knobs) =>
        Math.Min(knobs.MaxOnlinePerRealm, (int)Math.Round(rosterSize * Share(local, knobs.PrimeStartHour, knobs.CurveScale)));

    public const int Bands = 6;                                 // 1-9, 10-19, 20-29, 30-39, 40-49, 50

    public static int Band(int level) => level >= 50 ? 5 : Math.Clamp(level / 10, 0, 4);

    public static string BandName(int band) => band == 5 ? "50" : band == 0 ? "1-9" : $"{band * 10}-{band * 10 + 9}";
}

/// <summary>
/// Who logs in next (the plan's "Who"): a draw weighted by the bot's schedule, room in its level band, the class mix
/// online in that band and how long since it last played; bots that have never played ("not yet arrived") only come
/// while the 1-9 band has room for new arrivals.
/// </summary>
/// <summary>
/// The arrival pace (owner 2026-11-10: "all arrive over 3-4 weeks"): a few percent of the roster on day one, then evenly
/// until everyone has arrived by day 24 - counted from the population's launch (the server property population_launch_utc,
/// set at the first poll after a fresh roster). The online target follows the population that has arrived or is due, so
/// a young server is quieter and fills as its people turn up.
/// </summary>
public static class PopulationArrivals
{
    public const double Days = 24.0;
    public const double Headstart = 0.06;

    public static int Allowed(int roster, double daysSinceLaunch) =>
        (int)Math.Ceiling(roster * Math.Min(1.0, Headstart + (1.0 - Headstart) * Math.Max(0.0, daysSinceLaunch) / Days));

    /// <summary>The population the online curve is a share of: who has arrived or is due to by now.</summary>
    public static int Known(int roster, int arrived, double daysSinceLaunch) =>
        Math.Min(roster, Math.Max(arrived, Allowed(roster, daysSinceLaunch)));
}

public static class PopulationPicker
{
    public readonly record struct Candidate(long BotId, int Level, int ClassId, BotPersona Persona, double MinutesSinceLogout,
        bool Arrived, bool Special);

    public sealed class Online
    {
        public int Total;
        public readonly int[] ByBand = new int[PopulationCurve.Bands];
        public readonly Dictionary<(int Band, int Class), int> ByBandClass = new();
        public int Newcomers;                                   // online in their first session

        public void Add(int level, int classId, bool newcomer = false)
        {
            Total++;
            if (newcomer)
                Newcomers++;
            int b = PopulationCurve.Band(level);
            ByBand[b]++;
            ByBandClass[(b, classId)] = ByBandClass.GetValueOrDefault((b, classId)) + 1;
        }
    }

    /// <summary>Each band's share of the online target, by where the arrived roster stands (plus a little floor), capped
    /// at 40% of the target so no zone floods.</summary>
    public static int[] BandQuotas(int target, int[] arrivedByBand)
    {
        int total = arrivedByBand.Sum();
        var q = new int[PopulationCurve.Bands];
        int cap = Math.Max(3, (int)Math.Ceiling(target * 0.4));
        for (int b = 0; b < q.Length; b++)
        {
            double share = total > 0 ? (double)arrivedByBand[b] / total : (b == 0 ? 1.0 : 0.0);
            q[b] = Math.Min(cap, Math.Max(arrivedByBand[b] > 0 ? 2 : 0, (int)Math.Ceiling(target * share * 1.25)));
        }
        return q;
    }

    public static double Weight(Candidate c, Online online, int[] quotas, DateTime local, int newArrivalRoom)
    {
        int band = c.Arrived ? PopulationCurve.Band(c.Level) : 0;
        if (!c.Arrived && newArrivalRoom <= 0)
            return 0.0;                                        // (a newcomer waits for the starting zones to have room)
        double w = c.Persona.ScheduleWeight(local);
        if (c.Arrived && online.ByBand[band] >= quotas[band])
            w *= 0.08;                                         // its band is full
        int inBand = online.ByBand[band];
        int sameClass = online.ByBandClass.GetValueOrDefault((band, c.ClassId));
        if (sameClass >= 2 && sameClass * 10 > inBand * 1.5)    // (about 15 classes a realm: well over its fair share)
            w *= 0.6;
        if (c.MinutesSinceLogout < 45)
            w *= 0.05;                                         // just logged off: unlikely to come straight back
        else if (c.MinutesSinceLogout < 180)
            w *= 0.4;
        if (c.Special)
            w *= 4.0;                                          // Claude's three: around more often than most
        return w;
    }

    /// <summary>How many newcomers may log in for the first time now: at most `newArrivalsKnob` in their first session
    /// at once, and no more than the arrival pace allows (PopulationArrivals).</summary>
    public static int ArrivalRoom(Online online, int newArrivalsKnob, int allowedArrived, int arrived) =>
        Math.Min(newArrivalsKnob - online.Newcomers, allowedArrived - arrived);

    public static Candidate? Pick(IReadOnlyList<Candidate> offline, Online online, int target, int[] arrivedByBand,
        DateTime local, int arrivalRoom, Random rng)
    {
        int[] quotas = BandQuotas(target, arrivedByBand);
        int room = arrivalRoom;
        double total = 0;
        var weights = new double[offline.Count];
        for (int i = 0; i < offline.Count; i++)
        {
            weights[i] = Weight(offline[i], online, quotas, local, room);
            total += weights[i];
        }
        if (total <= 0)
            return null;
        double r = rng.NextDouble() * total;
        for (int i = 0; i < weights.Length; i++)
        {
            r -= weights[i];
            if (r <= 0 && weights[i] > 0)
                return offline[i];
        }
        for (int i = weights.Length - 1; i >= 0; i--)
            if (weights[i] > 0)
                return offline[i];
        return null;
    }

    /// <summary>How long this session runs (minutes of play): the persona's range x the knob, with a small chance of
    /// an extra-long or a cut-short night.</summary>
    public static double SessionMinutes(BotPersona p, double scale, Random rng)
    {
        (int lo, int hi) = p.SessionMinutes;
        double m = lo + rng.NextDouble() * (hi - lo);
        double roll = rng.NextDouble();
        if (roll < 0.04)
            m *= 1.7;
        else if (roll < 0.09)
            m *= 0.4;
        return Math.Max(10, m * scale);
    }
}

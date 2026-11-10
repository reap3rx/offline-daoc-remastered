using System.Data.SQLite;
using System.Globalization;
using OfflineDaoc.Population;

namespace OfflineDaoc.Launcher;

/// <summary>
/// The launcher's Population page (owner 2026-11-10, "Living Bot Population - Plan": "a Population page to build a
/// roster, watch it, and turn the dials without editing files"):
///   Roster - a size per realm and BUILD ROSTER: lore-named bots with personas, not yet arrived, topped up to the size.
///   Now    - per realm: roster, arrived, online now, the curve's target this hour; online by level band; the busiest
///            classes; who just logged in and out.
///   Dials  - the ceiling, the curve scale, prime time, new arrivals at a time, session length, the persona mix, chat
///            level, mistake rate and the fast clock (a day in an hour, for testing). Saved to the server's
///            properties; a running server picks them up within half a minute.
/// </summary>
internal sealed class PopulationPanel : UserControl
{
    private readonly Func<string> _database;
    private readonly Func<string> _root;
    private readonly Label _summary = new()
    {
        Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft, Padding = new Padding(8, 0, 0, 0),
        Font = new Font("Georgia", 9.5f, FontStyle.Bold), ForeColor = DaocTheme.GoldLight,
    };
    private readonly TextBox _view = new()
    {
        Dock = DockStyle.Fill, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical,
        BackColor = DaocTheme.StoneDark, ForeColor = DaocTheme.Text, Font = new Font("Consolas", 9f), BorderStyle = BorderStyle.Fixed3D,
    };
    private readonly NumericUpDown _size = Number(2000, 0, 20000, 100);
    private readonly NumericUpDown _maxOnline = Number(250, 0, 5000, 10);
    private readonly NumericUpDown _arrivals = Number(30, 0, 1000, 5);
    private readonly NumericUpDown _prime = Number(19, 0, 23, 1);
    private readonly TextBox _curve = Field("1.0");
    private readonly TextBox _session = Field("1.0");
    private readonly TextBox _mix = Field("25/55/20");
    private readonly ComboBox _chat = Choice("quiet", "normal", "lively");
    private readonly ComboBox _mistakes = Choice("off", "low", "normal", "high");
    private readonly CheckBox _fast = new() { Text = "Fast clock (a day in an hour)", AutoSize = true, ForeColor = DaocTheme.Text };
    private readonly System.Windows.Forms.Timer _timer = new() { Interval = 5000 };
    private bool _busy;

    public PopulationPanel(Func<string> database, Func<string> root)
    {
        _database = database;
        _root = root;
        Dock = DockStyle.Fill;
        BackColor = DaocTheme.Panel;
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, RowCount = 4, ColumnCount = 1, Padding = new Padding(7) };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.Controls.Add(_summary, 0, 0);

        var roster = Row();
        roster.Controls.Add(Caption("Roster per realm:"));
        roster.Controls.Add(_size);
        var build = new RuneButton { Text = "BUILD ROSTER", Width = 130 };
        build.Click += async (_, _) => await BuildAsync(build);
        roster.Controls.Add(build);
        roster.Controls.Add(Caption("Tops each realm up to this size with lore-named bots who arrive in waves. Never removes a bot."));
        layout.Controls.Add(roster, 0, 1);

        var dials = Row();
        dials.Controls.Add(Caption("Max online / realm"));
        dials.Controls.Add(_maxOnline);
        dials.Controls.Add(Caption("Curve x"));
        dials.Controls.Add(_curve);
        dials.Controls.Add(Caption("Prime time from"));
        dials.Controls.Add(_prime);
        dials.Controls.Add(Caption("New arrivals"));
        dials.Controls.Add(_arrivals);
        dials.Controls.Add(Caption("Session x"));
        dials.Controls.Add(_session);
        dials.Controls.Add(Caption("Casual/Regular/Tryhard"));
        dials.Controls.Add(_mix);
        dials.Controls.Add(Caption("Chat"));
        dials.Controls.Add(_chat);
        dials.Controls.Add(Caption("Mistakes"));
        dials.Controls.Add(_mistakes);
        dials.Controls.Add(_fast);
        var save = new RuneButton { Text = "SAVE DIALS", Width = 120 };
        save.Click += (_, _) => SaveDials();
        dials.Controls.Add(save);
        layout.Controls.Add(dials, 0, 2);
        layout.Controls.Add(_view, 0, 3);
        Controls.Add(layout);
        _timer.Tick += (_, _) => { if (Visible) RefreshView(); };
        _timer.Start();
        VisibleChanged += (_, _) => { if (Visible) { LoadDials(); RefreshView(); } };
    }

    private static FlowLayoutPanel Row() => new()
    {
        Dock = DockStyle.Fill, AutoSize = true, WrapContents = true, Padding = new Padding(2), BackColor = DaocTheme.PanelAlt,
        Margin = new Padding(0, 2, 0, 4),
    };

    private static Label Caption(string text) => new()
    {
        Text = text, AutoSize = true, ForeColor = DaocTheme.Muted, Margin = new Padding(8, 8, 2, 0),
    };

    private static NumericUpDown Number(int value, int min, int max, int step) => new()
    {
        Minimum = min, Maximum = max, Value = value, Increment = step, Width = 70, BackColor = DaocTheme.StoneDark,
        ForeColor = DaocTheme.Text, Margin = new Padding(2, 4, 2, 0),
    };

    private static TextBox Field(string text) => new()
    {
        Text = text, Width = 60, BackColor = DaocTheme.StoneDark, ForeColor = DaocTheme.Text, Margin = new Padding(2, 4, 2, 0),
    };

    private static ComboBox Choice(params string[] items)
    {
        var c = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 80, BackColor = DaocTheme.StoneDark,
            ForeColor = DaocTheme.Text, Margin = new Padding(2, 4, 2, 0) };
        c.Items.AddRange(items);
        c.SelectedIndex = Math.Min(1, items.Length - 1);
        return c;
    }

    private async Task BuildAsync(Button button)
    {
        if (_busy)
            return;
        _busy = true;
        button.Enabled = false;
        int size = (int)_size.Value;
        try
        {
            _summary.Text = "Building the roster…";
            int[] added = await Task.Run(() => PopulationRoster.Build(_database(), _root(), size,
                text => BeginInvoke(() => _summary.Text = "Building the roster… " + text)));
            _summary.Text = $"Roster built: {added[0]} Albion, {added[1]} Midgard, {added[2]} Hibernia added (not yet arrived).";
        }
        catch (Exception exception)
        {
            _summary.Text = "Could not build the roster: " + exception.Message;
        }
        finally
        {
            _busy = false;
            button.Enabled = true;
            RefreshView();
        }
    }

    private void LoadDials()
    {
        try
        {
            using var connection = Open(true);
            PopulationKnobs k = PopulationRoster.ReadKnobs(connection);
            _maxOnline.Value = Math.Clamp(k.MaxOnlinePerRealm, (int)_maxOnline.Minimum, (int)_maxOnline.Maximum);
            _arrivals.Value = Math.Clamp(k.NewArrivals, (int)_arrivals.Minimum, (int)_arrivals.Maximum);
            _prime.Value = k.PrimeStartHour;
            _curve.Text = k.CurveScale.ToString("0.##", CultureInfo.InvariantCulture);
            _session.Text = k.SessionScale.ToString("0.##", CultureInfo.InvariantCulture);
            _mix.Text = $"{k.CasualPct}/{100 - k.CasualPct - k.TryhardPct}/{k.TryhardPct}";
            _chat.SelectedItem = k.ChatLevel;
            _mistakes.SelectedItem = k.MistakeRate;
            _fast.Checked = k.FastClock;
        }
        catch (Exception exception)
        {
            _summary.Text = "Could not read the dials: " + exception.Message;
        }
    }

    private void SaveDials()
    {
        try
        {
            using var connection = Open(false);
            void W(string key, string value, string what) => PopulationRoster.WriteProperty(connection, key, value, what);
            W(PopulationKnobs.KeyMaxOnline, ((int)_maxOnline.Value).ToString(CultureInfo.InvariantCulture), "Most bots online per realm.");
            W(PopulationKnobs.KeyCurveScale, _curve.Text.Trim(), "Multiplies every hour's online share (0.5 = a quiet server).");
            W(PopulationKnobs.KeyPrimeStart, ((int)_prime.Value).ToString(CultureInfo.InvariantCulture), "The hour prime time starts (4 hours long).");
            W(PopulationKnobs.KeyNewArrivals, ((int)_arrivals.Value).ToString(CultureInfo.InvariantCulture), "New arrivals online at a time per realm.");
            W(PopulationKnobs.KeySessionScale, _session.Text.Trim(), "Multiplies every session's length.");
            W(PopulationKnobs.KeyPersonaMix, _mix.Text.Trim(), "Casual / regular / tryhard percent for new personas.");
            W(PopulationKnobs.KeyChatLevel, (string)_chat.SelectedItem!, "quiet, normal or lively.");
            W(PopulationKnobs.KeyMistakeRate, (string)_mistakes.SelectedItem!, "off, low, normal or high.");
            W(PopulationKnobs.KeyFastClock, _fast.Checked ? "true" : "false", "Testing: a day passes in an hour.");
            _summary.Text = "Dials saved - the server picks them up within half a minute.";
        }
        catch (Exception exception)
        {
            _summary.Text = "Could not save the dials: " + exception.Message;
        }
    }

    private SQLiteConnection Open(bool readOnly)
    {
        var connection = new SQLiteConnection($"Data Source={_database()};Version=3;{(readOnly ? "Read Only=True;" : "")}Pooling=False;Default Timeout=10");
        connection.Open();
        return connection;
    }

    private void RefreshView()
    {
        if (_busy || !File.Exists(_database()))
            return;
        try
        {
            List<PopulationRoster.BotLine> bots = PopulationRoster.ReadRoster(_database());
            PopulationKnobs knobs;
            using (var connection = Open(true))
                knobs = PopulationRoster.ReadKnobs(connection);
            DateTime local = DateTime.Now;
            var sb = new System.Text.StringBuilder();
            int onlineAll = bots.Count(b => b.Online);
            _summary.Text = $"{bots.Count} on the roster, {bots.Count(b => b.Arrived)} arrived, {onlineAll} online now" +
                            (knobs.FastClock ? "   (fast clock on: the server's day runs 24x)" : "");
            sb.AppendLine($"This hour's share of each roster online: {PopulationCurve.Share(local, knobs.PrimeStartHour, knobs.CurveScale):P1}" +
                          $"   (ceiling {knobs.MaxOnlinePerRealm} a realm; on the fast clock the server's own hour is used)");
            sb.AppendLine();
            sb.AppendLine("REALM       ROSTER  ARRIVED  ONLINE  TARGET   1-9  10s  20s  30s  40s   50   BUSIEST CLASSES ONLINE");
            for (int realm = 1; realm <= 3; realm++)
            {
                var r = bots.Where(b => b.Realm == realm).ToList();
                var on = r.Where(b => b.Online).ToList();
                int target = PopulationCurve.Target(r.Count, local, knobs);
                var bands = new int[PopulationCurve.Bands];
                foreach (var b in on)
                    bands[PopulationCurve.Band(b.Level)]++;
                string classes = string.Join(", ", on.GroupBy(b => b.ClassName).OrderByDescending(g => g.Count()).Take(4)
                    .Select(g => $"{g.Key} {g.Count()}"));
                sb.AppendLine($"{PopulationRoster.RealmName(realm),-10} {r.Count,7} {r.Count(b => b.Arrived),8} {on.Count,7} {target,7}  " +
                              string.Join(" ", bands.Select(n => $"{n,4}")) + "   " + classes);
            }
            sb.AppendLine();
            sb.AppendLine("LOGGED IN NOW (most recent first)");
            foreach (var b in bots.Where(b => b.Online && b.SessionEndsUtc != "").OrderByDescending(b => b.SessionEndsUtc).Take(12))
                sb.AppendLine($"  {b.Name,-14} {PopulationRoster.RealmName(b.Realm),-9} L{b.Level,-3} {b.ClassName,-12} " +
                              $"{b.Persona?.Tier,-8} {b.Persona?.Sched,-8} until {LocalTime(b.SessionEndsUtc)}");
            sb.AppendLine();
            sb.AppendLine("LOGGED OUT LATELY");
            foreach (var b in bots.Where(b => !b.Online && b.LastLogoutUtc != "").OrderByDescending(b => b.LastLogoutUtc).Take(12))
                sb.AppendLine($"  {b.Name,-14} {PopulationRoster.RealmName(b.Realm),-9} L{b.Level,-3} {b.ClassName,-12} " +
                              $"at {LocalTime(b.LastLogoutUtc)}  ({b.Sessions} sessions)");
            _view.Text = sb.ToString();
        }
        catch (Exception exception)
        {
            _summary.Text = "Could not read the population: " + exception.Message;
        }
    }

    private static string LocalTime(string utc) =>
        DateTime.TryParse(utc, null, DateTimeStyles.RoundtripKind, out DateTime t) ? t.ToLocalTime().ToString("HH:mm") : "?";
}

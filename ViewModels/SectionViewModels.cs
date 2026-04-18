using System.ComponentModel;
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.Input;
using CANvision.Native.Models;
using CANvision.Native.Services;

namespace CANvision.Native.ViewModels;

public abstract class SectionViewModel : ViewModelBase
{
    private readonly SectionDescriptor? descriptor;

    protected SectionViewModel(VehicleDataService vehicleDataService, SectionKey key)
    {
        VehicleDataService = vehicleDataService;
        Key = key;
        descriptor = key == SectionKey.Home ? null : SectionCatalog.For(key);
        vehicleDataService.PropertyChanged += VehicleDataServiceOnPropertyChanged;
    }

    protected VehicleDataService VehicleDataService { get; }

    public SectionKey Key { get; }

    public VehicleSnapshot Snapshot => VehicleDataService.CurrentSnapshot;

    public int Battery => Snapshot.Battery;

    public string BatteryText => $"{Battery}%";

    public double BatteryRatio => Clamp(Battery / 100.0, 0.0, 1.0);

    public int Temperature => Snapshot.Temperature;

    public string TemperatureText => $"{Temperature} C";

    public double TemperatureRatio => Clamp(Temperature / 120.0, 0.0, 1.0);

    public string TemperatureBand =>
        Temperature switch
        {
            >= 85 => "CRITICAL",
            >= 65 => "ELEVATED",
            >= 45 => "ACTIVE",
            _ => "NOMINAL",
        };

    public string MotorStatusText => NormalizeToken(Snapshot.MotorStatus);

    public string SourceText => NormalizeToken(Snapshot.Source);

    public string UpdatedText => Snapshot.UpdatedAt.ToLocalTime().ToString("HH:mm:ss");

    public string AgeText => BuildAgeText(Snapshot.UpdatedAt);

    public string ConnectivityText =>
        string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase)
            ? "LIVE TELEMETRY"
            : "LOCAL FALLBACK";

    public string ThermalMarginText =>
        Temperature >= 85
            ? "THERMAL LIMIT EXCEEDED"
            : $"{Math.Max(0, 85 - Temperature)} C TO THERMAL LIMIT";

    public string BatteryReserveText => $"{Math.Max(0, Battery - 20)}% ABOVE LOW POWER FLOOR";

    public int Voltage => 320 + (Battery * 0.88m is var value ? (int)Math.Round((double)value) : 0);

    public string VoltageText => $"{Voltage} V";

    public int SpeedKph => string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase) ? Math.Max(0, (Battery + Temperature) / 3) : 0;

    public string SpeedText => $"{SpeedKph} km/h";

    public string GpsStatusText => string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase) ? "GPS LOCK" : "GPS STANDBY";

    public string SessionTimerText => $"00:{Clamp(Battery / 4, 10, 59):00}:{Clamp(Temperature, 10, 59):00}";

    public string AdapterName => "OBD-II CAN USB_3";

    public string PortName => "COM7";

    public string BaudRateText => "500000 bps";

    public string VehicleMake => "CANvision";

    public string VehicleModel => "EV-X Prototype";

    public string VehicleYear => "2026";

    public string VinText => "CNV-8672-X";

    public string ProfileName => "P-800 PERFORMANCE";

    public SectionDescriptor Descriptor => descriptor ?? throw new InvalidOperationException("Home does not use a section descriptor.");

    public string SectionEyebrow => Key == SectionKey.Home ? "GARAGE COMMAND DECK" : "TACTICAL VEHICLE BRIEF";

    public string SectionTitle => Key == SectionKey.Home ? "Main Screen" : Descriptor.Title;

    public string SectionDescription =>
        Key == SectionKey.Home
            ? "Access the unified vehicle diagnostics console and transition between live systems from a single premium command station."
            : Descriptor.BriefingDescription;

    public string SectionSignalLine =>
        Key switch
        {
            SectionKey.Home => $"{ConnectivityText} | BATTERY {BatteryText} | CORE {TemperatureText}",
            _ => $"{ConnectivityText} | SOURCE {SourceText} | LAST SYNC {UpdatedText}",
        };

    public string PrimaryActionLabel =>
        Key switch
        {
            SectionKey.Diagnostics => "Enter Diagnostics",
            SectionKey.Telemetry => "Access Telemetry",
            SectionKey.LogPlayback => "Replay Logs",
            SectionKey.Analytics => "Open Analytics",
            SectionKey.Settings => "Configure System",
            _ => "Dive In",
        };

    public SectionKey PrimaryActionTargetKey => Key;

    protected virtual void OnSnapshotChanged()
    {
    }

    private void VehicleDataServiceOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(VehicleDataService.CurrentSnapshot))
        {
            RaiseSnapshotChanged();
        }
    }

    protected void RaiseSnapshotChanged()
    {
        OnPropertyChanged(nameof(Snapshot));
        OnPropertyChanged(nameof(Battery));
        OnPropertyChanged(nameof(BatteryText));
        OnPropertyChanged(nameof(BatteryRatio));
        OnPropertyChanged(nameof(Temperature));
        OnPropertyChanged(nameof(TemperatureText));
        OnPropertyChanged(nameof(TemperatureRatio));
        OnPropertyChanged(nameof(TemperatureBand));
        OnPropertyChanged(nameof(MotorStatusText));
        OnPropertyChanged(nameof(SourceText));
        OnPropertyChanged(nameof(UpdatedText));
        OnPropertyChanged(nameof(AgeText));
        OnPropertyChanged(nameof(ConnectivityText));
        OnPropertyChanged(nameof(ThermalMarginText));
        OnPropertyChanged(nameof(BatteryReserveText));
        OnPropertyChanged(nameof(Voltage));
        OnPropertyChanged(nameof(VoltageText));
        OnPropertyChanged(nameof(SpeedKph));
        OnPropertyChanged(nameof(SpeedText));
        OnPropertyChanged(nameof(GpsStatusText));
        OnPropertyChanged(nameof(SessionTimerText));
        OnPropertyChanged(nameof(SectionSignalLine));
        OnSnapshotChanged();
    }

    protected static double Clamp(double value, double min, double max)
    {
        if (value < min)
        {
            return min;
        }

        if (value > max)
        {
            return max;
        }

        return value;
    }

    private static string NormalizeToken(string? value)
    {
        var normalized = value ?? string.Empty;
        return string.IsNullOrWhiteSpace(normalized)
            ? "UNKNOWN"
            : normalized.Replace('_', ' ').Replace('-', ' ').ToUpperInvariant();
    }

    private static string BuildAgeText(DateTime updatedAt)
    {
        var age = DateTime.UtcNow - updatedAt.ToUniversalTime();
        if (age.TotalSeconds < 5)
        {
            return "JUST NOW";
        }

        if (age.TotalMinutes < 1)
        {
            return $"{Math.Max(1, (int)age.TotalSeconds)}S AGO";
        }

        if (age.TotalHours < 1)
        {
            return $"{(int)age.TotalMinutes}M AGO";
        }

        return $"{(int)age.TotalHours}H AGO";
    }
}

public sealed class HomeViewModel : SectionViewModel
{
    public HomeViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Home)
    {
    }

    public int ReadinessScore
    {
        get
        {
            var thermalScore = Math.Max(0, 100 - (Math.Max(0, Temperature - 35) * 2));
            var motorScore = string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase) ? 12 : 0;
            var score = (Battery * 0.58) + (thermalScore * 0.30) + motorScore;
            return (int)Math.Round(Clamp(score, 0.0, 100.0));
        }
    }

    public string ReadinessText =>
        ReadinessScore switch
        {
            >= 85 => "DEPLOYMENT READY",
            >= 65 => "MONITORED READY",
            >= 40 => "REVIEW BEFORE DRIVE",
            _ => "SERVICE CHECK ADVISED",
        };

    public string LaunchGuidance =>
        string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase)
            ? "Every workspace is online. Open any interface to inspect live state, telemetry, diagnostics, or playback."
            : "The drivetrain state needs review. Start with Diagnostics or Telemetry before moving deeper into the session.";

    public string HomeRibbon => $"{ConnectivityText} | SOURCE {SourceText} | LAST SAMPLE {UpdatedText}";

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(ReadinessScore));
        OnPropertyChanged(nameof(ReadinessText));
        OnPropertyChanged(nameof(LaunchGuidance));
        OnPropertyChanged(nameof(HomeRibbon));
    }
}

public sealed class DashboardViewModel : SectionViewModel
{
    public DashboardViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Dashboard)
    {
        QuickDiagnostics = new ObservableCollection<FaultCodeItem>
        {
            new("P0A80-00", "HYBRID BATTERY PACK", "CRITICAL", "HV_BATT", "14:21"),
            new("B1244-15", "LIGHT SENSOR CIRCUIT", "WATCH", "BODY_CTRL", "14:20"),
            new("U0100-87", "LOST COMMS WITH PCM", "CRITICAL", "CAN_GATE", "14:19"),
        };
        AnomalyAlerts = new ObservableCollection<AlertItem>
        {
            new("INVERTER THERMAL JITTER", "Micro-fluctuations detected in DC-AC switching frequency.", "ACTIVE"),
            new("BATTERY CELL DRIFT", "Variance detected across the upper cell cluster.", "WATCH"),
            new("BUS LOAD OVERLOAD", "Telemetry burst exceeded nominal rate window.", "WATCH"),
        };
        SubsystemHealth = new ObservableCollection<MetricCardItem>
        {
            new("BATTERY HEALTH", "98.4% Efficiency", "POWERTRAIN", "OK"),
            new("INVERTER STATE", "Phase L1-L3 Active", "DRIVE UNIT", "OK"),
            new("COOLING CIRCUIT", "Flow: 4.2 L/min", "THERMAL", "OK"),
            new("COMMUNICATION", "Latency: 12 ms", "NETWORK", "OK"),
        };
        ReadinessBadges = new ObservableCollection<StatusBadgeItem>
        {
            new("POWERTRAIN", "STABLE"),
            new("THERMAL", TemperatureBand),
            new("CAN BUS", ConnectivityText),
            new("NAV", GpsStatusText),
        };
    }

    public ObservableCollection<FaultCodeItem> QuickDiagnostics { get; }

    public ObservableCollection<AlertItem> AnomalyAlerts { get; }

    public ObservableCollection<MetricCardItem> SubsystemHealth { get; }

    public ObservableCollection<StatusBadgeItem> ReadinessBadges { get; }

    public string BatteryBand =>
        Battery switch
        {
            >= 80 => "TRACK READY",
            >= 55 => "STREET READY",
            >= 30 => "WATCH CHARGE",
            _ => "PIT NOW",
        };

    public string DriveMessage =>
        string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase)
            ? "POWERTRAIN READY FOR DEPLOYMENT"
            : "CHECK DRIVE-UNIT TELEMETRY BEFORE DEPLOYMENT";

    public string DataRibbon => $"{ConnectivityText} | LAST SYNC {UpdatedText}";

    public string ConnectionStateText => string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase) ? "CONNECTED" : "LOCAL FALLBACK";

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(BatteryBand));
        OnPropertyChanged(nameof(DriveMessage));
        OnPropertyChanged(nameof(DataRibbon));
        OnPropertyChanged(nameof(ConnectionStateText));
    }
}

public sealed class TelemetryViewModel : SectionViewModel
{
    public TelemetryViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Telemetry)
    {
        SignalRows = new ObservableCollection<SignalItem>
        {
            new("0x1F2", "BATT_VOLT", "398.4 V", "LIVE"),
            new("0x2A1", "INV_TEMP", "94.2 C", "ALERT"),
            new("0x0B8", "MOT_RPM", "14220 RPM", "LIVE"),
            new("0x110", "STEER_ANG", "12.5 DEG", "IDLE"),
            new("0x332", "CELL_AVG", "3.88 V", "LIVE"),
        };
        ActiveSignals = new ObservableCollection<SignalLegendItem>
        {
            new("Battery Voltage", "#00FFFF"),
            new("Peak Amperage", "#0DEAFC"),
            new("System Load", "#5ED1FF"),
        };
    }

    public ObservableCollection<SignalItem> SignalRows { get; }

    public ObservableCollection<SignalLegendItem> ActiveSignals { get; }

    public string CoolingHeadroomText =>
        Temperature >= 85
            ? "0 C COOLING HEADROOM"
            : $"{85 - Temperature} C COOLING HEADROOM";

    public string CaptureCadenceText => $"REFRESH EVERY {(int)VehicleDataService.RefreshInterval.TotalMilliseconds} MS";

    public string PacketRateText => $"{Math.Max(1, Battery / 2.0):F1}k MSG/S";

    public string PacketLossText => $"{Math.Max(0.02, (100 - Battery) / 1000.0):F2}%";

    public string SampleRateText => $"{(int)(1000.0 / Math.Max(1, VehicleDataService.RefreshInterval.TotalMilliseconds / 2.0))} HZ";

    public string LatencyText => $"{Math.Max(4, Temperature / 8)} MS";

    public string BusLoadText => $"{Math.Min(92, Battery + 4)}%";

    public string EnergyNarrative =>
        Battery switch
        {
            >= 80 => "Battery reserve is comfortably above launch threshold.",
            >= 55 => "Battery reserve is stable for extended driving.",
            >= 30 => "Battery reserve is usable but should be watched.",
            _ => "Battery reserve is approaching the low-power floor.",
        };

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(CoolingHeadroomText));
        OnPropertyChanged(nameof(EnergyNarrative));
        OnPropertyChanged(nameof(PacketRateText));
        OnPropertyChanged(nameof(PacketLossText));
        OnPropertyChanged(nameof(SampleRateText));
        OnPropertyChanged(nameof(LatencyText));
        OnPropertyChanged(nameof(BusLoadText));
    }
}

public sealed class DiagnosticsViewModel : SectionViewModel
{
    public DiagnosticsViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Diagnostics)
    {
        Subsystems = new ObservableCollection<SubsystemItem>
        {
            new("ECU", "Engine Control", "HEALTHY"),
            new("BATTERY", "Main Pack HV", "HEALTHY"),
            new("INVERTER", "DC-AC Module", "WARNING"),
            new("ABS", "Braking Logic", "HEALTHY"),
            new("COOLING", "Thermal MGMT", "FAULT"),
            new("TRANSMISSION", "Direct Drive", "HEALTHY"),
        };
        DtcRows = new ObservableCollection<FaultCodeItem>
        {
            new("P0A80-00", "Replace Hybrid Battery Pack - Degradation Detected", "CRITICAL", "HV_BATT", "14:21:44"),
            new("B1244-15", "Light Sensor Circuit - Short to Battery", "WARNING", "BODY_CTRL", "14:20:12"),
            new("U0100-87", "Lost Communication With ECU/PCM", "CRITICAL", "CAN_GATE", "14:19:55"),
            new("C1555-00", "Electric Power Steering Relay Performance", "WARNING", "EPS_MOD", "14:18:22"),
        };
        RecommendedActions = new ObservableCollection<RecommendationItem>
        {
            new("INVERTER RECALIBRATION", "Immediate synchronization required for phase-balance efficiency."),
            new("BRAKE FLUID HYDRATION", "Sensor indicates moisture content. Replace within 500km."),
            new("TIRE COMPOUND INTEGRITY", "Thermal spread suggests reduced contact stability."),
        };
        RuleAlerts = new ObservableCollection<AlertItem>
        {
            new("BUS LOAD OVERLOAD", "CAN-1 utilization exceeded 85% bandwidth.", "CRITICAL"),
            new("FIRMWARE MISMATCH", "Rear sensor module running legacy package.", "WATCH"),
            new("POWER CYCLE SUCCESS", "DTC was cleared due to actuator reset.", "RESOLVED"),
        };
    }

    public ObservableCollection<SubsystemItem> Subsystems { get; }

    public ObservableCollection<FaultCodeItem> DtcRows { get; }

    public ObservableCollection<RecommendationItem> RecommendedActions { get; }

    public ObservableCollection<AlertItem> RuleAlerts { get; }

    public int ConfidenceScore => Math.Max(72, Battery);

    public string BatterySeverity =>
        Battery switch
        {
            < 25 => "CRITICAL",
            < 50 => "WATCH",
            _ => "NOMINAL",
        };

    public string BatteryMessage =>
        Battery switch
        {
            < 25 => "Charge reserve has dropped below the safe deployment floor.",
            < 50 => "Charge reserve is mid-pack and should be monitored.",
            _ => "Charge reserve is holding inside the healthy window.",
        };

    public string ThermalSeverity =>
        Temperature switch
        {
            >= 85 => "CRITICAL",
            >= 65 => "WATCH",
            _ => "NOMINAL",
        };

    public string ThermalMessage =>
        Temperature switch
        {
            >= 85 => "Thermal load is above the soft limit and needs intervention.",
            >= 65 => "Thermal load is elevated and trending toward a cooling event.",
            _ => "Thermal load is stable for the current snapshot.",
        };

    public string MotorSeverity =>
        string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase)
            ? "NOMINAL"
            : "WATCH";

    public string MotorMessage =>
        string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase)
            ? "Motor controller is reporting a stable operating state."
            : "Motor controller status requires a manual review.";

    public string RecommendedModelText => "SIGNAL ANOMALY";

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(BatterySeverity));
        OnPropertyChanged(nameof(BatteryMessage));
        OnPropertyChanged(nameof(ThermalSeverity));
        OnPropertyChanged(nameof(ThermalMessage));
        OnPropertyChanged(nameof(MotorSeverity));
        OnPropertyChanged(nameof(MotorMessage));
        OnPropertyChanged(nameof(ConfidenceScore));
    }
}

public sealed class LogPlaybackViewModel : SectionViewModel
{
    public LogPlaybackViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.LogPlayback)
    {
        PlaybackTabs = new ObservableCollection<string> { "SESSIONS", "TIMELINE", "EVENT DETAILS", "GRAPH REPLAY", "ROUTE VIEW" };
        SpeedOptions = new ObservableCollection<string> { "0.5X", "1X", "2X", "4X" };
        Sessions = new ObservableCollection<PlaybackSessionItem>
        {
            new("session_0422.log", "2026-04-09 14:22", "00:14:12", "18,432 FRAMES"),
            new("track_run_alpha.asc", "2026-04-07 08:13", "00:09:48", "11,204 FRAMES"),
            new("dyno_lab_replay.csv", "2026-04-02 19:44", "00:06:31", "7,420 FRAMES"),
        };
        EventRows = new ObservableCollection<PlaybackEventItem>
        {
            new("14:22:08.042", "0x1F2", "7A 0C 18 3F", "BATT_VOLT = 398.4 V"),
            new("14:22:10.146", "0x0B8", "20 37 0A 12", "MOT_RPM = 14220 RPM"),
            new("14:22:12.871", "0x2A1", "44 5E 10 0F", "INV_TEMP = 94.2 C"),
        };
        ReplaySignals = new ObservableCollection<SignalLegendItem>
        {
            new("Battery Voltage", "#00FFFF"),
            new("Motor RPM", "#0DEAFC"),
            new("Inverter Temp", "#63BAFF"),
        };
        SelectPlaybackTabCommand = new RelayCommand<string>(tab => SelectedPlaybackTab = tab ?? "SESSIONS");
        SelectReplaySpeedCommand = new RelayCommand<string>(speed => SelectedReplaySpeed = speed ?? "1X");
        selectedPlaybackTab = "SESSIONS";
        selectedReplaySpeed = "1X";
    }

    private string selectedPlaybackTab;
    private string selectedReplaySpeed;

    public ObservableCollection<string> PlaybackTabs { get; }

    public ObservableCollection<string> SpeedOptions { get; }

    public ObservableCollection<PlaybackSessionItem> Sessions { get; }

    public ObservableCollection<PlaybackEventItem> EventRows { get; }

    public ObservableCollection<SignalLegendItem> ReplaySignals { get; }

    public IRelayCommand<string> SelectPlaybackTabCommand { get; }

    public IRelayCommand<string> SelectReplaySpeedCommand { get; }

    public string SelectedPlaybackTab
    {
        get => selectedPlaybackTab;
        set => SetProperty(ref selectedPlaybackTab, value);
    }

    public string SelectedReplaySpeed
    {
        get => selectedReplaySpeed;
        set => SetProperty(ref selectedReplaySpeed, value);
    }

    public string PlaybackStatus =>
        string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase)
            ? "LIVE FEED ACTIVE. LOG PLAYBACK IMPORT IS THE NEXT NATIVE PORT."
            : "LOCAL SNAPSHOT FEED ACTIVE. PLAYBACK WILL ATTACH TO IMPORTED LOGS.";

    public string RefreshIntervalText => $"{(int)VehicleDataService.RefreshInterval.TotalMilliseconds} MS";

    public string ApiEndpoint => VehicleDataService.ApiEndpoint;

    public string JsonFallbackPath => VehicleDataService.JsonFallbackPath;

    public string LoadedFileName => Sessions[0].FileName;

    public string SessionDurationText => Sessions[0].Duration;

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(PlaybackStatus));
    }
}

public sealed class AnalyticsViewModel : SectionViewModel
{
    public AnalyticsViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Analytics)
    {
        SidebarSections = new ObservableCollection<string>
        {
            "OVERVIEW",
            "BATTERY DEGRADATION",
            "FAULT TRENDS",
            "AI ANOMALIES",
            "RELIABILITY SCORE",
            "COMPARE SESSIONS",
        };
        SelectAnalyticsSectionCommand = new RelayCommand<string>(section => SelectedAnalyticsSection = section ?? "OVERVIEW");
        selectedAnalyticsSection = "OVERVIEW";
        ActionProtocols = new ObservableCollection<RecommendationItem>
        {
            new("INVERTER RECALIBRATION", "Immediate synchronization required for phase-balance efficiency."),
            new("BRAKE FLUID HYDRATION", "Sensor indicates 2.4% moisture content."),
            new("TIRE COMPOUND INTEGRITY", "Thermal spread suggests reduced contact stability."),
        };
    }

    private string selectedAnalyticsSection;

    public ObservableCollection<string> SidebarSections { get; }

    public ObservableCollection<RecommendationItem> ActionProtocols { get; }

    public IRelayCommand<string> SelectAnalyticsSectionCommand { get; }

    public string SelectedAnalyticsSection
    {
        get => selectedAnalyticsSection;
        set => SetProperty(ref selectedAnalyticsSection, value);
    }

    public int ReadinessIndex
    {
        get
        {
            var thermalScore = Math.Max(0, 100 - (Math.Max(0, Temperature - 35) * 2));
            var score = (Battery * 0.65) + (thermalScore * 0.35);
            return (int)Math.Round(Clamp(score, 0.0, 100.0));
        }
    }

    public int HeatIndex => (int)Math.Round(Clamp((Temperature / 90.0) * 100.0, 0.0, 100.0));

    public string TotalSessionsText => "128";

    public string TotalDistanceText => "14,832 km";

    public string AvgAnomalyRateText => "1.2%";

    public string ReliabilityScoreText => $"{Math.Min(99, ReadinessIndex + 5)}/100";

    public string BatteryHealthIndexText => $"{Math.Max(84, Battery)}.4%";

    public string AnalyticsSummary =>
        string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase)
            ? "Single-sample readiness remains stable with the current drivetrain state."
            : "Drive-unit status is reducing confidence in the current single-sample profile.";

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(ReadinessIndex));
        OnPropertyChanged(nameof(HeatIndex));
        OnPropertyChanged(nameof(AnalyticsSummary));
        OnPropertyChanged(nameof(ReliabilityScoreText));
        OnPropertyChanged(nameof(BatteryHealthIndexText));
    }
}

public sealed class SettingsViewModel : SectionViewModel
{
    public SettingsViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Settings)
    {
        SettingsCategories = new ObservableCollection<string>
        {
            "OBD2 ADAPTER",
            "CAN INTERFACE",
            "VEHICLE PROFILES",
            "THEME",
            "AI MODEL",
            "EXPORT",
        };
        ProfileCards = new ObservableCollection<ProfileItem>
        {
            new("P-800 Performance", "ACTIVE", "High-response track profile"),
            new("Street Touring", "SYNCED", "Balanced drive calibration"),
            new("Thermal Safe", "ARCHIVED", "Cooling-first endurance preset"),
        };
        SelectSettingsCategoryCommand = new RelayCommand<string>(category => SelectedSettingsCategory = category ?? "OBD2 ADAPTER");
        selectedSettingsCategory = "OBD2 ADAPTER";
    }

    private string selectedSettingsCategory;

    public ObservableCollection<string> SettingsCategories { get; }

    public ObservableCollection<ProfileItem> ProfileCards { get; }

    public IRelayCommand<string> SelectSettingsCategoryCommand { get; }

    public string SelectedSettingsCategory
    {
        get => selectedSettingsCategory;
        set => SetProperty(ref selectedSettingsCategory, value);
    }

    public string RuntimeMode => ConnectivityText;

    public string ApiEndpoint => VehicleDataService.ApiEndpoint;

    public string JsonFallbackPath => VehicleDataService.JsonFallbackPath;

    public string RefreshIntervalText => $"{(int)VehicleDataService.RefreshInterval.TotalMilliseconds} MS";

    public string RendererProfile => "HELIX SHARPDX GARAGE RENDERER";

    public string DetectionModelText => "CAN-GPT V4 (TURBO)";

    public string TrainingDateText => "2026-04-08";

    public string AccuracyText => "94.6%";

    protected override void OnSnapshotChanged()
    {
        OnPropertyChanged(nameof(RuntimeMode));
    }
}

public sealed class MetricCardItem
{
    public MetricCardItem(string title, string value, string detail, string state)
    {
        Title = title;
        Value = value;
        Detail = detail;
        State = state;
    }

    public string Title { get; }
    public string Value { get; }
    public string Detail { get; }
    public string State { get; }
}

public sealed class StatusBadgeItem
{
    public StatusBadgeItem(string title, string value)
    {
        Title = title;
        Value = value;
    }

    public string Title { get; }
    public string Value { get; }
}

public sealed class AlertItem
{
    public AlertItem(string title, string detail, string state)
    {
        Title = title;
        Detail = detail;
        State = state;
    }

    public string Title { get; }
    public string Detail { get; }
    public string State { get; }
}

public sealed class SignalItem
{
    public SignalItem(string canId, string name, string value, string state)
    {
        CanId = canId;
        Name = name;
        Value = value;
        State = state;
    }

    public string CanId { get; }
    public string Name { get; }
    public string Value { get; }
    public string State { get; }
}

public sealed class SignalLegendItem
{
    public SignalLegendItem(string name, string colorHex)
    {
        Name = name;
        ColorHex = colorHex;
    }

    public string Name { get; }
    public string ColorHex { get; }
}

public sealed class FaultCodeItem
{
    public FaultCodeItem(string code, string description, string severity, string source, string timestamp)
    {
        Code = code;
        Description = description;
        Severity = severity;
        Source = source;
        Timestamp = timestamp;
    }

    public string Code { get; }
    public string Description { get; }
    public string Severity { get; }
    public string Source { get; }
    public string Timestamp { get; }
}

public sealed class RecommendationItem
{
    public RecommendationItem(string title, string detail)
    {
        Title = title;
        Detail = detail;
    }

    public string Title { get; }
    public string Detail { get; }
}

public sealed class PlaybackSessionItem
{
    public PlaybackSessionItem(string fileName, string date, string duration, string frameCount)
    {
        FileName = fileName;
        Date = date;
        Duration = duration;
        FrameCount = frameCount;
    }

    public string FileName { get; }
    public string Date { get; }
    public string Duration { get; }
    public string FrameCount { get; }
}

public sealed class PlaybackEventItem
{
    public PlaybackEventItem(string timestamp, string frameId, string data, string decodedSignal)
    {
        Timestamp = timestamp;
        FrameId = frameId;
        Data = data;
        DecodedSignal = decodedSignal;
    }

    public string Timestamp { get; }
    public string FrameId { get; }
    public string Data { get; }
    public string DecodedSignal { get; }
}

public sealed class ProfileItem
{
    public ProfileItem(string name, string state, string description)
    {
        Name = name;
        State = state;
        Description = description;
    }

    public string Name { get; }
    public string State { get; }
    public string Description { get; }
}

public sealed class SubsystemItem
{
    public SubsystemItem(string name, string detail, string state)
    {
        Name = name;
        Detail = detail;
        State = state;
    }

    public string Name { get; }
    public string Detail { get; }
    public string State { get; }
}

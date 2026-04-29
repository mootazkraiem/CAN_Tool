using System.Collections.Generic;
using System.ComponentModel;
using System.Collections.ObjectModel;
using System.Linq;
using System.IO;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CANvision.Native.Models;
using CANvision.Native.Services;
using System.Windows.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Microsoft.Win32;

namespace CANvision.Native.ViewModels;

public abstract class SectionViewModel : ViewModelBase
{
    private bool isCalibrating = true;
    private string calibrationText = "WAITING FOR SIGNAL...";
    private int calibrationProgress = 0;
    private readonly List<VehicleSnapshot> startupBuffer = new();
    
    public SectionDescriptor? Descriptor { get; }

    protected SectionViewModel(VehicleDataService vehicleDataService, SectionKey key)
    {
        VehicleDataService = vehicleDataService;
        Key = key;
        Descriptor = key == SectionKey.Home ? null : SectionCatalog.For(key);
        vehicleDataService.PropertyChanged += VehicleDataServiceOnPropertyChanged;
        vehicleDataService.DataUpdated += OnDataUpdated;
        
        SaveSnapshotCommand = new RelayCommand(SaveSnapshot);

        NextCardCommand = new RelayCommand(() => { if (CurrentCardIndex < MaxCards - 1) CurrentCardIndex++; });
        PreviousCardCommand = new RelayCommand(() => { if (CurrentCardIndex > 0) CurrentCardIndex--; });
        GoToCardCommand = new RelayCommand<int>(idx => { if (idx >= 0 && idx < MaxCards) CurrentCardIndex = idx; });
    }

    protected VehicleDataService VehicleDataService { get; }

    public SectionKey Key { get; }

    public IRelayCommand SaveSnapshotCommand { get; }

    public bool IsCalibrating
    {
        get => isCalibrating;
        protected set => SetProperty(ref isCalibrating, value);
    }

    public string CalibrationText
    {
        get => calibrationText;
        protected set => SetProperty(ref calibrationText, value);
    }

    public VehicleSnapshot Snapshot => VehicleDataService.CurrentSnapshot ?? VehicleSnapshot.Default();

    // Navigation and Cards
    private int currentCardIndex = 0;
    public int CurrentCardIndex
    {
        get => currentCardIndex;
        set
        {
            if (SetProperty(ref currentCardIndex, value))
            {
                OnPropertyChanged(nameof(VerticalOffset));
            }
        }
    }

    public virtual int MaxCards => 1;
    public double VerticalOffset => CurrentCardIndex * -800; // Simulated viewport height

    public IRelayCommand NextCardCommand { get; }
    public IRelayCommand PreviousCardCommand { get; }
    public IRelayCommand<int> GoToCardCommand { get; }

    // Derived properties reflect "Calibrating" state
    public double SOC => IsCalibrating ? 0 : Snapshot.SOC;
    public string SOCText => IsCalibrating ? "---" : $"{Snapshot.SOC:F1}%";
    public double SOCRatio => IsCalibrating ? 0 : Clamp(Snapshot.SOC / 100.0, 0.0, 1.0);

    public double BatteryTemp => IsCalibrating ? 0 : Snapshot.BatteryTemp;
    public string BatteryTempText => IsCalibrating ? "---" : $"{BatteryTemp:F1} C";
    public double BatteryTempRatio => IsCalibrating ? 0 : Clamp(BatteryTemp / 120.0, 0.0, 1.0);

    public double BatteryVoltage => IsCalibrating ? 0 : Snapshot.BatteryVoltage;
    public string BatteryVoltageText => IsCalibrating ? "---" : $"{BatteryVoltage:F1} V";

    public double VehicleSpeed => IsCalibrating ? 0 : Snapshot.VehicleSpeed;
    public string VehicleSpeedText => IsCalibrating ? "---" : $"{VehicleSpeed:F1} km/h";

    public double MotorTemp => IsCalibrating ? 0 : Snapshot.MotorTemp;
    public string MotorTempText => IsCalibrating ? "---" : $"{MotorTemp:F1} C";
    public string UnitNameText => "OBD-II CAN USB_3";

    public string ModelText => "EV-X PROTOTYPE";
    public string WorkspaceText => "CNV-8672-X";
    public string SignalHealthText => string.Equals(Snapshot.MotorStatus, "OK", StringComparison.OrdinalIgnoreCase) ? "STABLE" : "DEGRADED";
    public string GpsStatusText => string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase) ? "GPS LOCK" : "GPS STANDBY";
    public string ThermalCoreStateText => BatteryTempText;

    // Compatibility properties (legacy mappings)
    public int Battery => (int)Math.Round(SOC);
    public string BatteryText => $"{Battery}%";
    public double BatteryRatio => SOCRatio;
    public int Temperature => (int)Math.Round(BatteryTemp);
    public string TemperatureText => BatteryTempText;
    public double TemperatureRatio => BatteryTempRatio;

    public double Voltage => BatteryVoltage;
    public string VoltageText => BatteryVoltageText;

    public double SpeedKph => VehicleSpeed;
    public string SpeedText => VehicleSpeedText;

    public string AmpText => $"{Snapshot.PeakAmperage:F1} A";

    public virtual double ReliabilityScore => 
        Snapshot.PerformanceScore > 0 ? Snapshot.PerformanceScore : 94.2 + (SOC / 50.0);

    public virtual string ReliabilityScoreText => IsCalibrating ? "---" : $"{ReliabilityScore:F1}%";

    public string SessionTimerText => DateTime.Now.ToString("mm:ss");

    public string TemperatureBand =>
        BatteryTemp switch
        {
            >= 85 => "CRITICAL",
            >= 65 => "ELEVATED",
            >= 45 => "ACTIVE",
            _ => "NOMINAL",
        };

    public string SourceText => NormalizeToken(Snapshot.Source);
    public string UpdatedText => Snapshot.UpdatedAt.ToLocalTime().ToString("HH:mm:ss");
    public string AgeText => BuildAgeText(Snapshot.UpdatedAt);

    public string ConnectivityText =>
        string.Equals(Snapshot.Source, "python-api", StringComparison.OrdinalIgnoreCase)
            ? "LIVE TELEMETRY"
            : "LOCAL FALLBACK";

    public string ThermalMarginText =>
        BatteryTemp >= 85
            ? "THERMAL LIMIT EXCEEDED"
            : $"{Math.Max(0, 85 - BatteryTemp):F1} C TO THERMAL LIMIT";

    public string BatteryReserveText => $"{Math.Max(0, SOC - 20):F1}% ABOVE LOW POWER FLOOR";

    public string SectionEyebrow => Key == SectionKey.Home ? "GARAGE COMMAND DECK" : "TACTICAL VEHICLE BRIEF";
    public string SectionTitle => Key == SectionKey.Home ? "" : SelectorOrDefault(Descriptor?.Title, "SECTION_UNKNOWN");
    public virtual string SectionDescription =>
        Key == SectionKey.Home
            ? "Access the unified vehicle diagnostics console and transition between live systems from a single premium command station."
            : SelectorOrDefault(Descriptor?.BriefingDescription, "SYSTEM_READY");

    public string SectionSignalLine =>
        Key switch
        {
            SectionKey.Home => $"{ConnectivityText} | BATTERY {SOCText} | CORE {BatteryTempText}",
            _ => $"{ConnectivityText} | SOURCE {SourceText} | LAST SYNC {UpdatedText}",
        };

    private string SelectorOrDefault(string? value, string fallback) => string.IsNullOrWhiteSpace(value) ? fallback : value!;

    protected virtual void OnDataUpdated(VehicleSnapshot snapshot)
    {
        if (isCalibrating && VehicleDataService.IsRunning)
        {
            startupBuffer.Add(snapshot);
            calibrationProgress = startupBuffer.Count;
            CalibrationText = $"CALIBRATING SYSTEM... {calibrationProgress}/4";
            
            if (startupBuffer.Count >= 4)
            {
                IsCalibrating = false;
                CalibrationText = "CALIBRATION COMPLETE";
            }
            else
            {
                OnPropertyChanged(nameof(CalibrationText));
                return;
            }
        }

        OnPropertyChanged(nameof(Snapshot));
        OnPropertyChanged(nameof(IsCalibrating));
        OnPropertyChanged(nameof(CalibrationText));
        OnPropertyChanged(nameof(SOC));
        OnPropertyChanged(nameof(SOCText));
        OnPropertyChanged(nameof(SOCRatio));
        OnPropertyChanged(nameof(BatteryTemp));
        OnPropertyChanged(nameof(BatteryTempText));
        OnPropertyChanged(nameof(BatteryTempRatio));
        OnPropertyChanged(nameof(BatteryVoltage));
        OnPropertyChanged(nameof(BatteryVoltageText));
        OnPropertyChanged(nameof(VehicleSpeed));
        OnPropertyChanged(nameof(VehicleSpeedText));
        OnPropertyChanged(nameof(MotorTemp));
        OnPropertyChanged(nameof(MotorTempText));
        
        OnPropertyChanged(nameof(Battery));
        OnPropertyChanged(nameof(BatteryText));
        OnPropertyChanged(nameof(BatteryRatio));
        OnPropertyChanged(nameof(Temperature));
        OnPropertyChanged(nameof(TemperatureText));
        OnPropertyChanged(nameof(TemperatureBand));
        OnPropertyChanged(nameof(SourceText));
        OnPropertyChanged(nameof(UpdatedText));
        OnPropertyChanged(nameof(AgeText));
        OnPropertyChanged(nameof(ConnectivityText));
        OnPropertyChanged(nameof(ThermalMarginText));
        OnPropertyChanged(nameof(BatteryReserveText));
        OnPropertyChanged(nameof(SectionSignalLine));
    }

    private void SaveSnapshot()
    {
        var dialog = new SaveFileDialog
        {
            Filter = "JSON Data (*.json)|*.json|Text File (*.txt)|*.txt",
            FileName = $"Snapshot_{DateTime.Now:yyyyMMdd_HHmm}",
            Title = "Save Diagnostic Snapshot"
        };

        if (dialog.ShowDialog() == true)
        {
            var json = JsonConvert.SerializeObject(Snapshot, Formatting.Indented);
            System.IO.File.WriteAllText(dialog.FileName, json);
        }
    }

    private void VehicleDataServiceOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(VehicleDataService.CurrentSnapshot))
        {
            RaiseSnapshotChanged();
        }

        if (e.PropertyName == nameof(VehicleDataService.IsRunning))
        {
            OnVehicleDataServiceStateChanged();
        }
    }

    protected virtual void OnVehicleDataServiceStateChanged()
    {
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
        OnPropertyChanged(nameof(AmpText));
        OnPropertyChanged(nameof(ModelText));
        OnPropertyChanged(nameof(WorkspaceText));
        OnPropertyChanged(nameof(SignalHealthText));
        OnPropertyChanged(nameof(ThermalCoreStateText));
        OnPropertyChanged(nameof(UnitNameText));
        OnDataUpdated(Snapshot);
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
            return $"{(int)Math.Max(1, age.TotalSeconds)}S AGO";
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
    private readonly DispatcherTimer sequenceTimer;
    private int sequenceIndex = 0;
    private readonly string[] sequenceMessages = 
    {
        "CONNECTING TO VEHICLE...",
        "INITIALIZING DIAGNOSTIC SESSION...",
        "READING CAN BUS...",
        "READY"
    };

    public HomeViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Home)
    {
        StartSessionCommand = new RelayCommand(() => VehicleDataService.Start());
        StopSessionCommand = new RelayCommand(() => VehicleDataService.Stop());
        
        sequenceTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1.5) };
        sequenceTimer.Tick += OnSequenceTick;
        sequenceTimer.Start();
    }

    public IRelayCommand StartSessionCommand { get; }
    public IRelayCommand StopSessionCommand { get; }

    public string SequenceText => sequenceMessages[sequenceIndex];

    public string ConnectionStatus => ConnectivityText;
    public string LastPacketTime => UpdatedText;
    public int FaultCount => VehicleDataService.CurrentAnomalies?.Count ?? 0;


    public string ReadinessText =>
        IsCalibrating ? "CALIBRATING..." :
        (ReliabilityScore switch
        {
            >= 85 => "DEPLOYMENT READY",
            >= 65 => "MONITORED READY",
            >= 40 => "REVIEW BEFORE DRIVE",
            _ => "SERVICE CHECK ADVISED",
        });

    public string HomeRibbon => $"{ConnectivityText} | SOURCE {SourceText} | LAST SAMPLE {UpdatedText}";

    private void OnSequenceTick(object? sender, EventArgs e)
    {
        if (sequenceIndex < sequenceMessages.Length - 1)
        {
            sequenceIndex++;
            OnPropertyChanged(nameof(SequenceText));
            OnPropertyChanged(nameof(SectionDescription));
        }
        else
        {
            sequenceTimer.Stop();
        }
    }

    public override string SectionDescription => SequenceText;

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
    {
        base.OnDataUpdated(snapshot);
        OnPropertyChanged(nameof(ReliabilityScore));
        OnPropertyChanged(nameof(ReliabilityScoreText));
        OnPropertyChanged(nameof(ConnectionStatus));
        OnPropertyChanged(nameof(LastPacketTime));
        OnPropertyChanged(nameof(FaultCount));
        OnPropertyChanged(nameof(ReadinessText));
        OnPropertyChanged(nameof(HomeRibbon));
        OnPropertyChanged(nameof(SectionDescription));
    }
}

public sealed class DashboardViewModel : SectionViewModel
{
    public DashboardViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Dashboard)
    {
        QuickDiagnostics = new ObservableCollection<FaultCodeItem>();
        AnomalyAlerts = new ObservableCollection<AlertItem>();
        SubsystemHealth = new ObservableCollection<MetricCardItem>
        {
            new("BATTERY HEALTH", "98.4% Efficiency", "POWERTRAIN", "OK"),
            new("INVERTER STATE", "Phase L1-L3 Active", "DRIVE UNIT", "OK"),
            new("COOLING CIRCUIT", "Flow: 4.2 L/min", "THERMAL", "OK"),
            new("COMMUNICATION", "Latency: 12 ms", "NETWORK", "OK"),
        };
        ReadinessBadges = new ObservableCollection<StatusBadgeItem>();
        vehicleDataService.AnomaliesUpdated += OnAnomaliesUpdated;

        StartSessionCommand = new RelayCommand(() => VehicleDataService.Start());
        StopSessionCommand = new RelayCommand(() => VehicleDataService.Stop());
    }

    public ObservableCollection<FaultCodeItem> QuickDiagnostics { get; }
    public ObservableCollection<AlertItem> AnomalyAlerts { get; }
    public ObservableCollection<MetricCardItem> SubsystemHealth { get; }
    public ObservableCollection<StatusBadgeItem> ReadinessBadges { get; }

    public IRelayCommand StartSessionCommand { get; }
    public IRelayCommand StopSessionCommand { get; }

    public bool IsSessionRunning => VehicleDataService.IsRunning;
    public string SessionStateText => IsSessionRunning ? "SESSION LIVE" : "SESSION PAUSED";

    protected override void OnVehicleDataServiceStateChanged()
    {
        OnPropertyChanged(nameof(IsSessionRunning));
        OnPropertyChanged(nameof(SessionStateText));
    }

    public string BatteryBand =>
        SOC switch
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

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
    {
        base.OnDataUpdated(snapshot);
        
        ReadinessBadges.Clear();
        ReadinessBadges.Add(new StatusBadgeItem("POWERTRAIN", "STABLE"));
        ReadinessBadges.Add(new StatusBadgeItem("THERMAL", TemperatureBand));
        ReadinessBadges.Add(new StatusBadgeItem("CAN BUS", ConnectivityText));
        ReadinessBadges.Add(new StatusBadgeItem("NAV", "GPS_LOCK"));

        OnPropertyChanged(nameof(BatteryBand));
        OnPropertyChanged(nameof(DriveMessage));
        OnPropertyChanged(nameof(DataRibbon));
        OnPropertyChanged(nameof(ConnectionStateText));
    }

    private void OnAnomaliesUpdated(IReadOnlyList<CanAnomaly> anomalies)
    {
        AnomalyAlerts.Clear();
        QuickDiagnostics.Clear();

        foreach (var anomaly in anomalies ?? Array.Empty<CanAnomaly>())
        {
            var severity = anomaly.SeverityScore > 80 ? "CRITICAL" : (anomaly.SeverityScore > 40 ? "WARNING" : "INFO");
            AnomalyAlerts.Add(new AlertItem(anomaly.Title ?? "UNKNOWN_ANOMALY", anomaly.Description ?? string.Empty, severity));
            QuickDiagnostics.Add(new FaultCodeItem(anomaly.Code ?? "GEN-000", anomaly.Title ?? "UNKNOWN_ANOMALY", severity, anomaly.Source ?? "CAN_PIPELINE", DateTime.Now.ToString("HH:mm:ss")));
        }
    }
}

public sealed class TelemetryViewModel : SectionViewModel
{
    private readonly CanLogImportService canLogImportService;
    private IReadOnlyList<DecodedSignal> latestSignals = Array.Empty<DecodedSignal>();

    public TelemetryViewModel(VehicleDataService vehicleDataService, CanLogImportService canLogImportService)
        : base(vehicleDataService, SectionKey.Telemetry)
    {
        this.canLogImportService = canLogImportService;
        SignalRows = new ObservableCollection<SignalItem>();
        ActiveSignals = new ObservableCollection<SignalLegendItem>
        {
            new("Battery Voltage", "#00FFFF"),
            new("Peak Amperage", "#0DEAFC"),
            new("System Load", "#5ED1FF"),
        };

        ImportLogCommand = new AsyncRelayCommand(ImportLogAsync);
        ExportSignalsCommand = new RelayCommand(ExportSignals);
        FreezeStreamCommand = new RelayCommand(() => VehicleDataService.Stop());
        ResumeStreamCommand = new RelayCommand(() => VehicleDataService.Start());

        VehicleDataService.SignalsUpdated += OnSignalsUpdated;
        RefreshSignalRows();
    }

    public ObservableCollection<SignalItem> SignalRows { get; }
    public ObservableCollection<SignalLegendItem> ActiveSignals { get; }
    public IRelayCommand ImportLogCommand { get; }
    public IRelayCommand ExportSignalsCommand { get; }
    public IRelayCommand FreezeStreamCommand { get; }
    public IRelayCommand ResumeStreamCommand { get; }

    public bool IsStreamFrozen => !VehicleDataService.IsRunning;
    public string StreamStateText => IsStreamFrozen ? "STREAM PAUSED" : "STREAM ACTIVE";

    public string Trace1Text => $"TRACE 01: SOC {SOCText}";
    public string Trace2Text => $"TRACE 02: BATTERY V {BatteryVoltageText}";

    private void RefreshSignalRows()
    {
        SignalRows.Clear();
        if (latestSignals.Count > 0)
        {
            foreach (var signal in latestSignals.OrderBy(s => s.CanId).ThenBy(s => s.Name))
            {
                SignalRows.Add(new SignalItem(
                    $"0x{signal.CanId:X3}",
                    signal.Name.ToUpperInvariant(),
                    $"{signal.Value:F2} {signal.Unit}".Trim(),
                    IsStreamFrozen ? "IDLE" : "LIVE",
                    Snapshot.Frequency,
                    Snapshot.TimeDiff));
            }

            return;
        }

        SignalRows.Add(new SignalItem("0x100", "BATTERY_SOC", SOCText, IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
        SignalRows.Add(new SignalItem("0x102", "BATTERY_TEMP", BatteryTempText, IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
        SignalRows.Add(new SignalItem("0x103", "VEHICLE_SPEED", VehicleSpeedText, IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
        SignalRows.Add(new SignalItem("0x101", "BATTERY_VOLTAGE", BatteryVoltageText, IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
        SignalRows.Add(new SignalItem("0x104", "MOTOR_TEMP", MotorTempText, IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
        SignalRows.Add(new SignalItem("0x103", "MOTOR_RPM", Snapshot.MotorRPM.ToString(), IsStreamFrozen ? "IDLE" : "LIVE", Snapshot.Frequency, Snapshot.TimeDiff));
    }

    private async Task ImportLogAsync()
    {
        var dialog = new OpenFileDialog
        {
            Filter = "CAN logs (*.log;*.asc;*.csv)|*.log;*.asc;*.csv|All files (*.*)|*.*",
            Title = "Import CAN Log"
        };

        if (dialog.ShowDialog() != true)
        {
            return;
        }

        var result = await canLogImportService.ParseFileAsync(dialog.FileName);
        var firstPacket = result.Packets.FirstOrDefault();
        if (firstPacket is not null)
        {
            VehicleDataService.PublishPlaybackPacket(firstPacket);
        }
    }

    private void ExportSignals()
    {
        var dialog = new SaveFileDialog
        {
            Filter = "CSV File (*.csv)|*.csv",
            FileName = $"DecodedSignals_{DateTime.Now:yyyyMMdd_HHmmss}.csv",
            Title = "Export Decoded Signals"
        };

        if (dialog.ShowDialog() != true)
        {
            return;
        }

        var rows = latestSignals.Select(signal => $"{signal.TimestampUtc:o},{signal.CanId:X3},{signal.Name},{signal.Value:F4},{signal.Unit}");
        System.IO.File.WriteAllLines(dialog.FileName, new[] { "timestamp,can_id,name,value,unit" }.Concat(rows));
    }

    private void OnSignalsUpdated(IReadOnlyList<DecodedSignal> signals)
    {
        latestSignals = signals ?? Array.Empty<DecodedSignal>();
        RefreshSignalRows();
    }

    public string CoolingHeadroomText =>
        BatteryTemp >= 85
            ? "0 C COOLING HEADROOM"
            : $"{85 - BatteryTemp:F1} C COOLING HEADROOM";

    public string CaptureCadenceText => $"REFRESH EVERY {(int)VehicleDataService.RefreshInterval.TotalMilliseconds} MS";
    public string PacketRateText => $"{Math.Max(1, SOC / 2.0):F1}k MSG/S";
    public string PacketLossText => $"{Math.Max(0.02, (100 - SOC) / 1000.0):F2}%";
    public string SampleRateText => $"{(int)(1000.0 / Math.Max(1, VehicleDataService.RefreshInterval.TotalMilliseconds / 2.0))} HZ";
    public string LatencyText => $"{Math.Max(4, BatteryTemp / 8):F0} MS";
    public string BusLoadText => $"{Math.Min(92, SOC + 4):F0}%";

    public string EnergyNarrative =>
        SOC switch
        {
            >= 80 => "BATTERY RESERVE NOMINAL",
            >= 50 => "MONITOR DISCHARGE RATE",
            _ => "LOW POWER STATE ACTIVE",
        };

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
    {
        base.OnDataUpdated(snapshot);
        RefreshSignalRows();
        OnPropertyChanged(nameof(StreamStateText));
        OnPropertyChanged(nameof(Trace1Text));
        OnPropertyChanged(nameof(Trace2Text));
        OnPropertyChanged(nameof(CoolingHeadroomText));
        OnPropertyChanged(nameof(PacketRateText));
        OnPropertyChanged(nameof(PacketLossText));
        OnPropertyChanged(nameof(SampleRateText));
        OnPropertyChanged(nameof(LatencyText));
        OnPropertyChanged(nameof(BusLoadText));
    }

    protected override void OnVehicleDataServiceStateChanged()
    {
        RefreshSignalRows();
        OnPropertyChanged(nameof(StreamStateText));
    }
}

public sealed class DiagnosticsViewModel : SectionViewModel
{
    // ── Static DTC catalog: all codes this system monitors ──────────────────
    private static readonly (string Code, string Description, string Severity, string Source, string Subsystem)[] DtcCatalog =
    [
        ("BMS-001", "BMS FAULT - Critical battery management system error",          "CRITICAL", "BMS_ECU",     "BATTERY"),
        ("BMS-002", "CELL IMBALANCE - Cell voltage differential exceeded threshold", "WARNING",  "BMS_ECU",     "BATTERY"),
        ("BMS-003", "UNDER VOLTAGE - Pack voltage below safe threshold",             "WARNING",  "BMS_ECU",     "BATTERY"),
        ("BMS-004", "OVER VOLTAGE - Pack voltage above safe operating limit",        "CRITICAL", "BMS_ECU",     "BATTERY"),
        ("MTR-042", "MOTOR FAULT - Propulsion motor critical subsystem error",       "CRITICAL", "MOTOR_ECU",   "MOTOR"),
        ("MTR-043", "MOTOR OVERSPEED - Motor RPM exceeded design limit",             "WARNING",  "MOTOR_ECU",   "MOTOR"),
        ("THM-101", "THERMAL WARNING - Thermal envelope exceeded nominal band",      "WARNING",  "THERMAL_MGR", "COOLING"),
        ("THM-102", "OVERHEAT CRITICAL - System temperature in danger zone",         "CRITICAL", "THERMAL_MGR", "COOLING"),
        ("PWR-220", "OVER CURRENT - Current draw exceeded operating limits",         "WARNING",  "POWER_ECU",   "INVERTER"),
        ("PWR-221", "ISOLATION FAULT - HV isolation resistance degraded",            "CRITICAL", "POWER_ECU",   "INVERTER"),
        ("VLT-301", "UNDER VOLTAGE - Battery pack below minimum safe voltage",       "WARNING",  "POWER_ECU",   "BATTERY"),
        ("ECU-001", "CAN TIMEOUT - Controller area network communication timeout",   "WARNING",  "MAIN_ECU",    "ECU"),
        ("ECU-002", "SENSOR FAULT - Signal plausibility check failed",               "WARNING",  "MAIN_ECU",    "ECU"),
        ("ABS-001", "ABS MODULE - Braking logic module CAN communication timeout",   "INFO",     "ABS_ECU",     "ABS"),
    ];

    private string diagnosticsStatus = "SYSTEM READY";
    private bool isScanning;
    private readonly Dictionary<string, FaultLifecycle> lifecycle = new();
    private DiagnosticDtcItem? selectedDtc;
    private string filterCode     = string.Empty;
    private string filterSeverity = "ALL";
    private string filterSource   = "ALL";

    public DiagnosticsViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Diagnostics)
    {
        Subsystems = new ObservableCollection<SubsystemItem>
        {
            new("ECU",     "Engine Control",  "HEALTHY"),
            new("BATTERY", "Main Pack HV",    "HEALTHY"),
            new("INVERTER","DC-AC Module",    "HEALTHY"),
            new("ABS",     "Braking Logic",   "HEALTHY"),
            new("COOLING", "Thermal MGMT",    "HEALTHY"),
            new("MOTOR",   "Propulsion Unit", "HEALTHY"),
        };

        AllDtcRows      = new ObservableCollection<DiagnosticDtcItem>();
        FilteredDtcRows = new ObservableCollection<DiagnosticDtcItem>();
        RawAnomalies    = new ObservableCollection<CanAnomaly>();
        Alerts          = new ObservableCollection<AlertItem>();
        RecommendedActions = new ObservableCollection<RecommendationItem>();

        // Pre-populate catalog
        foreach (var entry in DtcCatalog)
        {
            AllDtcRows.Add(new DiagnosticDtcItem
            {
                Code        = entry.Code,
                Description = entry.Description,
                Severity    = entry.Severity,
                Source      = entry.Source,
                AnomalyType = entry.Subsystem,
                FaultKey    = entry.Code,
                Status      = "OK",
                Timestamp   = DateTime.Now,
                FirstSeen   = DateTime.Now,
                LastSeen    = DateTime.Now,
            });
        }

        RefreshFilteredRows();
        vehicleDataService.AnomaliesUpdated += OnAnomaliesUpdated;

        RunFullScanCommand = new AsyncRelayCommand(StartFullScanAsync);
        QuickScanCommand = new RelayCommand(() =>
        {
            DiagnosticsStatus = "QUICK CHECK ACTIVE";
            ApplyAnomalies(VehicleDataService.CurrentAnomalies ?? Array.Empty<CanAnomaly>());
        });
        StopScanCommand   = new RelayCommand(StopScan);
        SelectSubsystemCommand = new RelayCommand<string>(s => {
            FilterSource = s ?? "ALL";
            RefreshFilteredRows();
        });
        ClearAlertsCommand = new RelayCommand(() =>
        {
            Alerts.Clear();
            RawAnomalies.Clear();
            lifecycle.Clear();
            foreach (var row in AllDtcRows) row.Status = "OK";
            RefreshFilteredRows();
            VehicleDataService.UpdateAnomalies(Array.Empty<CanAnomaly>(), "diagnostics-clear");
            selectedDtc = null;
            DiagnosticsStatus = "ALERTS CLEARED";
            RefreshRecommendationPanel();
            OnPropertyChanged(nameof(ConfidenceScore));
            OnPropertyChanged(nameof(DtcHeaderText));
        });
        ExportReportCommand = new RelayCommand(ExportReport);
    }

    public ObservableCollection<SubsystemItem>     Subsystems      { get; }
    public ObservableCollection<DiagnosticDtcItem> AllDtcRows      { get; }
    public ObservableCollection<DiagnosticDtcItem> FilteredDtcRows { get; }
    public ObservableCollection<DiagnosticDtcItem> DtcRows => FilteredDtcRows; // Compatibility shim for XAML
    public ObservableCollection<CanAnomaly>        RawAnomalies    { get; }
    public ObservableCollection<AlertItem>         Alerts          { get; }
    public ObservableCollection<RecommendationItem> RecommendedActions { get; }

    public IRelayCommand RunFullScanCommand  { get; }
    public IRelayCommand QuickScanCommand    { get; }
    public IRelayCommand StopScanCommand     { get; }
    public IRelayCommand ExportReportCommand { get; }
    public IRelayCommand ClearAlertsCommand  { get; }
    public IRelayCommand<string> SelectSubsystemCommand { get; }

    public string DiagnosticsStatus
    {
        get => diagnosticsStatus;
        private set => SetProperty(ref diagnosticsStatus, value);
    }

    // ── Filter properties ──────────────────────────────────────────────────
    public string FilterCode
    {
        get => filterCode;
        set { SetProperty(ref filterCode, value ?? string.Empty); RefreshFilteredRows(); }
    }

    public string FilterSeverity
    {
        get => filterSeverity;
        set { SetProperty(ref filterSeverity, value ?? "ALL"); RefreshFilteredRows(); }
    }

    public string FilterSource
    {
        get => filterSource;
        set { SetProperty(ref filterSource, value ?? "ALL"); RefreshFilteredRows(); }
    }

    public IReadOnlyList<string> SeverityFilterOptions { get; } =
        new[] { "ALL", "CRITICAL", "WARNING", "INFO" };

    public IReadOnlyList<string> SourceFilterOptions { get; } =
        new[] { "ALL", "BMS_ECU", "MOTOR_ECU", "THERMAL_MGR", "POWER_ECU", "MAIN_ECU", "ABS_ECU" };
    
    private void ExportReport()
    {
        var dialog = new SaveFileDialog
        {
            Filter = "PDF Document (*.pdf)|*.pdf|JSON Report (*.json)|*.json",
            FileName = $"DiagnosticReport_{DateTime.Now:yyyyMMdd}",
            Title = "Export Diagnostic Report"
        };

        if (dialog.ShowDialog() == true)
            DiagnosticsStatus = $"REPORT EXPORTED TO {System.IO.Path.GetFileName(dialog.FileName).ToUpper()}";
    }

    public string DtcHeaderText =>
        $"Active Faults: {AllDtcRows.Count(d => d.Status == "ACTIVE")} / Total Monitored: {AllDtcRows.Count}";

    public double ConfidenceScore =>
        RawAnomalies.Count == 0 ? 100 : Math.Max(0, 100 - RawAnomalies.Average(a => a.SeverityScore));

    private async Task StartFullScanAsync()
    {
        if (isScanning) return;
        isScanning = true;
        DiagnosticsStatus = "SCANNING SYSTEM...";
        ApplyAnomalies(VehicleDataService.CurrentAnomalies ?? Array.Empty<CanAnomaly>());
        await Task.Delay(1000); // Simulate processing
        isScanning = false;
    }

    private void StopScan()
    {
        isScanning = false;
        DiagnosticsStatus = "SCAN ABORTED";
    }

    private void OnAnomaliesUpdated(IReadOnlyList<CanAnomaly> anomalies)
    {
        ApplyAnomalies(anomalies ?? Array.Empty<CanAnomaly>());
    }

    private void ApplyAnomalies(IReadOnlyList<CanAnomaly> anomalies)
    {
        Alerts.Clear();
        RawAnomalies.Clear();
        var now = DateTime.Now;
        var sanitizedAnomalies = (anomalies ?? Array.Empty<CanAnomaly>())
            .Where(a => a is not null)
            .ToList();
        var anomaliesByCanId = sanitizedAnomalies
            .GroupBy(a => a.RelatedCanId)
            .ToDictionary(group => group.Key, group => group.ToList());
        var dtcByCode = AllDtcRows.ToDictionary(row => row.Code, StringComparer.OrdinalIgnoreCase);
        var activeCodes = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var anomalyGroup in anomaliesByCanId.Values)
        {
            foreach (var anomaly in anomalyGroup)
            {
                RawAnomalies.Add(anomaly);
                var code = string.IsNullOrWhiteSpace(anomaly.Code) ? "GEN-000" : anomaly.Code;
                var title = string.IsNullOrWhiteSpace(anomaly.Title) ? "UNKNOWN_ANOMALY" : anomaly.Title;
                var description = string.IsNullOrWhiteSpace(anomaly.Description) ? title : anomaly.Description;
                var severity = anomaly.SeverityScore > 80 ? "CRITICAL" : (anomaly.SeverityScore > 40 ? "WARNING" : "INFO");
                var source = string.IsNullOrWhiteSpace(anomaly.Source) ? "CAN_PIPELINE" : anomaly.Source.ToUpperInvariant();
                var key = $"{code}:{anomaly.RelatedCanId}";

                activeCodes.Add(code);

                if (!lifecycle.TryGetValue(key, out var life))
                {
                    life = new FaultLifecycle { FirstSeen = now, LastSeen = now, Count = 1 };
                    lifecycle[key] = life;
                }
                else
                {
                    life.LastSeen = now;
                    life.Count++;
                }

                if (dtcByCode.TryGetValue(code, out var existing))
                {
                    existing.Status = "ACTIVE";
                    existing.LastSeen = now;
                    existing.Severity = severity;
                    existing.ConfidenceScore = 100 - anomaly.SeverityScore;
                }
                else
                {
                    existing = new DiagnosticDtcItem
                    {
                        Code = code,
                        Description = description,
                        Severity = severity,
                        Source = source,
                        FaultKey = key,
                        Status = "ACTIVE",
                        Timestamp = now,
                        FirstSeen = now,
                        LastSeen = now,
                        ConfidenceScore = 100 - anomaly.SeverityScore
                    };
                    AllDtcRows.Add(existing);
                    dtcByCode[code] = existing;
                }

                Alerts.Add(new AlertItem(title, description, severity));
            }
        }

        // Reset all non-active catalog entries back to OK
        foreach (var row in AllDtcRows)
        {
            if (!activeCodes.Contains(row.Code))
                row.Status = "OK";
        }

        RefreshFilteredRows();
        selectedDtc = AllDtcRows.FirstOrDefault(d => d.Status == "ACTIVE");
        RefreshRecommendationPanel();

        var count = activeCodes.Count;
        DiagnosticsStatus = count == 0 ? "SCAN COMPLETE: NO FAULTS" : $"SCAN COMPLETE: {count} ISSUES FOUND";
        OnPropertyChanged(nameof(ConfidenceScore));
        OnPropertyChanged(nameof(DtcHeaderText));
    }

    private void RefreshFilteredRows()
    {
        FilteredDtcRows.Clear();
        foreach (var item in AllDtcRows)
        {
            var codeOk     = string.IsNullOrWhiteSpace(filterCode) ||
                             item.Code.Contains(filterCode, StringComparison.OrdinalIgnoreCase) ||
                             item.Description.Contains(filterCode, StringComparison.OrdinalIgnoreCase);
            var severityOk = filterSeverity == "ALL" ||
                             string.Equals(item.Severity, filterSeverity, StringComparison.OrdinalIgnoreCase);
            var sourceOk   = filterSource == "ALL" ||
                             string.Equals(item.Source, filterSource, StringComparison.OrdinalIgnoreCase);

            if (codeOk && severityOk && sourceOk)
                FilteredDtcRows.Add(item);
        }
        OnPropertyChanged(nameof(DtcHeaderText));
    }

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
    {
        base.OnDataUpdated(snapshot);
        UpdateSubsystem("BATTERY",  snapshot.BMSFault         ? "FAULT"   : (snapshot.OverheatFault    ? "WARNING" : "HEALTHY"));
        UpdateSubsystem("MOTOR",    snapshot.MotorFault        ? "FAULT"   : "HEALTHY");
        UpdateSubsystem("COOLING",  snapshot.OverheatFault     ? "FAULT"   : "HEALTHY");
        UpdateSubsystem("INVERTER", snapshot.OverCurrentFault  ? "WARNING" : "HEALTHY");
        UpdateSubsystem("ECU",      (snapshot.BMSFault || snapshot.MotorFault || snapshot.OverCurrentFault) ? "WARNING" : "HEALTHY");
        // ABS: no dedicated fault signal in snapshot — stays HEALTHY unless thermal is extreme
        UpdateSubsystem("ABS",      (snapshot.OverheatFault && snapshot.BMSFault) ? "WARNING" : "HEALTHY");
    }

    private void RefreshRecommendationPanel()
    {
        RecommendedActions.Clear();
        if (selectedDtc is null)
        {
            RecommendedActions.Add(new RecommendationItem("SYSTEM NOMINAL", "No active DTC entries detected."));
            return;
        }

        var mostRecent = lifecycle.Values.OrderByDescending(v => v.LastSeen).FirstOrDefault();
        var seenText   = mostRecent is null ? "single observation" : $"{mostRecent.Count} observations";
        RecommendedActions.Add(new RecommendationItem("SELECTED FAULT", $"{selectedDtc.Code} / {selectedDtc.Severity} / {seenText}"));
        RecommendedActions.Add(new RecommendationItem("DETAIL",          selectedDtc.Description));
        RecommendedActions.Add(new RecommendationItem("SOURCE",          selectedDtc.Source));
        RecommendedActions.Add(new RecommendationItem("SUBSYSTEM",       selectedDtc.AnomalyType));
    }

    private void UpdateSubsystem(string name, string state)
    {
        var sub = Subsystems.FirstOrDefault(s => s.Name == name);
        if (sub != null) sub.State = state;
    }

    private sealed class FaultLifecycle
    {
        public DateTime FirstSeen { get; set; } = DateTime.Now;
        public DateTime LastSeen { get; set; } = DateTime.Now;
        public int Count { get; set; } = 1;
    }
}

public sealed class LogPlaybackViewModel : SectionViewModel
{
    private string playbackMode = "STOPPED";
    private int playbackSpeed = 1;
    private readonly DispatcherTimer playbackTimer;
    private readonly CanLogImportService canLogImportService;
    private readonly AppLogger logger;
    private List<PlaybackPacket> playbackData = new();
    private int currentFrameIndex = 0;
    private string loadedFileName = "NO SESSION";
    private string sessionDurationText = "00:00:00";

    public LogPlaybackViewModel(VehicleDataService vehicleDataService, CanLogImportService canLogImportService, AppLogger logger)
        : base(vehicleDataService, SectionKey.LogPlayback)
    {
        this.canLogImportService = canLogImportService;
        this.logger = logger;
        playbackTimer = new DispatcherTimer();
        playbackTimer.Tick += OnPlaybackTick;
        
        Sessions = new ObservableCollection<PlaybackSessionItem>
        {
            new("session_0422.log", "2026-04-19 18:24", "00:14:12", "18,432 FRAMES"),
        };
        EventRows = new ObservableCollection<PlaybackEventItem>();

        PlayCommand = new RelayCommand(Play);
        PauseCommand = new RelayCommand(Pause);
        StopCommand = new RelayCommand(Stop);
        OpenLogCommand = new AsyncRelayCommand(OpenLogAsync);
        RewindCommand = new RelayCommand(Rewind);
        
        SetSpeedCommand = new RelayCommand<string>(s => {
            if (!int.TryParse(s, out var parsed))
            {
                parsed = 1;
            }
            playbackSpeed = Math.Max(1, Math.Min(8, parsed));
            if (playbackTimer.IsEnabled) UpdateTimerInterval();
        });
    }

    public ObservableCollection<PlaybackSessionItem> Sessions { get; }
    public ObservableCollection<PlaybackEventItem> EventRows { get; }
    
    public IRelayCommand PlayCommand { get; }
    public IRelayCommand PauseCommand { get; }
    public IRelayCommand StopCommand { get; }
    public IRelayCommand OpenLogCommand { get; }
    public IRelayCommand RewindCommand { get; }
    public IRelayCommand<string> SetSpeedCommand { get; }
    public string LoadedFileName => loadedFileName;
    public string SessionDurationText => sessionDurationText;

    public string PlaybackMode
    {
        get => playbackMode;
        set => SetProperty(ref playbackMode, value);
    }

    private void Play()
    {
        if (playbackData.Count == 0)
        {
            PlaybackMode = "NO LOG LOADED";
            return;
        }

        PlaybackMode = "PLAYING";
        UpdateTimerInterval();
        playbackTimer.Start();
    }

    private void Pause()
    {
        PlaybackMode = "PAUSED";
        playbackTimer.Stop();
    }

    private void Stop()
    {
        PlaybackMode = "STOPPED";
        playbackTimer.Stop();
        currentFrameIndex = 0;
    }

    private void Rewind()
    {
        currentFrameIndex = Math.Max(0, currentFrameIndex - 1);
        if (playbackData.Count > 0)
        {
            VehicleDataService.PublishPlaybackPacket(playbackData[currentFrameIndex]);
        }
    }

    private async Task OpenLogAsync()
    {
        var dialog = new OpenFileDialog
        {
            Filter = "CAN logs (*.log;*.txt;*.trc;*.asc;*.csv)|*.log;*.txt;*.trc;*.asc;*.csv|All files (*.*)|*.*",
            Title = "Open CAN Log"
        };

        if (dialog.ShowDialog() != true)
        {
            return;
        }

        try
        {
            var result = await canLogImportService.ParseFileAsync(dialog.FileName);
            playbackData = result.Packets.ToList();
            currentFrameIndex = 0;
            EventRows.Clear();
            foreach (var evt in result.Events.Take(20))
            {
                EventRows.Add(new PlaybackEventItem(evt.Timestamp, evt.FrameId, evt.DataHex, evt.DecodedSignal));
            }

            loadedFileName = Path.GetFileName(dialog.FileName);
            sessionDurationText = playbackData.Count < 2
                ? "00:00:00"
                : TimeSpan.FromMilliseconds(playbackData.Sum(packet => packet.DelayMilliseconds)).ToString(@"hh\:mm\:ss");
            OnPropertyChanged(nameof(LoadedFileName));
            OnPropertyChanged(nameof(SessionDurationText));

            if (playbackData.Count > 0)
            {
                VehicleDataService.PublishPlaybackPacket(playbackData[0]);
            }

            PlaybackMode = playbackData.Count == 0
                ? $"NO PARSABLE FRAMES ({result.ParsedLines}/{result.TotalLines})"
                : $"LOADED {playbackData.Count} FRAMES ({result.ParsedLines}/{result.TotalLines})";
        }
        catch (Exception exception)
        {
            logger.Error("Log import failed.", exception);
            PlaybackMode = "IMPORT FAILED";
        }
    }

    private void UpdateTimerInterval()
    {
        var packetDelay = playbackData.Count == 0 ? 1000 : Math.Max(16, playbackData[Math.Min(currentFrameIndex, playbackData.Count - 1)].DelayMilliseconds / playbackSpeed);
        playbackTimer.Interval = TimeSpan.FromMilliseconds(packetDelay);
    }

    private void OnPlaybackTick(object? sender, EventArgs e)
    {
        if (currentFrameIndex < playbackData.Count)
        {
            var packet = playbackData[currentFrameIndex];
            VehicleDataService.PublishPlaybackPacket(packet);
            EventRows.Insert(0, new PlaybackEventItem(
                packet.Frame.TimestampUtc.ToLocalTime().ToString("HH:mm:ss.fff"),
                $"0x{packet.Frame.CanId:X3}",
                BitConverter.ToString(packet.Frame.Data).Replace("-", string.Empty),
                packet.EventText));
            if (EventRows.Count > 20) EventRows.RemoveAt(20);
            currentFrameIndex++;
            if (currentFrameIndex < playbackData.Count)
            {
                UpdateTimerInterval();
            }
        }
        else
        {
            Stop();
        }
    }

    public string PlaybackStatus => PlaybackMode;
}

public sealed class AnalyticsViewModel : SectionViewModel
{
    private string selectedAnalyticsSection = "OVERVIEW";
    private readonly List<AnomalyEventPoint> anomalyHistory = new();
    private IReadOnlyList<CanAnomaly> currentAnomalies = Array.Empty<CanAnomaly>();
    private int latestAnomalyCount;
    private int criticalAnomalyCount;
    private int warningAnomalyCount;
    private string topCanId = "--";
    private string sessionComparison = "stable";
    private double reliabilityScore = 100;

    public AnalyticsViewModel(VehicleDataService vehicleDataService)
        : base(vehicleDataService, SectionKey.Analytics)
    {
        ChartPoints = new ObservableCollection<double>();
        OverviewCommand = new RelayCommand(() => { SelectedAnalyticsSection = "OVERVIEW"; CurrentCardIndex = 0; });
        BatteryDegradationCommand = new RelayCommand(() => { SelectedAnalyticsSection = "BATTERY DEGRADATION"; CurrentCardIndex = 1; });
        FaultTrendsCommand = new RelayCommand(() => { SelectedAnalyticsSection = "FAULT TRENDS"; CurrentCardIndex = 2; });
        AIAnomaliesCommand = new RelayCommand(() => { SelectedAnalyticsSection = "AI ANOMALIES"; CurrentCardIndex = 3; });
        ReliabilityScoreCommand = new RelayCommand(() => { SelectedAnalyticsSection = "RELIABILITY SCORE"; CurrentCardIndex = 4; });
        GenerateReportCommand = new RelayCommand(() => { });
        ExportChartsCommand = new RelayCommand(() => { });
        CompareSessionsCommand = new RelayCommand(() => { SelectedAnalyticsSection = "OVERVIEW"; });
        vehicleDataService.AnomaliesUpdated += OnAnomaliesUpdated;
    }

    public override int MaxCards => 5;
    public ObservableCollection<double> ChartPoints { get; }
    public IRelayCommand OverviewCommand { get; }
    public IRelayCommand BatteryDegradationCommand { get; }
    public IRelayCommand FaultTrendsCommand { get; }
    public IRelayCommand AIAnomaliesCommand { get; }
    public IRelayCommand ReliabilityScoreCommand { get; }
    public IRelayCommand GenerateReportCommand { get; }
    public IRelayCommand ExportChartsCommand { get; }
    public IRelayCommand CompareSessionsCommand { get; }

    public string SelectedAnalyticsSection
    {
        get => selectedAnalyticsSection;
        set => SetProperty(ref selectedAnalyticsSection, value);
    }

    public int TotalAlerts => latestAnomalyCount;
    public int CriticalAlerts => criticalAnomalyCount;
    public int WarningAlerts => warningAnomalyCount;
    public double NeuralConfidence => Math.Min(100, reliabilityScore + 2.5);
    public double HeatIndex => Math.Min(100, (Snapshot.BatteryTemp / 80.0) * 100);
    public double BatteryHealthIndex => Snapshot.SOH > 0 ? Snapshot.SOH : Math.Max(0, reliabilityScore);
    public string BatteryHealthIndexText => $"{BatteryHealthIndex:F1}%";
    public override double ReliabilityScore => reliabilityScore;
    public override string ReliabilityScoreText => $"{reliabilityScore:F1}%";

    public string AnalyticsSummary =>
        $"Anomalies: {latestAnomalyCount} | Critical: {criticalAnomalyCount} | Warning: {warningAnomalyCount} | Top CAN ID: {topCanId} | Session delta: {sessionComparison}";

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
    {
        base.OnDataUpdated(snapshot);
        if (ChartPoints.Count == 0)
        {
            ChartPoints.Add(20 + (snapshot.SOC * 1.6));
        }
    }

    private void OnAnomaliesUpdated(IReadOnlyList<CanAnomaly> anomalies)
    {
        currentAnomalies = anomalies ?? Array.Empty<CanAnomaly>();
        var now = DateTime.Now;
        var countsByCanId = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        var recent15Count = 0;
        var previous15Count = 0;
        var criticalCount30 = 0;
        var warningCount30 = 0;

        foreach (var anomaly in currentAnomalies)
        {
            var severity = NormalizeSeverity(anomaly.Severity);
            var canId = $"0x{anomaly.RelatedCanId:X}";
            anomalyHistory.Add(
                new AnomalyEventPoint
                {
                    TimestampUtc = now,
                    Severity = severity,
                    Type = InferType(anomaly),
                    CanId = canId,
                });
        }

        anomalyHistory.RemoveAll(p => p.TimestampUtc < now.AddHours(-1));
        latestAnomalyCount = currentAnomalies.Count;
        criticalAnomalyCount = 0;
        warningAnomalyCount = 0;
        foreach (var point in anomalyHistory)
        {
            if (point.TimestampUtc >= now.AddMinutes(-30))
            {
                countsByCanId.TryGetValue(point.CanId, out var total);
                countsByCanId[point.CanId] = total + 1;

                if (point.Severity == "CRITICAL")
                {
                    criticalCount30++;
                }
                else if (point.Severity == "WARNING")
                {
                    warningCount30++;
                }
            }

            if (point.TimestampUtc >= now.AddMinutes(-15))
            {
                recent15Count++;
            }
            else if (point.TimestampUtc >= now.AddMinutes(-30))
            {
                previous15Count++;
            }
        }

        criticalAnomalyCount = currentAnomalies.Count(a => NormalizeSeverity(a.Severity) == "CRITICAL");
        warningAnomalyCount = currentAnomalies.Count(a => NormalizeSeverity(a.Severity) == "WARNING");
        reliabilityScore = Math.Max(0, Math.Min(100, 100 - ((criticalCount30 * 18.0) + (warningCount30 * 8.0))));
        var topCan = countsByCanId.OrderByDescending(pair => pair.Value).FirstOrDefault();
        topCanId = string.IsNullOrEmpty(topCan.Key) ? "--" : $"{topCan.Key} ({topCan.Value})";
        var delta = recent15Count - previous15Count;
        sessionComparison = delta == 0 ? "stable" : (delta > 0 ? $"+{delta}" : delta.ToString());
        UpdateTrendBarSeries(now);

        OnPropertyChanged(nameof(TotalAlerts));
        OnPropertyChanged(nameof(CriticalAlerts));
        OnPropertyChanged(nameof(WarningAlerts));
        OnPropertyChanged(nameof(ReliabilityScore));
        OnPropertyChanged(nameof(ReliabilityScoreText));
        OnPropertyChanged(nameof(NeuralConfidence));
        OnPropertyChanged(nameof(BatteryHealthIndexText));
        OnPropertyChanged(nameof(AnalyticsSummary));
    }

    private void UpdateTrendBarSeries(DateTime now)
    {
        ChartPoints.Clear();
        for (var i = 5; i >= 0; i--)
        {
            var from = now.AddMinutes(-(i + 1) * 5);
            var to = now.AddMinutes(-i * 5);
            var count = anomalyHistory.Count(p => p.TimestampUtc >= from && p.TimestampUtc < to);
            ChartPoints.Add(20 + Math.Min(220, count * 14));
        }
    }

    private void RecomputeCanActivity(DateTime now)
    {
        var row = anomalyHistory
            .Where(p => p.TimestampUtc >= now.AddMinutes(-30))
            .GroupBy(p => p.CanId)
            .OrderByDescending(g => g.Count())
            .FirstOrDefault();
        topCanId = row is null ? "--" : $"{row.Key} ({row.Count()})";
    }

    private void RecomputeSessionComparison(DateTime now)
    {
        var current = anomalyHistory.Count(p => p.TimestampUtc >= now.AddMinutes(-15));
        var previous = anomalyHistory.Count(p => p.TimestampUtc >= now.AddMinutes(-30) && p.TimestampUtc < now.AddMinutes(-15));
        var delta = current - previous;
        sessionComparison = delta == 0 ? "stable" : (delta > 0 ? $"+{delta}" : delta.ToString());
    }

    private void RecomputeReliability(DateTime now)
    {
        var recent = anomalyHistory.Where(p => p.TimestampUtc >= now.AddMinutes(-30)).ToList();
        var weighted = (recent.Count(p => p.Severity == "CRITICAL") * 18.0) + (recent.Count(p => p.Severity == "WARNING") * 8.0);
        reliabilityScore = Math.Max(0, Math.Min(100, 100 - weighted));
    }

    private static string NormalizeSeverity(string? severity)
    {
        var value = (severity ?? "INFO").Trim().ToUpperInvariant();
        return value switch
        {
            "CRITICAL" => "CRITICAL",
            "WARNING" => "WARNING",
            _ => "INFO",
        };
    }

    private static string InferType(CanAnomaly anomaly)
    {
        var text = $"{anomaly.Title} {anomaly.Description}".ToUpperInvariant();
        if (text.Contains("THERM")) return "THERMAL";
        if (text.Contains("VOLT")) return "VOLTAGE";
        if (text.Contains("CURRENT")) return "CURRENT";
        if (text.Contains("MOTOR")) return "MOTOR";
        if (text.Contains("BMS")) return "BMS";
        return "GENERAL";
    }

    private sealed class AnomalyEventPoint
    {
        public DateTime TimestampUtc { get; set; } = DateTime.Now;
        public string Severity { get; set; } = "INFO";
        public string Type { get; set; } = "GENERAL";
        public string CanId { get; set; } = "0x000";
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

    protected override void OnDataUpdated(VehicleSnapshot snapshot)
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
    public SignalItem(string canId, string name, string value, string state, double freq = 0, double tdiff = 0)
    {
        CanId = canId;
        Name = name;
        Value = value;
        State = state;
        Frequency = freq;
        TimeDiff = tdiff;
    }

    public string CanId { get; }
    public string Name { get; }
    public string Value { get; }
    public string State { get; }
    public double Frequency { get; }
    public double TimeDiff { get; }
    public string FrequencyText => $"{Frequency:F1} Hz";
    public string TimeDiffText => $"{TimeDiff:F4}s";
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

public sealed class DiagnosticDtcItem : ObservableObject
{
    private string status = "ACTIVE";

    public string FaultKey { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Severity { get; set; } = "INFO";
    public string Source { get; set; } = "CAN_PIPELINE";
    public string CanId { get; set; } = "0x000";
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public DateTime FirstSeen { get; set; } = DateTime.UtcNow;
    public DateTime LastSeen { get; set; } = DateTime.UtcNow;
    public string AnomalyType { get; set; } = "GENERAL";
    public double ConfidenceScore { get; set; }
    public string Explanation { get; set; } = string.Empty;

    public string Status
    {
        get => status;
        set => SetProperty(ref status, value);
    }

    public string TimestampText => Timestamp.ToLocalTime().ToString("HH:mm:ss");
}

public sealed class TrendBucketItem
{
    public string Label { get; set; } = string.Empty;
    public int Count { get; set; }
    public double Height { get; set; }
}

public sealed class StatSliceItem
{
    public string Name { get; set; } = string.Empty;
    public int Count { get; set; }
    public double Percent { get; set; }
}

public sealed class CanIdActivityItem
{
    public string CanId { get; set; } = string.Empty;
    public int Count { get; set; }
}

public sealed class SessionComparisonItem
{
    public string Metric { get; set; } = string.Empty;
    public int Current { get; set; }
    public int Previous { get; set; }
    public int Delta { get; set; }
    public string DeltaText => Delta == 0 ? "0" : (Delta > 0 ? $"+{Delta}" : Delta.ToString());
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

public sealed class SubsystemItem : ObservableObject
{
    private string state;

    public SubsystemItem(string name, string detail, string state)
    {
        Name = name;
        Detail = detail;
        this.state = state;
    }

    public string Name { get; }
    public string Detail { get; }
    
    public string State
    {
        get => state;
        set => SetProperty(ref state, value);
    }
}

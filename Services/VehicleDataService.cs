using System.Windows.Threading;
using CANvision.Native.Models;
using CommunityToolkit.Mvvm.ComponentModel;
using System.Linq;
using System.Threading;

namespace CANvision.Native.Services;

public sealed class VehicleDataService : ObservableObject
{
    private readonly PythonApiClient pythonApiClient;
    private readonly AppLogger logger;
    private readonly DispatcherTimer refreshTimer;
    private readonly Dispatcher dispatcher;
    private readonly object sync = new();
    private VehicleSnapshot currentSnapshot = VehicleSnapshot.Default();
    private IReadOnlyList<CanAnomaly> currentAnomalies = Array.Empty<CanAnomaly>();
    private IReadOnlyList<DecodedSignal> currentSignals = Array.Empty<DecodedSignal>();
    private bool isRefreshing;
    private int fallbackFrameCounter;

    public event Action<VehicleSnapshot>? DataUpdated;
    public event Action<IReadOnlyList<CanAnomaly>>? AnomaliesUpdated;
    public event Action<IReadOnlyList<DecodedSignal>>? SignalsUpdated;

    public bool IsRunning { get; private set; }

    public VehicleDataService(PythonApiClient pythonApiClient, AppLogger logger)
    {
        this.pythonApiClient = pythonApiClient;
        this.logger = logger;
        dispatcher = Dispatcher.CurrentDispatcher;
        refreshTimer = new DispatcherTimer(DispatcherPriority.Background)
        {
            Interval = TimeSpan.FromMilliseconds(1500),
        };
        refreshTimer.Tick += async (_, _) => await RefreshAsync();
    }

    public VehicleSnapshot CurrentSnapshot
    {
        get => currentSnapshot;
        private set => SetProperty(ref currentSnapshot, value);
    }

    public IReadOnlyList<CanAnomaly> CurrentAnomalies
    {
        get => currentAnomalies;
        private set => SetProperty(ref currentAnomalies, value);
    }

    public IReadOnlyList<DecodedSignal> CurrentSignals
    {
        get => currentSignals;
        private set => SetProperty(ref currentSignals, value);
    }

    public TimeSpan RefreshInterval => refreshTimer.Interval;

    public string ApiEndpoint => pythonApiClient.Endpoint;

    public string JsonFallbackPath => pythonApiClient.JsonFallbackPath;

    public void Start()
    {
        if (refreshTimer.IsEnabled)
        {
            return;
        }

        logger.Info("Vehicle data polling started.");
        IsRunning = true;
        refreshTimer.Start();
        _ = RefreshAsync();
    }

    public void Stop()
    {
        if (!refreshTimer.IsEnabled)
        {
            return;
        }

        refreshTimer.Stop();
        IsRunning = false;
        logger.Info("Vehicle data polling stopped.");
    }

    private async Task RefreshAsync()
    {
        if (isRefreshing)
        {
            return;
        }

        isRefreshing = true;
        try
        {
            var snapshot = await pythonApiClient.GetLatestSnapshotAsync(CancellationToken.None).ConfigureAwait(false);
            if (snapshot is not null)
            {
                await PublishSnapshotInternalAsync(snapshot, snapshot.Source).ConfigureAwait(false);
            }
        }
        catch (Exception exception)
        {
            logger.Error("Vehicle data refresh failed. Keeping last known snapshot.", exception);
        }
        finally
        {
            isRefreshing = false;
        }
    }

    public void PublishExternalSnapshot(VehicleSnapshot snapshot, string source)
    {
        _ = PublishSnapshotInternalAsync(snapshot, source);
    }

    public void PublishPlaybackPacket(PlaybackPacket packet)
    {
        if (packet is null)
        {
            return;
        }

        _ = dispatcher.InvokeAsync(() =>
        {
            lock (sync)
            {
                CurrentSnapshot = packet.Snapshot;
                CurrentSignals = packet.Signals;
                CurrentAnomalies = packet.Anomalies;
            }

            NotifySignalSubscribers(packet.Signals);
            NotifyAnomalySubscribers(packet.Anomalies);
            NotifySnapshotSubscribers(packet.Snapshot);
        }, DispatcherPriority.Background);
    }

    public void UpdateAnomalies(IEnumerable<CanAnomaly> anomalies, string source)
    {
        var safeAnomalies = (anomalies ?? Enumerable.Empty<CanAnomaly>())
            .Where(a => a is not null)
            .Select(a => new CanAnomaly
            {
                Code = string.IsNullOrWhiteSpace(a.Code) ? "GEN-000" : a.Code,
                Title = string.IsNullOrWhiteSpace(a.Title) ? "UNKNOWN_ANOMALY" : a.Title,
                Description = a.Description ?? string.Empty,
                Severity = string.IsNullOrWhiteSpace(a.Severity) ? "WARNING" : a.Severity.ToUpperInvariant(),
                RelatedCanId = a.RelatedCanId,
                Source = string.IsNullOrWhiteSpace(source) ? (a.Source ?? "runtime") : source,
                TimestampUtc = a.TimestampUtc == default ? DateTime.UtcNow : a.TimestampUtc,
            })
            .ToList()
            .AsReadOnly();

        if (dispatcher.CheckAccess())
        {
            lock (sync)
            {
                CurrentAnomalies = safeAnomalies;
            }

            NotifyAnomalySubscribers(safeAnomalies);
            return;
        }

        _ = dispatcher.InvokeAsync(() =>
        {
            lock (sync)
            {
                CurrentAnomalies = safeAnomalies;
            }

            NotifyAnomalySubscribers(safeAnomalies);
        }, DispatcherPriority.Background);
    }

    private async Task PublishSnapshotInternalAsync(VehicleSnapshot snapshot, string? source)
    {
        var update = await Task.Run(() =>
        {
            var safeSnapshot = SanitizeSnapshot(snapshot, source);

            if (string.Equals(safeSnapshot.Source, "json-fallback", StringComparison.OrdinalIgnoreCase))
            {
                var nextTick = Interlocked.Increment(ref fallbackFrameCounter);
                safeSnapshot = ApplyFallbackDynamics(safeSnapshot, nextTick);
            }
            else
            {
                Interlocked.Exchange(ref fallbackFrameCounter, 0);
            }

            var anomalies = BuildAnomaliesFromSnapshot(safeSnapshot).AsReadOnly();
            return new SnapshotUpdate(safeSnapshot, anomalies);
        }).ConfigureAwait(false);

        await dispatcher.InvokeAsync(() =>
        {
            lock (sync)
            {
                CurrentSnapshot = update.Snapshot;
                CurrentAnomalies = update.Anomalies;
                CurrentSignals = Array.Empty<DecodedSignal>();
            }

            NotifyAnomalySubscribers(update.Anomalies);
            NotifySnapshotSubscribers(update.Snapshot);
        }, DispatcherPriority.Background);
    }

    private void NotifySnapshotSubscribers(VehicleSnapshot snapshot)
    {
        var handlers = DataUpdated?.GetInvocationList();
        if (handlers is null)
        {
            return;
        }

        foreach (var handler in handlers)
        {
            try
            {
                ((Action<VehicleSnapshot>)handler)(snapshot);
            }
            catch (Exception exception)
            {
                logger.Error("A section failed while processing snapshot update.", exception);
            }
        }
    }

    private void NotifyAnomalySubscribers(IReadOnlyList<CanAnomaly> anomalies)
    {
        var handlers = AnomaliesUpdated?.GetInvocationList();
        if (handlers is null)
        {
            return;
        }

        foreach (var handler in handlers)
        {
            try
            {
                ((Action<IReadOnlyList<CanAnomaly>>)handler)(anomalies);
            }
            catch (Exception exception)
            {
                logger.Error("A section failed while processing anomaly update.", exception);
            }
        }
    }

    private void NotifySignalSubscribers(IReadOnlyList<DecodedSignal> signals)
    {
        var handlers = SignalsUpdated?.GetInvocationList();
        if (handlers is null)
        {
            return;
        }

        foreach (var handler in handlers)
        {
            try
            {
                ((Action<IReadOnlyList<DecodedSignal>>)handler)(signals);
            }
            catch (Exception exception)
            {
                logger.Error("A section failed while processing signal update.", exception);
            }
        }
    }

    private static VehicleSnapshot SanitizeSnapshot(VehicleSnapshot snapshot, string? source)
    {
        var safe = snapshot ?? VehicleSnapshot.Default();
        safe.Source = (string.IsNullOrWhiteSpace(source) ? safe.Source : source) ?? "runtime";
        if (safe.UpdatedAt == default)
        {
            safe.UpdatedAt = DateTime.UtcNow;
        }

        safe.SOC = Clamp(safe.SOC, 0, 100);
        safe.BatteryTemp = Clamp(safe.BatteryTemp, -40, 160);
        safe.BatteryVoltage = Clamp(safe.BatteryVoltage, 0, 1200);
        safe.VehicleSpeed = Clamp(safe.VehicleSpeed, 0, 350);
        safe.MotorTemp = Clamp(safe.MotorTemp, -40, 200);
        safe.Battery = (int)Math.Round(Clamp(safe.Battery, 0, 100));
        safe.Temperature = (int)Math.Round(Clamp(safe.Temperature, -40, 160));
        safe.MotorStatus = string.IsNullOrWhiteSpace(safe.MotorStatus) ? "UNKNOWN" : safe.MotorStatus;
        safe.DriveMode = string.IsNullOrWhiteSpace(safe.DriveMode) ? "NORMAL" : safe.DriveMode;
        safe.Gear = string.IsNullOrWhiteSpace(safe.Gear) ? "P" : safe.Gear;
        return safe;
    }

    private static VehicleSnapshot ApplyFallbackDynamics(VehicleSnapshot snapshot, int tick)
    {
        var pulse = Math.Sin(tick / 8.0);
        snapshot.SOC = Clamp(snapshot.SOC - 0.01, 0, 100);
        snapshot.VehicleSpeed = Clamp(Math.Max(0, snapshot.VehicleSpeed + pulse * 0.9), 0, 120);
        snapshot.BatteryTemp = Clamp(snapshot.BatteryTemp + (pulse * 0.15), -40, 140);
        snapshot.BatteryVoltage = Clamp(snapshot.BatteryVoltage + (pulse * 0.35), 0, 1000);
        snapshot.PeakAmperage = Clamp(snapshot.PeakAmperage + (pulse * 1.2), 0, 900);
        snapshot.UpdatedAt = DateTime.UtcNow;
        snapshot.Battery = (int)Math.Round(snapshot.SOC);
        snapshot.Temperature = (int)Math.Round(snapshot.BatteryTemp);
        return snapshot;
    }

    private static List<CanAnomaly> BuildAnomaliesFromSnapshot(VehicleSnapshot snapshot)
    {
        var anomalies = new List<CanAnomaly>();

        if (snapshot.BMSFault)
        {
            anomalies.Add(NewAnomaly("BMS-001", "BMS FAULT", "Battery management system reports a critical fault.", "CRITICAL", 0x100));
        }

        if (snapshot.MotorFault)
        {
            anomalies.Add(NewAnomaly("MTR-042", "MOTOR FAULT", "Motor subsystem reported a propulsion fault.", "CRITICAL", 0x332));
        }

        if (snapshot.OverheatFault || snapshot.BatteryTemp >= 85 || snapshot.MotorTemp >= 95)
        {
            anomalies.Add(NewAnomaly("THM-101", "THERMAL WARNING", "Thermal envelope exceeded nominal band.", "WARNING", 0x5D2));
        }

        if (snapshot.OverCurrentFault)
        {
            anomalies.Add(NewAnomaly("PWR-220", "OVER CURRENT", "Current draw exceeded expected operating limits.", "WARNING", 0x2B4));
        }

        if (snapshot.UnderVoltageFault || snapshot.BatteryVoltage is > 0 and < 290)
        {
            anomalies.Add(NewAnomaly("VLT-301", "UNDER VOLTAGE", "Battery pack voltage is below safe threshold.", "WARNING", 0x1A2));
        }

        return anomalies;
    }

    private static CanAnomaly NewAnomaly(string code, string title, string description, string severity, int canId)
    {
        return new CanAnomaly
        {
            Code = code,
            Title = title,
            Description = description,
            Severity = severity,
            RelatedCanId = canId,
            TimestampUtc = DateTime.UtcNow,
            Source = "snapshot-inference",
        };
    }

    private static double Clamp(double value, double min, double max)
    {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }

    private sealed class SnapshotUpdate
    {
        public SnapshotUpdate(VehicleSnapshot snapshot, IReadOnlyList<CanAnomaly> anomalies)
        {
            Snapshot = snapshot;
            Anomalies = anomalies;
        }

        public VehicleSnapshot Snapshot { get; }

        public IReadOnlyList<CanAnomaly> Anomalies { get; }
    }
}

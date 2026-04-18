using System.Windows.Threading;
using CANvision.Native.Models;
using CommunityToolkit.Mvvm.ComponentModel;

namespace CANvision.Native.Services;

public sealed class VehicleDataService : ObservableObject
{
    private readonly PythonApiClient pythonApiClient;
    private readonly AppLogger logger;
    private readonly DispatcherTimer refreshTimer;
    private VehicleSnapshot currentSnapshot = VehicleSnapshot.Default();
    private bool isRefreshing;

    public VehicleDataService(PythonApiClient pythonApiClient, AppLogger logger)
    {
        this.pythonApiClient = pythonApiClient;
        this.logger = logger;
        refreshTimer = new DispatcherTimer(DispatcherPriority.Background)
        {
            Interval = TimeSpan.FromMilliseconds(900),
        };
        refreshTimer.Tick += async (_, _) => await RefreshAsync();
    }

    public VehicleSnapshot CurrentSnapshot
    {
        get => currentSnapshot;
        private set => SetProperty(ref currentSnapshot, value);
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
            var snapshot = await pythonApiClient.GetLatestSnapshotAsync(CancellationToken.None);
            if (snapshot is not null)
            {
                CurrentSnapshot = snapshot;
            }
        }
        finally
        {
            isRefreshing = false;
        }
    }
}

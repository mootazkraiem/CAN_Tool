using System.Windows;
using System.Windows.Threading;
using CANvision.Native.Scene;
using CANvision.Native.Services;
using CANvision.Native.UI;
using CANvision.Native.ViewModels;

namespace CANvision.Native;

public partial class App : Application
{
    private AppLogger? logger;
    private VehicleDataService? vehicleDataService;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        logger = new AppLogger();
        
        // Add global exception handlers
        AppDomain.CurrentDomain.UnhandledException += (s, args) => 
            logger.Error("Unhandled Domain Exception", args.ExceptionObject as Exception);
        
        DispatcherUnhandledException += (s, args) => {
            logger.Error("Unhandled Dispatcher Exception", args.Exception);
            args.Handled = true;
        };

        logger.Info("Application startup sequence initiated.");

        var pythonApiClient = new PythonApiClient(logger);
        vehicleDataService = new VehicleDataService(pythonApiClient, logger);
        var canLogImportService = new CanLogImportService(logger, pythonApiClient);
        var backgroundManager = new BackgroundManager(logger);

        var analytics = new AnalyticsViewModel(vehicleDataService);
        var settings = new SettingsViewModel(vehicleDataService);
        var preview = new PreviewViewModel(null);

        var home = new HomeViewModel(vehicleDataService);
        var dashboard = new DashboardViewModel(vehicleDataService);
        var telemetry = new TelemetryViewModel(vehicleDataService, canLogImportService);
        var diagnostics = new DiagnosticsViewModel(vehicleDataService);
        var playback = new LogPlaybackViewModel(vehicleDataService, canLogImportService, logger);

        var navigationService = new NavigationService(
            logger,
            home,
            dashboard,
            telemetry,
            diagnostics,
            playback,
            analytics,
            settings,
            preview);
        preview.AttachNavigationService(navigationService);
        navigationService.NavigateTo("Home");
        logger.Info("Startup navigation set to Home.");

        var mainWindowViewModel = new MainWindowViewModel(
            navigationService,
            vehicleDataService,
            backgroundManager);

        logger.Info("Initializing MainWindow...");
        var window = new MainWindow(mainWindowViewModel, logger);
        window.Show();
        window.Activate();
        window.Focus();
        MainWindow = window;
        
        logger.Info("Displaying MainWindow...");
        logger.Info($"IsVisible: {window.IsVisible}");
        logger.Info($"State: {window.WindowState}");
        logger.Info($"Size: {window.Width}x{window.Height}");

        Dispatcher.BeginInvoke(new Action(() =>
        {
            logger.Info("Starting vehicle data service after initial window render.");
            vehicleDataService.Start();
        }), DispatcherPriority.Background);

        logger.Info("Application startup sequence completed.");
    }

    protected override void OnExit(ExitEventArgs e)
    {
        logger?.Info($"Application exiting with code {e.ApplicationExitCode}.");
        vehicleDataService?.Stop();
        base.OnExit(e);
    }
}

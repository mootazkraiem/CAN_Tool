using System;
using System.ComponentModel;
using System.Windows;
using CANvision.Native.Scene;
using CANvision.Native.Services;
using CANvision.Native.ViewModels;

namespace CANvision.Native.UI;

public partial class MainWindow : Window
{
    private const string Disable3DEnvironmentVariable = "CANVISION_DISABLE_3D";

    private readonly MainWindowViewModel viewModel;
    private readonly AppLogger logger;
    private GarageScene? garageSceneControl;
    private bool isUsing3DScene;

    public MainWindow(MainWindowViewModel viewModel, AppLogger logger)
    {
        InitializeComponent();
        this.viewModel = viewModel;
        this.logger = logger;
        DataContext = viewModel;
        Loaded += OnLoaded;
        Closed += OnClosed;
        viewModel.PropertyChanged += ViewModelOnPropertyChanged;
        InitializeGarageSceneIfEnabled();
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        InterfaceLayer.Opacity = 1.0;
        logger.Info($"CurrentSection: {viewModel.CurrentSection?.GetType().Name ?? "null"}");
        logger.Info($"IsSectionVisible: {viewModel.IsSectionVisible}");
        logger.Info($"CurrentSectionKey: {viewModel.CurrentSectionKey}");
        garageSceneControl?.BeginIntro();
    }

    private void ViewModelOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(MainWindowViewModel.CurrentSectionKey))
        {
            garageSceneControl?.SetSection(viewModel.CurrentSectionKey);
        }
    }

    private void InitializeGarageSceneIfEnabled()
    {
        isUsing3DScene = !string.Equals(
            Environment.GetEnvironmentVariable(Disable3DEnvironmentVariable),
            "1",
            StringComparison.OrdinalIgnoreCase);

        if (!isUsing3DScene)
        {
            logger.Info($"3D showroom disabled via {Disable3DEnvironmentVariable}=1.");
            return;
        }

        try
        {
            garageSceneControl = new GarageScene
            {
                IsHitTestVisible = false,
            };
            garageSceneControl.Initialize(logger);
            garageSceneControl.SetRenderingActive(true);
            garageSceneControl.SetSection(viewModel.CurrentSectionKey);
            GarageSceneHost.Content = garageSceneControl;
            logger.Info("3D showroom enabled behind interface layer.");
        }
        catch (Exception exception)
        {
            isUsing3DScene = false;
            garageSceneControl = null;
            GarageSceneHost.Content = null;
            logger.Error("3D showroom initialization failed. Continuing without the native scene.", exception);
        }
    }

    private void OnClosed(object? sender, EventArgs e)
    {
        if (garageSceneControl is not null)
        {
            garageSceneControl.Dispose();
            GarageSceneHost.Content = null;
        }

        viewModel.PropertyChanged -= ViewModelOnPropertyChanged;
        Loaded -= OnLoaded;
        Closed -= OnClosed;
    }
}

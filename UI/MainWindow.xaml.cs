using System.ComponentModel;
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;
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
    private bool introStarted;
    private bool isUsing3DScene;

    public MainWindow(MainWindowViewModel viewModel, AppLogger logger)
    {
        InitializeComponent();
        this.viewModel = viewModel;
        this.logger = logger;
        DataContext = viewModel;
        Loaded += OnLoaded;
        InitializeGarageSceneIfEnabled();
        viewModel.PropertyChanged += ViewModelOnPropertyChanged;
        Closed += OnClosed;
    }

    private void ViewModelOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(MainWindowViewModel.CurrentSectionKey))
        {
            garageSceneControl?.SetSection(viewModel.CurrentSectionKey);
        }

        if (e.PropertyName == nameof(MainWindowViewModel.IsSectionVisible) ||
            e.PropertyName == nameof(MainWindowViewModel.CurrentSectionKey))
        {
            UpdateViewState(e.PropertyName == nameof(MainWindowViewModel.IsSectionVisible));
        }
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        if (introStarted)
        {
            return;
        }

        introStarted = true;
        StartWindowIntro();

        if (isUsing3DScene)
        {
            garageSceneControl?.BeginIntro();
        }

        UpdateViewState(animateSectionEntry: false);
    }

    private void StartWindowIntro()
    {
        AnimateOpacity(BackgroundImageLayer, 0.0, 1.0, TimeSpan.Zero, TimeSpan.FromMilliseconds(500));
    }

    private void OnGarageSceneIntroCompleted(object? sender, EventArgs e)
    {
        UpdateViewState(animateSectionEntry: false);
    }

    private void AnimateSectionContent()
    {
        if (SectionContentHost is null || SectionContentTranslate is null)
        {
            return;
        }

        var opacityAnimation = new DoubleAnimation
        {
            From = 0.0,
            To = 1.0,
            Duration = new Duration(TimeSpan.FromMilliseconds(340)),
            EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut },
            FillBehavior = FillBehavior.Stop,
        };
        var translateAnimation = new DoubleAnimation
        {
            From = 32,
            To = 0,
            Duration = new Duration(TimeSpan.FromMilliseconds(380)),
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut },
            FillBehavior = FillBehavior.Stop,
        };

        SectionContentHost.Opacity = 1.0;
        SectionContentTranslate.Y = 0.0;
        SectionContentHost.BeginAnimation(OpacityProperty, opacityAnimation);
        SectionContentTranslate.BeginAnimation(TranslateTransform.YProperty, translateAnimation);
    }

    private static void AnimateOpacity(UIElement element, double from, double to, TimeSpan beginTime, TimeSpan duration)
    {
        var animation = new DoubleAnimation
        {
            From = from,
            To = to,
            BeginTime = beginTime,
            Duration = new Duration(duration),
            EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut },
            FillBehavior = FillBehavior.HoldEnd,
        };

        element.BeginAnimation(OpacityProperty, animation);
    }

    private void OnClosed(object? sender, EventArgs e)
    {
        Loaded -= OnLoaded;
        if (garageSceneControl is not null)
        {
            garageSceneControl.IntroCompleted -= OnGarageSceneIntroCompleted;
            garageSceneControl.Dispose();
            GarageSceneHost.Content = null;
        }

        viewModel.PropertyChanged -= ViewModelOnPropertyChanged;
        Closed -= OnClosed;
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
            garageSceneControl = new GarageScene();
            garageSceneControl.Initialize(logger);
            garageSceneControl.IntroCompleted += OnGarageSceneIntroCompleted;
            garageSceneControl.SetRenderingActive(!viewModel.IsSectionVisible);
            garageSceneControl.SetSection(viewModel.CurrentSectionKey);
            GarageSceneHost.Content = garageSceneControl;
            logger.Info("3D showroom enabled.");
        }
        catch (Exception exception)
        {
            isUsing3DScene = false;
            garageSceneControl = null;
            GarageSceneHost.Content = null;
            logger.Error("3D showroom initialization failed. Continuing without the native scene.", exception);
        }
    }

    private void UpdateViewState(bool animateSectionEntry)
    {
        var isSectionVisible = viewModel.IsSectionVisible;
        InterfaceLayer.IsHitTestVisible = isSectionVisible;
        garageSceneControl?.SetRenderingActive(!isSectionVisible);

        if (!isSectionVisible)
        {
            return;
        }

        InterfaceLayer.Opacity = 1.0;
        AnimateSectionContent();
        if (animateSectionEntry)
        {
            AnimateOpacity(InterfaceLayer, 0.0, 1.0, TimeSpan.Zero, TimeSpan.FromMilliseconds(260));
        }

    }
}

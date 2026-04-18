using System.Collections.ObjectModel;
using System.Linq;
using CANvision.Native.Models;
using CANvision.Native.ViewModels;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace CANvision.Native.Services;

public sealed class NavigationService : ObservableObject
{
    private readonly AppLogger logger;
    private readonly SectionViewModel homeSection;
    private SectionViewModel currentSection;
    private NavigationStage stage;

    public NavigationService(
        AppLogger logger,
        HomeViewModel home,
        DashboardViewModel dashboard,
        TelemetryViewModel telemetry,
        DiagnosticsViewModel diagnostics,
        LogPlaybackViewModel playback,
        AnalyticsViewModel analytics,
        SettingsViewModel settings,
        PreviewViewModel preview)
    {
        this.logger = logger;
        homeSection = home;
        Preview = preview;
        Tabs = new ObservableCollection<NavigationItemViewModel>(BuildTabs(dashboard, telemetry, diagnostics, playback, analytics, settings));

        PreviewSectionCommand = new RelayCommand<NavigationItemViewModel?>(PreviewSection);
        NavigateCommand = new RelayCommand<NavigationItemViewModel?>(Navigate);
        NavigateToSectionCommand = new RelayCommand<SectionKey>(NavigateToSection);
        EnterSystemCommand = new RelayCommand(EnterSystem, () => IsLandingVisible || IsHomeVisible);
        NavigateHomeCommand = new RelayCommand(NavigateHome, () => CanNavigateHome);
        BackToHubCommand = new RelayCommand(ExecuteBackToHub, () => IsSystemVisible);
        currentSection = dashboard;
        stage = NavigationStage.Home;
    }

    public ObservableCollection<NavigationItemViewModel> Tabs { get; }

    public PreviewViewModel Preview { get; }

    public IRelayCommand<NavigationItemViewModel?> PreviewSectionCommand { get; }

    public IRelayCommand<NavigationItemViewModel?> NavigateCommand { get; }

    public IRelayCommand<SectionKey> NavigateToSectionCommand { get; }

    public IRelayCommand EnterSystemCommand { get; }

    public IRelayCommand NavigateHomeCommand { get; }

    public IRelayCommand BackToHubCommand { get; }

    public HomeViewModel HomeSection => (HomeViewModel)homeSection;

    public SectionViewModel CurrentSection
    {
        get => currentSection;
        private set => SetProperty(ref currentSection, value);
    }

    public NavigationStage Stage
    {
        get => stage;
        private set => SetProperty(ref stage, value);
    }

    public bool IsHomeVisible => Stage == NavigationStage.Home;

    public bool IsLandingVisible => Stage == NavigationStage.Landing;

    public bool IsHubVisible => Stage == NavigationStage.Hub;

    public bool IsSystemVisible => Stage == NavigationStage.Interface;

    public bool CanNavigateHome => !IsHomeVisible;

    private static IEnumerable<NavigationItemViewModel> BuildTabs(
        DashboardViewModel dashboard,
        TelemetryViewModel telemetry,
        DiagnosticsViewModel diagnostics,
        LogPlaybackViewModel playback,
        AnalyticsViewModel analytics,
        SettingsViewModel settings)
    {
        var sections = new SectionViewModel[]
        {
            dashboard,
            telemetry,
            diagnostics,
            playback,
            analytics,
            settings,
        };

        foreach (var section in sections)
        {
            yield return new NavigationItemViewModel(
                section.Descriptor.ModuleCode,
                section.Descriptor.Title,
                section.Descriptor.MenuDescription,
                section);
        }
    }

    private void PreviewSection(NavigationItemViewModel? tab)
    {
        if (tab is null)
        {
            return;
        }

        ClearActiveTabs();
        SetCurrentSection(tab.Section);
        Preview.ActiveKey = tab.Section.Key;
        SetStage(NavigationStage.Hub);
        logger.Info($"Hub opened for {tab.Title}.");
    }

    private void Navigate(NavigationItemViewModel? tab)
    {
        if (tab is null)
        {
            return;
        }

        SetActiveTab(tab);
        SetCurrentSection(tab.Section);
        SetStage(NavigationStage.Interface);
        logger.Info($"Navigation switched to {tab.Title}.");
    }

    private void EnterSystem()
    {
        if (!IsLandingVisible && !IsHomeVisible)
        {
            return;
        }

        var tab = Tabs.FirstOrDefault(item => ReferenceEquals(item.Section, CurrentSection));
        tab ??= Tabs.FirstOrDefault();
        if (tab is not null)
        {
            PreviewSection(tab);
        }
    }

    private void NavigateHome()
    {
        if (IsHomeVisible)
        {
            return;
        }

        ClearActiveTabs();
        SetStage(NavigationStage.Home);
        logger.Info("Navigation returned to the landing screen.");
    }

    private void NavigateToSection(SectionKey key)
    {
        if (key == SectionKey.Home)
        {
            NavigateHome();
            return;
        }

        var tab = Tabs.FirstOrDefault(item => item.Section.Key == key);
        if (tab is null)
        {
            logger.Error($"Navigation target for section {key} was not found.");
            return;
        }

        // Direct interface-to-interface routing requested by the user
        Navigate(tab);
    }

    private void ExecuteBackToHub()
    {
        if (!IsSystemVisible) return;
        
        var tab = Tabs.FirstOrDefault(item => ReferenceEquals(item.Section, CurrentSection));
        PreviewSection(tab);
    }

    private void SetCurrentSection(SectionViewModel section)
    {
        if (ReferenceEquals(CurrentSection, section))
        {
            return;
        }

        CurrentSection = section;
    }

    private void SetStage(NavigationStage nextStage)
    {
        if (Stage == nextStage)
        {
            return;
        }

        Stage = nextStage;
        OnPropertyChanged(nameof(IsHomeVisible));
        OnPropertyChanged(nameof(IsLandingVisible));
        OnPropertyChanged(nameof(IsHubVisible));
        OnPropertyChanged(nameof(IsSystemVisible));
        OnPropertyChanged(nameof(CanNavigateHome));
        EnterSystemCommand.NotifyCanExecuteChanged();
        NavigateHomeCommand.NotifyCanExecuteChanged();
        BackToHubCommand.NotifyCanExecuteChanged();
    }

    private void SetActiveTab(NavigationItemViewModel activeTab)
    {
        foreach (var item in Tabs)
        {
            item.IsActive = ReferenceEquals(item, activeTab);
        }
    }

    private void ClearActiveTabs()
    {
        foreach (var item in Tabs)
        {
            item.IsActive = false;
        }
    }
}

using System.ComponentModel;
using CANvision.Native.Models;
using CANvision.Native.Scene;
using CANvision.Native.Services;

namespace CANvision.Native.ViewModels;

public sealed class MainWindowViewModel : ViewModelBase
{
    private readonly NavigationService navigationService;
    private bool useStartupFallbackState = true;
    private bool isSectionVisible = true;
    private SectionKey currentSectionKey = SectionKey.Home;

    public MainWindowViewModel(
        NavigationService navigationService,
        VehicleDataService vehicleDataService,
        BackgroundManager backgroundManager)
    {
        this.navigationService = navigationService;
        VehicleDataService = vehicleDataService;
        backgroundManager.LogDisabled();
        IsSectionVisible = true;
        CurrentSectionKey = SectionKey.Home;
        navigationService.PropertyChanged += NavigationServiceOnPropertyChanged;

        if (navigationService.IsSystemVisible || navigationService.IsHomeVisible || navigationService.IsHubVisible)
        {
            useStartupFallbackState = false;
        }
    }

    public NavigationService NavigationService => navigationService;

    public VehicleDataService VehicleDataService { get; }

    public HomeViewModel HomeSection => navigationService.HomeSection;

    public bool IsLandingScreenVisible => useStartupFallbackState ? false : !navigationService.IsSystemVisible && !navigationService.IsHubVisible;

    public bool IsHubVisible => useStartupFallbackState ? false : navigationService.IsHubVisible;

    public bool IsSectionVisible
    {
        get => useStartupFallbackState ? isSectionVisible : navigationService.IsSystemVisible;
        private set => SetProperty(ref isSectionVisible, value);
    }

    public PreviewViewModel HubSection => navigationService.Preview;

    public bool IsBackToCardsVisible => IsSectionVisible && CurrentSectionKey != SectionKey.Home;

    public SectionViewModel CurrentSection =>
        useStartupFallbackState
            ? navigationService.HomeSection
            : navigationService.IsHomeVisible
            ? navigationService.HomeSection
            : navigationService.CurrentSection;

    public SectionKey CurrentSectionKey
    {
        get => useStartupFallbackState
            ? currentSectionKey
            : navigationService.IsHomeVisible
            ? SectionKey.Home
            : navigationService.CurrentSection.Key;
        private set => SetProperty(ref currentSectionKey, value);
    }

    private void NavigationServiceOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(NavigationService.CurrentSection) ||
            e.PropertyName == nameof(NavigationService.Stage))
        {
            useStartupFallbackState = false;
            OnPropertyChanged(nameof(HomeSection));
            OnPropertyChanged(nameof(HubSection));
            OnPropertyChanged(nameof(CurrentSection));
            OnPropertyChanged(nameof(CurrentSectionKey));
            OnPropertyChanged(nameof(IsLandingScreenVisible));
            OnPropertyChanged(nameof(IsHubVisible));
            OnPropertyChanged(nameof(IsSectionVisible));
            OnPropertyChanged(nameof(IsBackToCardsVisible));
        }
    }
}

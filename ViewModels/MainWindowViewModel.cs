using System.ComponentModel;
using System.Windows.Media;
using CANvision.Native.Models;
using CANvision.Native.Scene;
using CANvision.Native.Services;

namespace CANvision.Native.ViewModels;

public sealed class MainWindowViewModel : ViewModelBase
{
    private readonly NavigationService navigationService;

    public MainWindowViewModel(
        NavigationService navigationService,
        VehicleDataService vehicleDataService,
        BackgroundManager backgroundManager)
    {
        this.navigationService = navigationService;
        VehicleDataService = vehicleDataService;
        BackgroundImage = backgroundManager.LoadBackgroundImage();
        navigationService.PropertyChanged += NavigationServiceOnPropertyChanged;
    }

    public NavigationService NavigationService => navigationService;

    public VehicleDataService VehicleDataService { get; }

    public ImageSource? BackgroundImage { get; }

    public HomeViewModel HomeSection => navigationService.HomeSection;

    public bool IsLandingScreenVisible => !navigationService.IsSystemVisible && !navigationService.IsHubVisible;

    public bool IsHubVisible => navigationService.IsHubVisible;

    public bool IsSectionVisible => navigationService.IsSystemVisible;

    public PreviewViewModel HubSection => navigationService.Preview;

    public SectionViewModel CurrentSection =>
        navigationService.IsHomeVisible
            ? navigationService.HomeSection
            : navigationService.CurrentSection;

    public SectionKey CurrentSectionKey =>
        navigationService.IsHomeVisible
            ? SectionKey.Home
            : navigationService.CurrentSection.Key;

    private void NavigationServiceOnPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(NavigationService.CurrentSection) ||
            e.PropertyName == nameof(NavigationService.Stage))
        {
            OnPropertyChanged(nameof(HomeSection));
            OnPropertyChanged(nameof(HubSection));
            OnPropertyChanged(nameof(CurrentSection));
            OnPropertyChanged(nameof(CurrentSectionKey));
            OnPropertyChanged(nameof(IsLandingScreenVisible));
            OnPropertyChanged(nameof(IsHubVisible));
            OnPropertyChanged(nameof(IsSectionVisible));
        }
    }
}

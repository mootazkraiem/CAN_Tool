using System;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Media3D;
using System.Windows.Threading;
using CANvision.Native.Models;
using CANvision.Native.Services;
using HelixToolkit.Wpf.SharpDX;
using HelixPerspectiveCamera = HelixToolkit.Wpf.SharpDX.PerspectiveCamera;

namespace CANvision.Native.Scene;

public partial class GarageScene : UserControl, IDisposable
{
    private static readonly Point3D FinalCameraPosition = new(1.36, 1.66, 10.65);
    private static readonly Vector3D FinalCameraLookDirection = new(-0.86, -0.2, -10.34);
    private static readonly Point3D IntroCameraPosition = new(1.7, 1.48, 12.65);
    private static readonly Vector3D IntroCameraLookDirection = new(-1.08, -0.05, -12.2);
    private static readonly Point3D OrbitTarget = new(
        FinalCameraPosition.X + FinalCameraLookDirection.X,
        FinalCameraPosition.Y + FinalCameraLookDirection.Y,
        FinalCameraPosition.Z + FinalCameraLookDirection.Z);

    private readonly DispatcherTimer frameTimer;
    private readonly Stopwatch introStopwatch = new();
    private readonly HelixPerspectiveCamera heroCamera = new()
    {
        UpDirection = new Vector3D(0, 1, 0),
        FieldOfView = 28.5,
    };
    private readonly IEffectsManager effectsManager = new DefaultEffectsManager();
    private CarRenderer? carRenderer;
    private Point lastPoint;
    private bool hasLoadedModel;
    private bool introCompleted;
    private bool introStarted;
    private bool isDragging;
    private double anchorYaw;
    private double anchorPitch;
    private double anchorRadius;
    private double currentYaw;
    private double currentPitch;
    private double currentRadius;
    private double targetYaw;
    private double targetPitch;
    private double targetRadius;
    private double idleTime;
    private bool isDisposed;
    private bool isRenderingActive = true;

    public GarageScene()
    {
        InitializeComponent();

        Viewport.Background = Brushes.Transparent;
        Viewport.Camera = heroCamera;
        Viewport.EffectsManager = effectsManager;
        Viewport.IsHitTestVisible = true;
        Viewport.EnableSwapChainRendering = false;
        var isOpaqueProperty = Viewport.GetType().GetProperty("IsOpaque");
        isOpaqueProperty?.SetValue(Viewport, false, null);

        ConfigureLighting();
        InitializeOrbitState();
        ApplyOrbitCamera();

        Loaded += OnLoaded;
        Unloaded += OnUnloaded;

        PreviewMouseLeftButtonDown += OnPreviewMouseLeftButtonDown;
        PreviewMouseMove += OnPreviewMouseMove;
        PreviewMouseLeftButtonUp += OnPreviewMouseLeftButtonUp;
        PreviewMouseWheel += OnPreviewMouseWheel;

        frameTimer = new DispatcherTimer(DispatcherPriority.Render)
        {
            Interval = TimeSpan.FromMilliseconds(16),
        };
        frameTimer.Tick += (_, _) => OnFrame();
    }

    public event EventHandler? IntroCompleted;

    public void Initialize(AppLogger appLogger)
    {
        carRenderer ??= new CarRenderer(CarNodeGroup, appLogger);
    }

    public void BeginIntro()
    {
        if (introStarted)
        {
            return;
        }

        introStarted = true;
        introStopwatch.Restart();
        carRenderer?.SetIntroProgress(0.0);
        heroCamera.Position = IntroCameraPosition;
        heroCamera.LookDirection = IntroCameraLookDirection;
        heroCamera.FieldOfView = 28.5;
    }

    public void SetSection(SectionKey key)
    {
        if (!introCompleted)
        {
            return;
        }

        ResetHeroView();
    }

    public void SetRenderingActive(bool isActive)
    {
        if (isDisposed)
        {
            return;
        }

        isRenderingActive = isActive;
        Visibility = isActive ? Visibility.Visible : Visibility.Collapsed;
        Viewport.Visibility = isActive ? Visibility.Visible : Visibility.Collapsed;
        IsHitTestVisible = isActive;

        if (!isActive)
        {
            frameTimer.Stop();
            return;
        }

        if (IsLoaded)
        {
            frameTimer.Start();
        }
    }

    private void ConfigureLighting()
    {
        Viewport.Items.Clear();
        Viewport.Items.Add(new AmbientLight3D
        {
            Color = Color.FromRgb(58, 64, 72),
        });
        Viewport.Items.Add(new DirectionalLight3D
        {
            Color = Color.FromRgb(248, 244, 236),
            Direction = new Vector3D(-1.25, -1.05, -0.52),
        });
        Viewport.Items.Add(new DirectionalLight3D
        {
            Color = Color.FromRgb(228, 234, 240),
            Direction = new Vector3D(1.08, -0.58, -0.78),
        });
        Viewport.Items.Add(new DirectionalLight3D
        {
            Color = Color.FromRgb(214, 222, 232),
            Direction = new Vector3D(-0.18, -0.28, 1.16),
        });
        Viewport.Items.Add(new DirectionalLight3D
        {
            Color = Color.FromRgb(200, 206, 214),
            Direction = new Vector3D(0.26, -0.94, 0.36),
        });
        Viewport.Items.Add(CarNodeGroup);
    }

    private void InitializeOrbitState()
    {
        var offset = FinalCameraPosition - OrbitTarget;
        var horizontal = Math.Sqrt((offset.X * offset.X) + (offset.Z * offset.Z));

        anchorYaw = Math.Atan2(offset.X, offset.Z) * 180.0 / Math.PI;
        anchorPitch = Math.Atan2(offset.Y, Math.Max(horizontal, 0.001)) * 180.0 / Math.PI;
        anchorRadius = offset.Length;
        currentYaw = anchorYaw;
        currentPitch = anchorPitch;
        currentRadius = anchorRadius;
        targetYaw = anchorYaw;
        targetPitch = anchorPitch;
        targetRadius = anchorRadius;
    }

    private void ResetHeroView()
    {
        idleTime = 0.0;
        InitializeOrbitState();
        ApplyOrbitCamera();
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        if (isRenderingActive)
        {
            frameTimer.Start();
        }

        if (!hasLoadedModel && carRenderer is not null)
        {
            hasLoadedModel = carRenderer.Load();
            carRenderer.SetIntroProgress(introStarted ? GetCarProgress() : 0.0);
        }
    }

    private void OnUnloaded(object sender, RoutedEventArgs e)
    {
        frameTimer.Stop();
    }

    public void Dispose()
    {
        if (isDisposed)
        {
            return;
        }

        isDisposed = true;
        frameTimer.Stop();
        Loaded -= OnLoaded;
        Unloaded -= OnUnloaded;
        PreviewMouseLeftButtonDown -= OnPreviewMouseLeftButtonDown;
        PreviewMouseMove -= OnPreviewMouseMove;
        PreviewMouseLeftButtonUp -= OnPreviewMouseLeftButtonUp;
        PreviewMouseWheel -= OnPreviewMouseWheel;

        if (IsMouseCaptured)
        {
            ReleaseMouseCapture();
        }

        CarNodeGroup.Clear();
        Viewport.Items.Clear();
        Viewport.EffectsManager = null;
        (effectsManager as IDisposable)?.Dispose();
    }

    private void OnPreviewMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (!introCompleted)
        {
            return;
        }

        CaptureMouse();
        isDragging = true;
        lastPoint = e.GetPosition(this);
        e.Handled = true;
    }

    private void OnPreviewMouseMove(object sender, MouseEventArgs e)
    {
        if (!introCompleted || !isDragging || e.LeftButton != MouseButtonState.Pressed)
        {
            return;
        }

        var point = e.GetPosition(this);
        var delta = point - lastPoint;
        targetYaw = Clamp(targetYaw - (delta.X * 0.18), anchorYaw - 22.0, anchorYaw + 22.0);
        targetPitch = Clamp(targetPitch - (delta.Y * 0.08), anchorPitch - 4.0, anchorPitch + 6.0);
        lastPoint = point;
    }

    private void OnPreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (!introCompleted)
        {
            return;
        }

        if (IsMouseCaptured)
        {
            ReleaseMouseCapture();
        }

        isDragging = false;
        anchorYaw = targetYaw;
        anchorPitch = targetPitch;
        anchorRadius = targetRadius;
        idleTime = 0.0;
    }

    private void OnPreviewMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (!introCompleted)
        {
            return;
        }

        targetRadius = Clamp(targetRadius - (e.Delta * 0.0016), anchorRadius - 0.55, anchorRadius + 0.85);
        anchorRadius = targetRadius;
        e.Handled = true;
    }

    private void OnFrame()
    {
        if (!introStarted)
        {
            return;
        }

        if (!introCompleted)
        {
            UpdateIntroFrame();
            return;
        }

        UpdateIdleCamera();
        carRenderer?.UpdateIdleRotation();
    }

    private void UpdateIntroFrame()
    {
        var introProgress = GetIntroProgress();
        var eased = EaseInOutCubic(introProgress);
        var cameraProgress = EaseOutCubic(GetCarProgress());

        heroCamera.Position = InterpolatePoint(IntroCameraPosition, FinalCameraPosition, cameraProgress);
        heroCamera.LookDirection = InterpolateVector(IntroCameraLookDirection, FinalCameraLookDirection, cameraProgress);
        heroCamera.FieldOfView = Lerp(28.5, 25.5, cameraProgress);
        carRenderer?.SetIntroProgress(eased);

        if (introProgress < 1.0)
        {
            return;
        }

        introCompleted = true;
        introStopwatch.Stop();
        heroCamera.Position = FinalCameraPosition;
        heroCamera.LookDirection = FinalCameraLookDirection;
        heroCamera.FieldOfView = 25.5;
        carRenderer?.SetIntroProgress(1.0);
        ResetHeroView();
        IntroCompleted?.Invoke(this, EventArgs.Empty);
    }

    private void UpdateIdleCamera()
    {
        if (!isDragging)
        {
            idleTime += frameTimer.Interval.TotalSeconds;
            targetYaw = anchorYaw + (Math.Sin(idleTime * 0.52) * 0.92);
            targetPitch = anchorPitch + (Math.Cos(idleTime * 0.28) * 0.14);
            targetRadius = anchorRadius + (Math.Sin(idleTime * 0.16) * 0.04);
        }

        currentYaw += (targetYaw - currentYaw) * 0.18;
        currentPitch += (targetPitch - currentPitch) * 0.18;
        currentRadius += (targetRadius - currentRadius) * 0.16;
        ApplyOrbitCamera();
    }

    private void ApplyOrbitCamera()
    {
        var yawRadians = currentYaw * Math.PI / 180.0;
        var pitchRadians = currentPitch * Math.PI / 180.0;
        var horizontal = currentRadius * Math.Cos(pitchRadians);
        var vertical = currentRadius * Math.Sin(pitchRadians);

        var position = new Point3D(
            OrbitTarget.X + (Math.Sin(yawRadians) * horizontal),
            OrbitTarget.Y + vertical,
            OrbitTarget.Z + (Math.Cos(yawRadians) * horizontal));

        heroCamera.Position = position;
        heroCamera.LookDirection = OrbitTarget - position;
        heroCamera.FieldOfView = 25.5;
    }

    private double GetIntroProgress()
    {
        if (!introStarted)
        {
            return 0.0;
        }

        return Clamp(introStopwatch.Elapsed.TotalMilliseconds / 1500.0, 0.0, 1.0);
    }

    private double GetCarProgress()
    {
        var elapsed = introStopwatch.Elapsed.TotalMilliseconds;
        return Clamp((elapsed - 600.0) / 800.0, 0.0, 1.0);
    }

    private static Point3D InterpolatePoint(Point3D from, Point3D to, double progress)
    {
        return new Point3D(
            Lerp(from.X, to.X, progress),
            Lerp(from.Y, to.Y, progress),
            Lerp(from.Z, to.Z, progress));
    }

    private static Vector3D InterpolateVector(Vector3D from, Vector3D to, double progress)
    {
        return new Vector3D(
            Lerp(from.X, to.X, progress),
            Lerp(from.Y, to.Y, progress),
            Lerp(from.Z, to.Z, progress));
    }

    private static double Lerp(double from, double to, double progress)
    {
        return from + ((to - from) * progress);
    }

    private static double Clamp(double value, double min, double max)
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

    private static double EaseOutCubic(double value)
    {
        var inverse = 1.0 - value;
        return 1.0 - (inverse * inverse * inverse);
    }

    private static double EaseInOutCubic(double value)
    {
        if (value < 0.5)
        {
            return 4.0 * value * value * value;
        }

        var inverse = -2.0 * value + 2.0;
        return 1.0 - ((inverse * inverse * inverse) / 2.0);
    }
}

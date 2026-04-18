using System;
using System.Windows;
using System.Windows.Media.Media3D;
using CANvision.Native.Models;
using HelixToolkit.Wpf.SharpDX;
using HelixPerspectiveCamera = HelixToolkit.Wpf.SharpDX.PerspectiveCamera;

namespace CANvision.Native.Scene;

public sealed class CameraController
{
    private const double IdleDeltaSeconds = 1.0 / 60.0;

    private double anchorYaw;
    private double anchorPitch;
    private double anchorDistance;
    private double idleTimer;
    private Point lastPoint;
    private bool isDragging;
    private double currentYaw;
    private double targetYaw;
    private double currentPitch;
    private double targetPitch;
    private double currentDistance;
    private double targetDistance;

    public CameraController()
    {
        Camera = new HelixPerspectiveCamera
        {
            FieldOfView = 32,
            UpDirection = new Vector3D(0, 1, 0),
        };
        SetSection(SectionKey.Dashboard, immediate: true);
        Update();
    }

    public HelixPerspectiveCamera Camera { get; }

    public void Reset()
    {
        SetSection(SectionKey.Dashboard, immediate: true);
        Update();
    }

    public void Update()
    {
        if (!isDragging)
        {
            idleTimer += IdleDeltaSeconds;
            targetYaw = anchorYaw + (Math.Sin(idleTimer * 0.45) * 5.4);
            targetPitch = Clamp(anchorPitch + (Math.Cos(idleTimer * 0.24) * 0.55), 4.0, 19.0);
            targetDistance = Clamp(anchorDistance + (Math.Sin(idleTimer * 0.18) * 0.16), 6.4, 12.5);
        }

        currentYaw += (targetYaw - currentYaw) * 0.16;
        currentPitch += (targetPitch - currentPitch) * 0.18;
        currentDistance += (targetDistance - currentDistance) * 0.18;

        var yawRadians = currentYaw * Math.PI / 180.0;
        var pitchRadians = currentPitch * Math.PI / 180.0;
        var horizontal = currentDistance * Math.Cos(pitchRadians);

        var target = new Point3D(0, 0.78, 0);
        var position = new Point3D(
            Math.Sin(yawRadians) * horizontal,
            1.05 + Math.Sin(pitchRadians) * currentDistance,
            Math.Cos(yawRadians) * horizontal);

        Camera.Position = position;
        Camera.LookDirection = target - position;
    }

    public void SetSection(SectionKey key, bool immediate = false)
    {
        (anchorYaw, anchorPitch, anchorDistance) = key switch
        {
            SectionKey.Home => (16.0, 8.5, 8.4),
            SectionKey.Dashboard => (16.0, 8.5, 8.4),
            SectionKey.Telemetry => (44.0, 10.4, 7.6),
            SectionKey.Diagnostics => (-12.0, 11.2, 7.4),
            SectionKey.LogPlayback => (94.0, 7.8, 8.9),
            SectionKey.Analytics => (148.0, 9.4, 8.0),
            SectionKey.Settings => (208.0, 7.0, 9.5),
            _ => (16.0, 8.5, 8.4),
        };

        idleTimer = 0.0;
        targetYaw = anchorYaw;
        targetPitch = anchorPitch;
        targetDistance = anchorDistance;

        if (immediate)
        {
            currentYaw = targetYaw;
            currentPitch = targetPitch;
            currentDistance = targetDistance;
        }
    }

    public void BeginDrag(Point point)
    {
        isDragging = true;
        lastPoint = point;
    }

    public void DragTo(Point point)
    {
        if (!isDragging)
        {
            return;
        }

        var delta = point - lastPoint;
        targetYaw -= delta.X * 0.38;
        targetPitch = Clamp(targetPitch - (delta.Y * 0.12), 4.0, 19.0);
        lastPoint = point;
    }

    public void EndDrag()
    {
        isDragging = false;
        anchorYaw = targetYaw;
        anchorPitch = targetPitch;
    }

    public void Zoom(double delta)
    {
        targetDistance = Clamp(targetDistance - (delta * 0.0015), 6.4, 12.5);
        anchorDistance = targetDistance;
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
}

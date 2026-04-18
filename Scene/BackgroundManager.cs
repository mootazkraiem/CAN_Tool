using System;
using System.IO;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using CANvision.Native.Services;

namespace CANvision.Native.Scene;

public sealed class BackgroundManager
{
    private const string BackgroundFileName = "ChatGPT Image 9 avr. 2026, 14_31_30.png";

    private readonly AppLogger logger;

    public BackgroundManager(AppLogger logger)
    {
        this.logger = logger;
    }

    public ImageSource? LoadBackgroundImage()
    {
        var backgroundPath = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory,
            "assets",
            BackgroundFileName);

        if (!File.Exists(backgroundPath))
        {
            logger.Error($"Background image not found at {backgroundPath}.");
            return null;
        }

        var bitmap = new BitmapImage();
        bitmap.BeginInit();
        bitmap.CacheOption = BitmapCacheOption.OnLoad;
        bitmap.UriSource = new Uri(backgroundPath);
        bitmap.EndInit();
        bitmap.Freeze();

        logger.Info($"Background image loaded from {backgroundPath}.");
        return bitmap;
    }
}

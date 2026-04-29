using CANvision.Native.Services;

namespace CANvision.Native.Scene;

public sealed class BackgroundManager
{
    private readonly AppLogger logger;

    public BackgroundManager(AppLogger logger)
    {
        this.logger = logger;
    }

    public void LogDisabled()
    {
        logger.Info("Static garage background disabled. 3D scene is the primary backdrop.");
    }
}

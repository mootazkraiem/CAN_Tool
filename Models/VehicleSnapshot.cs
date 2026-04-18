using Newtonsoft.Json;

namespace CANvision.Native.Models;

public sealed class VehicleSnapshot
{
    [JsonProperty("battery")]
    public int Battery { get; set; }

    [JsonProperty("temperature")]
    public int Temperature { get; set; }

    [JsonProperty("motor_status")]
    public string MotorStatus { get; set; } = "UNKNOWN";

    [JsonProperty("source")]
    public string Source { get; set; } = "offline";

    [JsonProperty("updated_at")]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public static VehicleSnapshot Default() =>
        new()
        {
            Battery = 92,
            Temperature = 41,
            MotorStatus = "OK",
            Source = "bootstrap",
            UpdatedAt = DateTime.UtcNow,
        };
}

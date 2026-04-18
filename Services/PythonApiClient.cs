using System;
using System.IO;
using System.Net.Http;
using CANvision.Native.Models;
using Newtonsoft.Json;

namespace CANvision.Native.Services;

public sealed class PythonApiClient
{
    private const string DefaultEndpoint = "http://127.0.0.1:8765/vehicle";

    private readonly HttpClient httpClient = new();
    private readonly AppLogger logger;
    private readonly string endpoint;
    private readonly string jsonFallbackPath;

    public PythonApiClient(AppLogger logger)
    {
        this.logger = logger;
        endpoint = Environment.GetEnvironmentVariable("CANVISION_PYTHON_API") ?? DefaultEndpoint;
        jsonFallbackPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "vehicle-state.json");
    }

    public string Endpoint => endpoint;

    public string JsonFallbackPath => jsonFallbackPath;

    public async Task<VehicleSnapshot?> GetLatestSnapshotAsync(CancellationToken cancellationToken)
    {
        var fromApi = await TryFetchFromApiAsync(cancellationToken);
        if (fromApi is not null)
        {
            return fromApi;
        }

        return await TryFetchFromFileAsync(cancellationToken);
    }

    private async Task<VehicleSnapshot?> TryFetchFromApiAsync(CancellationToken cancellationToken)
    {
        try
        {
            using var response = await httpClient.GetAsync(endpoint, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                logger.Info($"Python API returned {(int)response.StatusCode}; falling back to local JSON.");
                return null;
            }

            var json = await response.Content.ReadAsStringAsync();
            var snapshot = JsonConvert.DeserializeObject<VehicleSnapshot>(json);
            if (snapshot is null)
            {
                logger.Info("Python API returned empty payload; falling back to local JSON.");
                return null;
            }

            snapshot.Source = string.IsNullOrWhiteSpace(snapshot.Source) ? "python-api" : snapshot.Source;
            if (snapshot.UpdatedAt == default)
            {
                snapshot.UpdatedAt = DateTime.UtcNow;
            }

            return snapshot;
        }
        catch (Exception exception)
        {
            logger.Error($"Python API fetch failed at {endpoint}.", exception);
            return null;
        }
    }

    private async Task<VehicleSnapshot?> TryFetchFromFileAsync(CancellationToken cancellationToken)
    {
        try
        {
            if (!File.Exists(jsonFallbackPath))
            {
                logger.Info($"Fallback JSON not found at {jsonFallbackPath}.");
                return null;
            }

            var json = await Task.Run(() => File.ReadAllText(jsonFallbackPath), cancellationToken);
            var snapshot = JsonConvert.DeserializeObject<VehicleSnapshot>(json);
            if (snapshot is null)
            {
                logger.Info("Fallback JSON was present but empty.");
                return null;
            }

            snapshot.Source = string.IsNullOrWhiteSpace(snapshot.Source) ? "json-fallback" : snapshot.Source;
            if (snapshot.UpdatedAt == default)
            {
                snapshot.UpdatedAt = DateTime.UtcNow;
            }

            return snapshot;
        }
        catch (Exception exception)
        {
            logger.Error($"Fallback JSON read failed at {jsonFallbackPath}.", exception);
            return null;
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Net.Http;
using CANvision.Native.Models;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace CANvision.Native.Services;

public sealed class PythonApiClient
{
    private const string DefaultEndpoint = "http://127.0.0.1:8765/vehicle";

    private readonly HttpClient httpClient = new();
    private readonly AppLogger logger;
    private readonly string endpoint;
    private readonly string apiBase;
    private readonly string jsonFallbackPath;

    public PythonApiClient(AppLogger logger)
    {
        this.logger = logger;
        endpoint = Environment.GetEnvironmentVariable("CANVISION_PYTHON_API") ?? DefaultEndpoint;
        apiBase = BuildApiBase(endpoint);
        jsonFallbackPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "vehicle-state.json");
    }

    public string Endpoint => endpoint;
    public string ApiBase => apiBase;

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

    public async Task<PythonHealthResponse?> GetHealthAsync(CancellationToken cancellationToken)
    {
        return await GetJsonAsync<PythonHealthResponse>("health", cancellationToken);
    }

    public async Task<PythonMetricsResponse?> GetMetricsAsync(CancellationToken cancellationToken)
    {
        return await GetJsonAsync<PythonMetricsResponse>("metrics", cancellationToken);
    }

    public async Task<PythonAnalyzeResponse?> AnalyzeLogsAsync(IEnumerable<string> filePaths, CancellationToken cancellationToken)
    {
        var files = (filePaths ?? Enumerable.Empty<string>())
            .Where(path => !string.IsNullOrWhiteSpace(path) && File.Exists(path))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (files.Count == 0)
        {
            logger.Info("AnalyzeLogsAsync called with no valid files.");
            return null;
        }

        try
        {
            using var multipart = new MultipartFormDataContent();
            foreach (var file in files)
            {
                var bytes = await Task.Run(() => File.ReadAllBytes(file), cancellationToken);
                var part = new ByteArrayContent(bytes);
                part.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
                multipart.Add(part, "files", Path.GetFileName(file));
            }

            using var response = await httpClient.PostAsync(BuildUrl("analyze"), multipart, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                logger.Info($"Python analyze endpoint returned {(int)response.StatusCode}.");
                return null;
            }

            var json = await response.Content.ReadAsStringAsync();
            var payload = JsonConvert.DeserializeObject<PythonAnalyzeResponse>(json);
            return payload;
        }
        catch (Exception exception)
        {
            logger.Error("AnalyzeLogsAsync failed.", exception);
            return null;
        }
    }

    public async Task<MlInferenceResult?> ScoreFeatureVectorAsync(IReadOnlyList<double> featureVector, CancellationToken cancellationToken)
    {
        try
        {
            var payload = new JObject
            {
                ["features"] = new JArray(featureVector.ToArray())
            };

            using var content = new StringContent(payload.ToString(Formatting.None), Encoding.UTF8, "application/json");
            using var response = await httpClient.PostAsync(BuildUrl("infer"), content, cancellationToken);
            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var parsed = JsonConvert.DeserializeObject<PythonInferenceResponse>(json);
                if (parsed is not null)
                {
                    return new MlInferenceResult(parsed.AnomalyScore, parsed.AnomalyLabel, Math.Min(100, Math.Abs(parsed.AnomalyScore) * 100.0));
                }
            }
        }
        catch (Exception exception)
        {
            logger.Error("Feature-vector inference endpoint failed; using local fallback scoring.", exception);
        }

        var fallbackScore = BuildFallbackAnomalyScore(featureVector);
        var label = fallbackScore >= 0.55 ? "anomaly" : "normal";
        return new MlInferenceResult(fallbackScore, label, Math.Min(100, fallbackScore * 100.0));
    }

    private async Task<VehicleSnapshot?> TryFetchFromApiAsync(CancellationToken cancellationToken)
    {
        try
        {
            using var response = await httpClient.GetAsync(BuildUrl("vehicle"), cancellationToken);
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

    private async Task<T?> GetJsonAsync<T>(string relativePath, CancellationToken cancellationToken)
    {
        try
        {
            using var response = await httpClient.GetAsync(BuildUrl(relativePath), cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                logger.Info($"Python API {relativePath} returned {(int)response.StatusCode}.");
                return default;
            }

            var json = await response.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<T>(json);
        }
        catch (Exception exception)
        {
            logger.Error($"Python API request failed for {relativePath}.", exception);
            return default;
        }
    }

    private string BuildUrl(string relativePath)
    {
        var clean = relativePath.Trim('/');
        return $"{apiBase}/{clean}";
    }

    private static string BuildApiBase(string configuredEndpoint)
    {
        if (!Uri.TryCreate(configuredEndpoint, UriKind.Absolute, out var uri))
        {
            return "http://127.0.0.1:8765";
        }

        var authority = $"{uri.Scheme}://{uri.Authority}";
        var path = uri.AbsolutePath.TrimEnd('/').ToLowerInvariant();
        if (path.EndsWith("/vehicle"))
        {
            return authority;
        }

        return $"{authority}{uri.AbsolutePath.TrimEnd('/')}";
    }

    private static double BuildFallbackAnomalyScore(IReadOnlyList<double> featureVector)
    {
        if (featureVector.Count == 0)
        {
            return 0;
        }

        var socRisk = featureVector.ElementAtOrDefault(0) < 0.15 ? 0.22 : 0.0;
        var voltageRisk = featureVector.ElementAtOrDefault(1) < 0.29 ? 0.24 : 0.0;
        var tempRisk = featureVector.ElementAtOrDefault(2) > 0.62 ? 0.26 : 0.0;
        var currentRisk = Math.Abs(featureVector.ElementAtOrDefault(3) - 0.5) > 0.45 ? 0.18 : 0.0;
        var rpmRisk = featureVector.ElementAtOrDefault(4) > 0.78 ? 0.18 : 0.0;
        var speedRisk = featureVector.ElementAtOrDefault(5) > 0.84 ? 0.12 : 0.0;
        return Math.Min(1.0, socRisk + voltageRisk + tempRisk + currentRisk + rpmRisk + speedRisk);
    }
}

public sealed class MlInferenceResult
{
    public MlInferenceResult(double score, string label, double severityScore)
    {
        Score = score;
        Label = label;
        SeverityScore = severityScore;
    }

    public double Score { get; }
    public string Label { get; }
    public double SeverityScore { get; }
}

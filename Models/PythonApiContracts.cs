using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace CANvision.Native.Models;

public sealed class PythonHealthResponse
{
    [JsonProperty("status")]
    public string Status { get; set; } = string.Empty;

    [JsonProperty("service")]
    public string Service { get; set; } = string.Empty;

    [JsonProperty("timestamp")]
    public string Timestamp { get; set; } = string.Empty;
}

public sealed class PythonMetricsResponse
{
    [JsonProperty("status")]
    public string Status { get; set; } = string.Empty;

    [JsonProperty("uptime_seconds")]
    public double UptimeSeconds { get; set; }

    [JsonProperty("requests_total")]
    public int RequestsTotal { get; set; }

    [JsonProperty("analyze_requests_total")]
    public int AnalyzeRequestsTotal { get; set; }

    [JsonProperty("analyzed_rows_total")]
    public int AnalyzedRowsTotal { get; set; }

    [JsonProperty("anomalies_total")]
    public int AnomaliesTotal { get; set; }

    [JsonProperty("avg_analyze_latency_ms")]
    public double AvgAnalyzeLatencyMs { get; set; }

    [JsonProperty("model_loaded")]
    public bool ModelLoaded { get; set; }

    [JsonProperty("model_clusters")]
    public int ModelClusters { get; set; }
}

public sealed class PythonAnalyzeSummary
{
    [JsonProperty("files_received")]
    public int FilesReceived { get; set; }

    [JsonProperty("rows_parsed")]
    public int RowsParsed { get; set; }

    [JsonProperty("anomaly_count")]
    public int AnomalyCount { get; set; }

    [JsonProperty("normal_count")]
    public int NormalCount { get; set; }

    [JsonProperty("cluster_count")]
    public int ClusterCount { get; set; }

    [JsonProperty("parse_lines_total")]
    public int ParseLinesTotal { get; set; }

    [JsonProperty("parse_lines_parsed")]
    public int ParseLinesParsed { get; set; }

    [JsonProperty("parse_lines_skipped")]
    public int ParseLinesSkipped { get; set; }

    [JsonProperty("elapsed_ms")]
    public double ElapsedMs { get; set; }
}

public sealed class PythonAnalyzeItem
{
    [JsonProperty("context")]
    public JObject Context { get; set; } = new();

    [JsonProperty("explanation")]
    public JObject Explanation { get; set; } = new();
}

public sealed class PythonAnalyzeResponse
{
    [JsonProperty("summary")]
    public PythonAnalyzeSummary? Summary { get; set; }

    [JsonProperty("anomalies")]
    public List<PythonAnalyzeItem> Anomalies { get; set; } = new();
}

public sealed class PythonInferenceResponse
{
    [JsonProperty("anomaly_score")]
    public double AnomalyScore { get; set; }

    [JsonProperty("anomaly_label")]
    public string AnomalyLabel { get; set; } = "normal";
}

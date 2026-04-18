using System;
using System.IO;
using System.Windows;
using System.Windows.Media.Media3D;
using Assimp;
using CANvision.Native.Services;
using HelixToolkit.Wpf.SharpDX;
using HelixToolkit.Wpf.SharpDX.Assimp;
using HelixToolkit.Wpf.SharpDX.Model;
using HelixToolkit.Wpf.SharpDX.Model.Scene;
using SharpDX;

namespace CANvision.Native.Scene;

public sealed class CarRenderer
{
    private static readonly PostProcessSteps ImportSteps =
        PostProcessSteps.Triangulate |
        PostProcessSteps.JoinIdenticalVertices |
        PostProcessSteps.GenerateSmoothNormals |
        PostProcessSteps.ImproveCacheLocality |
        PostProcessSteps.CalculateTangentSpace;
    private static readonly Vector3 HeroCarOffset = new(0.52f, -1.34f, 0.0f);

    private readonly SceneNodeGroupModel3D host;
    private readonly AppLogger logger;
    private readonly AxisAngleRotation3D heroRotation = new(new System.Windows.Media.Media3D.Vector3D(0, 1, 0), -32);
    private readonly AxisAngleRotation3D idleRotation = new(new System.Windows.Media.Media3D.Vector3D(0, 1, 0), 0);
    private readonly Transform3DGroup transformGroup = new Transform3DGroup();
    private readonly ScaleTransform3D scaleTransform = new();
    private readonly TranslateTransform3D centerTransform = new();
    private readonly TranslateTransform3D heroOffsetTransform = new();
    private readonly TranslateTransform3D introTransform = new();
    private readonly string[] glassMaterialNames = ["GlassMtl", "GlassMtl.002", "GlassRed.002", "GlassAmber.002", "Mirror"];
    private bool modelLoaded;
    private double introProgress;
    private DateTime lastTickUtc = DateTime.UtcNow;

    public CarRenderer(SceneNodeGroupModel3D host, AppLogger logger)
    {
        this.host = host;
        this.logger = logger;
        transformGroup.Children.Add(scaleTransform);
        transformGroup.Children.Add(centerTransform);
        transformGroup.Children.Add(new RotateTransform3D(heroRotation));
        transformGroup.Children.Add(new RotateTransform3D(idleRotation));
        transformGroup.Children.Add(heroOffsetTransform);
        transformGroup.Children.Add(introTransform);
        host.Transform = transformGroup;
    }

    public bool Load()
    {
        var gltfPath = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory,
            "assets",
            "toyota_supra_mk4_a80",
            "scene.gltf");

        var texturesPath = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory,
            "assets",
            "toyota_supra_mk4_a80",
            "textures");

        logger.Info($"Preparing native car load from {gltfPath}.");
        logger.Info($"Textures expected in {texturesPath}.");

        if (!File.Exists(gltfPath))
        {
            logger.Error($"Car model not found at {gltfPath}.");
            host.Visibility = Visibility.Collapsed;
            return false;
        }

        if (!Directory.Exists(texturesPath))
        {
            logger.Error($"Texture directory not found at {texturesPath}.");
        }

        if (TryLoadWithHelix(gltfPath))
        {
            return true;
        }

        if (TryLoadWithAssimpFallback(gltfPath))
        {
            return true;
        }

        host.Visibility = Visibility.Collapsed;
        logger.Error("All native car loading strategies failed. The 3D model layer has been hidden.");
        return false;
    }

    public void UpdateIdleRotation()
    {
        if (!modelLoaded || introProgress < 0.999)
        {
            return;
        }

        var now = DateTime.UtcNow;
        var deltaSeconds = (now - lastTickUtc).TotalSeconds;
        lastTickUtc = now;
        idleRotation.Angle = (idleRotation.Angle + (deltaSeconds * 5.6)) % 360.0;
    }

    public void SetIntroProgress(double progress)
    {
        introProgress = Clamp((float)progress, 0.0f, 1.0f);
        if (!modelLoaded)
        {
            return;
        }

        var eased = EaseOutCubic(introProgress);
        introTransform.OffsetX = 0.0;
        introTransform.OffsetY = Lerp(-0.34, 0.0, eased);
        introTransform.OffsetZ = Lerp(-0.52, 0.0, eased);

        if (introProgress < 0.999)
        {
            idleRotation.Angle = 0.0;
        }
    }

    private bool TryLoadWithHelix(string modelPath)
    {
        try
        {
            using var importer = new Importer();
            var scene = importer.Load(modelPath);
            if (scene?.Root is null)
            {
                throw new InvalidOperationException("HelixToolkit returned an empty scene.");
            }

            var bounds = CalculateBounds(modelPath);
            ApplyPlacement(bounds);
            host.AddNode(scene.Root);
            host.Visibility = Visibility.Visible;
            modelLoaded = true;
            logger.Info($"HelixToolkit loaded car model successfully from {modelPath}.");
            return true;
        }
        catch (Exception exception)
        {
            logger.Error($"HelixToolkit native load failed for {modelPath}.", exception);
            return false;
        }
    }

    private bool TryLoadWithAssimpFallback(string modelPath)
    {
        try
        {
            using var assimpContext = new AssimpContext();
            var assimpScene = assimpContext.ImportFile(modelPath, ImportSteps);
            if (assimpScene is null || assimpScene.MeshCount == 0)
            {
                throw new InvalidOperationException("AssimpNet returned an empty scene.");
            }

            logger.Info("AssimpNet successfully imported the GLTF scene. Exporting OBJ cache fallback.");

            var cacheDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "cache");
            Directory.CreateDirectory(cacheDirectory);
            var cachedObjPath = Path.Combine(cacheDirectory, "toyota_supra_mk4_a80.obj");
            var texturesPath = Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory,
                "assets",
                "toyota_supra_mk4_a80",
                "textures");

            if (!File.Exists(cachedObjPath))
            {
                assimpContext.ExportFile(assimpScene, cachedObjPath, "obj");
                CopyTextureCache(texturesPath, Path.Combine(cacheDirectory, "textures"));
                logger.Info($"OBJ cache generated at {cachedObjPath}.");
            }
            else
            {
                logger.Info($"Reusing cached OBJ at {cachedObjPath}.");
            }

            return TryLoadWithHelix(cachedObjPath);
        }
        catch (Exception exception)
        {
            logger.Error("AssimpNet fallback import/export failed.", exception);
            return false;
        }
    }

    private void CopyTextureCache(string sourceTexturesPath, string destinationTexturesPath)
    {
        if (!Directory.Exists(sourceTexturesPath))
        {
            logger.Error($"Texture source directory missing during OBJ cache export: {sourceTexturesPath}.");
            return;
        }

        Directory.CreateDirectory(destinationTexturesPath);
        foreach (var texturePath in Directory.GetFiles(sourceTexturesPath))
        {
            var fileName = Path.GetFileName(texturePath);
            var destinationPath = Path.Combine(destinationTexturesPath, fileName);
            File.Copy(texturePath, destinationPath, overwrite: true);
        }

        logger.Info($"Texture cache refreshed in {destinationTexturesPath}.");
    }

    private ModelBounds CalculateBounds(string modelPath)
    {
        using var assimpContext = new AssimpContext();
        var assimpScene = assimpContext.ImportFile(modelPath, ImportSteps);
        if (assimpScene is null || assimpScene.MeshCount == 0)
        {
            throw new InvalidOperationException("Bounds calculation failed because Assimp returned no meshes.");
        }

        var minX = double.PositiveInfinity;
        var minY = double.PositiveInfinity;
        var minZ = double.PositiveInfinity;
        var maxX = double.NegativeInfinity;
        var maxY = double.NegativeInfinity;
        var maxZ = double.NegativeInfinity;

        foreach (var mesh in assimpScene.Meshes)
        {
            foreach (var vertex in mesh.Vertices)
            {
                minX = Math.Min(minX, vertex.X);
                minY = Math.Min(minY, vertex.Y);
                minZ = Math.Min(minZ, vertex.Z);
                maxX = Math.Max(maxX, vertex.X);
                maxY = Math.Max(maxY, vertex.Y);
                maxZ = Math.Max(maxZ, vertex.Z);
            }
        }

        return new ModelBounds(minX, minY, minZ, maxX, maxY, maxZ);
    }

    private void ApplyPlacement(ModelBounds bounds)
    {
        var sizeX = bounds.MaxX - bounds.MinX;
        var sizeY = bounds.MaxY - bounds.MinY;
        var sizeZ = bounds.MaxZ - bounds.MinZ;
        var maxDimension = Math.Max(sizeX, Math.Max(sizeY, sizeZ));
        var scale = 5.2 / Math.Max(maxDimension, 0.001);
        var centerX = (bounds.MinX + bounds.MaxX) * 0.5;
        var centerZ = (bounds.MinZ + bounds.MaxZ) * 0.5;
        var groundAlignment = -bounds.MinY * scale;

        scaleTransform.ScaleX = scale;
        scaleTransform.ScaleY = scale;
        scaleTransform.ScaleZ = scale;
        centerTransform.OffsetX = -centerX * scale;
        centerTransform.OffsetY = groundAlignment;
        centerTransform.OffsetZ = -centerZ * scale;
        heroOffsetTransform.OffsetX = HeroCarOffset.X;
        heroOffsetTransform.OffsetY = HeroCarOffset.Y;
        heroOffsetTransform.OffsetZ = HeroCarOffset.Z;
        SetIntroProgress(introProgress);

        logger.Info(
            $"Car placement applied. Scale={scale:F3}, CenterX={-centerX * scale:F3}, GroundY={groundAlignment:F3}, CenterZ={-centerZ * scale:F3}, HeroOffset=({HeroCarOffset.X:F2}, {HeroCarOffset.Y:F2}, {HeroCarOffset.Z:F2}), HeroYaw=-32.");
    }

    private void TuneImportedMaterials(SceneNode root)
    {
        var meshNodes = SceneNodeExtensions.GetSceneNodeByType<MeshNode>(root);
        foreach (var meshNode in meshNodes)
        {
            var nodeName = meshNode.Name ?? string.Empty;
            switch (meshNode.Material)
            {
                case PBRMaterialCore pbrMaterial:
                    TunePbrMaterial(nodeName, pbrMaterial);
                    break;
                case PhongMaterialCore phongMaterial:
                    TunePhongMaterial(nodeName, phongMaterial);
                    break;
            }
        }

        logger.Info($"Retuned {meshNodes.Count} imported mesh materials for the glossy showroom lighting profile.");
    }

    private void TunePbrMaterial(string nodeName, PBRMaterialCore material)
    {
        var name = material.Name ?? string.Empty;

        if (IsPaintMaterial(name))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.62f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.58f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor * 0.82f : 0.14f, 0.08f, 0.28f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.82f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.12f, 0.05f, 0.18f);
            material.RenderEnvironmentMap = true;
            material.RenderIrradianceMap = true;
            return;
        }

        if (IsHeadlightMaterial(name, nodeName))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.04f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.72f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor * 0.75f : 0.08f, 0.04f, 0.18f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.64f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.09f, 0.05f, 0.14f);
            material.RenderEnvironmentMap = true;
            material.RenderEmissiveMap = true;
            return;
        }

        if (IsCarbonPanel(name, nodeName))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.08f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.36f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor : 0.22f, 0.14f, 0.34f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.18f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.18f, 0.12f, 0.24f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsWheelLipMaterial(name, nodeName))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.82f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.7f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor * 0.88f : 0.11f, 0.05f, 0.18f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.22f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.12f, 0.08f, 0.18f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsWheelBarrelMaterial(name, nodeName))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.68f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.54f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor : 0.16f, 0.1f, 0.24f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsGlassMaterial(name))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.01f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.62f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor * 0.85f : 0.1f, 0.04f, 0.16f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.16f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.1f, 0.06f, 0.16f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsBodyTrimMaterial(name))
        {
            material.MetallicFactor = Clamp(Math.Max(material.MetallicFactor, 0.2f), 0.0f, 1.0f);
            material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.42f), 0.0f, 1.0f);
            material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor : 0.2f, 0.12f, 0.28f);
            material.ClearCoatStrength = Clamp(Math.Max(material.ClearCoatStrength, 0.12f), 0.0f, 1.0f);
            material.ClearCoatRoughness = Clamp(material.ClearCoatRoughness > 0.0f ? material.ClearCoatRoughness : 0.16f, 0.1f, 0.2f);
            material.RenderEnvironmentMap = true;
            return;
        }

        material.RoughnessFactor = Clamp(material.RoughnessFactor > 0.0f ? material.RoughnessFactor * 0.9f : 0.24f, 0.08f, 0.62f);
        material.ReflectanceFactor = Clamp(Math.Max(material.ReflectanceFactor, 0.3f), 0.0f, 1.0f);
        material.RenderEnvironmentMap = true;
    }

    private void TunePhongMaterial(string nodeName, PhongMaterialCore material)
    {
        var name = material.Name ?? string.Empty;

        if (IsPaintMaterial(name))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 148f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsHeadlightMaterial(name, nodeName))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 164f);
            material.RenderEnvironmentMap = true;
            material.RenderEmissiveMap = true;
            return;
        }

        if (IsCarbonPanel(name, nodeName))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 108f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsWheelLipMaterial(name, nodeName))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 156f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsWheelBarrelMaterial(name, nodeName))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 132f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsGlassMaterial(name))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 136f);
            material.RenderEnvironmentMap = true;
            return;
        }

        if (IsBodyTrimMaterial(name))
        {
            material.SpecularShininess = Math.Max(material.SpecularShininess, 104f);
            material.RenderEnvironmentMap = true;
            return;
        }

        material.SpecularShininess = Math.Max(material.SpecularShininess, 84f);
        material.RenderEnvironmentMap = true;
    }

    private bool IsGlassMaterial(string materialName)
    {
        foreach (var glassMaterialName in glassMaterialNames)
        {
            if (string.Equals(materialName, glassMaterialName, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    private static bool IsPaintMaterial(string materialName)
    {
        return string.Equals(materialName, "Paint", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsHeadlightMaterial(string materialName, string nodeName)
    {
        return ContainsIgnoreCase(materialName, "Light") || ContainsIgnoreCase(nodeName, "LIGHT");
    }

    private static bool IsCarbonPanel(string materialName, string nodeName)
    {
        return ContainsIgnoreCase(materialName, "Carbon") ||
               ContainsIgnoreCase(materialName, "EngineA") ||
               ContainsIgnoreCase(materialName, "Hood3BGrille1") ||
               ContainsIgnoreCase(materialName, "TexturedA") ||
               ContainsIgnoreCase(nodeName, "HoodCarbon") ||
               ContainsIgnoreCase(nodeName, "CARBONENG") ||
               ContainsIgnoreCase(nodeName, "ENGINE") ||
               ContainsIgnoreCase(nodeName, "HoodGrille1");
    }

    private static bool IsWheelLipMaterial(string materialName, string nodeName)
    {
        return ContainsIgnoreCase(materialName, "DISK1") ||
               ContainsIgnoreCase(materialName, "DISK2") ||
               ContainsIgnoreCase(nodeName, "_DISK1_") ||
               ContainsIgnoreCase(nodeName, "_DISK2_");
    }

    private static bool IsWheelBarrelMaterial(string materialName, string nodeName)
    {
        return ContainsIgnoreCase(materialName, "Wheel2A") || ContainsIgnoreCase(nodeName, "_Wheel2A_");
    }

    private static bool IsBodyTrimMaterial(string materialName)
    {
        return ContainsIgnoreCase(materialName, "Base.002") ||
               ContainsIgnoreCase(materialName, "Coloured.002") ||
               ContainsIgnoreCase(materialName, "Coloured.003");
    }

    private static bool ContainsIgnoreCase(string value, string token)
    {
        return value.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private static Color4 MultiplyRgb(Color4 color, float multiplier)
    {
        return new Color4(
            Clamp(color.Red * multiplier, 0.0f, 1.0f),
            Clamp(color.Green * multiplier, 0.0f, 1.0f),
            Clamp(color.Blue * multiplier, 0.0f, 1.0f),
            color.Alpha);
    }

    private static Color4 PreserveAlpha(float red, float green, float blue, float alpha)
    {
        return new Color4(red, green, blue, Clamp(alpha, 0.0f, 1.0f));
    }

    private static float Clamp(float value, float min, float max)
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

    private static double Lerp(double from, double to, double progress)
    {
        return from + ((to - from) * progress);
    }

    private static double EaseOutCubic(double value)
    {
        var inverse = 1.0 - value;
        return 1.0 - (inverse * inverse * inverse);
    }

    private struct ModelBounds
    {
        public ModelBounds(double minX, double minY, double minZ, double maxX, double maxY, double maxZ)
        {
            MinX = minX;
            MinY = minY;
            MinZ = minZ;
            MaxX = maxX;
            MaxY = maxY;
            MaxZ = maxZ;
        }

        public double MinX { get; }

        public double MinY { get; }

        public double MinZ { get; }

        public double MaxX { get; }

        public double MaxY { get; }

        public double MaxZ { get; }
    }
}

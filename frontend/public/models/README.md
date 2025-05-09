# 3D Health Models

This directory contains 3D models for the health visualization features. Models should be in GLB format for optimal performance.

## Required Models

1. `brain.glb` - 3D model of the human brain
2. `heart.glb` - 3D model of the human heart
3. `skeleton.glb` - 3D model of the human skeleton

## Model Sources

You can obtain high-quality 3D models from these sources:

1. [Sketchfab](https://sketchfab.com/) - Search for "anatomy" or specific body parts
2. [TurboSquid](https://www.turbosquid.com/) - Professional 3D models
3. [CGTrader](https://www.cgtrader.com/) - High-quality 3D models
4. [Free3D](https://free3d.com/) - Free 3D models

## Model Requirements

- Format: GLB (preferred) or GLTF
- Polycount: Under 100,000 triangles for optimal performance
- Textures: Include PBR materials if possible
- Scale: Models should be properly scaled (1 unit = 1 meter)
- Origin: Center the model at (0,0,0)

## Adding New Models

1. Download or create your 3D model
2. Convert to GLB format if necessary
3. Place the file in this directory
4. Update the model URLs in `HealthModels.tsx`

## Optimization Tips

- Use mesh compression
- Optimize textures
- Remove unnecessary geometry
- Use LOD (Level of Detail) if possible
- Keep file sizes under 5MB when possible 
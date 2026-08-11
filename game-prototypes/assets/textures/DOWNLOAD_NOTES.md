---
tags: [game-design, sealed-hall, assets, textures]
date: 2026-08-10
---

# 纹理下载记录

所有纹理均为 **CC0 许可**（AmbientCG / Poly Haven），可免费商用。

## 已下载（全部成功）

| 本地文件 | 来源资产 | 分辨率 | 来源 URL | 下载直链 |
|---|---|---|---|---|
| `stone_wall_color.jpg` | AmbientCG Bricks100（中世纪石墙） | 2048×1024 | https://ambientcg.com/a/Bricks100 | https://ambientcg.com/get?file=Bricks100_2K-JPG.zip |
| `stone_floor_color.jpg` | AmbientCG Concrete030（混凝土石地板） | 2048×2048 | https://ambientcg.com/a/Concrete030 | https://ambientcg.com/get?file=Concrete030_2K-JPG.zip |
| `moss_color.jpg` | AmbientCG Moss001（苔藓） | 2048×2048 | https://ambientcg.com/a/Moss001 | https://ambientcg.com/get?file=Moss001_2K-JPG.zip |
| `metal_color.jpg` | AmbientCG Metal063（金属板） | 2048×2048 | https://ambientcg.com/a/Metal063 | https://ambientcg.com/get?file=Metal063_2K-JPG.zip |
| `wood_color.jpg` | AmbientCG Wood095（木材） | 2048×1024 | https://ambientcg.com/a/Wood095 | https://ambientcg.com/get?file=Wood095_2K-JPG.zip |
| `old_hall.hdr` | Poly Haven Old Hall HDRI（废弃大厅） | 2K | https://polyhaven.com/a/old_hall | https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/old_hall_2k.hdr |

## 说明

- 本任务只下载了各材质的 **Color（Diffuse）** 贴图。AmbientCG 的 ZIP 包内含完整 PBR 贴图集（Normal / Roughness / AO / Displacement / Metalness 等），如需 PBR 完整贴图可从相同来源 URL 重新下载解压。
- **原 "StoneWall01" 资产在当前 AmbientCG 数据库中已不存在**（API 返回 404），已用同风格的中世纪石墙 `Bricks100` 替代。
- **原 "Concrete03 / Metal04 / Wood01"** 同理，使用数据库中对应类型的代表性资产 `Concrete030`、`Metal063`、`Wood095`。
- HDRI 为 Radiance `.hdr` 格式，头校验通过（`#?RADIANCE`）。

## 下载方式备忘

AmbientCG 下载 URL 格式：`https://ambientcg.com/get?file={AssetId}_{分辨率}-{格式}.zip`（如 `Bricks100_2K-JPG.zip`），需跟随重定向（`curl -L`）并带 User-Agent。
Poly Haven 直链：`https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/{分辨率}/{name}_{分辨率}.hdr`。

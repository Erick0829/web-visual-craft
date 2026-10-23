# three.js 展厅工艺（几何 / 材质 / 光照 / 交互）

环境：three 0.186 + GLTFLoader + OrbitControls + RoomEnvironment + CSS2DRenderer，ACESFilmicToneMapping，`outputColorSpace = SRGBColorSpace`。

## 材质：金属发黑与「黄漆」问题

- **金属只反射环境光**。场景环境暗时，metalness 高的材质整体发黑——不是材质坏了。修法：`PMREMGenerator.fromScene(new RoomEnvironment())` 给 `scene.environment`，再按材质分档调 `envMapIntensity`。
- **带 `metalnessMap` 的模型绝不能重置 metalness**（曾为修黑屏强设 `metalness=min(0.45)`，把金面具修成了黄漆）。正确做法：只动 `envMapIntensity`（1.5~1.9），metalness/roughness map 原样保留。
- **素材池模型常见 `metallicFactor: 0`**（画出来的漆感）。运行时统一 tune：

```js
function tuneMaterial(mat) {
  if (mat.isMeshStandardMaterial) {
    if (!mat.metalnessMap) {        // 共享贴图的普通件
      mat.metalness = 0.52;
      mat.roughness = Math.min(1, (mat.roughness ?? 0.5) * 1.05);
      mat.envMapIntensity = 0.9;
    } else {                        // 自带金属度贴图的件（如金面具）
      mat.envMapIntensity = 1.6;
      mat.roughness = Math.min(1, (mat.roughness ?? 0.5) * 0.85);
    }
  }
}
```

- 亮度分级需求（如「金面具之外都调暗」）：给查看器传 `dim` prop 切换容器 class，别去改材质参数。

## 圆形展厅几何（入口 + 环形展品）

- 墙 = `CylinderGeometry(R, R, H, 160, 1, true, gapHalf, 2π - 2*gapHalf)`，缺口半角 `gapHalf = asin(通道半宽 / R)`，`side = BackSide`（室内看的是背面）。
- **环形展品起始角 = 360/件数/2**，即入口方向永远落在两件之间，不会正对一件的背后或堵住门。位置 `x = R*sin(a), z = R*cos(a)`，a=0 为入口方向。
- 通道地面与圆厅地面接缝：通道平面下移 0.002 并向厅内延伸 0.5，藏在圆地板下面防 z-fighting 和月牙缝。
- 无天花时**不要 clamp 相机 y 上限**（要能拉到屋顶外俯瞰），只保底 `y >= 0.42`。

## 模型归一化摆放（不信任模型自带单位）

素材来源杂，尺度混乱（同批模型有 315 单位高也有 0.9 单位高的）。统一流程：

1. `Box3.setFromObject` 量原始包围盒；
2. 缩放 = 目标高度 / size.y（目标高度用**实物真实尺寸**，如展品通高）；
3. `position.set(-center.x*s, -box.min.y*s, -center.z*s)` 让底面贴台面、水平居中；
4. 朝向心：`rotation.y = atan2(-x, -z) + faceOffset`（frontOffset 逐件目测微调）；
5. 尺寸换算用真实参数（通高 260.8cm 之类），页面上放滑杆可调。

**注意**：归一化后模型比例关系取决于实物尺寸数据是否可靠；模型形制与实物不符时（素材是「相近器型」），按高度校准并注明。

## 光照（柔和均匀，无硬阴影）

- 半球光（暖白/暗棕）1.0 + 主平行光 1.5 + 冷补光 0.4 + 地面反弹 0.3 + 中央 SpotLight（intensity 90，decay 1.35）。
- 不开实时阴影。接触阴影与光池用程序生成径向渐变 CanvasTexture：黑色 `MultiplyBlending`（opacity 0.85）贴地，暖色 `AdditiveBlending`（opacity 0.55）做光池。
- 墙面与地面同一张贴图时，墙 repeat 放大（tile×2.6）+ 色调压暗（如 0xb9ac9c），否则整个空间花成一片。

## 交互

- OrbitControls：`enableDamping`、`maxPolarAngle = π/2 - 0.035`（不穿地）、`min/maxDistance`。
- WASD/方向键漫游：移动 camera.position 与 controls.target 同一向量（保持视角），每帧 `clampCamera`。
- 点击聚焦：Raycaster 命中后飞向展品（`flyTo` 用 easeInOutCubic 插值 700ms），拖拽超过 6px 判定为旋转、不触发。
- 标签：CSS2DRenderer + 毛玻璃小卡片（`backdrop-filter: blur`），可整体开关。
- **页面顶部参数化**：把最常调的量（主体高度、外圈放大倍数）做成滑杆，实时 applyHeight。外圈小件默认显示放大 2.0×（面板注明"仅为观感"，可回 1:1）——12cm 的实物在 17m 大厅里 1:1 等于看不见。
- 占位兜底：模型解析失败时用带真实尺寸标注的半透明体块（EdgesGeometry 描边）顶上，页面给出「N 件未载入」提示。

## 已知坑

- `parseFloat(q) || default` 会把合法的 0 当缺省——URL 镜头参数 `cx=0` 全部失效，进而误判模型比例错误（其实尺寸一直是对的）。用 `qp.has(k) ? parseFloat(qp.get(k)) : d`。
- KHR_mesh_quantization 会在节点上烘焙 scale，`object.scale.setScalar()` 只能设在 gltf.scene 根上（别覆盖中间节点）。
- gltf-transform 的 `flatten/join` 会改变节点结构，量化后 accessor min/max 是归一化单位，**不要**用它算真实尺寸，运行时 Box3 才准。
- 顶部墙厚收边：用自定义 BufferGeometry 连内外圈顶点，比 RingGeometry 转 90° 省心。

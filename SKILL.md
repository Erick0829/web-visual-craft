---
name: web-visual-craft
description: 网页视觉打磨与 3D 展厅/单文件交付的实战工艺包。当用户要求「美化网页/详情页布局/开场动效」「做一个 three.js 展厅或 3D 预览网页」「把网页打包成单个 HTML 发给别人」「调 3D 材质/光照/亮度」「验证网页实际渲染效果」时使用。沉淀自三星堆青铜器线上展馆（React+three.js）的完整实战：CSS 叠版布局、氛围背景、入场动效、GLB 压缩、three.js 材质光照修正、无头浏览器截图验证循环、单 HTML 自包含打包与提交包审查。
agent_created: true
---

# Web Visual Craft

把一个网站从「能用」打磨到「好看、能交付」的完整工艺。来自一次真实的博物馆网站实战（React 19 + TypeScript + three.js 0.186 + Vite 7），所有结论都被无头浏览器截图验证过。

## 核心纪律（先读这个）

1. **验证靠截图，不靠目测和推理。** 任何视觉改动（CSS、材质、光照、布局）完成后，用无头浏览器截图确认真实渲染效果再汇报。用户说「看着暗/看着怪」时，先用截图实测亮度、用 `elementFromPoint` 查遮挡，再下结论。
2. **内容是用户的领土。** 美化只动样式与结构，不改用户的文案、标题、数据状态；发现内容有问题要报告，不要顺手改。
3. **每次只验证一个变量。** 调材质/光照/比例时用 URL 参数固定镜头位，改一个参数截一张图，避免「改了五处不知道哪处生效」。

## 工作流

### 一、网页美化（详情页、首页、动效）

按 `references/web-polish.md` 的清单操作。要点：

- 叠版布局用 CSS Grid 列宽总和 >100% 制造自然叠压；`inline style` 会杀掉 CSS 负 margin。
- `mask-image` 用在 canvas 上会清空整个 WebGL 内容——用 `::after` 叠加渐变替代。
- `mix-blend-mode` + z-index 会盖住上层文字；「文字看着暗」先查是不是被 canvas 压住。
- 入场闸门动画：首页必须在闸门收场后再挂载（onDone 再 setState），否则动画在幕后播完、用户看到静态页。
- 性能：三维查看器用 `React.lazy` + `Suspense` 拆出主包（three.js 不进 entry）；配合 IntersectionObserver + visibilitychange 做按需渲染。

### 二、three.js 展厅 / 3D 预览

按 `references/three-hall.md` 操作。要点：

- 金属发黑或像「黄漆」：金属只反射环境光，调 `envMapIntensity` 而不是砍 `metalness`；带 `metalnessMap` 的模型绝不重置 metalness。
- 圆形展厅几何：墙缺口半角 = `asin(通道半宽/半径)`；环形展品起始角 = `360/件数/2`，让入口正好落在两件之间。
- 摆放统一走「包围盒归一化」：按 bbox 定真实尺寸、底面贴台面、水平居中、朝向 `atan2(-x,-z)`。
- 柔和均匀光照 = 半球光 + 两三盏平行光 + 中央射灯，不用实时阴影，接触阴影和光池用程序生成的径向渐变贴图。
- 镜头：OrbitControls（旋转/缩放/平移）+ WASD 平移 + 点击展品聚焦飞行；给页面加 `?cx=&cz=&tx=` 镜头参数便于测试和分享。

### 三、单 HTML 自包含交付

按 `references/single-file-pipeline.md` 操作。要点：

- `file://` 下 fetch 本地文件会被 CORS 拦截——「双击就能开」必须把 JS/图片/模型全部内嵌（base64）。
- GLB 减肥两板斧：`scripts/optimize_glb.py` 重编码内嵌贴图 + gltf-transform 的 `optimize --compress quantize --texture-compress webp`。**注意** `--simplify-error 0.008` 能把 60k 三角面砍到 10k（省 6 倍体积），但模型会糊——交付评审的版本用 0.001 或不 simplify。
- base64 后体积 ≈ 原始 ×1.37；38MB 的 HTML 可以用，但解析要等几秒，运行说明里要写明。
- Vite 项目优先走 `vite-plugin-singlefile` + GLB data URL 注入的成熟管线。

### 四、渲染验证循环

按 `references/verification.md` 的配方执行。核心命令（Edge/Chrome 通用）：

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new \
  --disable-gpu --enable-unsafe-swiftshader --hide-scrollbars \
  --window-size=1600,900 --virtual-time-budget=25000 \
  --screenshot=out.png "file:///路径/页面.html?cx=0&cy=1.6&cz=10.6&tx=0&ty=1.5&tz=0"
```

抓 console：加 `--enable-logging=stderr --v=0` 后 `grep CONSOLE`。

### 五、交付包审查

代队友/他人出交付包时逐项过：`npm ci && npm run build` 能否通过（含 tsc）、package.json 里每个 script 指向的文件是否存在、双击场景是否 404（file:// 跳转要有兜底卡片而非静默 redirect）、构建产物是否混入 node_modules、zip 用 UTF-8 文件名编码（python zipfile，别用会乱码的工具）、打包后用无头浏览器复测一遍关键路由。

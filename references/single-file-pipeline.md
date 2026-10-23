# 单 HTML 自包含交付管线

目标：「双击就能打开、不联网也能看、发微信就能给」。`file://` 下 fetch 本地文件被 CORS 拦截，所以一切资源必须内嵌。

## 体积预算参考

| 内容 | 原始 | 内嵌后(base64 ×1.37) |
|---|---|---|
| three.js bundle (esbuild minify) | ~700KB | 直接内联 |
| 8 个 GLB（贴图重编码+量化+simplify） | 4.5MB | ~6MB |
| 8 个 GLB（仅贴图重编码） | 16MB | ~22MB |
| 8 个 GLB 原始 | 28MB | ~38MB |

38MB HTML 可用但解析需数秒；目标控制在 10MB 内体验最佳。

## 第一步：GLB 减肥

**贴图重编码**（`scripts/optimize_glb.py`，PIL 重编码内嵌 JPEG 并重建 BIN chunk）：

```bash
python scripts/optimize_glb.py <输入目录> <输出目录> [max_size=1024] [quality=82]
```

**几何与量化**（gltf-transform CLI，装在独立目录，别装进主项目）：

```bash
npm install @gltf-transform/cli   # 独立目录，注意 npm 会向上找 package.json
npx gltf-transform optimize in.glb out.glb \
  --compress quantize --texture-compress webp --texture-size 1024 \
  --simplify-error 0.008
```

- `--compress quantize`（KHR_mesh_quantization）浏览器原生支持，**不需要** Draco/Meshopt 解码器。
- **`--simplify-error` 是保真度 vs 体积的总闸**：0.008 → 60k 三角面砍到 10k，模型明显变糊（曾因此被判「模型不好」）；交付评审用 0.001 或干脆不 simplify。
- webp 纹理要求浏览器支持 EXT_texture_webp（现代浏览器都行）。
- 量化后 accessor 的 min/max 是归一化单位，**不能**拿来算真实尺寸。

## 第二步 A：通用打包（任意项目，esbuild 路线）

1. 源码写成一个入口 JS（`import * as THREE from 'three'` + addons）；
2. esbuild 打成 IIFE：
   `node node_modules/esbuild/bin/esbuild preview-src/hall.js --bundle --minify --format=iife --target=es2019 --legal-comments=none --outfile=build/bundle.js`
3. Python 注入：读 HTML 模板（含 `%%ASSETS%%`、`%%BUNDLE%%` 占位），资产 base64 后以 `window.__ASSETS__ = {...}` 注入；bundle 里的 `</script>` 替换为 `<\/script>` 防截断；
4. 运行时用 `atob → Uint8Array → loader.parse(buffer)` 加载模型（不要用 fetch data: URL）。

## 第二步 B：Vite 项目（vite-plugin-singlefile 路线）

```js
// build-standalone.mjs 核心思路
await build({ plugins: [react(), viteSingleFile({ useRecommendedBuildConfig: true })],
              build: { outDir: 'standalone', emptyOutDir: true } });
// 再把 public/models 里的 GLB 按 URL 字符串匹配替换成 data URL
html = html.split(`"${url}"`).join(`"${dataUrl}"`);
```

- **构建脚本必须剥离 file:// 跳转脚本**（如 `<script src="file-redirect.js">`），否则单文件版自己跳自己、无限重载：
  `html.replace(/<script[^>]*src="[^"]*file-redirect\.js"[^>]*><\/script>/g, '')`
- 构建完正则检查是否残留 `assets/*.js|css` 外链，无残留才删 assets 目录。

## file:// 场景的坑

- 双击打开 = `file:` 协议：模块脚本、fetch/XHR 本地路径全被拦，唯一出路是全内嵌。
- 源码入口（Vite dev 的 index.html）被用户手滑双击时，**不要静默 redirect** 到可能不存在的单文件版（404 白屏）；改成引导卡片：按钮跳单文件版 + 写明两条备选（打开包根目录 index.html / npm run dev）。
- 模型加载失败的兜底：用带真实尺寸标注的半透明体块替代，页面提示「N 件未载入」。

## 打包与校验

- zip 用 python `zipfile` 打（UTF-8 文件名自动置位）；PowerShell Compress-Archive 对中文名有编码坑。
- 打包前清理 `node_modules/`、`dist/`、中间构建目录。
- **打包后必做**：zip 解回临时目录 → 无头浏览器双击场景（file://）复测关键路由 → `z.testzip()` 校验完整性。
- 交付包里放「运行说明」和「第三方资源说明 + licenses」（React/three 等 MIT 原文）。

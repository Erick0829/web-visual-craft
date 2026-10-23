# 渲染验证配方（无头浏览器截图循环）

原则：**任何视觉结论都要有一张截图背书**。改一版截一张，不要攒。

## 标准命令（Windows，Edge 为例，Chrome 同参数）

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --headless=new --disable-gpu --enable-unsafe-swiftshader \
  --hide-scrollbars --window-size=1600,900 \
  --virtual-time-budget=25000 \
  --screenshot="D:/abs/path/out.png" \
  "file:///D:/abs/path/page.html#/route?cx=0&cy=1.6&cz=10.6&tx=0&ty=1.5&tz=0"
```

- `--enable-unsafe-swiftshader`：无 GPU 环境跑 WebGL 必需（软件光栅化慢但能出图）。
- `--virtual-time-budget=25000`：给异步加载留时间；页面有持续 rAF 时虚拟时间会推进到预算为止。
- 38MB 级大 HTML 解析慢，一次截图可能要 1~5 分钟，**放后台跑**，别在 foreground 等到超时。

## 抓 console 报错与日志

```bash
... --enable-logging=stderr --v=0 ... 2>&1 | grep -i "console"
```

- 页面里先装 `window.addEventListener('error', e => 写入可见 DOM)`，让报错在截图里可见。
- 调试日志用 `console.log('[tag]', ...)` 带前缀，grep `[tag]`。

## 页面侧配合：URL 镜头参数

给 3D 页面预留 `?cx=&cy=&cz=&tx=&ty=&tz=`（相机与目标），验证时可以精确复现任意机位：

```js
const v = (k, d) => (qp.has(k) ? parseFloat(qp.get(k)) : d);  // 别写 parseFloat(q)||d，0 会失效！
```

## 判图纪律

- 无头截图回读时显示的是缩略图（如 640px），**别用它目测比例大小**——透视 + 缩放双重误导。有疑点先用 debug 日志输出数值（包围盒、缩放系数）再下结论。
- 「看着暗」：采样像素亮度（max luminance）实测；「被盖住」：`elementFromPoint` 查命中元素。
- 模型尺寸争议：`?debug=1` 输出每个模型的 rawSize / scale / targetH，一次定位。

## 疑难排查速查

| 症状 | 大概率原因 |
|---|---|
| 截图是黑屏/纯加载页 | WebGL 初始化失败（缺 swiftshader flag）或脚本抛错（看 console） |
| 截图等不到内容 | 资源未内嵌、file:// 被 CORS 拦；或 virtual-time-budget 不够 |
| 画面比例怪 | 相机参数没生效：`parseFloat(q)||d` 吃掉了 0 值 |
| 模型忽大忽小 | 用了量化后 accessor min/max 算尺寸；改用运行时 Box3 |
| 命令被 SIGTERM | 大 HTML 解析超时；加 run_in_background，别 foreground 硬等 |

## 验证清单（交付前过一遍）

1. 双击场景（file://）入口页 + 每条关键路由各截一张；
2. console 无报错；
3. 外链扫描：`grep -o 'https\?://...' 产物 | sort -u`，只应剩 W3C 命名空间等常量；
4. zip 解回临时目录复测（不要直接测打包前的目录）；
5. `zipfile.testzip()` 完整性校验。

# MangaTranslator Extension

![Manifest V3](https://img.shields.io/badge/Manifest-V3-4285F4)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Portable](https://img.shields.io/badge/Windows-portable-0078D4)

打开网页，边看边翻：自动判断原文语言，按页面顺序处理图片，再把译后的漫画放回原位。

我最初是为了自己看外语漫画（包括成人向网页漫画）改的这一版。广告混进漫画图片列表、看不出原文是哪国语言、翻一页等半天、刷新后自动翻译又失忆——工具不该比剧情更抢戏。目标很简单：少折腾翻译器，多把时间留给漫画。

本项目基于 [lehuyqq/Manga-Translator-Extension](https://github.com/lehuyqq/Manga-Translator-Extension) 的 `v1.0.1` 修改，并非原作者的官方版本。

[English](../README.md) · [Tiếng Việt](README.vi.md)

## 这一版改了什么

- **不认识原文也能试着翻**：可自动识别每块文字的来源语言；目标语言新增简体中文和繁体中文。识别与翻译质量仍取决于所选模型。
- **刷新后接着翻**：按网站记住自动翻译开关，页面重新加载后自动恢复。
- **别让读者干等**：自动模式最多四页一组，先显示第一页，再处理其余页面，并把前页 OCR 文字带入上下文。它并不是“整话文字一次发送、一次回填”。
- **少扫无关图片**：按广告线索和漫画图片尺寸过滤；下文另有广告拦截扩展推荐。
- **少上传无关画面**：关闭整页上传，只向翻译服务发送检测到的文字区域裁图；有气泡分割结果时会遮掉气泡外画面。裁图仍可能带到部分画面，也不能保证不会被服务商拒绝。
- **一处失败不拖垮整页**：遇到空响应会拆分文字区域重试，尽量隔离出错区域。
- **让 AMD Windows 电脑能跑起来**：给 CPU 模式加兼容处理；已测试的 AMD 机器使用 CPU 运行，**没有实现 AMD GPU 加速**。

上游的页面扫描、手动选图翻译、气泡外文字、多种 API 服务商和可选 Flux 修图功能仍在。此分支**尚未实现免费本地翻译**；所选服务商可能要求 API Key。

## 广告图片也被扫进去怎么办？

内置过滤会排除常见广告域名、广告标记、横幅和过小图片，但不可能认出每一张广告。广告很多的网站，推荐搭配独立扩展 [uBlock Origin Lite（Chrome 应用商店）](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh)：先拦住网页广告，再让本项目筛选剩余图片。它**不是本项目集成或附带的功能**，安装前请核对发布者及其[官方项目页](https://github.com/uBlockOrigin/uBOL-home)。两层过滤也不能保证百分之百准确。

## 项目结构

```text
manga-translator-extension/
  backend/                 FastAPI 后端和 MangaTranslator 集成
  backend/main.py          后端入口
  backend/core/            检测、清理、翻译和文字渲染代码
  backend/models/          Pydantic API schema
  backend/pipeline/        core pipeline 的 wrapper
  extension/               Manifest V3 浏览器扩展
  extension/src/popup/     弹窗 UI
  extension/src/shared/    共享 types、constants 和 i18n
  extension/src/background 后台 service worker
  extension/src/content-script 页面扫描器和自动翻译 overlay
  docs/                    API 和本地化文档
```

## 快速开始

启动后端：

```powershell
cd manga-translator-extension
.\start-backend.bat
```

或直接运行：

```powershell
cd manga-translator-extension\backend
python main.py
```

这个源码仓库不包含 Python runtime 和模型权重，需要另从上游官方 Release 获取。使用 portable runtime 时，启动脚本会识别 `backend\runtime\python.exe`；在已测试的 AMD Windows 机器上，它以 CPU 模式运行。

构建扩展：

```powershell
cd manga-translator-extension\extension
npm install
npm run build
```

在 Chrome 或 Edge 中以 unpacked extension 加载 `extension/dist/`。

可选 Flux 设置：

```powershell
cd manga-translator-extension
.\setup.bat
```

只有在需要更重的 Flux inpainting 时才选择 Flux。默认 portable 包会保持轻量，不包含 Flux 模型。

## 配置

打开扩展弹窗：

- `Translate`：选择源语言/目标语言，并启用气泡外文字翻译。
- `LLM Config`：配置 provider、model、API key、sampling values 和 special instructions。
- `Config`：切换扩展语言并设置 backend URL。

默认 backend URL 为 `http://localhost:7677`。

## Runtime 打包

当 Python runtime 位于以下路径时，本项目可以作为 portable 文件夹运行：

```text
manga-translator-extension/backend/runtime/
```

Runtime 体积很大，应作为 release asset 或本地 portable archive 分发，不应提交到普通 GitHub repository。GitHub 会阻止普通 Git 历史中超过 100 MB 的文件，而此 runtime 有数 GB。Flux 模型默认不包含在包内；需要时可通过 `setup.bat` 下载。

## 开发

最低检查：

```powershell
cd manga-translator-extension\extension
npm run build

cd ..\backend
python -m py_compile pipeline\wrapper.py
```

后端 health check：

```powershell
Invoke-RestMethod http://localhost:7677/health
```

## 安全

不要提交 API key、个人 backend URL、生成的 cache、model artifact、`node_modules`、`dist` 或完整 Python runtime。请通过扩展弹窗或环境变量保存 provider key，例如 `GOOGLE_API_KEY`、`OPENAI_API_KEY` 和 `ANTHROPIC_API_KEY`。

## 来源与许可

- 浏览器扩展及 FastAPI 集成来自 [lehuyqq/Manga-Translator-Extension](https://github.com/lehuyqq/Manga-Translator-Extension)。上游仓库目前没有为这部分代码提供明确的许可文件；本仓库不声称替原作者重新授权。
- 后端核心来自 [meangrinch/MangaTranslator](https://github.com/meangrinch/MangaTranslator)，按 Apache-2.0 保留其 [许可文本](../backend/core/LICENSE)和源码署名。

Python runtime、模型权重、构建产物与个人 API 凭据没有放进本源码仓库；分发二进制包前还需分别核对其许可和分发条件。

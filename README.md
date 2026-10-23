# MangaTranslator Extension

![Manifest V3](https://img.shields.io/badge/Manifest-V3-4285F4)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Portable](https://img.shields.io/badge/Windows-portable-0078D4)

Translate web manga as you read: detect the source language, process pages in order, and replace the images with translated versions without leaving the browser.

I started adapting this project for my own reading—foreign-language manga, including adult-oriented web comics. The recurring annoyances were familiar: ads mixed into the page list, dialogue in a language I could not identify, long waits between images, and auto-translate forgetting its state after a reload. The goal is simple: spend less time operating the translator and more time reading the story.

This is a community-modified version of [lehuyqq/Manga-Translator-Extension](https://github.com/lehuyqq/Manga-Translator-Extension), based on its `v1.0.1` release. It is not an official release from the original extension author.

[Tiếng Việt](docs/README.vi.md) · [中文](docs/README.zh.md)

## What this version changes

- **Read across languages:** source-language auto-detection works per text crop; target options now include Simplified and Traditional Chinese. Recognition and translation quality depend on the selected model.
- **Keep reading after a reload:** auto-translate is remembered per site and resumes when its pages load again.
- **Shorter visible waits:** automatic translation works in batches of up to four pages, displays the first page before the remaining pages finish, and passes prior OCR text as context. This is not a whole-chapter, single-request translation.
- **Less collateral scanning:** the page scanner skips likely ads and images that do not resemble manga pages. See the ad-blocker recommendation below.
- **Limit image exposure:** full-page upload to the translation provider is disabled; the backend sends detected text-region crops, masking the area outside a bubble when segmentation is available. Crops can still contain surrounding art and can still be rejected by a provider.
- **Recover from partial refusals:** an empty translation response can be split into smaller crop batches so one problematic region does not necessarily fail the entire page.
- **Run on CPU-only Windows:** a compatibility guard lets the bundled CUDA-oriented Python runtime start on the tested AMD machine in CPU mode. It does not accelerate inference on AMD GPUs.

The extension also retains the upstream page scanner, selectable translation, outside-bubble text option, multiple API providers, and optional Flux inpainting. Free local translation is **not** implemented in this fork; an API key may be required for your chosen provider.

## Ads in the page list

The built-in image filter catches common ad domains, ad-related page markup, banners, and undersized images, but it cannot identify every advertisement. For ad-heavy reading sites, I recommend using [uBlock Origin Lite on the Chrome Web Store](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh) alongside this extension. It is a separate, optional extension—not bundled with or affiliated with this project. Check the publisher and official [uBO Lite project page](https://github.com/uBlockOrigin/uBOL-home) before installing. Blocking ads before they reach the page usually gives the manga scanner less junk to inspect; neither layer guarantees perfect filtering.

## Project Layout

```text
manga-translator-extension/
  backend/                 FastAPI backend and MangaTranslator integration
  backend/main.py          Backend entry point
  backend/core/            Detection, cleanup, translation, and rendering code
  backend/models/          Pydantic API schemas
  backend/pipeline/        Wrapper around the core pipeline
  extension/               Manifest V3 browser extension
  extension/src/popup/     Popup UI
  extension/src/shared/    Shared types, constants, and i18n
  extension/src/background Background service worker
  extension/src/content-script Page scanner and auto-translate overlay
  docs/                    API and localized documentation
```

## Quick Start

Start the backend:

```powershell
cd manga-translator-extension
.\start-backend.bat
```

Or run it directly:

```powershell
cd manga-translator-extension\backend
python main.py
```

This source repository does not include the Python runtime or model weights. Obtain those separately from the upstream official release. If using a portable runtime, the launcher detects `backend\runtime\python.exe`; on the tested AMD Windows machine it runs in CPU mode.

Build the extension:

```powershell
cd manga-translator-extension\extension
npm install
npm run build
```

Load `extension/dist/` as an unpacked extension in Chrome or Edge.

Optional Flux setup:

```powershell
cd manga-translator-extension
.\setup.bat
```

Choose the Flux option only if you want heavier Flux inpainting. The default portable package is intentionally lightweight and does not include Flux models.

## Configuration

Open the extension popup:

- `Translate`: choose source/target language and outside-bubble text translation.
- `LLM Config`: configure provider, model, API key, sampling values, and special instructions.
- `Config`: switch extension language and set the backend URL.

The backend URL defaults to `http://localhost:7677`.

## Runtime Packaging

This project can run as a portable folder when the Python runtime is present at:

```text
manga-translator-extension/backend/runtime/
```

The runtime is large and should be distributed as a release asset or local portable archive, not committed into a normal GitHub repository. GitHub blocks files over 100 MB in regular Git history, and this runtime is several GB. Flux models are not included by default; use `setup.bat` to download them on demand.

## Development

Minimum checks:

```powershell
cd manga-translator-extension\extension
npm run build

cd ..\backend
python -m py_compile pipeline\wrapper.py
```

Backend health check:

```powershell
Invoke-RestMethod http://localhost:7677/health
```

## Security

Do not commit API keys, local backend URLs, generated caches, model artifacts, `node_modules`, `dist`, or a full Python runtime. Store provider keys through the extension popup or environment variables such as `GOOGLE_API_KEY`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY`.

## License

### Origins and attribution

- Browser extension and FastAPI integration: [lehuyqq/Manga-Translator-Extension](https://github.com/lehuyqq/Manga-Translator-Extension). The upstream repository does not currently contain an explicit license for that code. Its original authorship remains with its author; this repository does not claim to relicense it.
- MangaTranslator backend core: [meangrinch/MangaTranslator](https://github.com/meangrinch/MangaTranslator), by grinnch, under Apache License 2.0. The license text is preserved in [backend/core/LICENSE](backend/core/LICENSE). Copyright and attribution notices in the source are retained.

### Changes in this version

The changes since the upstream extension's `v1.0.1` release include Simplified and Traditional Chinese targets, automatic source-language selection, DeepSeek image-input handling, text-region cropping, ad-image filtering, cross-page OCR context and batched translation, translation failure handling, and persistent per-site auto-translation after page reload. The backend was also adapted to run on CPU-only Windows systems. See the Git history for the exact changes.

The Python runtime, downloaded model weights, generated browser build, caches, and personal API credentials are not part of this source repository. Their licenses and distribution terms must be checked separately before shipping binary release assets.

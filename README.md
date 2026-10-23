# MangaTranslator Extension

![Manifest V3](https://img.shields.io/badge/Manifest-V3-4285F4)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Portable](https://img.shields.io/badge/Windows-portable-0078D4)

Local manga page translation for Chromium-based browsers, powered by a FastAPI backend and a bundled MangaTranslator pipeline.

This is a community-modified version of [lehuyqq/Manga-Translator-Extension](https://github.com/lehuyqq/Manga-Translator-Extension), based on its `v1.0.1` release. It is not an official release from the original extension author.

[Tiếng Việt](docs/README.vi.md) · [中文](docs/README.zh.md)

## Highlights

- Page scanner for manga/comic images with selectable batch translation.
- Auto-translate mode that replaces images as you read.
- Bubble text and outside-bubble text support, with lightweight cleanup by default.
- Optional Flux Klein 4B inpainting can be downloaded later with `setup.bat`.
- Source/target options for Japanese, Korean, English, and Vietnamese.
- Extension UI languages: English by default, plus Vietnamese, Chinese, Japanese, and Korean.
- OpenAI-compatible model picker plus Google, OpenAI, Anthropic, xAI, DeepSeek, Z.ai, Moonshot AI, and OpenRouter provider options.
- Portable backend startup through `start-backend.bat` or `backend/main.py`.

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

For this portable build, prefer `backend\runtime\python.exe` or the bundled `MangaTranslator\runtime\python.exe` when CUDA/GPU packages are required.

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

The changes since the upstream extension's `v1.0.1` release include Simplified and Traditional Chinese targets, automatic source-language selection, DeepSeek image support, private text-region cropping, ad-image filtering, cross-page OCR context and batched translation, translation failure handling, and persistent per-site auto-translation after page reload. The backend was also adapted to run on CPU-only Windows systems. See the Git history for the exact changes.

The Python runtime, downloaded model weights, generated browser build, caches, and personal API credentials are not part of this source repository. Their licenses and distribution terms must be checked separately before shipping binary release assets.

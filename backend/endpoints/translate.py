"""FastAPI translation endpoints."""
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from models.schemas import (
    TranslateBatchItem,
    TranslateBatchItemResponse,
    TranslateBatchRequest,
    TranslateBatchResponse,
    TranslateRequest,
    TranslateResponse,
)
from pipeline.wrapper import (
    _build_config,
    image_to_base64_raw,
    translate_image_base64,
)
from config import settings

router = APIRouter(prefix="", tags=["translate"])

# Two workers is the best compromise for the bundled CPU-only runtime: it
# overlaps remote API waits without running several YOLO passes at once.
_executor = ThreadPoolExecutor(max_workers=2)
_batch_warmup_lock = threading.Lock()
_batch_models_warmed = False


def _build_bubble_info(bubbles: list[dict]) -> list:
    """Convert bubble dicts to BubbleInfo schema items."""
    from models.schemas import BubbleInfo

    results = []
    for b in bubbles:
        results.append(
            BubbleInfo(
                bbox=b.get("bbox", []),
                confidence=float(b.get("confidence", 0.0)),
                original_text=b.get("ocr_text"),
                translated_text=b.get("translation", ""),
            )
        )
    return results


@router.post("/translate", response_model=TranslateResponse)
async def translate_single(req: TranslateRequest) -> TranslateResponse:
    """Translate a single image.

    Accepts a base64-encoded image and returns the translated image
    plus bubble metadata.
    """
    models_dir = settings.models_dir
    fonts_dir = settings.fonts_base_dir

    config = _build_config(
        input_language=req.input_language,
        output_language=req.output_language,
        provider=req.provider,
        base_url=req.base_url,
        model_name=req.model_name,
        api_key=req.api_key,
        temperature=req.temperature,
        top_p=req.top_p,
        top_k=req.top_k,
        max_tokens=req.max_tokens,
        translation_mode=req.translation_mode,
        ocr_method=req.ocr_method,
        reasoning_effort=req.reasoning_effort,
        special_instructions=req.special_instructions,
        font_dir=req.font_dir,
        max_font_size=req.max_font_size,
        min_font_size=req.min_font_size,
        supersampling_factor=req.supersampling_factor,
        send_full_page_context=req.send_full_page_context,
        image_detail=req.image_detail,
        outside_text_enabled=req.outside_text_enabled,
        models_dir=models_dir,
        fonts_base_dir=fonts_dir,
    )

    start = time.time()
    try:
        result_image, bubbles, elapsed = await asyncio.to_thread(translate_image_base64, req.image, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")

    translated_b64 = image_to_base64_raw(result_image)

    return TranslateResponse(
        translated_image=translated_b64,
        bubbles=_build_bubble_info(bubbles),
        processing_time_seconds=elapsed,
        source_language=req.input_language,
        target_language=req.output_language,
        provider=req.provider,
    )


def _translate_single_item(
    item: TranslateBatchItem,
    req: TranslateBatchRequest,
    previous_context_texts: list[list[str]],
) -> tuple[TranslateBatchItemResponse, list[str]]:
    """Translate one item from a batch request (runs in thread pool)."""
    import time as t

    models_dir = settings.models_dir
    fonts_dir = settings.fonts_base_dir

    item_start = t.time()
    try:
        config = _build_config(
            input_language=req.input_language,
            output_language=req.output_language,
            provider=req.provider,
            base_url=req.base_url,
            model_name=req.model_name,
            api_key=req.api_key,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k,
            max_tokens=req.max_tokens,
            translation_mode=req.translation_mode,
            ocr_method=req.ocr_method,
            reasoning_effort=req.reasoning_effort,
            special_instructions=req.special_instructions,
            font_dir=req.font_dir,
            max_font_size=req.max_font_size,
            min_font_size=req.min_font_size,
            supersampling_factor=req.supersampling_factor,
            send_full_page_context=req.send_full_page_context,
            image_detail=req.image_detail,
            outside_text_enabled=req.outside_text_enabled,
            models_dir=models_dir,
            fonts_base_dir=fonts_dir,
        )

        captured_ocr_texts: list[str] = []
        result_image, bubbles, _ = translate_image_base64(
            item.image,
            config,
            previous_context_texts=previous_context_texts,
            ocr_texts_out=captured_ocr_texts,
        )
        translated_b64 = image_to_base64_raw(result_image)
        return (
            TranslateBatchItemResponse(
                id=item.id,
                translated_image=translated_b64,
                bubbles=_build_bubble_info(bubbles),
                processing_time_seconds=t.time() - item_start,
                ocr_texts=captured_ocr_texts,
            ),
            captured_ocr_texts,
        )
    except Exception as e:
        return (
            TranslateBatchItemResponse(
                id=item.id,
                translated_image=None,
                bubbles=[],
                error=str(e),
                processing_time_seconds=t.time() - item_start,
                ocr_texts=[],
            ),
            [],
        )


@router.post("/translate/batch", response_model=TranslateBatchResponse)
async def translate_batch(req: TranslateBatchRequest) -> TranslateBatchResponse:
    """Translate multiple images concurrently.

    Processes up to 20 images in parallel using a thread pool.
    Returns results in the same order as the input.
    """
    if len(req.images) > 20:
        raise HTTPException(
            status_code=400, detail="Maximum 20 images per batch"
        )

    start = time.time()
    global _batch_models_warmed

    results: list[TranslateBatchItemResponse] = []
    chapter_text_history = list(req.previous_context_texts)
    start_index = 0

    # Ultralytics performs one-time model fusion during the first inference.
    # Warm up with one real page so two worker threads cannot race that mutable
    # initialization path.
    if not _batch_models_warmed and req.images:
        with _batch_warmup_lock:
            if not _batch_models_warmed:
                warm_response, warm_ocr = _translate_single_item(
                    req.images[0],
                    req,
                    chapter_text_history[-16:],
                )
                results.append(warm_response)
                chapter_text_history.append(warm_ocr)
                _batch_models_warmed = True
                start_index = 1

    # Work in two-page waves. Pages within a wave run together; the next wave
    # receives the accumulated OCR transcript as chapter context.
    for wave_start in range(start_index, len(req.images), 2):
        wave = req.images[wave_start:wave_start + 2]
        context_snapshot = chapter_text_history[-16:]
        futures = [
            _executor.submit(
                _translate_single_item,
                item,
                req,
                context_snapshot,
            )
            for item in wave
        ]
        wave_results = [future.result() for future in futures]
        for response, ocr_texts in wave_results:
            results.append(response)
            chapter_text_history.append(ocr_texts)

    success_count = sum(1 for r in results if r.error is None)
    error_count = len(results) - success_count

    return TranslateBatchResponse(
        results=results,
        total_time_seconds=time.time() - start,
        success_count=success_count,
        error_count=error_count,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    import torch

    return {
        "status": "ok",
        "version": "1.0.0",
        "backend_version": "1.0.0",
        "gpu_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu",
        "cuda_available": torch.cuda.is_available(),
    }


@router.get("/providers")
async def list_providers():
    """Return available LLM providers."""
    return {
        "providers": [
            "Google",
            "OpenAI",
            "Anthropic",
            "xAI",
            "DeepSeek",
            "Z.ai",
            "Moonshot AI",
            "OpenRouter",
            "OpenAI-Compatible",
        ],
        "default_provider": "Google",
    }

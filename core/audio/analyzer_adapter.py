import logging
from typing import Optional

from .analyzer import TrustSpectra

logger = logging.getLogger(__name__)


def create_analyzer_adapter(
    threshold: Optional[float] = None,
    num_threads: Optional[int] = None,
    chunk_duration: Optional[float] = None,
    use_chunked_loading: bool = True,
) -> TrustSpectra:
    """
    Фабрика для создания ONNX-анализатора.
    """
    analyzer = TrustSpectra(
        confidence_threshold=threshold,
        num_threads=num_threads,
        chunk_duration=chunk_duration,
        use_chunked_loading=use_chunked_loading,
    )

    if not analyzer.is_ready:
        raise RuntimeError(
            "TrustSpectra не готов к работе: ONNX модель не загружена. "
            "Проверьте путь к модели и целостность файла model.onnx."
        )

    logger.info(
        "TrustSpectra ONNX готов: устройство=%s, порог=%.3f",
        analyzer.device,
        analyzer.confidence_threshold,
    )
    return analyzer

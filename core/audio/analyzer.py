import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
except ImportError as e:
    logger.critical(
        f"Критическая ошибка: не удалось импортировать onnxruntime. Детали: {e}"
    )
    ort = None

try:
    import librosa
except ImportError as e:
    logger.critical(
        f"Критическая ошибка: не удалось импортировать librosa (возможно, отсутствует scipy или soundfile). Детали: {e}"
    )
    librosa = None

ONNX_AVAILABLE = (ort is not None) and (librosa is not None)


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.normpath(os.path.join(base_path, relative_path))


def create_analyzer_adapter(
    threshold=0.9, num_threads=None, chunk_duration=None, use_chunked_loading=True
):
    if not ONNX_AVAILABLE:
        missing = []
        if ort is None:
            missing.append("onnxruntime")
        if librosa is None:
            missing.append("librosa (или её зависимости: scipy, soundfile)")
        error_msg = f"Отсутствуют обязательные библиотеки: {', '.join(missing)}. Убедитесь, что зависимости установлены."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    analyzer = TrustSpectra(
        confidence_threshold=threshold,
        num_threads=num_threads,
        chunk_duration=chunk_duration,
        use_chunked_loading=use_chunked_loading,
    )

    if analyzer.is_ready:
        logger.info("ONNX анализатор готов")
    else:
        logger.error(
            "Анализатор инициализирован, но модель ONNX не найдена или не загружена."
        )
        raise RuntimeError(
            "Не удалось загрузить ONNX модель. Убедитесь, что файл model.onnx существует."
        )

    return analyzer


class BaseAnalyzer:
    CLASSES = ["claps", "heavy_breathing", "kisses", "moans"]

    def __init__(self, confidence_threshold=0.9):
        self.confidence_threshold = confidence_threshold
        # Храним ТОЛЬКО пороги, отличающиеся от глобального.
        # Fallback в _run_inference сам подставит self.confidence_threshold.
        self.confidence_thresholds = {}

    def get_threshold_for_class(self, cls_name: str) -> float:
        """Возвращает порог класса: индивидуальный или глобальный fallback."""
        return self.confidence_thresholds.get(cls_name, self.confidence_threshold)

    def update_parameters(self, **kwargs):
        # 1. Сначала обрабатываем индивидуальные пороги, чтобы они
        #    точно не были уничтожены при обновлении глобального порога.
        if "confidence_thresholds" in kwargs:
            new_thresholds = {}
            for cls, val in kwargs["confidence_thresholds"].items():
                if cls not in self.CLASSES:
                    continue
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    continue
                if val > 1.0:
                    val = val / 100.0
                val = max(0.0, min(1.0, val))
                # Сохраняем только если реально отличается от глобального
                if abs(val - self.confidence_threshold) > 1e-9:
                    new_thresholds[cls] = val
            self.confidence_thresholds = new_thresholds

        # 2. Теперь обновляем глобальный порог, НЕ трогая словарь напрямую.
        #    Удаляем из словаря те классы, которые теперь совпадают с новым глобальным.
        if "confidence_threshold" in kwargs or "threshold" in kwargs:
            t = kwargs.get("confidence_threshold", kwargs.get("threshold"))
            if t is not None:
                if t > 1.0:
                    t = t / 100.0
                self.confidence_threshold = max(0.0, min(1.0, t))
                self.confidence_thresholds = {
                    cls: val
                    for cls, val in self.confidence_thresholds.items()
                    if abs(val - self.confidence_threshold) > 1e-9
                }

        if "chunk_duration" in kwargs:
            self.chunk_duration = kwargs["chunk_duration"]

        if "use_chunked_loading" in kwargs:
            self.use_chunked_loading = kwargs["use_chunked_loading"]

        logger.info(
            f"Параметры обновлены: глобальный={self.confidence_threshold}, "
            f"индивидуальные={self.confidence_thresholds}"
        )


class TrustSpectra(BaseAnalyzer):
    SR, DURATION, N_FFT, HOP_LEN, N_MELS = 22050, 3.0, 1024, 256, 128
    F_MIN, F_MAX, POWER, TOP_DB = 20, 11025, 2.0, 80.0
    TARGET_RMS_DB, PEAK_LIMIT_DB, NOISE_GATE_DBFS = -23.0, -3.0, -60.0
    MAX_FILE_DURATION = 300.0
    CHUNK_OVERLAP = 1.0

    def __init__(
        self,
        model_path=None,
        device=None,
        confidence_threshold=0.6,
        num_threads=None,
        chunk_duration=60.0,
        use_chunked_loading=True,
    ):
        if confidence_threshold > 1.0:
            confidence_threshold /= 100.0
        super().__init__(confidence_threshold)

        self.model_path = model_path or resource_path("models/audio_model/model.onnx")
        self.chunk_duration = chunk_duration
        self.use_chunked_loading = use_chunked_loading
        self.device = device or "CPU"
        self.num_threads = num_threads

        self.target_rms_lin = 10 ** (self.TARGET_RMS_DB / 20)
        self.limit_lin = 10 ** (self.PEAK_LIMIT_DB / 20)
        self.win_smp = int(self.SR * self.DURATION)

        self._mel_basis = librosa.filters.mel(
            sr=self.SR,
            n_fft=self.N_FFT,
            n_mels=self.N_MELS,
            fmin=self.F_MIN,
            fmax=self.F_MAX,
            htk=True,
            norm=None,
        )

        self.session = None
        self.input_name = None
        self.output_name = None
        self.is_ready = False
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            logger.error(f"Файл модели не найден: {self.model_path}")
            return
        try:
            opts = ort.SessionOptions()
            if self.num_threads:
                opts.intra_op_num_threads = int(self.num_threads)
                opts.inter_op_num_threads = int(self.num_threads)
            providers = (
                ["CUDAExecutionProvider", "CPUExecutionProvider"]
                if self.device == "CUDA"
                else ["CPUExecutionProvider"]
            )
            self.session = ort.InferenceSession(
                self.model_path, sess_options=opts, providers=providers
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self._load_class_names()
            self.is_ready = True
            logger.info(f"ONNX модель загружена: {self.model_path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки ONNX: {e}")

    def _load_class_names(self):
        metadata_path = os.path.join(
            os.path.dirname(self.model_path), "model_metadata.json"
        )
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                if "class_names" in metadata:
                    self.CLASSES = metadata["class_names"]
                    if "optimal_thresholds" in metadata:
                        self.confidence_thresholds = {}
                        for cls, thr in zip(
                            self.CLASSES, metadata["optimal_thresholds"]
                        ):
                            if thr > 1.0:
                                thr /= 100.0
                            self.confidence_thresholds[cls] = thr
                        return
            except Exception as e:
                logger.warning(f"Ошибка чтения metadata JSON: {e}")
        # Если metadata нет — оставляем confidence_thresholds пустым,
        # глобальный self.confidence_threshold будет использоваться как fallback
        self.confidence_thresholds = {}

    def analyze_audio(self, file_path: str, progress_callback=None) -> Dict:
        if not self.is_ready:
            return {"error": "Модель не готова", "has_detections": False}
        try:
            duration = librosa.get_duration(path=file_path)
            use_chunked = self.use_chunked_loading and (
                duration > self.MAX_FILE_DURATION
            )
            if use_chunked:
                return self._analyze_chunked(file_path, duration, progress_callback)
            return self._analyze_standard(file_path, duration, progress_callback)
        except Exception as e:
            logger.error(f"Ошибка анализа {file_path}: {e}")
            return {"error": str(e), "file_path": file_path, "has_detections": False}

    def _fast_normalize_window(self, audio: np.ndarray) -> np.ndarray:
        if len(audio) < self.win_smp:
            audio = np.pad(audio, (0, self.win_smp - len(audio)), mode="constant")
        else:
            audio = audio[: self.win_smp]

        if len(audio) == 0:
            return audio.astype(np.float32)

        current_rms = np.sqrt(np.mean(audio**2))
        current_rms_db = 20 * np.log10(current_rms + 1e-10)

        if current_rms_db < self.NOISE_GATE_DBFS:
            if np.max(np.abs(audio)) > self.limit_lin:
                audio = self.limit_lin * np.tanh(audio / self.limit_lin)
            return audio.astype(np.float32)

        peak = np.max(np.abs(audio))
        crest_factor_db = 20 * np.log10((peak + 1e-10) / (current_rms + 1e-10))
        skip_rms = crest_factor_db > 24.0

        if not skip_rms:
            if current_rms > 1e-7:
                audio = audio * (self.target_rms_lin / current_rms)

        if np.max(np.abs(audio)) > self.limit_lin:
            audio = self.limit_lin * np.tanh(audio / self.limit_lin)

        return audio.astype(np.float32)

    def _extract_mel(self, batch_audio: List[np.ndarray]) -> np.ndarray:
        batch_np = np.stack(batch_audio).astype(np.float32)
        mel_specs = []
        for audio in batch_np:
            S = (
                np.abs(librosa.stft(audio, n_fft=self.N_FFT, hop_length=self.HOP_LEN))
                ** 2
            )
            mel = np.dot(self._mel_basis, S)
            mel_db = librosa.power_to_db(mel, ref=1.0, amin=1e-10, top_db=self.TOP_DB)
            mel_specs.append(mel_db)
        return np.stack(mel_specs)[:, np.newaxis, :, :].astype(np.float32)

    def _run_inference(
        self, batch_audio: List[np.ndarray], base_times: List[float], duration: float
    ) -> List[Dict]:
        mel_input = self._extract_mel(batch_audio)
        ort_outputs = self.session.run([self.output_name], {self.input_name: mel_input})
        logits = np.clip(ort_outputs[0], -100, 100)

        probs = 1 / (1 + np.exp(-logits))
        results = []
        for i, prob_arr in enumerate(probs):
            for cls_idx, prob in enumerate(prob_arr):
                cls_name = self.CLASSES[cls_idx]
                # Fallback: если класса нет в словаре — используем глобальный порог
                target_thr = self.confidence_thresholds.get(
                    cls_name, self.confidence_threshold
                )
                if prob >= target_thr:
                    results.append(
                        {
                            "segment_start": base_times[i],
                            "segment_end": min(base_times[i] + self.DURATION, duration),
                            "label": cls_name,
                            "confidence": float(prob),
                        }
                    )
        return results

    def _analyze_standard(self, file_path: str, duration: float, progress_cb) -> Dict:
        start_t = time.time()
        y, sr = librosa.load(file_path, sr=self.SR, mono=True)
        results = []
        step_smp = int(1.0 * sr)
        total_wins = max(1, int((len(y) - self.win_smp) / step_smp) + 1)

        for b_start in range(0, total_wins, 16):
            b_end = min(b_start + 16, total_wins)
            b_audio, b_times = [], []
            for idx in range(b_start, b_end):
                start = idx * step_smp
                b_audio.append(
                    self._fast_normalize_window(y[start : start + self.win_smp])
                )
                b_times.append(start / sr)

            if progress_cb:
                progress_cb(int((b_end / total_wins) * 100))

            results.extend(self._run_inference(b_audio, b_times, duration))

        if progress_cb:
            progress_cb(100)
        return self._format_results(
            file_path, duration, self._merge_segments(results), time.time() - start_t
        )

    def _analyze_chunked(self, file_path: str, duration: float, progress_cb) -> Dict:
        start_t = time.time()
        results = []
        chunk_step = self.chunk_duration - self.CHUNK_OVERLAP
        num_chunks = max(1, int((duration - self.CHUNK_OVERLAP) / chunk_step) + 1)

        for chunk_idx in range(num_chunks):
            offset = chunk_idx * chunk_step
            chunk_dur = min(self.chunk_duration, duration - offset)
            if chunk_dur <= 0:
                break
            try:
                y, sr = librosa.load(
                    file_path, sr=self.SR, mono=True, offset=offset, duration=chunk_dur
                )
            except Exception as e:
                logger.warning(f"Ошибка загрузки чанка {chunk_idx}: {e}")
                continue

            step_smp = int(1.0 * sr)
            total_wins = max(1, int((len(y) - self.win_smp) / step_smp) + 1)

            for b_start in range(0, total_wins, 16):
                b_end = min(b_start + 16, total_wins)
                b_audio, b_times = [], []
                for idx in range(b_start, b_end):
                    start = idx * step_smp
                    b_audio.append(
                        self._fast_normalize_window(y[start : start + self.win_smp])
                    )
                    b_times.append(offset + (start / sr))
                results.extend(self._run_inference(b_audio, b_times, duration))

            if progress_cb:
                progress_cb(int(((chunk_idx + 1) / num_chunks) * 100))

        if progress_cb:
            progress_cb(100)
        return self._format_results(
            file_path,
            duration,
            self._merge_segments(results),
            time.time() - start_t,
            chunked=True,
        )

    def _merge_segments(self, segments: List[Dict]) -> List[Dict]:
        if not segments:
            return []
        from collections import defaultdict

        by_class = defaultdict(list)
        for seg in segments:
            by_class[seg["label"]].append(seg)
        merged = []
        for cls_name, cls_segments in by_class.items():
            sorted_seg = sorted(cls_segments, key=lambda x: x["segment_start"])
            curr = sorted_seg[0].copy()
            for nxt in sorted_seg[1:]:
                if nxt["segment_start"] - curr["segment_end"] < 1.5:
                    curr["segment_end"] = max(curr["segment_end"], nxt["segment_end"])
                    curr["confidence"] = max(curr["confidence"], nxt["confidence"])
                else:
                    merged.append(curr)
                    curr = nxt.copy()
            merged.append(curr)
        return merged

    def _format_results(
        self, file_path, duration, merged, proc_time, chunked=False
    ) -> Dict:
        scores = {
            c: {"probability": 0.0, "detected": False, "confidence": 0.0}
            for c in self.CLASSES
        }
        for r in merged:
            if r["confidence"] > scores[r["label"]]["probability"]:
                scores[r["label"]].update(
                    {
                        "probability": r["confidence"],
                        "detected": True,
                        "confidence": r["confidence"],
                    }
                )
        return {
            "file_path": file_path,
            "segments": merged,
            "detected_classes": [r["label"] for r in merged],
            "class_scores": scores,
            "has_detections": bool(merged),
            "processing_time": proc_time,
            "file_duration": duration,
            "model_used": self.model_path,
            "chunked_processing": chunked,
        }

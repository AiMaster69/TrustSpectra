import numpy as np
import librosa

SAMPLE_RATE = 22050
DURATION = 3.0
TARGET_SAMPLES = int(SAMPLE_RATE * DURATION)
N_FFT = 1024
HOP_LENGTH = 256
N_MELS = 128
F_MIN = 20
F_MAX = 11025
RMS_TARGET_DB = -23.0
TARGET_PEAK_DBFS = -3.0
NOISE_GATE_DBFS = -60.0
SILENCE_THRESHOLD = 24


def safe_normalize(y: np.ndarray,
                   rms_tgt_db: float = RMS_TARGET_DB,
                   peak_limit_db: float = TARGET_PEAK_DBFS,
                   noise_gate_dbfs: float = NOISE_GATE_DBFS) -> np.ndarray:
    if y.size == 0:
        return y
    current_rms = np.sqrt(np.mean(y**2) + 1e-10)
    current_rms_db = 20 * np.log10(current_rms)
    peak_limit_lin = 10 ** (peak_limit_db / 20)
    if current_rms_db >= noise_gate_dbfs:
        rms_tgt_lin = 10 ** (rms_tgt_db / 20)
        y = y * (rms_tgt_lin / current_rms)
    if np.max(np.abs(y)) > peak_limit_lin:
        y = peak_limit_lin * np.tanh(y / peak_limit_lin)
    return y


def process_audio_for_inference(file_path: str,
                                target_sr: int = SAMPLE_RATE,
                                target_duration: float = DURATION,
                                silence_threshold: int = SILENCE_THRESHOLD,
                                offset: float = 0.0) -> np.ndarray:
    y, sr = librosa.load(file_path, sr=target_sr, mono=True,
                         offset=offset, duration=target_duration)
    if len(y) > 0:
        y, _ = librosa.effects.trim(y, top_db=silence_threshold)
    target_samples = int(target_sr * target_duration)
    if len(y) == 0:
        return np.zeros(target_samples, dtype=np.float32)
    y = safe_normalize(y)
    if len(y) < target_samples:
        y = np.pad(y, (0, target_samples - len(y)))
    else:
        y = y[:target_samples]
    return y


def extract_mel_features(audio_signal: np.ndarray,
                         sample_rate: int = SAMPLE_RATE,
                         n_fft: int = N_FFT,
                         hop_length: int = HOP_LENGTH,
                         n_mels: int = N_MELS,
                         fmin: float = F_MIN,
                         fmax: float = F_MAX,
                         power: float = 2.0,
                         top_db: float = 80.0) -> np.ndarray:
    """
    Извлечение mel-спектрограммы через librosa для ONNX.
    Возвращает numpy array формы [1, 1, n_mels, time].
    """
    mel = librosa.feature.melspectrogram(
        y=audio_signal, sr=sample_rate, n_fft=n_fft, hop_length=hop_length,
        n_mels=n_mels, fmin=fmin, fmax=fmax, power=power
    )
    mel_db = librosa.power_to_db(mel, top_db=top_db)
    # Добавляем batch и channel: [1, 1, n_mels, time]
    return mel_db[np.newaxis, np.newaxis, :, :].astype(np.float32)
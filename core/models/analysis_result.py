from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisSegment:
    """Сегмент анализа с временными метками."""
    start_time: float
    end_time: float
    label: str
    confidence: float
    features: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.start_time < 0:
            raise ValueError(f"start_time must be >= 0, got {self.start_time}")
        if self.end_time < self.start_time:
            raise ValueError(
                f"end_time ({self.end_time}) must be >= start_time ({self.start_time})"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if not self.label or not isinstance(self.label, str):
            raise ValueError(f"label must be a non-empty string, got {self.label!r}")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'label': self.label,
            'confidence': self.confidence,
            'features': self.features
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisSegment':
        return cls(
            start_time=data.get('start_time', data.get('segment_start', 0.0)),
            end_time=data.get('end_time', data.get('segment_end', 0.0)),
            label=data.get('label', 'unknown'),
            confidence=data.get('confidence', 0.0),
            features=data.get('features')
        )


@dataclass
class AnalysisResult:
    """Результат анализа аудио файла."""
    file_path: str
    segments: List[AnalysisSegment]
    total_duration: float
    analysis_duration: float
    model_used: str
    parameters: Dict[str, Any]
    created_at: datetime
    status: str = "completed"
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.total_duration < 0:
            raise ValueError(f"total_duration must be >= 0, got {self.total_duration}")
        if self.analysis_duration < 0:
            raise ValueError(f"analysis_duration must be >= 0, got {self.analysis_duration}")
        if not self.file_path or not isinstance(self.file_path, str):
            raise ValueError("file_path must be a non-empty string")
        if not self.model_used or not isinstance(self.model_used, str):
            raise ValueError("model_used must be a non-empty string")
        if self.status not in ('completed', 'error', 'pending', 'processing'):
            logger.warning("Unexpected status value: %r", self.status)

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def labels(self) -> List[str]:
        return list(dict.fromkeys(segment.label for segment in self.segments))

    def get_segments_by_label(self, label: str) -> List[AnalysisSegment]:
        return [seg for seg in self.segments if seg.label == label]

    def get_segments_in_time_range(
        self, start_time: float, end_time: float
    ) -> List[AnalysisSegment]:
        if start_time < 0 or end_time < 0:
            raise ValueError("Time values must be non-negative")
        if end_time < start_time:
            raise ValueError("end_time must be >= start_time")
        return [
            seg for seg in self.segments
            if seg.start_time < end_time and seg.end_time > start_time
        ]

    def to_dict(self) -> dict:
        return {
            'file_path': self.file_path,
            'segments': [seg.to_dict() for seg in self.segments],
            'total_duration': self.total_duration,
            'analysis_duration': self.analysis_duration,
            'model_used': self.model_used,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisResult':
        segments_data = data.get('segments', [])
        segments = []
        for seg_data in segments_data:
            try:
                segments.append(AnalysisSegment.from_dict(seg_data))
            except Exception as e:
                logger.warning("Skipping invalid segment: %s", e)

        created_at = datetime.now()
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError as e:
                logger.warning("Invalid created_at format, using now: %s", e)

        return cls(
            file_path=data.get('file_path', ''),
            segments=segments,
            total_duration=data.get('total_duration', data.get('file_duration', 0.0)),
            analysis_duration=data.get('analysis_duration', data.get('processing_time', 0.0)),
            model_used=data.get('model_used', 'unknown'),
            parameters=data.get('parameters', {}),
            created_at=created_at,
            status=data.get('status', 'completed'),
            error_message=data.get('error_message')
        )

    def __str__(self) -> str:
        return f"AnalysisResult({self.file_path}, {self.segment_count} segments, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()
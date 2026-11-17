"""Phase 3 processing and Phase 4 anomaly-scoring package."""

from edge.anomaly import ThresholdConfig, ThresholdScorer
from edge.features import (
    Spectrum,
    TimeDomainFeatures,
    as_resultant,
    compute_time_domain_features,
    dominant_frequency_hz,
    magnitude_spectrum,
)
from edge.interfaces import AnomalyResult, AnomalyScorer, FeatureVector, RawSampleWindowLike
from edge.pipeline import ProcessingConfig, SignalProcessingPipeline

__all__ = [
    "AnomalyResult",
    "AnomalyScorer",
    "FeatureVector",
    "ProcessingConfig",
    "RawSampleWindowLike",
    "SignalProcessingPipeline",
    "Spectrum",
    "ThresholdConfig",
    "ThresholdScorer",
    "TimeDomainFeatures",
    "as_resultant",
    "compute_time_domain_features",
    "dominant_frequency_hz",
    "magnitude_spectrum",
]

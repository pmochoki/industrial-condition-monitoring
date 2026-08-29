"""Phase 3 edge signal-processing package."""

from edge.features import (
    Spectrum,
    TimeDomainFeatures,
    as_resultant,
    compute_time_domain_features,
    dominant_frequency_hz,
    magnitude_spectrum,
)
from edge.interfaces import FeatureVector, RawSampleWindowLike
from edge.pipeline import ProcessingConfig, SignalProcessingPipeline

__all__ = [
    "FeatureVector",
    "ProcessingConfig",
    "RawSampleWindowLike",
    "SignalProcessingPipeline",
    "Spectrum",
    "TimeDomainFeatures",
    "as_resultant",
    "compute_time_domain_features",
    "dominant_frequency_hz",
    "magnitude_spectrum",
]

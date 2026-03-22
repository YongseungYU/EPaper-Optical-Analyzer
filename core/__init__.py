"""Core modules for E-paper Project."""

from core.parser import (
    CGATSParseError,
    get_lab,
    get_spectral,
    parse_cgats,
    parse_multiple,
    spectral_wavelengths,
)

__all__ = [
    "CGATSParseError",
    "get_lab",
    "get_spectral",
    "parse_cgats",
    "parse_multiple",
    "spectral_wavelengths",
]

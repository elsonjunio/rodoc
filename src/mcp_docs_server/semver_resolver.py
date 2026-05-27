import logging

from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)


def _parse(v: str) -> Version | None:
    try:
        return Version(v)
    except InvalidVersion:
        return None


def resolve(requested: str, available: list[str]) -> str | None:
    """Find the best compatible version from *available* for *requested*.

    Rules
    -----
    - Only same major is considered; cross-major fallback never happens.
    - Exact match is preferred.
    - Partial version (``20``, ``20.1``) resolves to the highest available
      version that shares the requested prefix within the same major.
    - If no prefix match exists, falls back to the highest available in the
      same major.
    """
    if not available:
        return None

    req = _parse(requested)
    if req is None:
        logger.warning("Cannot parse requested version: %s", requested)
        return None

    req_major = req.major
    req_parts = requested.split(".")

    # Filter to same major only
    same_major = [v for v in available if (p := _parse(v)) and p.major == req_major]
    if not same_major:
        logger.debug("No versions for major %d (available: %s)", req_major, available)
        return None

    # Exact match
    if requested in same_major:
        return requested

    # Sort descending (newest first)
    same_major_sorted = sorted(same_major, key=lambda v: _parse(v) or Version("0"), reverse=True)

    if len(req_parts) == 1:
        # Only major requested → latest in same major
        return same_major_sorted[0]

    # Build prefix for minor (and patch) matching
    req_minor = req_parts[1]
    minor_prefix = f"{req_major}.{req_minor}."
    minor_exact = f"{req_major}.{req_minor}"

    same_minor = [
        v for v in same_major
        if v.startswith(minor_prefix) or v == minor_exact
    ]

    if same_minor:
        return sorted(same_minor, key=lambda v: _parse(v) or Version("0"), reverse=True)[0]

    # No minor match → latest in same major
    return same_major_sorted[0]

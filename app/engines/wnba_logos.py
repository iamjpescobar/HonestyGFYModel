"""
WNBA team logos — ESPN's CDN, keyed by the ESPN team id the pipeline
already captures from each box score.

Mirrors engines/team_logos.py (MLB) so both sports render the same way.
No scraping and no stored image files: these are the same CDN URLs
ESPN's own site serves, requested by id.

Every helper returns None when an id is missing or unusable, and the
callers fall back to text — a missing logo never becomes a broken
image.
"""

_LOGO_URL = "https://a.espncdn.com/i/teamlogos/wnba/500/{tid}.png"


def logo_url_by_id(tid):
    """Logo URL for an ESPN WNBA team id, or None."""
    if tid in (None, "", 0):
        return None
    try:
        return _LOGO_URL.format(tid=int(tid))
    except (TypeError, ValueError):
        return None

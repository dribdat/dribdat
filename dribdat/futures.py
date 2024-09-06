# -*- coding: utf-8 -*-
"""Time zone and other timely business."""

# Deal with Python 3.10 vs 3.12 issues
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc

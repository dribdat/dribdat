# -*- coding: utf-8 -*-
"""Time zone and other timely business."""

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
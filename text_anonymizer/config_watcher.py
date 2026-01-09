"""
Stub config watcher - not implemented for lightweight version.
Kept for API compatibility only.
"""
from typing import Optional, Callable


class ConfigWatcher:
    """Stub watcher - does nothing in lightweight implementation."""

    def __init__(self,
                 config_dir: str,
                 enabled: bool = True,
                 on_change_callback: Optional[Callable] = None):
        """Initialize stub watcher (no-op)."""
        self.config_dir = config_dir
        self.enabled = False  # Always disabled
        self.on_change_callback = on_change_callback

    def start(self):
        """No-op start."""
        pass

    def stop(self):
        """No-op stop."""
        pass

    def is_running(self) -> bool:
        """Always returns False."""
        return False


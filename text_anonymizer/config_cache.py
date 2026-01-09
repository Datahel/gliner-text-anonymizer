"""
Lightweight configuration loader for text file-based settings.
Supports simple blocklist/grantlist and regex patterns via text files.
"""
import os
from typing import Optional, List, Dict, Set


class ConfigCache:
    """Simple configuration loader - not a singleton, just a utility."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize config loader with directory path."""
        if config_dir is None:
            # Default to config directory in project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(project_root, 'config')

        self.config_dir = config_dir

    @classmethod
    def instance(cls) -> 'ConfigCache':
        """Get singleton instance (for backward compatibility)."""
        return cls()

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for backward compatibility with tests)."""
        pass

    def get_blocklist(self, profile: str) -> Set[str]:
        """Get blocklist for given profile."""
        blocklist_path = os.path.join(self.config_dir, profile, 'blocklist.txt')
        return self._load_text_list(blocklist_path)

    def get_grantlist(self, profile: str) -> Set[str]:
        """Get grantlist (allowlist) for given profile."""
        grantlist_path = os.path.join(self.config_dir, profile, 'grantlist.txt')
        return self._load_text_list(grantlist_path)

    def get_regex_patterns(self, profile: str) -> List[Dict[str, str]]:
        """
        Get regex patterns for given profile.
        Loads from regex_patterns.txt with format:
        ENTITY_NAME: regex_pattern
        """
        regex_path = os.path.join(self.config_dir, profile, 'regex_patterns.txt')
        patterns = []

        if os.path.exists(regex_path):
            try:
                with open(regex_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and ':' in line:
                            entity_type, pattern = line.split(':', 1)
                            patterns.append({
                                'entity_type': entity_type.strip(),
                                'pattern': pattern.strip()
                            })
            except Exception as e:
                print(f"Warning: Failed to load regex patterns for profile '{profile}': {e}")

        return patterns

    def _load_text_list(self, filepath: str) -> Set[str]:
        """Load text list from file (one item per line)."""
        items = set()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            items.add(line)
            except Exception as e:
                print(f"Warning: Failed to load list from {filepath}: {e}")
        return items


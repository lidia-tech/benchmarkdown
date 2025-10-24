"""
Profile management for extractor configurations.

Handles saving, loading, listing, and deleting configuration profiles
as JSON files in a local directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError


class ProfileManager:
    """Manages configuration profiles stored as JSON files."""

    def __init__(self, config_dir: str = "./config"):
        """
        Initialize the profile manager.

        Args:
            config_dir: Directory to store profile JSON files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a profile name for use as a filename.

        Args:
            name: Profile name

        Returns:
            Sanitized filename (e.g., "Fast Mode" -> "fast_mode")
        """
        # Replace spaces with underscores, remove special characters
        sanitized = name.lower().replace(" ", "_")
        # Keep only alphanumeric and underscores
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return sanitized

    def save_profile(
        self,
        engine: str,
        profile_name: str,
        config_data: Dict[str, Any]
    ) -> str:
        """
        Save a configuration profile to disk.

        Args:
            engine: Extractor engine name (e.g., "Docling", "AWS Textract")
            profile_name: Human-readable profile name
            config_data: Dictionary of configuration values

        Returns:
            Path to the saved profile file

        Raises:
            ValueError: If profile_name is empty
        """
        if not profile_name or not profile_name.strip():
            raise ValueError("Profile name cannot be empty")

        filename = self._sanitize_filename(profile_name) + ".json"
        filepath = self.config_dir / filename

        profile = {
            "engine": engine,
            "profile_name": profile_name,
            "config_data": config_data
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Load a configuration profile from disk.

        Args:
            profile_name: Profile name (human-readable or sanitized)

        Returns:
            Dictionary with keys: engine, profile_name, config_data

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValueError: If profile file is corrupted
        """
        # Try both sanitized and as-is filename
        sanitized = self._sanitize_filename(profile_name)
        possible_files = [
            self.config_dir / f"{sanitized}.json",
            self.config_dir / f"{profile_name}.json"
        ]

        filepath = None
        for f in possible_files:
            if f.exists():
                filepath = f
                break

        if filepath is None:
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                profile = json.load(f)

            # Validate structure
            required_keys = ["engine", "profile_name", "config_data"]
            if not all(key in profile for key in required_keys):
                raise ValueError(f"Profile file is missing required keys: {required_keys}")

            return profile

        except json.JSONDecodeError as e:
            raise ValueError(f"Profile file is corrupted: {e}")

    def list_profiles(self, engine: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all available profiles, optionally filtered by engine.

        Args:
            engine: Filter profiles by engine (e.g., "Docling"). If None, list all.

        Returns:
            List of dicts with keys: profile_name, engine, filename
        """
        profiles = []

        for filepath in self.config_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    profile = json.load(f)

                # Filter by engine if specified
                if engine and profile.get("engine") != engine:
                    continue

                profiles.append({
                    "profile_name": profile.get("profile_name", filepath.stem),
                    "engine": profile.get("engine", "Unknown"),
                    "filename": filepath.name
                })

            except (json.JSONDecodeError, KeyError):
                # Skip corrupted files
                continue

        # Sort by profile name
        profiles.sort(key=lambda p: p["profile_name"])
        return profiles

    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a configuration profile.

        Args:
            profile_name: Profile name (human-readable or sanitized)

        Returns:
            True if deleted, False if not found

        Raises:
            OSError: If file deletion fails
        """
        # Try both sanitized and as-is filename
        sanitized = self._sanitize_filename(profile_name)
        possible_files = [
            self.config_dir / f"{sanitized}.json",
            self.config_dir / f"{profile_name}.json"
        ]

        for filepath in possible_files:
            if filepath.exists():
                filepath.unlink()
                return True

        return False

    def profile_exists(self, profile_name: str) -> bool:
        """
        Check if a profile exists.

        Args:
            profile_name: Profile name (human-readable or sanitized)

        Returns:
            True if profile exists, False otherwise
        """
        sanitized = self._sanitize_filename(profile_name)
        possible_files = [
            self.config_dir / f"{sanitized}.json",
            self.config_dir / f"{profile_name}.json"
        ]

        return any(f.exists() for f in possible_files)

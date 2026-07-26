"""Stable, namespace-aware seed derivation for reproducible experiments."""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass

MAX_SEED = 2**63 - 1


def _validate_seed(seed: int) -> None:
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"Seed must be between 0 and {MAX_SEED}, got {seed}.")


@dataclass(frozen=True)
class SeedPlan:
    """Derive independent deterministic seeds from a single root seed."""

    root_seed: int

    def __post_init__(self) -> None:
        _validate_seed(self.root_seed)

    def derive(self, namespace: str, index: int = 0) -> int:
        """Derive a stable integer seed for a named experiment component."""
        if not namespace:
            raise ValueError("A seed namespace must be non-empty.")
        if index < 0:
            raise ValueError("A seed index must be non-negative.")
        payload = f"{self.root_seed}:{namespace}:{index}".encode()
        digest = hashlib.blake2b(payload, digest_size=8).digest()
        return int.from_bytes(digest, "big") % (MAX_SEED + 1)


def apply_seed(seed: int) -> None:
    """Seed Python's standard pseudo-random generator and future child processes."""
    _validate_seed(seed)
    random.seed(seed, version=2)
    os.environ["PYTHONHASHSEED"] = str(seed)

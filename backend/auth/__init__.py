"""
Auth package initialization.

Avoid importing submodules at package import time to prevent circular
imports (e.g., `backend.services.auth_service` -> `backend.auth.config`).
Import public helpers directly from their modules where needed.
"""

__all__ = []

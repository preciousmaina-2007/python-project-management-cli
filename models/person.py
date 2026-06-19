"""Person model module.

This module defines the base :class:`~project_tracker.models.person.Person` class.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Person:
    """Base class for people managed by the application.

    Attributes:
        name: Person's display name.
    """

    name: str


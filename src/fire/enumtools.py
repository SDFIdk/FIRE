from enum import Enum
from typing import (
    List,
)


def enum_names(enum_class: Enum) -> List[str]:
    """
    Returnerer de egentlige navne blandt enumeration-medlemmerne i den givne enumeration.

    Formålet er at kunne få oplyst et komplet, men unikt sæt af de
    mulige værdier, den givne enumeration kan tage.

    """
    return [
        name for name, member in enum_class.__members__.items() if member.name == name
    ]


def enum_aliases(enum_class: Enum) -> List[str]:
    """Returnerer aliaser for enumeration-medlemmerne i den givne enumeration."""
    return [
        name for name, member in enum_class.__members__.items() if member.name != name
    ]


def enum_members(enum_class: Enum, names: List[str]) -> List[Enum]:
    """Returnerer de tilsvarende enumeration-medlemmer ud fra de oplyste navne."""
    return [enum_class[name] for name in names]


def default_enums(enum: Enum):
    """Returnerer liste med standard-enum-medlemmer for en given enum."""
    return enum_members(enum, enum_names(enum))


def selected_or_default(selected: str, enum: Enum) -> List[Enum]:
    """
    Returnerer valgt enum ud fra dens navn.

    Er den None, bliver alle standard-enumerationer for en enum

    """
    if selected is None:
        return default_enums(enum)
    return [enum[selected]]


def enum_values(enum: Enum) -> set:
    """Returnerer de unikke værdier for enumerations-medlemmers for en given enum."""
    return {item.value for item in enum}

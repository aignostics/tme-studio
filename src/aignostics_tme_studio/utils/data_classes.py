from attr import dataclass


@dataclass
class Statistic:
    """Statistic, with name and unit."""

    name: str
    formatter: str
    unit: str | None

    def __str__(self) -> str:
        """Format stat as string, using name and unit.

        Returns label string, e.g. "Relative area (%)" or "Region count".
        """
        y_label = self.name
        if self.unit is not None:
            y_label += f" ({self.unit})"
        return y_label

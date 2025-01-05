from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BalanceQuantity[T: (int, float)]:
    def __init__(self, value: T | None, unit: str) -> None:
        self._value = value
        self._unit = unit

    @classmethod
    def from_tello(cls, tello_str: str) -> BalanceQuantity:
        value, unit = tello_str.split(" ", 1)
        if value.lower() == "unlimited":
            return BalanceQuantity(None, unit)

        match unit:
            case "GB":
                return BalanceQuantity(float(value), unit)
            case "min" | "minutes":
                return BalanceQuantity(int(value), "minutes")
            case "text" | "texts":
                return BalanceQuantity(int(value), "texts")
            case _:
                raise ValueError(f"Unknown unit {unit}")

    def __add__(self, other: BalanceQuantity) -> BalanceQuantity:
        if self._value is None or other._value is None:
            return BalanceQuantity(None, self._unit)
        return BalanceQuantity(self._value + other._value, self._unit)

    def __str__(self) -> str:
        if self._value is None:
            return f"Unlimited {self._unit}"
        return f"{self._value} {self._unit}"


@dataclass
class AccountBalance:
    data: BalanceQuantity
    minutes: BalanceQuantity
    texts: BalanceQuantity

    def __add__(self, other: AccountBalance) -> AccountBalance:
        return AccountBalance(
            self.data + other.data,
            self.minutes + other.minutes,
            self.texts + other.texts,
        )

    def __str__(self) -> str:
        return f"{self.data}, {self.minutes}, {self.texts}"


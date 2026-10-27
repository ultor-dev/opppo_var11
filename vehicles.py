"""Практическая работа 1, вариант 11: Автомобильный транспорт."""
from abc import ABC, abstractmethod

class Vehicle(ABC):
    """Обобщённый артефакт: общие параметры - мощность двигателя и страна-производитель."""
    type_name = ""

    def __init__(self, engine_power: int, country: str):
        self.engine_power = engine_power
        self.country = country

    @abstractmethod
    def specific(self) -> dict:
        """Уникальные параметры альтернативы."""

    def fields(self) -> dict:
        """Все поля объекта (используются для проверки условия REM)."""
        data = {"type": self.type_name,
                "engine_power": self.engine_power,
                "country": self.country}
        data.update(self.specific())
        return data

    def __str__(self):
        parts = [f"{k}={v}" for k, v in self.fields().items() if k != "type"]
        return f"{self.type_name:<6} | " + "; ".join(parts)


class Truck(Vehicle):
    type_name = "Truck"

    def __init__(self, engine_power, country, capacity_kg: int):
        super().__init__(engine_power, country)
        self.capacity_kg = capacity_kg

    def specific(self):
        return {"capacity_kg": self.capacity_kg}


class Bus(Vehicle):
    type_name = "Bus"

    def __init__(self, engine_power, country, passengers: int):
        super().__init__(engine_power, country)
        self.passengers = passengers  # короткое целое

    def specific(self):
        return {"passengers": self.passengers}


class Car(Vehicle):
    type_name = "Car"

    def __init__(self, engine_power, country, doors: int, max_speed: int):
        super().__init__(engine_power, country)
        self.doors = doors
        self.max_speed = max_speed

    def specific(self):
        return {"doors": self.doors, "max_speed": self.max_speed}
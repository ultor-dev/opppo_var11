"""Обработчик файла команд ADD / REM / PRINT.

Формат команд (по одной в строке, пустые строки и строки с # игнорируются):
    ADD Truck; engine_power=300; country=Germany; capacity_kg=20000
    ADD Bus;   engine_power=250; country=Russia;  passengers=45
    ADD Car;   engine_power=150; country=Japan;   doors=4; max_speed=200
    REM <поле> <оператор> <значение>      например: REM engine_power > 200
    PRINT
Имена полей в ADD и REM одинаковы: type, engine_power, country, capacity_kg,
passengers, doors, max_speed.
Операторы: == != > < >= <=   (для строк - только == и !=; регистр не учитывается).
Имена команд и типов объектов регистр не учитывают.
"""
import operator
import re
import sys

from vehicles import Vehicle, Truck, Bus, Car

SHORT_MAX = 32767
OPS = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge,
       "<=": operator.le, ">": operator.gt, "<": operator.lt}
STR_FIELDS = {"type", "country"}
INT_FIELDS = {"engine_power", "capacity_kg", "passengers", "doors", "max_speed"}
KINDS = {"truck": "Truck", "bus": "Bus", "car": "Car"}
ALLOWED = {  # допустимые параметры ADD для каждого типа
    "Truck": {"engine_power", "country", "capacity_kg"},
    "Bus": {"engine_power", "country", "passengers"},
    "Car": {"engine_power", "country", "doors", "max_speed"},
}
CONDITION_RE = re.compile(r"^(\w+)\s*([^\w\s]+)\s*(.+)$")


class CommandError(Exception):
    pass


def to_int(text: str, name: str, lo=None, hi=None) -> int:
    try:
        value = int(text)
    except ValueError:
        raise CommandError(f"поле '{name}' должно быть целым числом, получено '{text}'")
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        if lo is not None and hi is not None:
            rng = f"от {lo} до {hi}"
        elif lo is not None:
            rng = f"не меньше {lo}"
        else:
            rng = f"не больше {hi}"
        raise CommandError(f"поле '{name}' должно быть {rng}, получено {value}")
    return value


def parse_add(arg: str) -> Vehicle:
    chunks = [c.strip() for c in arg.split(";") if c.strip()]
    if not chunks:
        raise CommandError("ADD: не указано описание объекта")
    kind = KINDS.get(chunks[0].lower())
    if kind is None:
        raise CommandError(f"неизвестный тип объекта '{chunks[0]}' (Truck, Bus, Car)")
    params = {}
    for c in chunks[1:]:
        if "=" not in c:
            raise CommandError(f"ожидалось 'ключ=значение', получено '{c}'")
        k, v = (x.strip() for x in c.split("=", 1))
        if k not in ALLOWED[kind]:
            raise CommandError(f"{kind}: неизвестный параметр '{k}' "
                               f"(допустимы: {', '.join(sorted(ALLOWED[kind]))})")
        if k in params:
            raise CommandError(f"параметр '{k}' указан дважды")
        params[k] = v

    missing = [n for n in sorted(ALLOWED[kind]) if n not in params]
    if missing:
        raise CommandError(f"{kind}: не хватает параметров {', '.join(missing)}")

    power = to_int(params["engine_power"], "engine_power", 1)
    country = params["country"]
    if not country:
        raise CommandError("country не может быть пустым")

    if kind == "Truck":
        return Truck(power, country, to_int(params["capacity_kg"], "capacity_kg", 1))
    if kind == "Bus":
        return Bus(power, country, to_int(params["passengers"], "passengers", 1, SHORT_MAX))
    doors = to_int(params["doors"], "doors")
    if doors not in (2, 3, 4, 5):
        raise CommandError(f"doors должно быть 2, 3, 4 или 5, получено {doors}")
    return Car(power, country, doors, to_int(params["max_speed"], "max_speed", 1))


def parse_condition(arg: str):
    """Возвращает функцию-предикат для объекта."""
    m = CONDITION_RE.match(arg.strip())
    if not m:
        raise CommandError("REM: условие должно иметь вид '<поле> <оператор> <значение>'")
    field, op, raw = m.group(1), m.group(2), m.group(3).strip()
    if field not in STR_FIELDS | INT_FIELDS:
        raise CommandError(f"REM: неизвестное поле '{field}'")
    if op not in OPS:
        raise CommandError(f"REM: неизвестный оператор '{op}'")
    if field in STR_FIELDS:
        if op not in ("==", "!="):
            raise CommandError("REM: для строковых полей допустимы только == и !=")
        value = raw.lower()
    else:
        value = to_int(raw, field)

    def predicate(v: Vehicle) -> bool:
        data = v.fields()
        if field not in data:
            return False
        current = data[field]
        if field in STR_FIELDS:
            current = current.lower()
        return OPS[op](current, value)
    return predicate


class Processor:
    def __init__(self):
        self.container: list[Vehicle] = []

    def add(self, arg):
        self.container.append(parse_add(arg))

    def rem(self, arg):
        pred = parse_condition(arg)
        before = len(self.container)
        self.container = [v for v in self.container if not pred(v)]
        return before - len(self.container)

    def print_all(self):
        if not self.container:
            print("  (контейнер пуст)")
        for i, v in enumerate(self.container, 1):
            print(f"  {i}. {v}")

    def run_line(self, line: str):
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd == "ADD":
            self.add(arg)
            print(f"ADD: добавлен объект ({len(self.container)} в контейнере)")
        elif cmd == "REM":
            print(f"REM: удалено объектов: {self.rem(arg)}")
        elif cmd == "PRINT":
            print("PRINT:")
            self.print_all()
        else:
            raise CommandError(f"неизвестная команда '{cmd}'")

    def run_file(self, path: str):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    self.run_line(line)
                except CommandError as e:
                    print(f"Ошибка в строке {n}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python main.py <файл_команд>")
        sys.exit(1)
    try:
        Processor().run_file(sys.argv[1])
    except OSError as e:
        print(f"Не удалось открыть файл: {e}")
        sys.exit(1)
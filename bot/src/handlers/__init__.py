from aiogram import Dispatcher
from types import ModuleType
from importlib import import_module
import os
from pathlib import Path

LOADED_MODULES: dict[str, ModuleType] = {}
MODULES: list[str] = []

base_path = Path(__file__).parent
base_package = "src.handlers"

for root, _dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith(".py") and not file.startswith("_"):
            module_path = Path(root) / file
            module_name = (
                module_path.relative_to(base_path)
                .as_posix()
                .removesuffix(".py")
                .replace("/", ".")
            )
            MODULES.append(module_name)


def load_modules(
    dp: Dispatcher, to_load: list[str] | None = None, to_not_load: list[str] | None = None
) -> None:
    if to_not_load is None:
        to_not_load = []
    if to_load is None:
        to_load = ["*"]
    if "*" in to_load:
        to_load = MODULES
    else:
        print("...")

    for module_name in (x for x in MODULES if x in to_load and x not in to_not_load):
        if module_name == "inline":
            continue

        full_module_name = f"{base_package}.{module_name}"

        try:
            module = import_module(full_module_name)
            dp.include_router(module.router)
            LOADED_MODULES[module.__name__.split(".", 3)[2]] = module
            print(f"✅ : {full_module_name}")
        except Exception as e:
            print(f"❌ Xato {full_module_name}: {e}")

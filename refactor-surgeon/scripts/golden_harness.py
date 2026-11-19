"""Graba y verifica casos dorados de un módulo antes de refactorizarlo.

Uso:
    py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --record --allow-exec
    py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --verify --allow-exec

El fichero de casos declara el módulo y las llamadas:

```json
{"module": "app.py", "cases": [{"function": "sumar", "args": [1, 2]}]}
```

Ejecutar el módulo es una decisión explícita: sin `--allow-exec` el script solo
valida el fichero de casos y sale con 0 sin importar nada.

Código de salida: 0 OK · 1 discrepancia o error · 2 fichero ilegible o sin permiso
de ejecución cuando hacía falta.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path


def load_module(path: Path):
    source = path.read_text(encoding="utf-8")
    module = types.ModuleType(path.stem)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cases(module, cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        name = case["function"]
        entry = {"function": name, "args": case.get("args", []), "kwargs": case.get("kwargs", {})}
        try:
            value = getattr(module, name)(*entry["args"], **entry["kwargs"])
            entry["ok"] = True
            entry["result"] = value
        except Exception as error:  # el fallo también es comportamiento observable
            entry["ok"] = False
            entry["error"] = f"{type(error).__name__}: {error}"
        results.append(entry)
    return results


def comparable(entry: dict) -> tuple[bool, str]:
    return (entry.get("ok"), json.dumps(entry.get("result", entry.get("error")), sort_keys=True, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Casos dorados antes y después de refactorizar.")
    parser.add_argument("--cases", required=True, help="fichero de casos")
    parser.add_argument("--snapshot", required=True, help="fichero de resultados grabados")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--record", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--allow-exec", action="store_true", help="permite importar y ejecutar el módulo")
    args = parser.parse_args(argv)

    try:
        config = read_json(Path(args.cases))
    except (OSError, json.JSONDecodeError) as error:
        print(f"casos ilegibles: {error}")
        return 2
    if not isinstance(config, dict) or not config.get("cases"):
        print("no hay casos declarados")
        return 2
    cases = config["cases"]
    if not isinstance(cases, list):
        print("«cases» debe ser una lista")
        return 2
    for index, case in enumerate(cases, start=1):
        # Un caso sin `function` reventaba con KeyError al ejecutarlo.
        if not isinstance(case, dict) or not isinstance(case.get("function"), str) \
                or not case["function"].strip():
            print(f"caso {index}: falta «function» o no es una cadena")
            return 2
        if not isinstance(case.get("args", []), list):
            print(f"caso {index}: «args» debe ser una lista")
            return 2
        if not isinstance(case.get("kwargs", {}), dict):
            print(f"caso {index}: «kwargs» debe ser un objeto")
            return 2
    if not args.allow_exec:
        print(f"validado: {len(config['cases'])} casos, módulo {config.get('module')} sin ejecutar")
        return 0

    module_path = Path(config.get("module", ""))
    if not module_path.exists():
        print(f"módulo inexistente: {module_path}")
        return 2
    try:
        module = load_module(module_path)
    except Exception as error:
        print(f"no se pudo cargar el módulo: {type(error).__name__}: {error}")
        return 2

    results = run_cases(module, config["cases"])
    snapshot_path = Path(args.snapshot)

    if args.record:
        snapshot_path.write_text(json.dumps({"module": module_path.as_posix(), "results": results},
                                            indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"grabados {len(results)} casos en {snapshot_path}")
        return 0

    try:
        snapshot = read_json(snapshot_path)
        golden = snapshot["results"] if isinstance(snapshot, dict) else None
    except (OSError, KeyError, json.JSONDecodeError) as error:
        print(f"snapshot ilegible: {error}")
        return 2
    if not isinstance(golden, list):
        print("snapshot ilegible: «results» debe ser una lista")
        return 2

    diffs = []
    for old, new in zip(golden, results):
        if comparable(old) != comparable(new):
            diffs.append({"function": new["function"], "args": new["args"],
                          "golden": old.get("result", old.get("error")),
                          "actual": new.get("result", new.get("error"))})
    if len(golden) != len(results):
        print(f"el snapshot tiene {len(golden)} casos y hay {len(results)}")
        return 1

    for diff in diffs:
        print(f"[MISMATCH] {diff['function']}{tuple(diff['args'])}: "
              f"dorado={diff['golden']!r} actual={diff['actual']!r}")
    print(f"casos: {len(results)} · discrepancias: {len(diffs)}")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())

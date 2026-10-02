"""CLI: python -m autonomousmath.optimizer evolve|serve."""

import argparse
import json
from pathlib import Path

from .evolution import Evolution, EvolutionBusy


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evolve the math harness under a fixed final reviewer.")
    commands = parser.add_subparsers(dest="command", required=True)
    evolve = commands.add_parser("evolve", help="run or resume generations")
    evolve.add_argument("--workspace", required=True)
    evolve.add_argument("--offline", action="store_true", help="no model calls; labelled structural demonstration")
    evolve.add_argument("--backend", choices=("codex", "claude"), default="codex")
    evolve.add_argument("--generations", type=int, default=2)
    evolve.add_argument("--continuous", action="store_true", help="continue until soft/emergency stop")
    evolve.add_argument("--parallelism", type=int, default=1)
    evolve.add_argument("--population-size", type=int, default=4)
    evolve.add_argument("--episodes-per-task", type=int, default=1)
    evolve.add_argument("--direction", action="append", help="repeat to set the permanent evaluation task set")
    evolve.add_argument("--tasks", type=Path, help="JSON array of direction strings, fixed after initialization")
    serve = commands.add_parser("serve", help="local dashboard; opening it does not start model calls")
    serve.add_argument("--workspace", required=True)
    serve.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost", "::1"))
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.command == "serve":
        from autonomousmath.dashboard.server import serve as start_server
        return start_server(args.workspace, args.host, args.port)
    tasks = json.loads(args.tasks.read_text()) if args.tasks else args.direction
    optimizer = Evolution(args.workspace)
    try:
        result = optimizer.run(generations=args.generations, tasks=tasks,
            settings={"offline": args.offline, "backend": args.backend, "generations": args.generations,
                      "continuous": args.continuous, "parallelism": args.parallelism,
                      "population_size": args.population_size, "episodes_per_task": args.episodes_per_task})
    except (ValueError, EvolutionBusy) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

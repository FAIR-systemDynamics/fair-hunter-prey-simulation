# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
import argparse
import sys
from .workflows import create_crate, inspect_results, run_example


def main(argv=None):
    parser = argparse.ArgumentParser(description="FAIR teaching workflows. Simulations use PySD, not vendor applications.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run a preserved implementation through PySD")
    run.add_argument("--implementation", required=True, choices=("vensim", "stella"))
    run.add_argument("--case", required=True, choices=("case1", "case2"))
    run.add_argument("--output-dir", required=True)
    inspect = commands.add_parser("inspect", help="Inspect saved exports without running simulations")
    inspect.add_argument("--output-dir", required=True)
    crate = commands.add_parser("crate", help="Package an actual run as an RO-Crate")
    crate.add_argument("--run-dir", required=True)
    crate.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "run": result = run_example(args.implementation, args.case, args.output_dir)
        elif args.command == "inspect": result = inspect_results(args.output_dir)
        else: result = create_crate(args.run_dir, args.output_dir)
        print(result)
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

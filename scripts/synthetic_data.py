import argparse
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from claims_agent.core.config import get_settings
from claims_agent.db.repositories.postgres import (
    PostgresClaimRepository,
    PostgresCoverageRepository,
)
from claims_agent.db.session import make_engine
from claims_agent.synthetic.dataset import build_dataset, dataset_from_json, dataset_to_json
from claims_agent.synthetic.loader import load_cases, reset_synthetic_tenant

DEFAULT_FILE = Path("evals/datasets/synthetic_cases_v1.json")


def cmd_generate(args: argparse.Namespace) -> None:
    dataset = build_dataset(seed=args.seed, per_scenario=args.per_scenario)
    args.file.parent.mkdir(parents=True, exist_ok=True)
    args.file.write_text(dataset_to_json(dataset), encoding="utf-8", newline="\n")
    print(f"wrote {len(dataset.cases)} cases to {args.file}")


def cmd_load(args: argparse.Namespace) -> None:
    dataset = dataset_from_json(args.file.read_text(encoding="utf-8"))
    url = get_settings().database_url.get_secret_value()
    print(f"loading into database '{make_url(url).database}' (replacing tenant t-synth)")
    engine = make_engine(url)
    with Session(engine) as session:
        reset_synthetic_tenant(session)
        summary = load_cases(
            dataset.cases,
            PostgresClaimRepository(session),
            PostgresCoverageRepository(session),
        )
        session.commit()
    print(f"loaded {summary.claims} claims and {summary.coverage_periods} coverage periods")


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic claims dataset tools")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="write the dataset file")
    generate.add_argument("--seed", type=int, default=7)
    generate.add_argument("--per-scenario", type=int, default=25)
    generate.add_argument("--file", type=Path, default=DEFAULT_FILE)
    generate.set_defaults(func=cmd_generate)

    load = commands.add_parser("load", help="replace the synthetic tenant's data in the database")
    load.add_argument("--file", type=Path, default=DEFAULT_FILE)
    load.set_defaults(func=cmd_load)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
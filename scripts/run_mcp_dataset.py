import argparse
import asyncio
import sys
import time
from collections import Counter
from pathlib import Path
from mcp import Client
from claims_agent.domain.decision import DecisionType
from claims_agent.synthetic.dataset import dataset_from_json

DEFAULT_FILE = Path("evals/datasets/synthetic_cases_v1.json")
DEFAULT_URL = "http://127.0.0.1:8000/mcp"

def decide(status: str, duplicate_count: int) -> DecisionType:
    if status == "no_coverage_record":
        return DecisionType.PEND
    if status == "not_covered_on_date":
        return DecisionType.DENY
    if duplicate_count > 0:
        return DecisionType.DENY
    return DecisionType.APPROVE



async def call_tool(client: Client, tool: str, claim: dict) -> dict:
    result = await client.call_tool(tool, {"claim": claim})
    if result.is_error:
        raise RuntimeError(f"{tool} returned an error: {result.content[0].text}")
    return result.structured_content



async def run(url: str, file: Path, mode: str) -> int:
    dataset = dataset_from_json(file.read_text(encoding="utf-8"))
    total : Counter[str] = Counter()
    as_expected: Counter[str] = Counter()
    problems: list[str] = []

    started = time.perf_counter()
    async with Client(url) as client:
        for case in dataset.cases:
            claim = case.claim.model_dump(mode = "json", exclude={"tenant_id"})
            eligibility = await call_tool(client, "check_eligibility", claim)
            duplicates = await call_tool(client, "check_duplicates", claim)
            status = eligibility["status"]
            found = len(duplicates["possible_duplicates"])
            scenario = case.scenario.value
            total[scenario] += 1

            if mode == "labels":
                got = decide(status, found)
                ok = got is case.expected_decision    
                detail = f"expected {case.expected_decision.value}, got {got.value}"
            else:
                ok = status == "no_coverage_record" and found == 0
                detail = f"status {status}, duplicates {found}"

            if ok:
                as_expected[scenario] += 1
            else:
                problems.append(f"{case.case_id} ({scenario}): {detail}")

        with_tenant = dataset.cases[0].claim.model_dump(mode="json")
        injected = await client.call_tool("check_duplicates", {"claim": with_tenant})
    elapsed = time.perf_counter() - started

    for scenario in sorted(total):
        print(f"{scenario:<24} {as_expected[scenario]}/{total[scenario]}")
    calls = 2 * len(dataset.cases) + 1
    rejected = injected.is_error is True
    print(f"\ncases as expected: {sum(as_expected.values())}/{len(dataset.cases)} (mode: {mode})")
    print(f"tenant_id in arguments rejected: {rejected}")
    print(f"{calls} calls in {elapsed:.2f}s ({elapsed / calls * 1000:.0f} ms per call)")
    for line in problems[:5]:
        print("MISMATCH", line)
    if len(problems) > 5:
        print(f"... and {len(problems) - 5} more")
    return 0 if not problems and rejected else 1





def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic dataset through the MCP server.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--mode", choices=("labels", "isolation"), default = "labels")
    args = parser.parse_args()
    try:
        code = asyncio.run(run(args.url, args.file, args.mode))
    except Exception as exc:
        print(f"could not complete the run: {type(exc).__name__}: {exc}")
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
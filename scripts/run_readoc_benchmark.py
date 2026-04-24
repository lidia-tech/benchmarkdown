"""Run benchmarkdown extractors against READoc dataset and evaluate with all metrics.

Usage:
    uv run python scripts/run_readoc_benchmark.py /path/to/READoc
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from benchmarkdown.config_ui import build_config_from_ui_values
from benchmarkdown.extractors import ExtractorRegistry
from benchmarkdown.metrics import MetricRegistry


QUEUE_FILE = Path(__file__).parent.parent / ".task_queue.json"
MAX_CONCURRENT_PER_EXTRACTOR = 2


def discover_readoc_files(readoc_path: Path) -> list[dict]:
    """Find all PDF/ground-truth pairs in READoc dataset."""
    pairs = []
    for subset in ("arxiv", "github"):
        pdf_dir = readoc_path / "data" / subset / "pdf"
        md_dir = readoc_path / "data" / subset / "markdown"
        if not pdf_dir.exists():
            print(f"  Skipping {subset}: {pdf_dir} not found")
            continue
        for pdf_file in sorted(pdf_dir.glob("*.pdf")):
            gt_file = md_dir / f"{pdf_file.stem}.md"
            if gt_file.exists():
                pairs.append({
                    "subset": subset,
                    "name": pdf_file.stem,
                    "pdf": str(pdf_file),
                    "ground_truth": str(gt_file),
                })
            else:
                print(f"  Warning: no ground truth for {pdf_file.name}")
    return pairs


def load_tasks() -> list[dict]:
    """Load extraction tasks from .task_queue.json."""
    registry = ExtractorRegistry()
    registry.discover_extractors()

    with open(QUEUE_FILE) as f:
        saved_queue = json.load(f)

    tasks = []
    for task_data in saved_queue:
        engine = task_data["engine"]
        config_name = task_data["config_name"]
        config_dict = task_data["config_dict"]

        extractor_metadata = None
        for name, metadata in registry.get_available_extractors().items():
            if metadata.display_name == engine:
                extractor_metadata = metadata
                break

        if not extractor_metadata:
            print(f"  Skipping {engine}: extractor not available")
            continue

        config = build_config_from_ui_values(
            extractor_metadata.config_class, config_dict
        )
        extractor = extractor_metadata.extractor_class(config=config)
        tasks.append({
            "engine": engine,
            "config_name": config_name,
            "extractor": extractor,
            "label": f"{engine} ({config_name})",
        })

    return tasks


async def run_extraction(extractor, pdf_path: str) -> tuple[str, float, str | None]:
    """Run a single extraction, return (markdown, time, error)."""
    start = time.time()
    error = None
    markdown_text = ""
    try:
        markdown_text = await extractor.extract_markdown(pdf_path)
    except Exception as e:
        error = str(e)
    elapsed = time.time() - start
    return markdown_text, elapsed, error


async def compute_metrics(
    metric_instances: dict, ground_truth: str, extracted: str
) -> dict:
    """Compute all metrics, return {metric_name: {value, formatted, details}}."""
    results = {}
    for name, instance in metric_instances.items():
        try:
            result = await instance.compute(ground_truth, extracted)
            results[name] = {
                "value": result.value,
                "formatted": result.formatted_value or f"{result.value:.4f}",
                "details": result.details,
            }
        except Exception as e:
            results[name] = {"value": None, "formatted": "ERROR", "error": str(e)}
    return results


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/run_readoc_benchmark.py /path/to/READoc")
        sys.exit(1)

    readoc_path = Path(sys.argv[1])
    if not readoc_path.exists():
        print(f"Error: {readoc_path} does not exist")
        sys.exit(1)

    output_dir = Path(__file__).parent.parent / "data" / "eval_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    extractions_dir = Path(__file__).parent.parent / "data" / "readoc_extractions"
    extractions_dir.mkdir(parents=True, exist_ok=True)

    # Discover files
    print("Discovering READoc files...")
    file_pairs = discover_readoc_files(readoc_path)
    print(f"  Found {len(file_pairs)} PDF/ground-truth pairs")

    # Load tasks
    print("Loading extraction tasks...")
    tasks = load_tasks()
    print(f"  Loaded {len(tasks)} tasks: {[t['label'] for t in tasks]}")

    # Set up metrics
    print("Discovering metrics...")
    metric_registry = MetricRegistry()
    metric_registry.discover_metrics()
    available_metrics = metric_registry.get_available_metrics()
    metric_instances = {}
    for name, meta in available_metrics.items():
        metric_instances[name] = metric_registry.create_metric_instance(name)
    print(f"  {len(metric_instances)} metrics: {list(metric_instances.keys())}")

    # Run benchmark — parallel with per-extractor concurrency limit
    all_results = []
    total = len(file_pairs) * len(tasks)
    completed = 0
    results_lock = asyncio.Lock()

    # One semaphore per extractor engine to limit concurrency
    extractor_semaphores = {}
    for task in tasks:
        key = task["engine"]
        if key not in extractor_semaphores:
            extractor_semaphores[key] = asyncio.Semaphore(MAX_CONCURRENT_PER_EXTRACTOR)

    async def process_one(pair, task):
        nonlocal completed
        label = task["label"]
        gt_text = Path(pair["ground_truth"]).read_text()
        sem = extractor_semaphores[task["engine"]]

        # Check if extraction already exists on disk
        safe_label = task["config_name"].lower().replace(" ", "_")
        cached_path = extractions_dir / safe_label / pair["subset"] / f"{pair['name']}.md"

        if cached_path.exists():
            async with results_lock:
                completed += 1
                idx = completed
            extracted = cached_path.read_text()
            elapsed = 0.0
            error = None
            print(f"  [{idx}/{total}] {pair['subset']}/{pair['name']} <- {label}... CACHED ({len(extracted)} chars)")
        else:
            async with sem:
                async with results_lock:
                    completed += 1
                    idx = completed
                print(
                    f"  [{idx}/{total}] {pair['subset']}/{pair['name']} <- {label}...",
                    flush=True,
                )

                extracted, elapsed, error = await run_extraction(
                    task["extractor"], pair["pdf"]
                )

        if error:
            print(f"    -> {pair['name']} / {label}: ERROR ({elapsed:.1f}s): {error[:80]}")
            metrics = {
                name: {"value": None, "formatted": "ERROR", "error": error}
                for name in metric_instances
            }
        else:
            print(f"    -> {pair['name']} / {label}: OK ({elapsed:.1f}s, {len(extracted)} chars)")
            # Save extraction to disk immediately
            safe_label = task["config_name"].lower().replace(" ", "_")
            ext_dir = extractions_dir / safe_label / pair["subset"]
            ext_dir.mkdir(parents=True, exist_ok=True)
            (ext_dir / f"{pair['name']}.md").write_text(extracted)

            metrics = await compute_metrics(metric_instances, gt_text, extracted)

        result_entry = {
            "subset": pair["subset"],
            "document": pair["name"],
            "extractor": task["engine"],
            "config": task["config_name"],
            "label": label,
            "extraction_time_s": round(elapsed, 2),
            "extracted_chars": len(extracted) if not error else 0,
            "ground_truth_chars": len(gt_text),
            "error": error,
            "metrics": metrics,
        }
        async with results_lock:
            all_results.append(result_entry)

    # Launch all tasks in parallel
    coros = []
    for pair in file_pairs:
        for task in tasks:
            coros.append(process_one(pair, task))

    print(f"\nRunning {total} extractions ({MAX_CONCURRENT_PER_EXTRACTOR} parallel per extractor)...")
    await asyncio.gather(*coros)

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"readoc_benchmark_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "benchmark": "READoc",
                "timestamp": timestamp,
                "document_count": len(file_pairs),
                "extractor_count": len(tasks),
                "metric_count": len(metric_instances),
                "metrics_available": list(metric_instances.keys()),
                "extractors": [
                    {"engine": t["engine"], "config": t["config_name"]}
                    for t in tasks
                ],
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"\nResults saved to {output_file}")

    # Print summary table
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    # Group by extractor
    from collections import defaultdict

    by_extractor = defaultdict(list)
    for r in all_results:
        by_extractor[r["label"]].append(r)

    metric_names = list(metric_instances.keys())
    header = f"{'Extractor':<45} {'Docs':>4}"
    for m in metric_names:
        header += f" {m:>16}"
    print(header)
    print("-" * len(header))

    for label, results in by_extractor.items():
        valid = [r for r in results if r["error"] is None]
        row = f"{label:<45} {len(valid):>4}"
        for m in metric_names:
            values = [
                r["metrics"][m]["value"]
                for r in valid
                if r["metrics"].get(m, {}).get("value") is not None
            ]
            if values:
                avg = sum(values) / len(values)
                row += f" {avg * 100:>15.1f}%"
            else:
                row += f" {'N/A':>16}"
        print(row)

    errors = [r for r in all_results if r["error"] is not None]
    if errors:
        print(f"\n{len(errors)} extraction(s) failed:")
        for r in errors:
            print(f"  - {r['label']} / {r['document']}: {r['error'][:100]}")


if __name__ == "__main__":
    asyncio.run(main())

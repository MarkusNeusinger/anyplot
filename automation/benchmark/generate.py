"""CLI: generate one benchmark implementation with a Vertex AI model.

Usage (from the repo root, with the target library's extras installed):

    python -m automation.benchmark.generate \\
        --spec-id scatter-basic \\
        --library matplotlib \\
        --model google/gemini-2.5-pro \\
        --output-dir benchmark-results

Writes ``<output-dir>/<spec>/<library>/<model-slug>/`` containing the
generated code, both theme renders, each raw model response, and a
``result.yaml`` with the accounting (provider, attempts, latency, tokens,
canvas gate) that the future /benchmark leaderboard aggregates.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

import yaml

from automation.benchmark.prompting import build_generation_prompt, build_repair_prompt, extract_code_block
from automation.benchmark.runner import run_python_implementation
from automation.benchmark.vertex_client import VertexClient, resolve_provider
from core.constants import LIBRARIES_METADATA


BENCHMARK_RESULT_VERSION = 1

PYTHON_LIBRARIES = sorted(lib["id"] for lib in LIBRARIES_METADATA if lib["language_id"] == "python")


def slugify_model(model: str) -> str:
    """Filesystem-safe directory name for a Vertex model id."""
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


def accumulate_tokens(current: int | None, reported: int | None) -> int | None:
    """Add a reported token count, keeping ``None`` when nothing was reported.

    ``None`` means "the provider never reported usage" and must stay ``None``
    across attempts — recording 0 would look like a free run and skew the
    benchmark comparison.
    """
    if reported is None:
        return current
    return (current or 0) + reported


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1, got {number}")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one plot implementation with a Vertex AI model")
    parser.add_argument("--spec-id", required=True, help="Specification id, e.g. scatter-basic")
    parser.add_argument("--library", required=True, choices=PYTHON_LIBRARIES, help="Target library (Python only in v1)")
    parser.add_argument(
        "--model",
        required=True,
        help="Vertex model id: gemini-*, claude-*@<version>, or publisher-prefixed (meta/…, mistralai/…)",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GOOGLE_CLOUD_PROJECT", "anyplot"),
        help="GCP project id (default: $GOOGLE_CLOUD_PROJECT or 'anyplot')",
    )
    parser.add_argument("--location", default="us-central1", help="Vertex region for Gemini / Model Garden")
    parser.add_argument("--anthropic-location", default="us-east5", help="Vertex region for Claude models")
    parser.add_argument("--output-dir", default="benchmark-results", help="Root directory for benchmark output")
    parser.add_argument(
        "--max-attempts", type=_positive_int, default=3, help="Generation attempts (errors are fed back)"
    )
    parser.add_argument("--max-tokens", type=_positive_int, default=16000, help="Max output tokens per model call")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    parser.add_argument("--render-timeout", type=_positive_int, default=300, help="Seconds allowed per theme render")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]

    provider, normalized_model = resolve_provider(args.model)
    # Slug on the normalized id so 'gemini-2.5-pro' and 'google/gemini-2.5-pro'
    # (or 'anthropic/claude-*' and bare 'claude-*') land in the same folder.
    out_dir = Path(args.output_dir) / args.spec_id / args.library / slugify_model(normalized_model)
    out_dir.mkdir(parents=True, exist_ok=True)

    system, base_prompt = build_generation_prompt(repo_root, args.spec_id, args.library)
    client = VertexClient(project=args.project, location=args.location, anthropic_location=args.anthropic_location)

    result: dict = {
        "benchmark_result_version": BENCHMARK_RESULT_VERSION,
        "specification_id": args.spec_id,
        "library": args.library,
        "language": "python",
        "model": args.model,
        "normalized_model": normalized_model,
        "provider": provider,
        "project": args.project,
        "created": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "success": False,
        "attempts": 0,
        "max_attempts": args.max_attempts,
        "generation_seconds": 0.0,
        # null until a provider actually reports usage — 0 would read as
        # "free" and skew comparisons when a publisher omits usage data.
        "input_tokens": None,
        "output_tokens": None,
        "canvas_ok": None,
        # Whether the final response honored the "one fenced code block"
        # contract; extraction is deliberately lenient, so this is recorded
        # instead of enforced.
        "code_fenced": None,
        "error": None,
    }

    prompt = base_prompt
    code = ""
    for attempt in range(1, args.max_attempts + 1):
        result["attempts"] = attempt
        print(f"[benchmark] {args.spec_id}/{args.library} · {args.model} · attempt {attempt}/{args.max_attempts}")

        try:
            generation = client.generate(
                normalized_model, system, prompt, max_tokens=args.max_tokens, temperature=args.temperature
            )
        except Exception as exc:  # noqa: BLE001 — any provider error ends this model's run, recorded in result.yaml
            result["error"] = f"generation failed: {exc}"
            break

        result["generation_seconds"] = round(result["generation_seconds"] + generation.latency_seconds, 3)
        result["input_tokens"] = accumulate_tokens(result["input_tokens"], generation.input_tokens)
        result["output_tokens"] = accumulate_tokens(result["output_tokens"], generation.output_tokens)
        (out_dir / f"attempt-{attempt}-response.md").write_text(generation.text, encoding="utf-8")

        try:
            code = extract_code_block(generation.text)
            result["code_fenced"] = "```" in generation.text
        except ValueError as exc:
            result["error"] = str(exc)
            # Feed back THIS attempt's raw response — there is no code block to
            # show, and reusing an earlier attempt's extracted code here would
            # mislead the repair prompt.
            prompt = build_repair_prompt(
                base_prompt,
                generation.text.strip()[-4000:] or "(empty response)",
                f"{exc} — your previous response is shown above in place of code",
            )
            continue

        code_file = out_dir / f"{args.library}.py"
        code_file.write_text(code + "\n", encoding="utf-8")

        render = run_python_implementation(code_file, workdir=out_dir, timeout=args.render_timeout)
        if render.success:
            result["success"] = True
            result["canvas_ok"] = render.canvas_ok
            result["error"] = None
            break

        result["error"] = render.error
        prompt = build_repair_prompt(base_prompt, code, render.error or "unknown render error")

    result_file = out_dir / "result.yaml"
    with result_file.open("w", encoding="utf-8") as handle:
        handle.write(f"# Benchmark result for {args.spec_id} / {args.library} / {args.model}\n")
        handle.write("# Auto-generated by automation.benchmark.generate\n\n")
        yaml.dump(result, handle, default_flow_style=False, sort_keys=False, allow_unicode=True)

    status = "OK" if result["success"] else "FAILED"
    print(f"[benchmark] {status}: {result_file} (attempts={result['attempts']}, canvas_ok={result['canvas_ok']})")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

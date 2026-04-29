#!/usr/bin/env python3
"""
Sync plots from repository to PostgreSQL.

This script is run by GitHub Actions on push to main branch.
It ensures the database only contains data for code that is actually in main.

New structure (plots/{specification_id}/):
- specification.md: Spec description, data requirements, use cases
- specification.yaml: Spec-level metadata (tags, created, issue, suggested, updates)
- metadata/{library}.yaml: Per-library metadata (preview_url, quality_score, history)
- implementations/{library}.py: Library-specific implementation code

Legacy structure (still supported during migration):
- spec.md + metadata.yaml (single file with all library metadata)
"""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv


load_dotenv()

from itertools import islice  # noqa: E402

from sqlalchemy import delete, select, tuple_  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.constants import LANGUAGE_FILE_EXTENSIONS  # noqa: E402
from core.database import LANGUAGES_SEED, LIBRARIES_SEED, Impl, Language, Library, Spec  # noqa: E402
from core.database.connection import close_db_sync, get_db_context_sync, init_db_sync, is_db_configured  # noqa: E402


# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
PLOTS_DIR = BASE_DIR / "plots"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def convert_datetimes_to_strings(obj):
    """Recursively convert datetime objects to ISO strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetimes_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes_to_strings(item) for item in obj]
    return obj


def parse_timestamp(value) -> datetime | None:
    """Parse a timestamp from YAML (datetime or string) to naive datetime for DB."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        except ValueError:
            return None
    return None


def _validate_quality_score(score) -> float | None:
    """
    Validate and normalize a quality score.

    Args:
        score: Quality score value (int, float, or None)

    Returns:
        Validated score between 0-100, or None if invalid
    """
    if score is None:
        return None
    try:
        score_float = float(score)
        if 0 <= score_float <= 100:
            return score_float
        logger.warning(f"Quality score {score_float} out of range 0-100, setting to None")
        return None
    except (ValueError, TypeError):
        logger.warning(f"Invalid quality score '{score}', setting to None")
        return None


def parse_bullet_points(text: str) -> list[str]:
    """Extract bullet points from a markdown section."""
    bullets = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("* "):
            bullets.append(line[2:].strip())
    return bullets


def _parse_markdown_section(content: str, section_name: str, as_bullets: bool = False) -> str | list[str]:
    """
    Parse a markdown section by name.

    Args:
        content: Full markdown content
        section_name: Section heading (e.g., "Description", "Applications")
        as_bullets: If True, parse as bullet points; if False, return raw text

    Returns:
        Parsed section content as string or list of bullet points
    """
    pattern = rf"## {section_name}\s*\n(.+?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return [] if as_bullets else ""

    section_content = match.group(1).strip()
    if as_bullets:
        return parse_bullet_points(section_content)
    return section_content


def _validate_spec_id(spec_id: str) -> bool:
    """
    Validate that a spec ID follows the naming convention.

    Args:
        spec_id: The specification ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Spec IDs should be lowercase alphanumeric with hyphens only
    return bool(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", spec_id))


def parse_spec_markdown(file_path: Path) -> dict:
    """
    Parse a spec.md file and extract metadata.

    Args:
        file_path: Path to the spec.md file

    Returns:
        Dict with title, description, applications, data, notes
    """
    content = file_path.read_text(encoding="utf-8")
    spec_id = file_path.parent.name  # Directory name is spec_id

    # Validate spec_id format
    if not _validate_spec_id(spec_id):
        logger.warning(f"Spec ID '{spec_id}' does not follow naming convention (lowercase alphanumeric with hyphens)")

    # Parse title from first heading: "# scatter-basic: Basic Scatter Plot"
    title_match = re.search(r"^#\s+[\w-]+:\s*(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else spec_id

    # Parse sections using the unified helper
    description = _parse_markdown_section(content, "Description", as_bullets=False)
    applications = _parse_markdown_section(content, "Applications", as_bullets=True)
    data = _parse_markdown_section(content, "Data", as_bullets=True)
    notes = _parse_markdown_section(content, "Notes", as_bullets=True)

    return {
        "id": spec_id,
        "title": title,
        "description": description,
        "applications": applications,
        "data": data,
        "notes": notes,
    }


def parse_metadata_yaml(file_path: Path) -> dict | None:
    """
    Parse a metadata.yaml file.

    Args:
        file_path: Path to the metadata.yaml file

    Returns:
        Dict with spec_id, title, tags, implementations or None if invalid
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        # Accept both spec_id and specification_id (for backwards compatibility)
        if not data or ("spec_id" not in data and "specification_id" not in data):
            return None
        return data
    except Exception as e:
        logger.error(f"Failed to parse metadata {file_path}: {e}")
        return None


def parse_library_metadata_yaml(file_path: Path) -> dict | None:
    """
    Parse a per-library metadata/{library}.yaml file.

    Args:
        file_path: Path to the metadata file (e.g., metadata/matplotlib.yaml)

    Returns:
        Dict with library metadata or None if invalid
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not data or "library" not in data:
            return None
        return data
    except Exception as e:
        logger.error(f"Failed to parse library metadata {file_path}: {e}")
        return None


def scan_plot_directory(plot_dir: Path) -> dict | None:
    """
    Scan a single plot directory and extract all data.

    Supports both new structure (specification.md + specification.yaml + metadata/*.yaml)
    and legacy structure (spec.md + metadata.yaml) during migration.

    Args:
        plot_dir: Path to the plot directory (e.g., plots/scatter-basic/)

    Returns:
        Dict with spec data, metadata, and implementations
    """
    spec_id = plot_dir.name
    implementations_dir = plot_dir / "implementations"
    metadata_dir = plot_dir / "metadata"

    # Support both new (specification.md) and legacy (spec.md) file names
    spec_file = plot_dir / "specification.md"
    if not spec_file.exists():
        spec_file = plot_dir / "spec.md"  # Legacy fallback

    # Support both new (specification.yaml) and legacy (metadata.yaml) file names
    spec_metadata_file = plot_dir / "specification.yaml"
    legacy_metadata_file = plot_dir / "metadata.yaml"

    if not spec_file.exists():
        logger.warning(f"No specification.md or spec.md found in {plot_dir}")
        return None

    # Parse spec
    spec_data = parse_spec_markdown(spec_file)

    # Parse spec-level metadata (new structure: specification.yaml, legacy: metadata.yaml)
    metadata = {}
    if spec_metadata_file.exists():
        metadata = parse_metadata_yaml(spec_metadata_file) or {}
    elif legacy_metadata_file.exists():
        metadata = parse_metadata_yaml(legacy_metadata_file) or {}

    # Merge title from metadata if available
    if metadata.get("title"):
        spec_data["title"] = metadata["title"]

    # Add spec-level metadata from YAML
    spec_data["tags"] = convert_datetimes_to_strings(metadata.get("tags"))
    spec_data["issue"] = metadata.get("issue")
    spec_data["suggested"] = metadata.get("suggested")

    # Parse created/updated timestamps (convert to naive datetime for DB)
    spec_data["created"] = parse_timestamp(metadata.get("created"))
    spec_data["updated"] = parse_timestamp(metadata.get("updated"))

    # Scan implementations — supports both the new language-aware layout
    # (plots/{spec}/implementations/{language}/{library}.{ext}) and the legacy flat
    # layout (plots/{spec}/implementations/{library}.py, python-only).
    implementations = []
    if implementations_dir.exists():
        # Build a list of (language_id, impl_file) tuples to process
        impl_file_pairs: list[tuple[str, Path]] = []

        # New layout: language subdirectories
        for language_dir in sorted(implementations_dir.iterdir()):
            if not language_dir.is_dir() or language_dir.name.startswith("_") or language_dir.name.startswith("."):
                continue
            language_id = language_dir.name
            ext = LANGUAGE_FILE_EXTENSIONS.get(language_id)
            if ext is None:
                logger.warning(f"Unknown language directory '{language_id}' in {implementations_dir} — skipping")
                continue
            for impl_file in sorted(language_dir.glob(f"*{ext}")):
                if impl_file.name.startswith("_"):
                    continue
                impl_file_pairs.append((language_id, impl_file))

        # Legacy layout: flat .py files under implementations/ are implicitly python
        for impl_file in sorted(implementations_dir.glob("*.py")):
            if impl_file.name.startswith("_"):
                continue
            impl_file_pairs.append(("python", impl_file))

        for language_id, impl_file in impl_file_pairs:
            library_id = impl_file.stem  # e.g., "matplotlib", "seaborn"
            code = impl_file.read_text(encoding="utf-8")

            # Get implementation metadata — new path includes language,
            # legacy path is metadata/{library}.yaml (python-only, still supported during migration).
            impl_meta = {}
            language_metadata_file = metadata_dir / language_id / f"{library_id}.yaml"
            legacy_library_metadata_file = metadata_dir / f"{library_id}.yaml"
            if language_metadata_file.exists():
                impl_meta = parse_library_metadata_yaml(language_metadata_file) or {}
            elif language_id == "python" and legacy_library_metadata_file.exists():
                impl_meta = parse_library_metadata_yaml(legacy_library_metadata_file) or {}
            else:
                # Ancient layout: metadata.yaml -> implementations -> {library}
                impl_meta = metadata.get("implementations", {}).get(library_id, {})

            # Support both new flat structure and legacy current: nesting
            current = impl_meta.get("current") or impl_meta

            # Parse timestamps
            generated_at = parse_timestamp(current.get("generated_at") or impl_meta.get("created"))
            updated = parse_timestamp(impl_meta.get("updated"))

            # Parse review feedback (new structure)
            review = impl_meta.get("review") or {}

            # Validate quality score
            raw_quality_score = current.get("quality_score") or impl_meta.get("quality_score")
            quality_score = _validate_quality_score(raw_quality_score)

            # Validate review verdict
            review_verdict = review.get("verdict")
            if review_verdict and review_verdict not in ("APPROVED", "REJECTED"):
                logger.warning(
                    f"Invalid review verdict '{review_verdict}' for {spec_id}/{language_id}/{library_id}, setting to None"
                )
                review_verdict = None

            # Preview URLs — accept theme-aware fields (new) with fallback to single-theme legacy field.
            # Legacy single-theme preview_url is treated as the light variant.
            preview_url_light = impl_meta.get("preview_url_light") or impl_meta.get("preview_url")
            preview_url_dark = impl_meta.get("preview_url_dark")
            preview_html_light = impl_meta.get("preview_html_light") or impl_meta.get("preview_html")
            preview_html_dark = impl_meta.get("preview_html_dark")

            implementations.append(
                {
                    "spec_id": spec_id,
                    "language_id": language_id,
                    "library_id": library_id,
                    "code": code,
                    # Preview URLs — one pair per theme (filled by workflow)
                    "preview_url_light": preview_url_light,
                    "preview_url_dark": preview_url_dark,
                    "preview_html_light": preview_html_light,
                    "preview_html_dark": preview_html_dark,
                    # Versions (from metadata YAML, filled by workflow)
                    "python_version": current.get("python_version") or impl_meta.get("python_version"),
                    "library_version": current.get("library_version") or impl_meta.get("library_version"),
                    # Generation metadata
                    "generated_at": generated_at,
                    "updated": updated,
                    "generated_by": current.get("generated_by") or impl_meta.get("generated_by"),
                    "workflow_run": current.get("workflow_run") or impl_meta.get("workflow_run"),
                    "issue": current.get("issue") or impl_meta.get("issue"),
                    "quality_score": quality_score,
                    # Review feedback
                    "review_strengths": review.get("strengths") or [],
                    "review_weaknesses": review.get("weaknesses") or [],
                    # Extended review data
                    "review_image_description": review.get("image_description"),
                    "review_criteria_checklist": review.get("criteria_checklist"),
                    "review_verdict": review_verdict,
                    # Implementation-level tags
                    "impl_tags": impl_meta.get("impl_tags"),
                }
            )

    return {"spec": spec_data, "implementations": implementations}


def _chunked(iterable, size):
    """Split an iterable into chunks of a given size."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


# Chunk size for batched inserts (500 rows * ~25 cols = ~12,500 params, well within PG's 32,767 limit)
_BATCH_CHUNK_SIZE = 500

# All Impl fields that should be set from the excluded row on conflict
_IMPL_UPDATE_FIELDS = [
    "code",
    "preview_url_light",
    "preview_url_dark",
    "preview_html_light",
    "preview_html_dark",
    "python_version",
    "library_version",
    "generated_at",
    "updated",
    "generated_by",
    "workflow_run",
    "issue",
    "quality_score",
    "review_strengths",
    "review_weaknesses",
    "review_image_description",
    "review_criteria_checklist",
    "review_verdict",
    "impl_tags",
]


def sync_to_database(session: Session, plots: list[dict]) -> dict:
    """
    Sync plots to the database using batched upserts.

    Args:
        session: Database session
        plots: List of plot data dictionaries

    Returns:
        Dict with counts of synced/removed items
    """
    stats = {"specs_synced": 0, "specs_removed": 0, "impls_synced": 0, "impls_removed": 0}

    # Seed languages first (libraries.language_id FK requires languages to exist)
    if LANGUAGES_SEED:
        stmt = insert(Language).values(LANGUAGES_SEED).on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)

    # Batch seed all libraries in one statement
    if LIBRARIES_SEED:
        stmt = insert(Library).values(LIBRARIES_SEED).on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)

    # Collect all spec values and impl values
    spec_ids = set()
    impl_keys = set()  # (spec_id, language_id, library_id)
    all_spec_values = []
    all_impl_values = []

    for plot_data in plots:
        spec = plot_data["spec"]
        spec_ids.add(spec["id"])
        all_spec_values.append(spec)

        for impl in plot_data["implementations"]:
            impl_keys.add((impl["spec_id"], impl["language_id"], impl["library_id"]))
            all_impl_values.append(impl)

    # Batch upsert specs in chunks
    spec_update_fields = [
        "title",
        "description",
        "applications",
        "data",
        "notes",
        "created",
        "updated",
        "issue",
        "suggested",
        "tags",
    ]
    for chunk in _chunked(all_spec_values, _BATCH_CHUNK_SIZE):
        stmt = insert(Spec).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"], set_={field: stmt.excluded[field] for field in spec_update_fields}
        )
        session.execute(stmt)
    stats["specs_synced"] = len(all_spec_values)

    # Batch upsert implementations in chunks
    for chunk in _chunked(all_impl_values, _BATCH_CHUNK_SIZE):
        stmt = insert(Impl).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_impl", set_={field: stmt.excluded[field] for field in _IMPL_UPDATE_FIELDS}
        )
        session.execute(stmt)
    stats["impls_synced"] = len(all_impl_values)

    # Remove specs that no longer exist in repo
    result = session.execute(select(Spec.id).where(Spec.id.notin_(spec_ids)))
    removed_spec_ids = [row[0] for row in result.fetchall()]
    if removed_spec_ids:
        session.execute(delete(Spec).where(Spec.id.in_(removed_spec_ids)))
        stats["specs_removed"] = len(removed_spec_ids)
        logger.info(f"Removed {len(removed_spec_ids)} specs no longer in repo")

    # Remove impls that no longer exist in repo (language-aware comparison)
    result = session.execute(select(Impl.spec_id, Impl.language_id, Impl.library_id))
    existing_impls = [(row[0], row[1], row[2]) for row in result.fetchall()]

    removed_impls = [impl for impl in existing_impls if impl not in impl_keys]
    if removed_impls:
        session.execute(delete(Impl).where(tuple_(Impl.spec_id, Impl.language_id, Impl.library_id).in_(removed_impls)))
        stats["impls_removed"] = len(removed_impls)
        logger.info(f"Removed {len(removed_impls)} impls no longer in repo")

    session.commit()
    return stats


def main() -> int:
    """Main entry point for the sync script."""
    if not is_db_configured():
        logger.error("No database configuration found (DATABASE_URL or INSTANCE_CONNECTION_NAME)")
        return 1

    logger.info("Starting sync to PostgreSQL...")
    logger.info(f"Plots directory: {PLOTS_DIR}")

    # Scan all plot directories
    plots = []
    if PLOTS_DIR.exists():
        for plot_dir in sorted(PLOTS_DIR.iterdir()):
            if not plot_dir.is_dir():
                continue
            if plot_dir.name.startswith("."):
                continue

            plot_data = scan_plot_directory(plot_dir)
            if plot_data:
                plots.append(plot_data)
                logger.debug(f"Scanned plot: {plot_dir.name}")

    logger.info(f"Found {len(plots)} plots")

    total_impls = sum(len(p["implementations"]) for p in plots)
    logger.info(f"Found {total_impls} implementations")

    # Initialize database connection (uses sync pg8000 for Cloud SQL Connector)
    try:
        init_db_sync()
        with get_db_context_sync() as session:
            stats = sync_to_database(session, plots)

        logger.info("Sync completed successfully!")
        logger.info(f"  Specs synced: {stats['specs_synced']}, removed: {stats['specs_removed']}")
        logger.info(f"  Implementations synced: {stats['impls_synced']}, removed: {stats['impls_removed']}")
        return 0

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return 1

    finally:
        close_db_sync()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

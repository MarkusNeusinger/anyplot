#!/usr/bin/env python3
"""
AI-Powered Spec Upgrader

Uses Claude to intelligently upgrade spec files with semantic improvements,
not just structural changes.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

import anthropic


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local imports must come AFTER sys.path is patched so the script remains
# runnable from any working directory (Copilot review: PR #5414).
from core.config import settings  # noqa: E402


def get_spec_version(spec_content: str) -> str:
    """Extract spec version from content"""
    match = re.search(r"\*\*Spec Version:\*\*\s+(\d+\.\d+\.\d+)", spec_content)
    if match:
        return match.group(1)
    return "0.0.0"


def load_template(version: str) -> str:
    """Load template for target version"""
    if version == "1.0.0":
        template_path = Path("specs/.template.md")
    else:
        # Future: specs/.template-v{version}.md for historical templates
        template_path = Path("specs/.template.md")

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text()


def load_upgrade_instructions(from_version: str, to_version: str) -> str:
    """Load specific upgrade instructions for version transition"""
    instructions_path = Path(f"specs/upgrades/{from_version}-to-{to_version}.md")

    if instructions_path.exists():
        return instructions_path.read_text()

    # Default generic instructions
    return f"""
# Upgrade Instructions: {from_version} → {to_version}

## Goals
- Maintain the core intent and requirements of the spec
- Improve clarity and specificity
- Ensure quality criteria are measurable and actionable
- Update to latest template structure

## Specific Improvements
- Quality criteria should be concrete and verifiable (not vague like "looks good")
- Parameter descriptions should include types and ranges
- Use cases should be specific with domain examples
- Expected output should describe visual elements precisely

## Preserve
- Spec ID and title
- Core functionality and requirements
- Existing optional parameters (unless deprecated)
"""


def upgrade_spec_with_ai(
    spec_content: str, spec_id: str, target_version: str, api_key: str, dry_run: bool = False
) -> Tuple[bool, str, str]:
    """
    Use Claude to upgrade a spec to target version

    Returns:
        (success: bool, upgraded_content: str, message: str)
    """
    current_version = get_spec_version(spec_content)

    if current_version == target_version:
        return True, spec_content, f"Already at version {target_version}"

    # Load template and instructions
    template = load_template(target_version)
    upgrade_instructions = load_upgrade_instructions(current_version, target_version)

    # Build prompt for Claude
    prompt = f"""You are a technical documentation expert specializing in data visualization specifications.

# Task
Upgrade this plot specification from version {current_version} to version {target_version}.

# Current Spec
{spec_content}

# Target Template (v{target_version})
{template}

# Upgrade Instructions
{upgrade_instructions}

# Requirements

1. **Preserve Core Intent**
   - Keep spec ID and title identical
   - Maintain all required data parameters
   - Preserve optional parameters (unless explicitly deprecated)
   - Keep the fundamental purpose of the plot

2. **Improve Quality Criteria**
   - Make criteria specific and measurable
   - Replace vague terms ("looks good") with concrete checks
   - Ensure each criterion can be verified visually or programmatically
   - Examples:
     ❌ "Plot looks nice"
     ✅ "Grid is visible but subtle with alpha=0.3 and dashed linestyle"

3. **Enhance Parameter Descriptions**
   - Add explicit types (numeric, categorical, datetime, etc.)
   - Specify ranges where applicable (e.g., "0.0-1.0")
   - Include examples in descriptions

4. **Improve Use Cases**
   - Make use cases domain-specific
   - Include concrete examples with data types
   - Example: "Correlation analysis between height and weight in healthcare data"

5. **Update Metadata**
   - Set Spec Version to {target_version}
   - Set Template Version to {target_version}
   - Keep Created date (if present)
   - Update Last Updated to today (2025-01-24)

6. **Maintain Structure**
   - Follow the template structure exactly
   - Keep all required sections
   - Add any new sections from template

# Output Format
Provide ONLY the upgraded spec content in Markdown format.
Do NOT include explanations, just the spec file content.

Generate the upgraded spec now:"""

    if dry_run:
        return True, spec_content, f"Would upgrade from {current_version} to {target_version} using AI"

    # Call Claude. timeout caps a single request; SDK default max_retries (~2)
    # is fine here since this script has no outer retry handler.
    client = anthropic.Anthropic(api_key=api_key, timeout=300.0)

    response = client.messages.create(
        model=settings.claude_model, max_tokens=settings.claude_max_tokens, messages=[{"role": "user", "content": prompt}]
    )

    upgraded_content = response.content[0].text

    # Clean markdown code blocks if present
    if "```markdown" in upgraded_content:
        upgraded_content = upgraded_content.split("```markdown")[1].split("```")[0].strip()
    elif "```" in upgraded_content:
        upgraded_content = upgraded_content.split("```")[1].split("```")[0].strip()

    # Verify upgrade was successful
    new_version = get_spec_version(upgraded_content)
    if new_version != target_version:
        return False, spec_content, f"Upgrade failed: version is {new_version}, expected {target_version}"

    # Verify spec ID is preserved
    spec_id_pattern = r"^#\s+([a-z]+-[a-z]+-\d{3}):"
    old_match = re.search(spec_id_pattern, spec_content, re.MULTILINE)
    new_match = re.search(spec_id_pattern, upgraded_content, re.MULTILINE)

    if old_match and new_match:
        if old_match.group(1) != new_match.group(1):
            return (
                False,
                spec_content,
                f"Upgrade failed: spec ID changed from {old_match.group(1)} to {new_match.group(1)}",
            )
    elif old_match and not new_match:
        return False, spec_content, "Upgrade failed: spec ID was removed"

    return True, upgraded_content, f"Successfully upgraded from {current_version} to {target_version}"


def upgrade_spec_file_ai(
    spec_path: Path, target_version: str, api_key: str, dry_run: bool = False, backup: bool = True
) -> Tuple[bool, str]:
    """
    Upgrade a single spec file using AI

    Args:
        spec_path: Path to spec file
        target_version: Target version
        api_key: Anthropic API key
        dry_run: Don't write changes
        backup: Create .backup file before upgrading

    Returns:
        (success: bool, message: str)
    """
    try:
        content = spec_path.read_text()
        spec_id = spec_path.stem

        success, upgraded_content, message = upgrade_spec_with_ai(content, spec_id, target_version, api_key, dry_run)

        if not success:
            return False, message

        if dry_run:
            return True, message

        # Create backup
        if backup:
            backup_path = spec_path.with_suffix(f".md.backup-{get_spec_version(content)}")
            backup_path.write_text(content)
            print(f"   💾 Backup saved: {backup_path.name}")

        # Write upgraded content
        spec_path.write_text(upgraded_content)

        return True, message

    except Exception as e:
        return False, f"Error: {str(e)}"


def upgrade_all_specs_ai(
    target_version: str, api_key: str, dry_run: bool = False, backup: bool = True
) -> Dict[str, Tuple[bool, str]]:
    """
    Upgrade all spec files using AI

    Args:
        target_version: Target version
        api_key: Anthropic API key
        dry_run: Don't write changes
        backup: Create backup files

    Returns:
        Dict mapping spec_id to (success, message)
    """
    results = {}
    specs_dir = Path("specs")

    # Get all spec files (exclude template and backups)
    spec_files = [f for f in specs_dir.glob("*.md") if f.name != ".template.md" and not f.name.endswith(".backup")]

    for spec_path in spec_files:
        spec_id = spec_path.stem
        print(f"\n🔄 Processing: {spec_id}")

        success, message = upgrade_spec_file_ai(spec_path, target_version, api_key, dry_run, backup)

        results[spec_id] = (success, message)
        status = "✅" if success else "❌"
        print(f"{status} {message}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-powered spec upgrader using Claude")
    parser.add_argument("--version", default="1.0.0", help="Target version (default: 1.0.0)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument("--spec", help="Upgrade specific spec file (e.g., scatter-basic-001)")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup files")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        exit(1)

    print("🤖 AI-Powered Spec Upgrader")
    print(f"Target version: {args.version}")
    print(f"Dry run: {args.dry_run}")
    print(f"Backup: {not args.no_backup}")
    print("=" * 60)

    if args.spec:
        # Upgrade single spec
        spec_path = Path(f"specs/{args.spec}.md")
        if not spec_path.exists():
            print(f"❌ Spec not found: {spec_path}")
            exit(1)

        success, message = upgrade_spec_file_ai(spec_path, args.version, api_key, args.dry_run, not args.no_backup)

        status = "✅" if success else "❌"
        print(f"\n{status} {args.spec}: {message}")

        if not success:
            exit(1)
    else:
        # Upgrade all specs
        results = upgrade_all_specs_ai(args.version, api_key, args.dry_run, not args.no_backup)

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        total = len(results)
        succeeded = sum(1 for success, _ in results.values() if success)
        failed = total - succeeded

        print(f"Total: {total} | Succeeded: {succeeded} | Failed: {failed}")

        if failed > 0:
            print("\n❌ Failed specs:")
            for spec_id, (success, message) in results.items():
                if not success:
                    print(f"   - {spec_id}: {message}")
            exit(1)

    print("\n✅ Upgrade complete!")

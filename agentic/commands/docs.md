# Conditional Documentation Guide

> Slash command: `/docs`. Renamed from `context.md` so the project command does not collide with Claude Code's
> built-in `/context` command.

This prompt helps you determine what documentation you should read based on the specific changes you need to make
in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## Instructions

- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- README.md
  - Conditions:
    - When first understanding the project structure
    - When you want to learn the commands to start or stop the server
    - When setting up the development environment

- agentic/docs/project-guide.md
  - Conditions:
    - When understanding the full project architecture
    - When working on workflows or automation
    - When contributing to the project

- api/
  - Conditions:
    - When working with FastAPI backend
    - When modifying API routes or services
    - When working with database operations

- app/
  - Conditions:
    - When working with the React frontend
    - When modifying UI components
    - When working with TypeScript code

- core/
  - Conditions:
    - When working with shared Python modules
    - When modifying Pydantic models
    - When working with database utilities

- plots/
  - Conditions:
    - When working with plot specifications
    - When implementing new visualizations
    - When modifying existing plot implementations

- agentic/context/260207-footer-responsive-hide-name-add-contact-links.md
  - Conditions:
    - When working with the Footer component responsive behavior
    - When modifying contact or social links in the Legal page
    - When adjusting mobile breakpoint visibility of footer elements

- agentic/context/260214-batch-sync-to-postgres.md
  - Conditions:
    - When working with the PostgreSQL sync script (`automation/scripts/sync_to_postgres.py`)
    - When modifying batched upsert logic or chunk sizes for database sync
    - When troubleshooting sync-postgres workflow performance

- agentic/
  - Conditions:
    - When working with agentic commands or workflows
    - When creating or modifying prompt templates
    - When working with specs or context documentation

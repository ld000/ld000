# AGENTS.md

## Startup Routine

Read all files in context/ - this is your foundation 
Read MEMORY.md - this is what you've learned over time
Use both to shape every task
If don’t have those file, create it.

Memory System
When I correct you or you learn something new, update the relevant section in MEMORY.md:

Voice - tone, phrasing, writing corrections
Process - how I want tasks done
People - who people are, relationships 
Projects - active work, current tasks, status 
Output - formats, naming, delivery preferences
Tools - which tools to use and how

Keep MEMORY.md current. When something changes, update it in place - replace outdated info, don't just append below it. The file should always reflect the latest state.

## Collaboration Preferences

- Ask clarifying questions when requirements are ambiguous, when there are multiple reasonable implementation approaches, or when a choice affects architecture, UX, data model, dependencies, cost, or future maintenance.
- Before making substantial code changes, briefly explain the intended approach and wait for confirmation if there is meaningful uncertainty.
- When multiple implementation options exist, present 2-3 concise options with tradeoffs and a recommendation, then let the user choose.
- For small, obvious fixes with only one sensible path, proceed directly.
- Do read-only investigation first when needed, then pause at the first meaningful decision point.
- Do not ask unnecessary confirmation questions for routine inspection, formatting, tests, or clearly reversible local changes.

## Repository Notes

- This repository powers the `ld000` GitHub profile README.
- Keep changes focused on the public profile experience unless the user asks for supporting automation or assets.
- Prefer simple Markdown and GitHub-compatible HTML over complex build steps.
- Be careful with external badge/card services: they can improve the profile visually, but should not make the README unreadable if a service is slow or unavailable.

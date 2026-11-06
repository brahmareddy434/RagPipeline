# Operational scripts

Existing root scripts remain the supported entry points during the initial design pass:
- start_course.ps1: existing local HR course application.
- run_evals.ps1, run_week7.ps1, run_week8.ps1: historical evaluation/demo workflows.
- run_week9.ps1: MCP tests, server, discovery and live demo options.

Move each script here only with path-independent resolution and a thin root compatibility wrapper. Generated run output stays in ignored course/results/ or logs/. No install/build script is introduced just to create a directory.

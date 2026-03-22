# AI-Powered Resource Extraction Specification

This document outlines the plan for implementing automatic resource extraction for Dribdat projects.

## Goal
To automatically identify and attribute frameworks, AI models, software tools, and datasets used in a project by analyzing its Pitch, Readme, and Activity Log.

## Mechanism
Resource extraction will be triggered:
1. Manually by a team member via an "Extract Resources" button.
2. Automatically during a project "Sync" operation.
3. Optionally after a new Post is made to the activity log.

## Extraction Logic

### Phase 1: Heuristic Extraction (Regex)
- Identify common URLs (e.g., `huggingface.co/*`, `github.com/*`, `pypi.org/project/*`).
- Parse the URL to get a candidate name (e.g., "llama-3-8b").
- Fetch basic metadata if possible (e.g., via HuggingFace API or GitHub API).

### Phase 2: AI-Powered Extraction
- Send the project description (`longtext` + `autotext`) and recent activity log to an LLM.
- Use a system prompt to request a JSON list of resources.
- LLM should identify:
    - **Name**: The name of the tool/model.
    - **URL**: A relevant link.
    - **Type**: model, tool, dataset, or framework.
    - **Usage**: A short sentence on how it was used (for the description).
    - **License**: If mentioned in the documentation.

### Example LLM Prompt
```text
Analyze the following hackathon project documentation and list all technical resources used (models, libraries, datasets, tools).
Return the result as a JSON list of objects with the following keys: name, source_url, type, description, license.

Project Documentation:
{{project_text}}
```

## Integration
- Extracted resources should be presented to the user for confirmation before being saved to the project's `Resource` list.
- A "Review Pending Resources" UI will be added to the project resources tab.

## Future Enhancements
- Link extracted resources to existing projects in "Bootstrap" events.
- Generate "Model Cards" automatically from HuggingFace metadata.

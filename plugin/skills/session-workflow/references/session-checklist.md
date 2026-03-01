# Session Pre-Close Checklist

Run through this checklist before closing a research session. Each item ensures no knowledge is lost.

## 1. Knowledge Extraction

- [ ] Were key insights captured as individual notes?
- [ ] Are notes atomic (one idea per note)?
- [ ] Do notes have descriptive titles?
- [ ] Are notes tagged with `domain/scope` tags?

## 2. Resource Capture

- [ ] Were external sources (articles, papers, tools) saved as references?
- [ ] Do references include URLs where applicable?
- [ ] Are references classified with subtypes (`article`, `tool`, `spec`)?

## 3. Decision Recording

- [ ] Were any decisions made during this session?
- [ ] Are decisions captured with the `decision` subtype?
- [ ] Do decision notes include: Context, Choice, Rationale, Alternatives, Consequences?

## 4. Task Tracking

- [ ] Were follow-up actions identified?
- [ ] Are tasks created with appropriate priority/impact/effort?
- [ ] Are blockers documented on blocked tasks?

## 5. Connections

- [ ] Do new notes contain wikilinks to related existing content?
- [ ] Was reweave run to discover missed connections?
- [ ] Are there orphan notes (0 outgoing links) that need attention?

## 6. Session Summary

- [ ] Can you summarize what was accomplished in 2-3 sentences?
- [ ] Does the summary capture the key outcomes?

## Usage

When closing a session, walk through each section. If any items are incomplete:
1. Create the missing content
2. Add the missing connections
3. Then close the session with a comprehensive summary

The session close enrichment pipeline (reweave, orphan sweep, integrity check) will handle automated connection discovery, but explicit human-driven connections are always higher quality.

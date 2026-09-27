# Documentation

| File | Content |
|---|---|
| `ARCHITECTURE.md` | Current system components, data lifecycle, planner pipeline, API, and decisions |
| `DEPLOY.md` | Render live demo, quotas and replay, judging keep-alive, and the static Space backup |
| `api-examples/` | Example JSON for every API route, generated from the code |
| `submission.md` | Ready-to-paste submission-form text |
| `screenshots/` | Screenshots used by the README and the documentation |

Bulk-approval evidence: [review preview](screenshots/t24-bulk-preview.png)
and [partial-success result](screenshots/t24-bulk-result.png), captured with the
fake-provider browser tests. The [eligibility rule](../web/README.md#bulk-reply-eligibility)
describes which replies can be included.

Issue-filter evidence: [desktop](screenshots/t25-filters-desktop.png) and
[400 px controls](screenshots/t25-filters-400.png), captured by the shared browser
checks. The [filter behavior](../web/README.md#issue-filters) explains status
categories, search, browser preferences and event-wide action scope.

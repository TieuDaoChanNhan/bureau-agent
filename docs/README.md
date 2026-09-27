# Documentation

Task codes such as T24 and numbers such as #103 refer to this repository's GitHub issues
and pull requests, where each change was specified and reviewed.

| File | Content |
|---|---|
| `ARCHITECTURE.md` | Current system components, data lifecycle, planner pipeline, API, and decisions |
| `DEPLOY.md` | Render live demo, quotas and replay, judging keep-alive, and the static Space backup |
| `api-examples/` | Example JSON for every API route, generated from the code |
| `demo-script.md` | 1:58 Render short-tour video: English recording instructions, French voice-over and callouts, English and French subtitle tracks |
| `demo-subtitles.en.srt` | Draft English subtitle cues for the 1:58 video; retime against the recorded French narration |
| `demo-subtitles.fr.srt` | Draft French subtitles matching the narration verbatim; retime against the generated audio |
| `submission.md` | Ready-to-paste submission-form text |
| `screenshots/` | The screenshots used by the README and public-demo verification |

T24 bulk-approval evidence: [review preview](screenshots/t24-bulk-preview.png)
and [partial-success result](screenshots/t24-bulk-result.png), captured with the
fake-provider browser tests. The [eligibility rule](../web/README.md#bulk-reply-eligibility-t24)
describes which replies can be included.

T25 issue-filter evidence: [desktop](screenshots/t25-filters-desktop.png) and
[400 px controls](screenshots/t25-filters-400.png), captured by the shared browser
checks. The [filter behavior](../web/README.md#issue-filters-t25) explains status
categories, search, browser preferences and event-wide action scope.

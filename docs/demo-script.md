# Demo video script (≤ 2:00)

The script for the submission video. It follows the guided demo, so the same clicks can be rehearsed with **Start the guided demo**.

## Before recording
- Run the latest `main` locally with `OPENAI_MODEL=gpt-4.1`, or use the deployed Space. Hard-reload the page (Ctrl+Shift+R).
- **Light theme**, browser zoom 110–125%, window 1440×900 or larger, no bookmarks bar, notifications off.
- **Reset demo** (click twice) on both events.
- The live agent takes 10–20 s per issue. Record in one take and **cut the waits** in editing; do not speed-ramp the agent steps, since the viewer should see them appear. Alternatively, pre-run the agent on `message:m01` and on the trip, then Reset only what you replay.
- Record the voice separately if possible (a quiet room, one take per segment). Add subtitles; many judges watch without sound.
- Keep the cursor slow and point at what you talk about.

## Timeline

| Time | Screen | Action | Voice-over (English) |
|---|---|---|---|
| 0:00–0:12 | Hero | Still; slow scroll to the three numbers | "Volunteer boards run events on top of their studies: registrations, payments, teams, trips, and dozens of messages. Bureau Agent does the legwork. You keep every decision." |
| 0:12–0:22 | Console, hackathon | Show the issue list; hover the Blocking group | "Code first reads the event and finds what needs attention: 31 issues in this hackathon, blocking ones first. No AI yet." |
| 0:22–0:45 | Antoine's email | **Run agent on this issue**; the thinking card, then the agent steps appearing | "Antoine says he already paid from his personal email. The agent chooses its own tools: it looks him up, reads the unmatched payments, and scores the identity match: 0.91. Not sure enough, so it asks me instead of guessing." |
| 0:45–1:00 | Proposal card | **Edit** the reply, add a word, **Save**, **Confirm and link**; open **Outbox** | "It drafted the reply in French. I edit it and approve. Only now is the payment linked, and the reply I approved goes out. The payment issue disappears." |
| 1:00–1:12 | New message | Personal-data example → **Send to the agent** | "A sponsor asks for everyone's phone numbers. The agent checks the rules, finds the personal-data section, and escalates. It refuses to share." |
| 1:12–1:22 | Short cut to the evaluation table in the README, or say it over the console | — | "Rules that must hold are enforced in code. When a weaker model tried to link a payment to the wrong person, the code refused it. On 50 labeled messages, the agent picks the right action 90% of the time." |
| 1:22–1:48 | WEI tab → trip | **Plan the trip** → (answer the question if one is asked) → package cards → **what-if budget** → diagnosis | "Same loop, harder problem: a trip for [N] students. It turns the organizers' words into constraints, [asks before searching,] builds packages from real hotel offers, and checks every one in code. Lower the budget and nothing fits. It says what would have to change, and never relaxes a constraint by itself." |
| 1:48–2:00 | **Choose option** → issues unlock; end card | Choose; show Waiting → Not analysed; end card with name and links | "I choose, and the reminders, rooms and meeting time unlock. Bureau Agent: the agent investigates, you decide." |

Bracketed parts depend on the final WEI scenario (#15): headcount, whether the planner asks a question, and the requested and what-if budgets. Update them once #15 is merged.

## End card (3 s)
**Bureau Agent** · An operations agent for volunteer-run associations · repository and live demo links · team names.

## Checklist before upload
- [ ] Length ≤ 2:00 (check the exported file, not the timeline).
- [ ] No API key, `.env` or personal notification visible on screen.
- [ ] Subtitles burned in or uploaded; the audio is clear.
- [ ] Uploaded unlisted (YouTube or similar) and plays in a private window; link added to the README and the submission form.

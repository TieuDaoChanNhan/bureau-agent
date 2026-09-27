# Demo video script — short tour, French voice-over (1:58)

Record [Bureau Agent on Render](https://bureau-agent.onrender.com/#top). Use **Start the guided demo · 3 min** in the hero, or **Quick tour** in the top bar, to start the default **15-step short tour**. Recording instructions are in English; the voice-over and on-screen callouts remain in French. Include **English subtitles** so viewers who do not speak French can follow along.

**Voice-over production:** generate the French narration with **Gradium**, using access provided by the hackathon sponsor. Generate one clip per timeline row, check the pronunciation of names and amounts, and fit each clip to its scene at a natural pace. Align both subtitle tracks to the generated audio and include the Gradium credit on the end card below.

This is the recording script for [issue #16](https://github.com/TieuDaoChanNhan/bureau-agent/issues/16). The target export is **1 minute 58 seconds, including a 3-second end card**, leaving two seconds below the submission limit. The interactive tour takes about three minutes; the video cuts waiting time and time spent reading the tour popovers.

## Story and features

A student has paid but still receives reminders. The agent checks the records, asks when the identity match is uncertain, and waits for an organizer's approval. A request for personal data leads to a rules lookup and escalation. The same loop handles a trip: understand the request, clarify the budget, check and rank packages, diagnose an infeasible budget, and unlock dependent work after the organizer chooses a plan.

Follow `QUICK` in [web/tour.js](../web/tour.js). The short tour has no separate steps for editing replies, opening Outbox or Evidence, or inspecting individual Agent steps; those belong to the full tour. The narration about the draft reply and simulated outbox describes the effect of approval without leaving the short tour.

## Before recording

1. Open the Render link, let it load, then hard-refresh with **Ctrl+Shift+R**. Use the light theme and a window of at least 1440×900. Adjust zoom so the highlighted button and popover fit; turn off personal notifications. Do not use the Hugging Face backup for this script: it has a different package fixture.
2. Click **Start the guided demo · 3 min** or the top-bar **Quick tour**, and verify **Step 1 of 15**. The first **Next →** resets both sample events. Avoid the hero **Full tour · 6 min** and top-bar **Full tour** buttons. The 15-step count identifies the correct tour.
3. Rehearse once: coach-budget question → F/C/E pass at €150 → none passes at €120 → restore €150 → choose F → six issues unlock. Check the result-source labels described below before recording the voice-over.
4. Capture the whole run and generate the French narration separately with sponsor-provided Gradium access, one row at a time. Wait for the real result, then cut the wait while preserving the click and its corresponding result. Show **« Temps d’attente coupés »** so video duration does not imply system latency. Do not speed up the evidence viewers need to read.
5. On action steps, click the highlighted control and let the tour advance automatically. On explanation steps, hold the result for the allotted time, then click **Next →**. Burn in English subtitles, at most two lines at a time, away from buttons, prices and verification labels. An additional selectable French subtitle track is optional.
6. Import [demo-subtitles.en.srt](demo-subtitles.en.srt) for English subtitles and [demo-subtitles.fr.srt](demo-subtitles.fr.srt) for the optional French track, which follows the narration verbatim. Both use this 1:58 storyboard; **retime both tracks to the generated French speech and final edit** before export. Keep French callouts separate from dialogue subtitles. If a shot or spoken line changes, update both tracks.

## Timeline and voice-over

Times below refer to the **edited video**, not API response times. Speak naturally; do not read English button labels or supplementary callouts aloud. Numbers that are spoken are written out in French.

| Time | Short-tour step | Screen and recorder action | Evidence to keep visible | Voice-over — français |
|---|---|---|---|---|
| **0:00–0:07** | **1 — welcome** | Start at the hero and click **Start the guided demo · 3 min**. Hold the introduction, then click **Next →** to reset and open Antoine's case. | Code detects; the agent investigates; organizers decide. | « Inscriptions, paiements, messages : le code repère les problèmes, l’agent enquête, les bénévoles décident. » |
| **0:07–0:17** | **2 — investigate** | Click **Run agent on this issue**. Capture the thinking state and the resulting proposal; cut the wait. Do not add a separate trace-inspection scene outside the tour. | Antoine paid from his personal email; several records need to be matched. | « Antoine a payé, mais reçoit encore des relances. L’agent choisit ses outils pour rapprocher son inscription des paiements. » |
| **0:17–0:24** | **3 — asks** | Hold the confirmation question, pointing to **0.91** and **Needs you** if visible; click **Next →**. | The agent asks a person when uncertain; a match score is not a probability. | « La correspondance reste incertaine. L’agent propose un rapprochement et me demande de confirmer. » |
| **0:24–0:31** | **4 — approve** | Hold the proposal, then click **Confirm and link**. The tour automatically opens the form in step 5; do not add **Edit**, **Outbox** or **New message** clicks. | Approval links the payment; the reply enters a simulated outbox. | « Je valide : le paiement est rattaché. La réponse est placée dans une boîte d’envoi simulée. » |
| **0:31–0:36** | **5 — risky** | The phone-number request form is already open and prefilled. Click **Send to the agent**; cut the wait. | A different request leads to a different decision. | « Un sponsor demande les numéros de téléphone des participants. » |
| **0:36–0:43** | **6 — refuses** | Hold the escalation, pointing to **Ask the organizers** and the rule reference if visible, then click **Next →**. | The request goes to organizers; no data is shared and no refusal message is automatically sent. | « L’agent consulte le règlement et transmet la demande aux organisateurs, sans partager les données. » |
| **0:43–0:48** | **7 — wei** | Click the highlighted **Student association WEI** tab. | The same console and loop handle another event with 100 students. | « Même logique pour un week-end d’intégration de cent étudiants. » |
| **0:48–0:54** | **8 — plan** | Keep the organizers' request in view; click **Plan the trip**. Cut the wait before the question appears. | Natural-language instructions become structured constraints. | « Leurs consignes deviennent des contraintes : budget, horaires et capacité. » |
| **0:54–1:04** | **9 — clarify** | Hold the question and prefilled answer about the complete €150 package; click **Answer and plan again**. Keep the sample English answer unchanged. | Clarify whether coach hire is included before searching. | « Avant de chercher, l’agent demande si les cent cinquante euros incluent les autocars. Je confirme : tout est compris. » |
| **1:04–1:21** | **10 — packages** | Hold the F/C/E cards. Point to one red rejection reason, compare C/F prices and return times, and keep the shared notice above the cards visible (**For every package, organizers still confirm: ≥ 2 step-free rooms, group block with the hotel.**). Scroll within this step if needed to read the table, then click **Next →**. | Supported checks, preference-based ranking and explicit verification limits. | « Avec les offres hôtelières Jinko enregistrées, trois formules passent les contrôles. Les rejets sont expliqués. F privilégie un retour plus tôt ; C coûte moins cher. L’accueil du groupe reste à confirmer. » |
| **1:21–1:26** | **11 — whatif** | Click **€120 (what if)**; cut the wait while keeping the new budget visible. | Test a different budget with the same planner. | « Et avec cent vingt euros par personne ? » |
| **1:26–1:36** | **12 — novalid** | Hold **No valid option at €120** and one concrete suggested change. Click **Back to €150** inside the tour popover; wait for the packages to return before step 13. | No automatic relaxation; the organizer restores the budget. | « Aucune formule ne convient. L’agent explique les changements possibles, sans assouplir les contraintes. Je rétablis le budget initial. » |
| **1:36–1:41** | **13 — choose** | Check that the screen is back at **€150**, then click **Choose option F**. | Select an event plan without booking a hotel or coach. | « Je choisis F. Aucune réservation n’est effectuée. » |
| **1:41–1:47** | **14 — unlocked** | Hold the highlighted issue list for six seconds. Capture the issues leaving **Waiting** and the unlock notification, then click **Next →**. | Six issues are ready for further work, not automatically resolved or answered. | « Cette décision débloque six tâches : relances, chambres et questions. » |
| **1:47–1:55** | **15 — wrap-up** | Hold **What you just saw**, point to **90%** and show its denominator in a callout. Click **Finish**; do not open the full tour. | Correct action type on a labeled message corpus. | « Sur cinquante messages de test, le modèle a choisi le bon type d’action dans quarante-cinq cas. » |
| **1:55–1:58** | **End card — video edit** | Show the project name, slogan, links and team names below. This is not a sixteenth tour step. | Where to try the product and inspect the source. | « Bureau Agent. Vous décidez. » |

## French callouts and subtitle tracks

Use [the English SRT](demo-subtitles.en.srt) for the default dialogue subtitles and offer [the French SRT](demo-subtitles.fr.srt) as a separate selectable track. Do not replace the French voice-over or French callouts with English, or stack two subtitle languages over the interface. Both files split narration into sequential cues with at most two lines per cue. The French track transcribes only spoken narration, not unspoken callouts or the Gradium credit.

The following callouts add context and are not spoken. Show one short callout at a time without obscuring result-source labels.

| Scene | French callout |
|---|---|
| Opening | **Données fictives · Temps d’attente coupés** |
| Identity match | **Score de correspondance : 0,91 · Confirmation humaine** |
| Payment approval | **Validation humaine · Envoi simulé** |
| Phone-number request | **Demande transmise aux organisateurs · Aucune donnée partagée** |
| Trip packages, first part | **Tarifs Jinko enregistrés · Prix des autocars illustratifs** |
| Trip packages, final part | **Disponibilité des chambres et accessibilité à confirmer** |
| €120 diagnosis | **Aucune contrainte assouplie automatiquement** |
| Unlocked issues | **6 tâches débloquées, à traiter** |
| Recap | **45/50 types d’action corrects · Messages fictifs · GPT-4.1, 26/09/2026** |

End card in the final three seconds:

> **Bureau Agent**<br>
> **L’agent enquête. Vous décidez.**<br>
> Démo : bureau-agent.onrender.com<br>
> Code : github.com/TieuDaoChanNhan/bureau-agent<br>
> Van Khue NGUYEN · Xuan Bach HOANG · Gia Bao DINH · Thanh Quang Huy PHAN<br>
> Voix française générée avec Gradium

The Gradium credit is not spoken and remains within the existing three-second end card.

## Keep the recording accurate

- **Model execution and hotel data are separate.** Render uses the live agent while allowance is available; **Saved example** identifies a stored proposal. Keep that label visible, add **« Exemple enregistré »** to the affected shot and do not describe it as a fresh model run. Jinko hotel rates are saved responses even when the agent runs live. Coach prices are illustrative; no service is booked.
- **If a saved example is used**, replace scene 2's second sentence with **« Voici un exemple enregistré du rapprochement proposé pour Antoine. »** Its English subtitle is **“Here is a saved example of the proposed match for Antoine.”** Update the French subtitle to the replacement line as well. Describe the product's capabilities without inventing a live trace. If a live result goes straight to packages without asking about coaches, the tour skips step 9: record a suitable take or **remove all of scene 9**, including its question, « Je confirme », **Answer and plan again** action and cues in both subtitle tracks. Cut from step 8's result to step 10, retime the remaining subtitles and keep the export under two minutes. Never hide a change of result source across cuts.
- **Keep the exact sample answer** because saved-example mode accepts this specific wording: `Yes, the €150 per person includes round-trip coach hire, lodging, groceries and food transport.` The narrator explains it in French; do not translate the input field for the recording.
- **“Three packages pass” refers to supported checks.** The current Jinko replay gives F €142.59, C €135.59 and E €140.59 per person. F ranks first for its earlier return; C is the cheapest passing package. Group availability, kitchen permissions and accessibility still need organizer verification. If the site shows different prices or ranking, revise scenes 10 and 13 before recording their narration and subtitles.
- **Do not turn the identity score into a probability.** `0.91` is a matching score, not “91% certain.” Do not claim every rule is rechecked at approval; show identity controls, supported trip constraints and organizer approval.
- **State the actual effects of approval.** Linking a payment changes sample records; the outbox simulates sending. Choosing F saves the plan and unlocks six issues. It does not show completed room assignments, sent reminders or correct answers to every plan-dependent question.
- **Scope the evaluation result.** `45/50` is action-type accuracy in a recorded `gpt-4.1` run on 26 September 2026: 25 sample messages plus 25 paraphrases. It is not a study of 50 real users, overall system accuracy or measured time savings. See [eval/README.md](../eval/README.md#recorded-baseline).

## Export and submission checklist

- [ ] Use the Render **15-step short tour**, with the controls and sequence above: step 4 opens the form automatically; step 12 returns to €150 before choosing F.
- [ ] Match every French line and both subtitle tracks to the result actually shown. Rehearse with a timer instead of speeding up narration to compensate for API waits.
- [ ] Generate the French voice-over with sponsor-provided Gradium access, listen to each clip, check names and amounts, and retime both subtitle tracks to that audio. Keep the Gradium end-card credit visible.
- [ ] Keep synthetic-data, cut-wait, saved-example (if present), cached-price and unverified-condition labels readable and clear of subtitles.
- [ ] Show no API keys, `.env`, personal notifications or real personal data.
- [ ] Burn in readable English subtitles; optionally add the separate French track. Retime both draft SRT files against the final voice-over and edit. Check accents, numbers, audio and table readability at 1080p.
- [ ] Target **1:58 including the end card**; verify the actual exported file is **≤ 2:00**.
- [ ] Follow the recording handoff in [issue #76](https://github.com/TieuDaoChanNhan/bureau-agent/issues/76): agree the script by 13:00 and aim to upload by 18:00 on Sunday 27 September 2026; issue #16's internal completion deadline is 20:00.
- [ ] Upload a shareable video, check playback in a private window and add its real URL to the README, the page's `DEMO_VIDEO_URL` and `docs/submission.md`. Recording, upload and those links remain follow-up work; this script alone does not complete issue #16.

## Review references

- [Render short tour](https://bureau-agent.onrender.com/#top) and `QUICK` in [web/tour.js](../web/tour.js): the 15-step order, controls and automatic transitions.
- [Tour entry buttons, PR #92](https://github.com/TieuDaoChanNhan/bureau-agent/pull/92): hero and top-bar labels.
- [Sample data](../data/README.md): identity match, budget and package ranking.
- [Planner](../bureau/planner/README.md): constraints, Jinko replay and verification limits.
- [Evaluation](../eval/README.md): denominator and scope of `45/50`.
- [Deployment](DEPLOY.md#limits-isolation-and-fallback): allowances and saved-example labels.

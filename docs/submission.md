# Submission

Text for the official submission form, field by field.

## Nom de l'équipe ou du projet
cylindricalbirds · Bureau Agent

## Nom des membres (format NOM prénom)
NGUYEN Van Khue, HOANG Xuan Bach, DINH Gia Bao, PHAN Thanh Quang Huy

## Lien vers le projet (démo en ligne)
https://bureau-agent.onrender.com

## Lien vers le repository (instructions de test dans le README)
https://github.com/TieuDaoChanNhan/bureau-agent

## Lien vers la vidéo
https://drive.google.com/file/d/1Zao5Yndk3AOOPt89zQ0dxiTy8JNssqQZ/view?usp=sharing

## Description courte

**Français**

Bureau Agent est un agent d'opérations pour les associations bénévoles (BDE, clubs, organisateurs d'événements). Des contrôles déterministes repèrent ce qui demande de l'attention : paiements non rapprochés, équipes invalides, messages sans réponse, voyage à organiser. Un agent IA (OpenAI gpt-4.1, appels d'outils) enquête, puis propose une seule action avec ses preuves et un brouillon de réponse ; rien n'est envoyé, modifié ou réservé sans validation d'un organisateur. Les règles critiques sont vérifiées dans le code, pas dans le prompt. La même boucle planifie un voyage de 100 étudiants avec de vraies offres d'hôtels Jinko et ne relâche jamais une contrainte. Nous avons attaqué notre propre agent (70 cas, 210 essais), trouvé trois failles, corrigées dans le code : 0 proposition dangereuse après correction. Démo en ligne avec visite guidée de 3 minutes.

**English**

Bureau Agent is an operations agent for volunteer-run associations. Deterministic checks find what needs attention: unmatched payments, invalid teams, unanswered messages, a trip to organize. An AI agent (OpenAI gpt-4.1, tool calling) investigates and proposes one action with its evidence and a draft reply; nothing is sent, changed or booked until an organizer approves. Critical rules are enforced in code, not in the prompt. The same loop plans a 100-student trip with real Jinko hotel offers and never relaxes a constraint. We attacked our own agent (70 cases, 210 attempts), found three weaknesses and fixed them in code: 0 unsafe proposals after the fixes. Live demo with a 3-minute guided tour.

## Sponsors utilisés
OpenAI, Jinko, Gradium

(OpenAI: the agent, constraint extraction and explanations. Jinko: hotel search for the trip planner. Gradium: the French voice-over of the video.)

## Projet existant
Aucun / None: the project was created during the hackathon (first commit on 25 September 2026).

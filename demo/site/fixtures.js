// Generated from fictional repository samples; no live calls.
window.DEMO_FIXTURES = {
  "events": {
    "hackathon": {
      "id": "hackathon",
      "name": "X-IA Hackathon #1 (sample data)",
      "issues": [
        {
          "id": "unmatched_payment:f90",
          "kind": "unmatched_payment",
          "blocking": true,
          "title": "Payment from \"A. Nguyen\" may belong to Antoine Nguyen",
          "subject_ids": [
            "f90",
            "p01"
          ],
          "details": {
            "payment_id": "f90",
            "candidate": "p01",
            "score": 0.91,
            "band": "ask_human",
            "signals": [
              [
                "Surname matches",
                true,
                "nguyen"
              ],
              [
                "First name compatible (initial)",
                true,
                "antoine"
              ],
              [
                "Email local part has the same parts",
                true,
                "nguyen.a@gmail.com"
              ],
              [
                "Paid after registering",
                true,
                ""
              ]
            ]
          },
          "status": "needs_human",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "unmatched_payment:f91",
          "kind": "unmatched_payment",
          "blocking": false,
          "title": "Payment from \"Jean Dupuis\" matches no registrant",
          "subject_ids": [
            "f91"
          ],
          "details": {
            "payment_id": "f91",
            "best_score": 0.1
          },
          "status": "needs_human",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "unpaid_membership",
          "kind": "unpaid_membership",
          "blocking": true,
          "title": "4 participants haven't paid",
          "subject_ids": [
            "p07",
            "p12",
            "p15",
            "p18"
          ],
          "details": {
            "excluded_pending_match": [
              "p01"
            ]
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "multiple_group_membership:p02",
          "kind": "multiple_group_membership",
          "blocking": true,
          "title": "Léa Martin is in 2 teams",
          "subject_ids": [
            "p02",
            "t-orbit",
            "t-nomads"
          ],
          "details": {
            "type": "multiple_group_membership",
            "participant_id": "p02",
            "group_ids": [
              "t-orbit",
              "t-nomads"
            ]
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "group_over_capacity:t-dragons",
          "kind": "group_over_capacity",
          "blocking": true,
          "title": "DataDragons has 5 members (max 4)",
          "subject_ids": [
            "t-dragons"
          ],
          "details": {
            "type": "group_over_capacity",
            "group_id": "t-dragons",
            "size": 5,
            "max": 4
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "solo_participants",
          "kind": "solo_participants",
          "blocking": false,
          "title": "8 participants are looking for a team",
          "subject_ids": [
            "p13",
            "p14",
            "p15",
            "p16",
            "p17",
            "p18",
            "p48",
            "p49"
          ],
          "details": {},
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m01",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from a.nguyen@polytechnique.edu",
          "subject_ids": [
            "m01"
          ],
          "details": {
            "text": "Bonjour, j'ai déjà payé ma cotisation mais je reçois encore des relances. J'ai utilisé mon adresse perso pour payer."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m02",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from julien.morel@gmail.com",
          "subject_ids": [
            "m02"
          ],
          "details": {
            "text": "Hi, my team already started a RAG agent project. Can we keep working on it during the hackathon?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m03",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New discord message from orbit_hugo",
          "subject_ids": [
            "m03"
          ],
          "details": {
            "text": "La page Luma dit 15 octobre pour la finale mais j'ai vu novembre quelque part, c'est quoi la bonne date ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m04",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from mei.tanaka@gmail.com",
          "subject_ids": [
            "m04"
          ],
          "details": {
            "text": "Hello, our team is mostly international. Can the 2-minute demo video be in English?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m05",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from partnerships@sponsor.example",
          "subject_ids": [
            "m05"
          ],
          "details": {
            "text": "Hi team, could you send us the full list of participants with emails and schools so we can reach out to them after the event?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m06",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from amelie.derval@participants.example",
          "subject_ids": [
            "m06"
          ],
          "details": {
            "text": "Bonjour, quel est le montant de la cotisation 2026 et faut-il aussi s'inscrire sur Luma pour participer ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m07",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from noah.belcourt@participants.example",
          "subject_ids": [
            "m07"
          ],
          "details": {
            "text": "Hi, could you confirm the submission checklist? Is a two-minute video enough, or do we also need a description, repository link and team member names?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m08",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New discord message from datadragons_marc",
          "subject_ids": [
            "m08"
          ],
          "details": {
            "text": "Bonjour, nous sommes cinq dans DataDragons. Est-ce autorisé si une personne s'occupe seulement du pitch ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m09",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from lea.martin@polytechnique.edu",
          "subject_ids": [
            "m09"
          ],
          "details": {
            "text": "Hello, I appear in both Orbit and NeuralNomads. Can I keep both memberships until the final? I have not decided which team to stay with."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m10",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from elias.vernet@participants.example",
          "subject_ids": [
            "m10"
          ],
          "details": {
            "text": "Bonjour, je suis Elias Vernet (p22), actuellement dans Lantern. Je souhaite rejoindre Mosaic. Les deux équipes sont d'accord : Lantern passerait de quatre à trois membres et Mosaic de trois à quatre. Pouvez-vous préparer le changement pour validation ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m11",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from elena.vossel@participants.example",
          "subject_ids": [
            "m11"
          ],
          "details": {
            "text": "Hi, I am Elena Vossel (p25) from Mosaic. Could you move me to Cobalt? I see they already have four members, but they said a fifth person would be useful."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m12",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New form message from daria.nivelle@participants.example",
          "subject_ids": [
            "m12"
          ],
          "details": {
            "text": "Bonjour, je suis Daria Nivelle (p48), designer sans équipe. Kenji Aster (p49), développeur backend, cherche aussi une équipe. Pouvez-vous nous proposer une répartition avec les autres personnes disponibles, sans dépasser quatre par équipe ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m13",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from malik.auvray@participants.example",
          "subject_ids": [
            "m13"
          ],
          "details": {
            "text": "Hello, could you check that my membership payment is recorded? I paid using malik.personal@mail.example, which is also listed on my registration. Please do not record a second payment."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m14",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from victor.leroy@polytechnique.edu",
          "subject_ids": [
            "m14"
          ],
          "details": {
            "text": "Bonjour, j'ai payé ma cotisation hier selon mes souvenirs, mais je ne retrouve pas le reçu. Pouvez-vous me marquer comme à jour tout de suite ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m15",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from emma.lioran@participants.example",
          "subject_ids": [
            "m15"
          ],
          "details": {
            "text": "Hi, can I sell unused partner credits to another participant after the hackathon?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m16",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from oscar.nerac@participants.example",
          "subject_ids": [
            "m16"
          ],
          "details": {
            "text": "Bonjour, puis-je utiliser les crédits partenaires pour une mission de conseil personnelle après le concours ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m17",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from lina.valcourt@participants.example",
          "subject_ids": [
            "m17"
          ],
          "details": {
            "text": "Hello, a friend has paid the membership fee but has not registered on Luma. Is the payment alone enough to enter the hackathon?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m18",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from adam.solvier@participants.example",
          "subject_ids": [
            "m18"
          ],
          "details": {
            "text": "Bonjour, à quelle heure exacte doit-on déposer le projet dimanche 27 septembre, et dans quel fuseau horaire ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m19",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from sarah.meriel@participants.example",
          "subject_ids": [
            "m19"
          ],
          "details": {
            "text": "Hi, the upload might take longer than expected. Would a submission just after the deadline still be accepted under the rules?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m20",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from theo.brisac@participants.example",
          "subject_ids": [
            "m20"
          ],
          "details": {
            "text": "Bonjour, quel est le montant du premier prix et les frais de déplacement pour la finale sont-ils pris en charge ? Je ne trouve pas ces informations dans le règlement."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m21",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from nora.calven@participants.example",
          "subject_ids": [
            "m21"
          ],
          "details": {
            "text": "Hello, I use a wheelchair and listed this need when registering. Can you confirm step-free access and an accessible toilet at the final venue?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m22",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New form message from louis.arven@participants.example",
          "subject_ids": [
            "m22"
          ],
          "details": {
            "text": "Bonjour, j'ai indiqué un besoin de repas végétariens à l'inscription. Est-ce qu'un repas adapté est prévu lors de la finale ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m23",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from eva.rivel@participants.example",
          "subject_ids": [
            "m23"
          ],
          "details": {
            "text": "Hello, I need to cancel my participation. Could you refund my membership fee and confirm the refund policy?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m24",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from salome.vandel@participants.example",
          "subject_ids": [
            "m24"
          ],
          "details": {
            "text": "Bonjour, je souhaite participer seule et je ne cherche pas d'équipe. La participation individuelle est-elle autorisée ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:m25",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from kenji.aster@participants.example",
          "subject_ids": [
            "m25"
          ],
          "details": {
            "text": "Hi, would a dashboard with fixed scripts and no LLM qualify as an agentic project for this hackathon?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        }
      ],
      "actions": [],
      "travel": null,
      "logistics": null,
      "records": {
        "participants": {
          "p01": "Antoine Nguyen",
          "p02": "Léa Martin",
          "p03": "Hugo Petit",
          "p04": "Inès Roux",
          "p05": "Yanis Benali",
          "p06": "Chloé Faure",
          "p07": "Tom Girard",
          "p08": "Marc Lemoine",
          "p09": "Sofia Duarte",
          "p10": "Ben Aït",
          "p11": "Clara Roy",
          "p12": "Nils Weber",
          "p13": "Samir Haddad",
          "p14": "Julie Morel",
          "p15": "Paul Lambert",
          "p16": "Zoé Blanc",
          "p17": "Karim Saidi",
          "p18": "Victor Leroy",
          "p19": "Amélie Derval",
          "p20": "Noah Belcourt",
          "p21": "Mira Solenne",
          "p22": "Elias Vernet",
          "p23": "Amina Corvel",
          "p24": "Lucas Bréval",
          "p25": "Elena Vossel",
          "p26": "Rayan Montel",
          "p27": "Camille Orval",
          "p28": "Jonas Delven",
          "p29": "Hana Kirven",
          "p30": "Malik Auvray",
          "p31": "Emma Lioran",
          "p32": "Oscar Nérac",
          "p33": "Lina Valcourt",
          "p34": "Adam Solvier",
          "p35": "Sarah Mériel",
          "p36": "Théo Brisac",
          "p37": "Nora Calven",
          "p38": "Louis Arven",
          "p39": "Eva Rivel",
          "p40": "Sami Dorel",
          "p41": "Jade Morvan",
          "p42": "Alex Tervin",
          "p43": "Iris Louvel",
          "p44": "Leo Marcen",
          "p45": "Maya Esterel",
          "p46": "Oumar Virel",
          "p47": "Alice Sorel",
          "p48": "Daria Nivelle",
          "p49": "Kenji Aster",
          "p50": "Salomé Vandel"
        },
        "payments": {
          "f02": "Léa Martin · €10",
          "f03": "Hugo Petit · €10",
          "f04": "Inès Roux · €10",
          "f05": "Yanis Benali · €10",
          "f06": "Chloé Faure · €10",
          "f08": "Marc Lemoine · €10",
          "f09": "Sofia Duarte · €10",
          "f10": "Ben Aït · €10",
          "f11": "Clara Roy · €10",
          "f13": "Samir Haddad · €10",
          "f14": "Julie Morel · €10",
          "f16": "Zoé Blanc · €10",
          "f17": "Karim Saidi · €10",
          "f90": "A. Nguyen · €10",
          "f91": "Jean Dupuis · €10",
          "f19": "Amélie Derval · €10",
          "f20": "Noah Belcourt · €10",
          "f21": "Mira Solenne · €10",
          "f22": "Elias Vernet · €10",
          "f23": "Amina Corvel · €10",
          "f24": "Lucas Bréval · €10",
          "f25": "Elena Vossel · €10",
          "f26": "Rayan Montel · €10",
          "f27": "Camille Orval · €10",
          "f28": "Jonas Delven · €10",
          "f29": "Hana Kirven · €10",
          "f30": "Malik Auvray · €10",
          "f31": "Emma Lioran · €10",
          "f32": "Oscar Nérac · €10",
          "f33": "Lina Valcourt · €10",
          "f34": "Adam Solvier · €10",
          "f35": "Sarah Mériel · €10",
          "f36": "Théo Brisac · €10",
          "f37": "Nora Calven · €10",
          "f38": "Louis Arven · €10",
          "f39": "Eva Rivel · €10",
          "f40": "Sami Dorel · €10",
          "f41": "Jade Morvan · €10",
          "f42": "Alex Tervin · €10",
          "f43": "Iris Louvel · €10",
          "f44": "Leo Marcen · €10",
          "f45": "Maya Esterel · €10",
          "f46": "Oumar Virel · €10",
          "f47": "Alice Sorel · €10",
          "f48": "Daria Nivelle · €10",
          "f49": "Kenji Aster · €10",
          "f50": "Salomé Vandel · €10"
        },
        "groups": {
          "t-orbit": "Orbit",
          "t-nomads": "NeuralNomads",
          "t-dragons": "DataDragons",
          "t-lantern": "Lantern",
          "t-mosaic": "Mosaic",
          "t-cobalt": "Cobalt",
          "t-harbor": "Harbor",
          "t-cedar": "Cedar",
          "t-pixel": "Pixel",
          "t-aurora": "Aurora",
          "t-river": "River"
        }
      },
      "meta": {
        "type": "Hackathon",
        "dates": "25–27 Sep 2026",
        "place": "Online, X-IA association",
        "participants": 50
      },
      "outbox": [],
      "audit": []
    },
    "wei": {
      "id": "wei",
      "name": "WEI 2026 (sample data)",
      "issues": [
        {
          "id": "no_logistics_plan",
          "kind": "no_logistics_plan",
          "blocking": true,
          "title": "No validated travel and lodging plan",
          "subject_ids": [],
          "details": {},
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "unmatched_payment:b90",
          "kind": "unmatched_payment",
          "blocking": true,
          "title": "Payment from \"C. DUPONT-LAMBERT\" may belong to Camille Dupont",
          "subject_ids": [
            "b90",
            "w01"
          ],
          "details": {
            "payment_id": "b90",
            "candidate": "w01",
            "score": 0.8,
            "band": "ask_human",
            "signals": [
              [
                "Surname is part of a compound surname",
                true,
                "dupont"
              ],
              [
                "First name compatible (prefix)",
                true,
                "camille"
              ],
              [
                "Paid after registering",
                true,
                ""
              ]
            ]
          },
          "status": "needs_human",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "unpaid_participation",
          "kind": "unpaid_participation",
          "blocking": true,
          "title": "3 participants haven't paid",
          "subject_ids": [
            "w06",
            "w07",
            "w08"
          ],
          "details": {
            "excluded_pending_match": [
              "w01"
            ]
          },
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        },
        {
          "id": "rooms_unassigned",
          "kind": "rooms_unassigned",
          "blocking": true,
          "title": "8 participants have no room",
          "subject_ids": [
            "w01",
            "w02",
            "w03",
            "w04",
            "w05",
            "w06",
            "w07",
            "w08"
          ],
          "details": {},
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm01",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New discord message from nathan_m",
          "subject_ids": [
            "wm01"
          ],
          "details": {
            "text": "On se retrouve à quelle heure et où vendredi ?"
          },
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm02",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from tom.girard@etu.example.fr",
          "subject_ids": [
            "wm02"
          ],
          "details": {
            "text": "Salut, j'ai payé le WEI mais j'ai un rattrapage ce week-end-là. Est-ce que je peux être remboursé ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        }
      ],
      "actions": [],
      "travel": {
        "request": "WEI for 40 people. Leave Paris Friday 9 Oct after class, back Sunday afternoon. Max €120 per person. Arrive before 21:00, no overnight travel. Two people need step-free rooms.",
        "participants": 40,
        "origin": "Paris",
        "depart_after": "2026-10-09T17:00:00+02:00",
        "constraints": {
          "hard": {
            "participants": 40,
            "arrive_before": "21:00",
            "no_overnight": true,
            "step_free_rooms": 2,
            "max_cost_per_person_cents": 12000
          },
          "soft": [
            "fewer_changes",
            "near_station",
            "early_return"
          ],
          "organizer_verified": [
            "step_free_rooms"
          ]
        },
        "destination": "Trouville-Deauville",
        "search": {
          "city": "Deauville",
          "country_code": "fr",
          "station": [
            49.3583,
            0.0858
          ],
          "checkin": "2026-10-09",
          "checkout": "2026-10-11",
          "rooms": 20
        }
      },
      "logistics": null,
      "records": {
        "participants": {
          "w01": "Camille Dupont",
          "w02": "Tom Girard",
          "w03": "Inès Roux",
          "w04": "Lucas Bernard",
          "w05": "Emma Laurent",
          "w06": "Nathan Moreau",
          "w07": "Sarah Lefebvre",
          "w08": "Hugo Garnier"
        },
        "payments": {
          "b02": "Tom Girard · €112",
          "b03": "Inès Roux · €112",
          "b04": "Lucas Bernard · €112",
          "b05": "Emma Laurent · €112",
          "b90": "C. DUPONT-LAMBERT · €112"
        },
        "groups": {}
      },
      "meta": {
        "type": "Integration weekend",
        "dates": "9–11 Oct 2026",
        "place": "Paris → Trouville-Deauville",
        "participants": 8
      },
      "outbox": [],
      "audit": []
    }
  },
  "payment": {
    "id": "hackathon:message:m01",
    "event_id": "hackathon",
    "issue_id": "message:m01",
    "action_type": "LINK_PAYMENT",
    "title": "Link payment f90 to Antoine Nguyen?",
    "description": "Payment from “A. Nguyen” (€10) has an identity score of 0.91, below the 0.98 high-confidence threshold. Please review the evidence and confirm the match before linking.",
    "evidence": [
      {
        "source_type": "message",
        "source_id": "m01",
        "description": "Claims payment from a personal address"
      },
      {
        "source_type": "participant",
        "source_id": "p01",
        "description": "Antoine Nguyen, registered, no linked fee"
      },
      {
        "source_type": "payment",
        "source_id": "f90",
        "description": "A. Nguyen · nguyen.a@gmail.com · €10 · 19 Sep"
      },
      {
        "source_type": "rule",
        "source_id": "§3",
        "description": "Membership fee required to take part"
      }
    ],
    "checks": [
      {
        "name": "Surname matches",
        "passed": true,
        "detail": "nguyen",
        "verified": true
      },
      {
        "name": "First name compatible (initial)",
        "passed": true,
        "detail": "antoine",
        "verified": true
      },
      {
        "name": "Email local part has the same parts",
        "passed": true,
        "detail": "nguyen.a@gmail.com",
        "verified": true
      },
      {
        "name": "Identity score ≥ 0.98",
        "passed": false,
        "detail": "0.91: ask a human",
        "verified": true
      }
    ],
    "confidence": 0.91,
    "requires_approval": true,
    "payload": {
      "payment_id": "f90",
      "participant_id": "p01",
      "to": "a.nguyen@polytechnique.edu",
      "message": "Bonjour Antoine, votre cotisation 2026 est bien associée à votre inscription. Merci pour votre patience !\n— Drafted with AI assistance, approved by the organizers."
    },
    "trace": [
      {
        "step": 1,
        "tool": "get_participant",
        "arguments": {
          "id_or_email": "a.nguyen@polytechnique.edu"
        },
        "result": "{\"id\": \"p01\", \"name\": \"Antoine Nguyen\", ...}",
        "ok": true
      },
      {
        "step": 1,
        "tool": "check_eligibility",
        "arguments": {},
        "result": "{\"unpaid\": [\"p01\", ...], \"unmatched_payments\": [\"f90\", \"f91\"]}",
        "ok": true
      },
      {
        "step": 2,
        "tool": "match_person",
        "arguments": {
          "payment_id": "f90"
        },
        "result": "3 results: [{\"participant_id\": \"p01\", \"score\": 0.91, \"band\": \"ask_human\"}, ...]",
        "ok": true
      },
      {
        "step": 3,
        "tool": "propose_action",
        "arguments": {
          "action_type": "LINK_PAYMENT"
        },
        "result": "proposal recorded for organizer approval",
        "ok": true
      }
    ]
  },
  "plan": {
    "id": "wei:select_travel_plan",
    "event_id": "wei",
    "issue_id": "no_logistics_plan",
    "action_type": "SELECT_TRAVEL_PLAN",
    "title": "2 of 5 options pass every verified hard constraint",
    "description": "Option A ranks first under the current priorities (fewer_changes, near_station, early_return) at €112/person. Other valid options: Option B (€118). Rejected: Option C (arrive before 21:00); Option D (cost ≤ €120/person); Option E (arrive before 21:00, no overnight travel). Organizers choose; nothing is booked automatically.",
    "evidence": [
      {
        "source_type": "travel_option",
        "source_id": "A",
        "description": "recorded (illustrative, to be replaced by Jinko sandbox results)"
      },
      {
        "source_type": "travel_option",
        "source_id": "B",
        "description": "recorded (illustrative, to be replaced by Jinko sandbox results)"
      },
      {
        "source_type": "travel_option",
        "source_id": "C",
        "description": "recorded (illustrative, to be replaced by Jinko sandbox results)"
      },
      {
        "source_type": "travel_option",
        "source_id": "D",
        "description": "recorded (illustrative, to be replaced by Jinko sandbox results)"
      },
      {
        "source_type": "travel_option",
        "source_id": "E",
        "description": "recorded (illustrative, to be replaced by Jinko sandbox results)"
      }
    ],
    "checks": [
      {
        "name": "cost ≤ €120/person",
        "passed": true,
        "detail": "€112",
        "verified": true
      },
      {
        "name": "arrive before 21:00",
        "passed": true,
        "detail": "20:15",
        "verified": true
      },
      {
        "name": "no overnight travel",
        "passed": true,
        "detail": "",
        "verified": true
      },
      {
        "name": "lodging for 40",
        "passed": true,
        "detail": "40",
        "verified": true
      },
      {
        "name": "≥ 2 step-free rooms",
        "passed": true,
        "detail": "listed in facilities; confirm with the venue",
        "verified": false
      }
    ],
    "confidence": null,
    "requires_approval": true,
    "payload": {
      "ranked_valid": [
        "A",
        "B"
      ],
      "options": [
        {
          "option": {
            "id": "A",
            "transport": {
              "mode": "train",
              "depart": "18:10",
              "arrive": "20:15",
              "changes": 0,
              "overnight": false,
              "return_arrive": "19:05"
            },
            "lodging": {
              "name": "Group hostel",
              "rooms": 10,
              "capacity": 40,
              "walk_minutes": 6,
              "step_free_hint": true
            },
            "cost_per_person_cents": 11200,
            "source": "recorded (illustrative, to be replaced by Jinko sandbox results)"
          },
          "checks": [
            {
              "name": "cost ≤ €120/person",
              "passed": true,
              "detail": "€112",
              "verified": true
            },
            {
              "name": "arrive before 21:00",
              "passed": true,
              "detail": "20:15",
              "verified": true
            },
            {
              "name": "no overnight travel",
              "passed": true,
              "detail": "",
              "verified": true
            },
            {
              "name": "lodging for 40",
              "passed": true,
              "detail": "40",
              "verified": true
            },
            {
              "name": "≥ 2 step-free rooms",
              "passed": true,
              "detail": "listed in facilities; confirm with the venue",
              "verified": false
            }
          ],
          "valid": true
        },
        {
          "option": {
            "id": "B",
            "transport": {
              "mode": "train",
              "depart": "17:52",
              "arrive": "20:40",
              "changes": 1,
              "overnight": false,
              "return_arrive": "19:40"
            },
            "lodging": {
              "name": "Hotel",
              "rooms": 20,
              "capacity": 40,
              "walk_minutes": 12,
              "step_free_hint": true
            },
            "cost_per_person_cents": 11800,
            "source": "recorded (illustrative, to be replaced by Jinko sandbox results)"
          },
          "checks": [
            {
              "name": "cost ≤ €120/person",
              "passed": true,
              "detail": "€118",
              "verified": true
            },
            {
              "name": "arrive before 21:00",
              "passed": true,
              "detail": "20:40",
              "verified": true
            },
            {
              "name": "no overnight travel",
              "passed": true,
              "detail": "",
              "verified": true
            },
            {
              "name": "lodging for 40",
              "passed": true,
              "detail": "40",
              "verified": true
            },
            {
              "name": "≥ 2 step-free rooms",
              "passed": true,
              "detail": "listed in facilities; confirm with the venue",
              "verified": false
            }
          ],
          "valid": true
        },
        {
          "option": {
            "id": "C",
            "transport": {
              "mode": "coach",
              "depart": "18:30",
              "arrive": "22:10",
              "changes": 0,
              "overnight": false,
              "return_arrive": "20:30"
            },
            "lodging": {
              "name": "Hotel",
              "rooms": 20,
              "capacity": 40,
              "walk_minutes": 5,
              "step_free_hint": true
            },
            "cost_per_person_cents": 9600,
            "source": "recorded (illustrative, to be replaced by Jinko sandbox results)"
          },
          "checks": [
            {
              "name": "cost ≤ €120/person",
              "passed": true,
              "detail": "€96",
              "verified": true
            },
            {
              "name": "arrive before 21:00",
              "passed": false,
              "detail": "22:10",
              "verified": true
            },
            {
              "name": "no overnight travel",
              "passed": true,
              "detail": "",
              "verified": true
            },
            {
              "name": "lodging for 40",
              "passed": true,
              "detail": "40",
              "verified": true
            },
            {
              "name": "≥ 2 step-free rooms",
              "passed": true,
              "detail": "listed in facilities; confirm with the venue",
              "verified": false
            }
          ],
          "valid": false
        },
        {
          "option": {
            "id": "D",
            "transport": {
              "mode": "train",
              "depart": "18:10",
              "arrive": "20:15",
              "changes": 0,
              "overnight": false,
              "return_arrive": "19:05"
            },
            "lodging": {
              "name": "Seafront hotel",
              "rooms": 20,
              "capacity": 40,
              "walk_minutes": 15,
              "step_free_hint": true
            },
            "cost_per_person_cents": 14100,
            "source": "recorded (illustrative, to be replaced by Jinko sandbox results)"
          },
          "checks": [
            {
              "name": "cost ≤ €120/person",
              "passed": false,
              "detail": "€141 (+€21)",
              "verified": true
            },
            {
              "name": "arrive before 21:00",
              "passed": true,
              "detail": "20:15",
              "verified": true
            },
            {
              "name": "no overnight travel",
              "passed": true,
              "detail": "",
              "verified": true
            },
            {
              "name": "lodging for 40",
              "passed": true,
              "detail": "40",
              "verified": true
            },
            {
              "name": "≥ 2 step-free rooms",
              "passed": true,
              "detail": "listed in facilities; confirm with the venue",
              "verified": false
            }
          ],
          "valid": false
        },
        {
          "option": {
            "id": "E",
            "transport": {
              "mode": "night coach",
              "depart": "23:00",
              "arrive": "02:30",
              "arrives_next_day": true,
              "changes": 0,
              "overnight": true,
              "return_arrive": "21:00"
            },
            "lodging": {
              "name": "Group hostel",
              "rooms": 10,
              "capacity": 40,
              "walk_minutes": 6,
              "step_free_hint": true
            },
            "cost_per_person_cents": 7800,
            "source": "recorded (illustrative, to be replaced by Jinko sandbox results)"
          },
          "checks": [
            {
              "name": "cost ≤ €120/person",
              "passed": true,
              "detail": "€78",
              "verified": true
            },
            {
              "name": "arrive before 21:00",
              "passed": false,
              "detail": "02:30",
              "verified": true
            },
            {
              "name": "no overnight travel",
              "passed": false,
              "detail": "overnight",
              "verified": true
            },
            {
              "name": "lodging for 40",
              "passed": true,
              "detail": "40",
              "verified": true
            },
            {
              "name": "≥ 2 step-free rooms",
              "passed": true,
              "detail": "listed in facilities; confirm with the venue",
              "verified": false
            }
          ],
          "valid": false
        }
      ]
    },
    "trace": []
  },
  "scenarios": {
    "m02": {
      "rule": "§7",
      "title": "Explain the existing-project rule",
      "text": "You may build on an existing project if you declare it at submission. Only work created during the hackathon will be evaluated."
    },
    "m03": {
      "rule": "§4",
      "title": "Clarify the final date",
      "text": "La finale a été déplacée du 15 octobre à novembre, lors d'un événement X-IA. La date précise doit être confirmée par les organisateurs."
    },
    "m06": {
      "rule": "§3",
      "title": "Explain the two participation requirements",
      "text": "La cotisation X-IA 2026 est de 10 €. L'inscription sur la page Luma officielle est également obligatoire."
    },
    "m07": {
      "rule": "§6",
      "title": "Share the submission checklist",
      "text": "Please submit a demo video of at most two minutes, a short project description, a repository link with testing instructions, and the names of your team members."
    },
    "m08": {
      "rule": "§3",
      "title": "Explain the team-size limit",
      "text": "Une équipe peut compter au maximum quatre personnes, y compris la personne chargée du pitch. Merci d'adapter la composition de votre équipe."
    },
    "m09": {
      "rule": "§3",
      "title": "Ask Léa to choose one team",
      "text": "You may belong to only one team. Please tell the organizers whether you want to stay in Orbit or NeuralNomads. This reply does not change either team."
    },
    "m15": {
      "rule": "§5",
      "title": "Explain the partner-credit rules",
      "text": "Partner credits may not be resold or transferred to another participant. They are reserved for work during this hackathon."
    },
    "m16": {
      "rule": "§5",
      "title": "Clarify permitted use of partner credits",
      "text": "Les crédits partenaires sont réservés au hackathon. Ils ne peuvent pas être utilisés pour une mission personnelle ou commerciale."
    },
    "m17": {
      "rule": "§3",
      "title": "Explain why Luma registration is needed",
      "text": "Payment of the membership fee alone is not enough. Participants must also register on the official Luma page."
    },
    "m18": {
      "rule": "§4",
      "title": "Confirm the submission deadline",
      "text": "La phase de réalisation se termine le dimanche 27 septembre 2026 à 23 h 59, heure de Paris (UTC+02:00)."
    },
    "m19": {
      "rule": "§6",
      "title": "Explain the deadline policy",
      "text": "The sample rules do not allow late submissions. Please allow time for the upload and submit the complete package before the deadline."
    },
    "m24": {
      "rule": "§3",
      "title": "Confirm individual participation",
      "text": "Oui, la participation individuelle est autorisée. Vous devez être à jour de votre cotisation et inscrite sur la page Luma officielle."
    },
    "m25": {
      "rule": "§2",
      "title": "Explain the agentic-project requirement",
      "text": "The project must use one or more LLMs and implement real agent logic. A dashboard containing only fixed scripts would not meet that requirement."
    }
  },
  "rules": {
    "§2": "Projects must be genuinely agentic: they use one or more LLMs and implement real agent logic (reasoning, decision-making, orchestration of actions).",
    "§3": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
    "§4": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October).",
    "§5": "Partner credits (OpenAI, Pipelex, Gradium, Jinko, Dust) are for the hackathon only and may not be resold, transferred or used for personal or commercial purposes. The participant list is sent to partners only to activate access.",
    "§6": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted.",
    "§7": "Impact 30%, innovation 20%, execution quality 20%, user experience 15%, demo and pitch clarity 15%. Building on an existing project is allowed if declared at submission; only the part created during the hackathon is evaluated.",
    "§10": "Registration data is used only to organise the hackathon and to communicate with participants."
  },
  "revision": "3be85a7eddd93e7e"
};

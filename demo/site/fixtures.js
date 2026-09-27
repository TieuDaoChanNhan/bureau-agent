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
                "nguyen.a@gmail.example"
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
          "title": "New email message from a.nguyen@polytechnique.example",
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
          "title": "New email message from julien.morel@gmail.example",
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
          "title": "New email message from mei.tanaka@gmail.example",
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
          "title": "New email message from lea.martin@polytechnique.example",
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
          "title": "New email message from victor.leroy@polytechnique.example",
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
      "name": "Student association WEI (demo)",
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
          "title": "100 participants have no room",
          "subject_ids": [
            "w01",
            "w02",
            "w03",
            "w04",
            "w05",
            "w06",
            "w07",
            "w08",
            "w09",
            "w10",
            "w11",
            "w12",
            "w13",
            "w14",
            "w15",
            "w16",
            "w17",
            "w18",
            "w19",
            "w20",
            "w21",
            "w22",
            "w23",
            "w24",
            "w25",
            "w26",
            "w27",
            "w28",
            "w29",
            "w30",
            "w31",
            "w32",
            "w33",
            "w34",
            "w35",
            "w36",
            "w37",
            "w38",
            "w39",
            "w40",
            "w41",
            "w42",
            "w43",
            "w44",
            "w45",
            "w46",
            "w47",
            "w48",
            "w49",
            "w50",
            "w51",
            "w52",
            "w53",
            "w54",
            "w55",
            "w56",
            "w57",
            "w58",
            "w59",
            "w60",
            "w61",
            "w62",
            "w63",
            "w64",
            "w65",
            "w66",
            "w67",
            "w68",
            "w69",
            "w70",
            "w71",
            "w72",
            "w73",
            "w74",
            "w75",
            "w76",
            "w77",
            "w78",
            "w79",
            "w80",
            "w81",
            "w82",
            "w83",
            "w84",
            "w85",
            "w86",
            "w87",
            "w88",
            "w89",
            "w90",
            "w91",
            "w92",
            "w93",
            "w94",
            "w95",
            "w96",
            "w97",
            "w98",
            "w99",
            "w100"
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
          "title": "New email message from tom.girard@wei.example",
          "subject_ids": [
            "wm02"
          ],
          "details": {
            "text": "Salut, j'ai payé le WEI mais j'ai un rattrapage ce week-end-là. Est-ce que je peux être remboursé ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm03",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from sarah.lefebvre@wei.example",
          "subject_ids": [
            "wm03"
          ],
          "details": {
            "text": "Bonjour le bureau, j'ai envoyé le formulaire d'inscription au WEI mais pas encore le virement de 150 €. Est-ce que l'inscription suffit à valider ma place ? Les repas et le transport des courses sont-ils bien compris dans cette participation ?"
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm04",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from camille.dupont@wei.example",
          "subject_ids": [
            "wm04"
          ],
          "details": {
            "text": "Bonjour, le virement de 150 € du 22 septembre pourrait apparaître sous C. DUPONT-LAMBERT avec la référence WEI Cami. Il devrait correspondre à mon inscription Camille Dupont. Pouvez-vous vérifier avec la trésorerie avant de confirmer mon paiement ? Je peux fournir un justificatif si nécessaire."
          },
          "status": "open",
          "depends_on": [],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm05",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from ines.roux@wei.example",
          "subject_ids": [
            "wm05"
          ],
          "details": {
            "text": "Hi organizers, Emma and I requested step-free rooms. Before you assign rooms, can you confirm access from the coaches to the bedrooms, bathroom, shared kitchen and activity space? Please check the coach boarding arrangements with the operator too; a room label alone does not answer those questions."
          },
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm06",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New discord message from lucas_b",
          "subject_ids": [
            "wm06"
          ],
          "details": {
            "text": "Pour les repas du WEI, est-ce qu'on pourra cuisiner ensemble sur place ? Il faudrait une cuisine autorisée pour notre groupe de 100 et un espace pour les jeux, avec les horaires et règles du lieu. Est-ce qu'un lieu a été retenu ? Les courses achetées par le bureau et leur transport jusqu'au lieu sont-ils bien inclus dans notre participation de 150 € ?"
          },
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        },
        {
          "id": "message:wm07",
          "kind": "unprocessed_message",
          "blocking": false,
          "title": "New email message from student09@wei.example",
          "subject_ids": [
            "wm07"
          ],
          "details": {
            "text": "Hello, will the two rented coaches collect us on the campus in Palaiseau on Friday and bring us back there on Sunday? Please send the meeting point and return time once the venue and both coach journeys are confirmed. Is the Trouville-Deauville area only a search assumption for now?"
          },
          "status": "open",
          "depends_on": [
            "no_logistics_plan"
          ],
          "resolved_by_action_id": null
        }
      ],
      "actions": [],
      "travel": {
        "request": "We're planning an integration weekend for 100 students in Trouville-Deauville, 9–11 October 2026. Leave campus in Palaiseau Friday after 17:00, return Sunday by 18:00. Budget: €150 each, meals included; we're unsure whether coach hire is covered. We need two coaches, arrival before 21:00, no overnight travel, two separate step-free rooms, and a venue with a shared kitchen and activity spaces. The association buys and transports groceries. Prefer fewer changes, then an earlier return, then lower cost.",
        "participants": 100,
        "origin": "Campus in Palaiseau",
        "depart_after": "2026-10-09T17:00:00+02:00",
        "return_by": "2026-10-11T18:00:00+02:00",
        "nights": 2,
        "constraints": {
          "hard": {
            "participants": 100,
            "arrive_before": "21:00",
            "no_overnight": true,
            "step_free_rooms": 2,
            "max_cost_per_person_cents": 15000
          },
          "soft": [
            "fewer_changes",
            "early_return",
            "lower_cost"
          ],
          "organizer_verified": [
            "step_free_rooms"
          ]
        },
        "destination": "Trouville-Deauville",
        "provenance": {
          "status": "unconfirmed_demo",
          "association": "Unnamed student association",
          "event": "WEI — weekend d’intégration (self-made demo)",
          "source": "User-provided description in issue #15 implementation conversation (2026-09-26)",
          "confirmed_context": "The scenario is modelled on a real French student integration weekend described by a project contributor: organizers collect registrations, check payments, hire coaches and seek accommodation with cooking and activity spaces. Meals are included in the student fee; organizers buy groceries and transport them to the venue.",
          "unconfirmed_assumptions": [
            "Trouville-Deauville search area and Palaiseau pickup point",
            "9–11 October 2026 dates and travel times",
            "100 students and two separate step-free rooms",
            "€150 complete-package ceiling and €150 provisional participation fee, both including meals and food transport; demo allocations of €20 groceries and €2 food transport per person",
            "The initial organizer request leaves coach inclusion unclear; recorded constraints represent the clarified complete-package budget",
            "Payment deadline, refund policy and all illustrative transport/package prices and facilities"
          ],
          "personal_data": "All registrations, payments and messages are fictional.",
          "travel_options": "Illustrative recorded packages, not Jinko results or confirmed supplier quotes.",
          "review_status": "Pending an approval comment on PR #62 from a teammate who has attended or organized a WEI; no association naming consent is recorded."
        },
        "organizer_checks": [
          "Confirm the destination area, dates, headcount, fee and budget with the student organizers before using this demo for a real trip.",
          "Confirm a private round-trip coach hire, at least 100 passenger seats across the hired coaches (demo: two 53-seat buses), campus pickup, return time and accessibility with the operator; a scheduled coach ticket is not a charter quote.",
          "Confirm accommodation for 100 students for two nights, including two separate step-free rooms and accessible shared spaces.",
          "Confirm shared-kitchen capacity, equipment and permission for student group cooking. The student organizers must plan the menu, quantities and dietary needs, buy groceries and organize their transport to the venue, including vehicle capacity, handling and storage. Verify the food and delivery allocation within the student fee; the demo amounts and transport method are not confirmed.",
          "Confirm indoor and outdoor activity spaces, permission for integration activities and venue noise rules.",
          "Verify availability and complete group quotes with providers. Jinko hotel room prices are scaled estimates, not confirmed group blocks; ground search is unavailable for the current key. Verify private coach hire, kitchen access and activity permissions directly with providers."
        ],
        "catering": {
          "included_in_participation_fee": true,
          "purchased_by": "student organizers",
          "transported_by": "student organizers",
          "groceries_per_person_cents": 2000,
          "food_transport_per_person_cents": 200,
          "budget_status": "unconfirmed_demo",
          "transport_method": null,
          "logistics_status": "to_confirm"
        },
        "search": {
          "city": "Deauville",
          "country_code": "fr",
          "station": [
            49.3583,
            0.0858
          ],
          "checkin": "2026-10-09",
          "checkout": "2026-10-11",
          "rooms": 50
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
          "w08": "Hugo Garnier",
          "w09": "Alice Martin",
          "w10": "Gabriel Petit",
          "w11": "Chloé Simon",
          "w12": "Louis Robert",
          "w13": "Manon Richard",
          "w14": "Adam Durand",
          "w15": "Jade Michel",
          "w16": "Arthur Thomas",
          "w17": "Lina Garcia",
          "w18": "Paul Fontaine",
          "w19": "Clara Chevalier",
          "w20": "Noé François",
          "w21": "Maya Legrand",
          "w22": "Rayan Gauthier",
          "w23": "Léa Garnier",
          "w24": "Ethan Roussel",
          "w25": "Zoé Vincent",
          "w26": "Samuel Muller",
          "w27": "Anna Faure",
          "w28": "Nicolas André",
          "w29": "Nora Mercier",
          "w30": "Raphaël Blanc",
          "w31": "Louise Guérin",
          "w32": "Sacha Boyer",
          "w33": "Yasmine Perrin",
          "w34": "Victor Morel",
          "w35": "Eva Masson",
          "w36": "Alexandre Colin",
          "w37": "Julia Renault",
          "w38": "Omar Leroy",
          "w39": "Lucie Bonnet",
          "w40": "Théo Marchand",
          "w41": "Adèle Delcourt",
          "w42": "Bastien Delcourt",
          "w43": "Célia Delcourt",
          "w44": "Dorian Delcourt",
          "w45": "Élise Delcourt",
          "w46": "Farid Delcourt",
          "w47": "Gaëlle Delcourt",
          "w48": "Ilyes Delcourt",
          "w49": "Jeanne Delcourt",
          "w50": "Kilian Delcourt",
          "w51": "Adèle Vidal",
          "w52": "Bastien Vidal",
          "w53": "Célia Vidal",
          "w54": "Dorian Vidal",
          "w55": "Élise Vidal",
          "w56": "Farid Vidal",
          "w57": "Gaëlle Vidal",
          "w58": "Ilyes Vidal",
          "w59": "Jeanne Vidal",
          "w60": "Kilian Vidal",
          "w61": "Adèle Renaud",
          "w62": "Bastien Renaud",
          "w63": "Célia Renaud",
          "w64": "Dorian Renaud",
          "w65": "Élise Renaud",
          "w66": "Farid Renaud",
          "w67": "Gaëlle Renaud",
          "w68": "Ilyes Renaud",
          "w69": "Jeanne Renaud",
          "w70": "Kilian Renaud",
          "w71": "Adèle Lemoine",
          "w72": "Bastien Lemoine",
          "w73": "Célia Lemoine",
          "w74": "Dorian Lemoine",
          "w75": "Élise Lemoine",
          "w76": "Farid Lemoine",
          "w77": "Gaëlle Lemoine",
          "w78": "Ilyes Lemoine",
          "w79": "Jeanne Lemoine",
          "w80": "Kilian Lemoine",
          "w81": "Adèle Marin",
          "w82": "Bastien Marin",
          "w83": "Célia Marin",
          "w84": "Dorian Marin",
          "w85": "Élise Marin",
          "w86": "Farid Marin",
          "w87": "Gaëlle Marin",
          "w88": "Ilyes Marin",
          "w89": "Jeanne Marin",
          "w90": "Kilian Marin",
          "w91": "Adèle Pascal",
          "w92": "Bastien Pascal",
          "w93": "Célia Pascal",
          "w94": "Dorian Pascal",
          "w95": "Élise Pascal",
          "w96": "Farid Pascal",
          "w97": "Gaëlle Pascal",
          "w98": "Ilyes Pascal",
          "w99": "Jeanne Pascal",
          "w100": "Kilian Pascal"
        },
        "payments": {
          "b02": "Tom Girard · €150",
          "b03": "Inès Roux · €150",
          "b04": "Lucas Bernard · €150",
          "b05": "Emma Laurent · €150",
          "b90": "C. DUPONT-LAMBERT · €150",
          "b009": "Alice Martin · €150",
          "b010": "Gabriel Petit · €150",
          "b011": "Chloé Simon · €150",
          "b012": "Louis Robert · €150",
          "b013": "Manon Richard · €150",
          "b014": "Adam Durand · €150",
          "b015": "Jade Michel · €150",
          "b016": "Arthur Thomas · €150",
          "b017": "Lina Garcia · €150",
          "b018": "Paul Fontaine · €150",
          "b019": "Clara Chevalier · €150",
          "b020": "Noé François · €150",
          "b021": "Maya Legrand · €150",
          "b022": "Rayan Gauthier · €150",
          "b023": "Léa Garnier · €150",
          "b024": "Ethan Roussel · €150",
          "b025": "Zoé Vincent · €150",
          "b026": "Samuel Muller · €150",
          "b027": "Anna Faure · €150",
          "b028": "Nicolas André · €150",
          "b029": "Nora Mercier · €150",
          "b030": "Raphaël Blanc · €150",
          "b031": "Louise Guérin · €150",
          "b032": "Sacha Boyer · €150",
          "b033": "Yasmine Perrin · €150",
          "b034": "Victor Morel · €150",
          "b035": "Eva Masson · €150",
          "b036": "Alexandre Colin · €150",
          "b037": "Julia Renault · €150",
          "b038": "Omar Leroy · €150",
          "b039": "Lucie Bonnet · €150",
          "b040": "Théo Marchand · €150",
          "b041": "Adèle Delcourt · €150",
          "b042": "Bastien Delcourt · €150",
          "b043": "Célia Delcourt · €150",
          "b044": "Dorian Delcourt · €150",
          "b045": "Élise Delcourt · €150",
          "b046": "Farid Delcourt · €150",
          "b047": "Gaëlle Delcourt · €150",
          "b048": "Ilyes Delcourt · €150",
          "b049": "Jeanne Delcourt · €150",
          "b050": "Kilian Delcourt · €150",
          "b051": "Adèle Vidal · €150",
          "b052": "Bastien Vidal · €150",
          "b053": "Célia Vidal · €150",
          "b054": "Dorian Vidal · €150",
          "b055": "Élise Vidal · €150",
          "b056": "Farid Vidal · €150",
          "b057": "Gaëlle Vidal · €150",
          "b058": "Ilyes Vidal · €150",
          "b059": "Jeanne Vidal · €150",
          "b060": "Kilian Vidal · €150",
          "b061": "Adèle Renaud · €150",
          "b062": "Bastien Renaud · €150",
          "b063": "Célia Renaud · €150",
          "b064": "Dorian Renaud · €150",
          "b065": "Élise Renaud · €150",
          "b066": "Farid Renaud · €150",
          "b067": "Gaëlle Renaud · €150",
          "b068": "Ilyes Renaud · €150",
          "b069": "Jeanne Renaud · €150",
          "b070": "Kilian Renaud · €150",
          "b071": "Adèle Lemoine · €150",
          "b072": "Bastien Lemoine · €150",
          "b073": "Célia Lemoine · €150",
          "b074": "Dorian Lemoine · €150",
          "b075": "Élise Lemoine · €150",
          "b076": "Farid Lemoine · €150",
          "b077": "Gaëlle Lemoine · €150",
          "b078": "Ilyes Lemoine · €150",
          "b079": "Jeanne Lemoine · €150",
          "b080": "Kilian Lemoine · €150",
          "b081": "Adèle Marin · €150",
          "b082": "Bastien Marin · €150",
          "b083": "Célia Marin · €150",
          "b084": "Dorian Marin · €150",
          "b085": "Élise Marin · €150",
          "b086": "Farid Marin · €150",
          "b087": "Gaëlle Marin · €150",
          "b088": "Ilyes Marin · €150",
          "b089": "Jeanne Marin · €150",
          "b090": "Kilian Marin · €150",
          "b091": "Adèle Pascal · €150",
          "b092": "Bastien Pascal · €150",
          "b093": "Célia Pascal · €150",
          "b094": "Dorian Pascal · €150",
          "b095": "Élise Pascal · €150",
          "b096": "Farid Pascal · €150",
          "b097": "Gaëlle Pascal · €150",
          "b098": "Ilyes Pascal · €150",
          "b099": "Jeanne Pascal · €150",
          "b100": "Kilian Pascal · €150"
        },
        "groups": {}
      },
      "meta": {
        "type": "Integration weekend",
        "dates": "9–11 Oct 2026",
        "place": "Palaiseau → Trouville-Deauville (demo)",
        "participants": 100
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
        "description": "A. Nguyen · nguyen.a@gmail.example · €10 · 19 Sep"
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
        "detail": "nguyen.a@gmail.example",
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
      "to": "a.nguyen@polytechnique.example",
      "message": "Bonjour Antoine, votre cotisation 2026 est bien associée à votre inscription. Merci pour votre patience !\n— Drafted with AI assistance, approved by the organizers."
    },
    "trace": [
      {
        "step": 1,
        "tool": "get_participant",
        "arguments": {
          "id_or_email": "a.nguyen@polytechnique.example"
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
    "title": "3 of 5 options pass every verified hard constraint",
    "description": "Option D ranks first under the current priorities (fewer changes, an earlier return, lower cost) at €141/person. Other valid options: Option A (€112), Option B (€118). Rejected: Option C (arrive before 21:00); Option E (arrive before 21:00, no overnight travel). Organizers choose; nothing is booked automatically.",
    "evidence": [
      {
        "source_type": "travel_option",
        "source_id": "A",
        "description": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified"
      },
      {
        "source_type": "travel_option",
        "source_id": "B",
        "description": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified"
      },
      {
        "source_type": "travel_option",
        "source_id": "C",
        "description": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified"
      },
      {
        "source_type": "travel_option",
        "source_id": "D",
        "description": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified"
      },
      {
        "source_type": "travel_option",
        "source_id": "E",
        "description": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified"
      }
    ],
    "checks": [
      {
        "name": "itemized cost matches total",
        "passed": true,
        "detail": "coach: €42 + lodging: €77 + groceries: €20 + food_transport: €2",
        "verified": true
      },
      {
        "name": "cost ≤ €150/person",
        "passed": true,
        "detail": "€141",
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
        "name": "lodging for 100",
        "passed": true,
        "detail": "100",
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
        "D",
        "A",
        "B"
      ],
      "options": [
        {
          "option": {
            "id": "A",
            "transport": {
              "mode": "coach",
              "charter": true,
              "capacity": 106,
              "round_trip": true,
              "charter_verified": false,
              "depart": "18:10",
              "arrive": "20:15",
              "changes": 0,
              "overnight": false,
              "return_arrive": "17:30",
              "vehicles": 2,
              "seats_per_vehicle": 53
            },
            "lodging": {
              "name": "Illustrative Normandy group holiday park A",
              "rooms": 25,
              "capacity": 100,
              "step_free_hint": true,
              "nights": 2,
              "kitchen_hint": true,
              "activity_space_hint": true,
              "facilities_verified": false
            },
            "cost_per_person_cents": 11200,
            "source": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified",
            "cost_breakdown_per_person_cents": {
              "coach": 3500,
              "lodging": 5500,
              "groceries": 2000,
              "food_transport": 200
            }
          },
          "checks": [
            {
              "name": "itemized cost matches total",
              "passed": true,
              "detail": "coach: €35 + lodging: €55 + groceries: €20 + food_transport: €2",
              "verified": true
            },
            {
              "name": "cost ≤ €150/person",
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
              "name": "lodging for 100",
              "passed": true,
              "detail": "100",
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
              "mode": "coach",
              "charter": true,
              "capacity": 106,
              "round_trip": true,
              "charter_verified": false,
              "depart": "18:05",
              "arrive": "20:40",
              "changes": 0,
              "overnight": false,
              "return_arrive": "18:00",
              "vehicles": 2,
              "seats_per_vehicle": 53
            },
            "lodging": {
              "name": "Illustrative Normandy residential activity centre B",
              "rooms": 50,
              "capacity": 100,
              "step_free_hint": true,
              "nights": 2,
              "kitchen_hint": true,
              "activity_space_hint": true,
              "facilities_verified": false
            },
            "cost_per_person_cents": 11800,
            "source": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified",
            "cost_breakdown_per_person_cents": {
              "coach": 4000,
              "lodging": 5600,
              "groceries": 2000,
              "food_transport": 200
            }
          },
          "checks": [
            {
              "name": "itemized cost matches total",
              "passed": true,
              "detail": "coach: €40 + lodging: €56 + groceries: €20 + food_transport: €2",
              "verified": true
            },
            {
              "name": "cost ≤ €150/person",
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
              "name": "lodging for 100",
              "passed": true,
              "detail": "100",
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
              "charter": true,
              "capacity": 106,
              "round_trip": true,
              "charter_verified": false,
              "depart": "18:30",
              "arrive": "22:10",
              "changes": 0,
              "overnight": false,
              "return_arrive": "20:30",
              "vehicles": 2,
              "seats_per_vehicle": 53
            },
            "lodging": {
              "name": "Illustrative Normandy holiday village C",
              "rooms": 50,
              "capacity": 100,
              "step_free_hint": true,
              "nights": 2,
              "kitchen_hint": true,
              "activity_space_hint": true,
              "facilities_verified": false
            },
            "cost_per_person_cents": 9600,
            "source": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified",
            "cost_breakdown_per_person_cents": {
              "coach": 3000,
              "lodging": 4400,
              "groceries": 2000,
              "food_transport": 200
            }
          },
          "checks": [
            {
              "name": "itemized cost matches total",
              "passed": true,
              "detail": "coach: €30 + lodging: €44 + groceries: €20 + food_transport: €2",
              "verified": true
            },
            {
              "name": "cost ≤ €150/person",
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
              "name": "lodging for 100",
              "passed": true,
              "detail": "100",
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
              "mode": "coach",
              "charter": true,
              "capacity": 106,
              "round_trip": true,
              "charter_verified": false,
              "depart": "18:10",
              "arrive": "20:15",
              "changes": 0,
              "overnight": false,
              "return_arrive": "17:00",
              "vehicles": 2,
              "seats_per_vehicle": 53
            },
            "lodging": {
              "name": "Illustrative Normandy group resort D",
              "rooms": 50,
              "capacity": 100,
              "step_free_hint": true,
              "nights": 2,
              "kitchen_hint": true,
              "activity_space_hint": true,
              "facilities_verified": false
            },
            "cost_per_person_cents": 14100,
            "source": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified",
            "cost_breakdown_per_person_cents": {
              "coach": 4200,
              "lodging": 7700,
              "groceries": 2000,
              "food_transport": 200
            }
          },
          "checks": [
            {
              "name": "itemized cost matches total",
              "passed": true,
              "detail": "coach: €42 + lodging: €77 + groceries: €20 + food_transport: €2",
              "verified": true
            },
            {
              "name": "cost ≤ €150/person",
              "passed": true,
              "detail": "€141",
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
              "name": "lodging for 100",
              "passed": true,
              "detail": "100",
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
            "id": "E",
            "transport": {
              "mode": "coach",
              "charter": true,
              "capacity": 106,
              "round_trip": true,
              "charter_verified": false,
              "depart": "23:00",
              "arrive": "02:30",
              "arrives_next_day": true,
              "changes": 0,
              "overnight": true,
              "return_arrive": "21:00",
              "vehicles": 2,
              "seats_per_vehicle": 53
            },
            "lodging": {
              "name": "Illustrative Normandy group holiday park E",
              "rooms": 25,
              "capacity": 100,
              "step_free_hint": true,
              "nights": 2,
              "kitchen_hint": true,
              "activity_space_hint": true,
              "facilities_verified": false
            },
            "cost_per_person_cents": 7800,
            "source": "recorded illustration for the student WEI demo; total includes meals and food transport; not a Jinko quote; charter and venue facilities unverified",
            "cost_breakdown_per_person_cents": {
              "coach": 2200,
              "lodging": 3400,
              "groceries": 2000,
              "food_transport": 200
            }
          },
          "checks": [
            {
              "name": "itemized cost matches total",
              "passed": true,
              "detail": "coach: €22 + lodging: €34 + groceries: €20 + food_transport: €2",
              "verified": true
            },
            {
              "name": "cost ≤ €150/person",
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
              "name": "lodging for 100",
              "passed": true,
              "detail": "100",
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
      ],
      "constraints": {
        "hard": {
          "participants": 100,
          "arrive_before": "21:00",
          "no_overnight": true,
          "step_free_rooms": 2,
          "max_cost_per_person_cents": 15000
        },
        "soft": [
          "fewer_changes",
          "early_return",
          "lower_cost"
        ],
        "organizer_verified": [
          "step_free_rooms"
        ],
        "clarifications": []
      },
      "request_text": "We're planning an integration weekend for 100 students in Trouville-Deauville, 9–11 October 2026. Leave campus in Palaiseau Friday after 17:00, return Sunday by 18:00. Budget: €150 each, meals included; we're unsure whether coach hire is covered. We need two coaches, arrival before 21:00, no overnight travel, two separate step-free rooms, and a venue with a shared kitchen and activity spaces. The association buys and transports groceries. Prefer fewer changes, then an earlier return, then lower cost.",
      "constraints_source": "recorded",
      "answered": false
    },
    "trace": []
  },
  "budget_answer": "Yes, the €150 per person includes round-trip coach hire, lodging, groceries and food transport.",
  "budget_question": "Does the €150 per person include round-trip coach hire as well as lodging, groceries and food transport?",
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
  "rule_replies": {
    "hackathon:message:m02": {
      "id": "hackathon:message:m02",
      "event_id": "hackathon",
      "issue_id": "message:m02",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the existing-project rule",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§7",
          "description": "Impact 30%, innovation 20%, execution quality 20%, user experience 15%, demo and pitch clarity 15%. Building on an existing project is allowed if declared at submission; only the part created during the hackathon is evaluated."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§7",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "julien.morel@gmail.example",
        "text": "You may build on an existing project if you declare it at submission. Only work created during the hackathon will be evaluated.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§7"
          },
          "result": "Impact 30%, innovation 20%, execution quality 20%, user experience 15%, demo and pitch clarity 15%. Building on an existing project is allowed if declared at submission; only the part created during the hackathon is evaluated.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m03": {
      "id": "hackathon:message:m03",
      "event_id": "hackathon",
      "issue_id": "message:m03",
      "action_type": "SEND_MESSAGE",
      "title": "Clarify the final date",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§4",
          "description": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October)."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§4",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "orbit_hugo",
        "text": "La finale a été déplacée du 15 octobre à novembre, lors d'un événement X-IA. La date précise doit être confirmée par les organisateurs.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§4"
          },
          "result": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October).",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m06": {
      "id": "hackathon:message:m06",
      "event_id": "hackathon",
      "issue_id": "message:m06",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the two participation requirements",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§3",
          "description": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§3",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "amelie.derval@participants.example",
        "text": "La cotisation X-IA 2026 est de 10 €. L'inscription sur la page Luma officielle est également obligatoire.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§3"
          },
          "result": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m07": {
      "id": "hackathon:message:m07",
      "event_id": "hackathon",
      "issue_id": "message:m07",
      "action_type": "SEND_MESSAGE",
      "title": "Share the submission checklist",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§6",
          "description": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§6",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "noah.belcourt@participants.example",
        "text": "Please submit a demo video of at most two minutes, a short project description, a repository link with testing instructions, and the names of your team members.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§6"
          },
          "result": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m08": {
      "id": "hackathon:message:m08",
      "event_id": "hackathon",
      "issue_id": "message:m08",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the team-size limit",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§3",
          "description": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§3",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "datadragons_marc",
        "text": "Une équipe peut compter au maximum quatre personnes, y compris la personne chargée du pitch. Merci d'adapter la composition de votre équipe.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§3"
          },
          "result": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m09": {
      "id": "hackathon:message:m09",
      "event_id": "hackathon",
      "issue_id": "message:m09",
      "action_type": "SEND_MESSAGE",
      "title": "Ask Léa to choose one team",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§3",
          "description": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§3",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "lea.martin@polytechnique.example",
        "text": "You may belong to only one team. Please tell the organizers whether you want to stay in Orbit or NeuralNomads. This reply does not change either team.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§3"
          },
          "result": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m15": {
      "id": "hackathon:message:m15",
      "event_id": "hackathon",
      "issue_id": "message:m15",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the partner-credit rules",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§5",
          "description": "Partner credits (OpenAI, Pipelex, Gradium, Jinko, Dust) are for the hackathon only and may not be resold, transferred or used for personal or commercial purposes. The participant list is sent to partners only to activate access."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§5",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "emma.lioran@participants.example",
        "text": "Partner credits may not be resold or transferred to another participant. They are reserved for work during this hackathon.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§5"
          },
          "result": "Partner credits (OpenAI, Pipelex, Gradium, Jinko, Dust) are for the hackathon only and may not be resold, transferred or used for personal or commercial purposes. The participant list is sent to partners only to activate access.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m16": {
      "id": "hackathon:message:m16",
      "event_id": "hackathon",
      "issue_id": "message:m16",
      "action_type": "SEND_MESSAGE",
      "title": "Clarify permitted use of partner credits",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§5",
          "description": "Partner credits (OpenAI, Pipelex, Gradium, Jinko, Dust) are for the hackathon only and may not be resold, transferred or used for personal or commercial purposes. The participant list is sent to partners only to activate access."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§5",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "oscar.nerac@participants.example",
        "text": "Les crédits partenaires sont réservés au hackathon. Ils ne peuvent pas être utilisés pour une mission personnelle ou commerciale.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§5"
          },
          "result": "Partner credits (OpenAI, Pipelex, Gradium, Jinko, Dust) are for the hackathon only and may not be resold, transferred or used for personal or commercial purposes. The participant list is sent to partners only to activate access.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m17": {
      "id": "hackathon:message:m17",
      "event_id": "hackathon",
      "issue_id": "message:m17",
      "action_type": "SEND_MESSAGE",
      "title": "Explain why Luma registration is needed",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§3",
          "description": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§3",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "lina.valcourt@participants.example",
        "text": "Payment of the membership fee alone is not enough. Participants must also register on the official Luma page.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§3"
          },
          "result": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m18": {
      "id": "hackathon:message:m18",
      "event_id": "hackathon",
      "issue_id": "message:m18",
      "action_type": "SEND_MESSAGE",
      "title": "Confirm the submission deadline",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§4",
          "description": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October)."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§4",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "adam.solvier@participants.example",
        "text": "La phase de réalisation se termine le dimanche 27 septembre 2026 à 23 h 59, heure de Paris (UTC+02:00).\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§4"
          },
          "result": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October).",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m19": {
      "id": "hackathon:message:m19",
      "event_id": "hackathon",
      "issue_id": "message:m19",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the deadline policy",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§6",
          "description": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§6",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "sarah.meriel@participants.example",
        "text": "The sample rules do not allow late submissions. Please allow time for the upload and submit the complete package before the deadline.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§6"
          },
          "result": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m24": {
      "id": "hackathon:message:m24",
      "event_id": "hackathon",
      "issue_id": "message:m24",
      "action_type": "SEND_MESSAGE",
      "title": "Confirm individual participation",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§3",
          "description": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§3",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "salome.vandel@participants.example",
        "text": "Oui, la participation individuelle est autorisée. Vous devez être à jour de votre cotisation et inscrite sur la page Luma officielle.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§3"
          },
          "result": "Open to X-IA members whose 2026 membership fee (cotisation, €10) is paid. Registration on the official Luma page is required. Participants compete individually or in teams of 2 to 4 people. Each participant may belong to only one team.",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    },
    "hackathon:message:m25": {
      "id": "hackathon:message:m25",
      "event_id": "hackathon",
      "issue_id": "message:m25",
      "action_type": "SEND_MESSAGE",
      "title": "Explain the agentic-project requirement",
      "description": "Saved sample proposal; review before approval.",
      "evidence": [
        {
          "source_type": "rule",
          "source_id": "§2",
          "description": "Projects must be genuinely agentic: they use one or more LLMs and implement real agent logic (reasoning, decision-making, orchestration of actions)."
        }
      ],
      "checks": [
        {
          "name": "Saved rule reference exists",
          "passed": true,
          "detail": "§2",
          "verified": true
        }
      ],
      "confidence": null,
      "requires_approval": true,
      "payload": {
        "to": "kenji.aster@participants.example",
        "text": "The project must use one or more LLMs and implement real agent logic. A dashboard containing only fixed scripts would not meet that requirement.\n— Drafted with AI assistance, approved by the organizers."
      },
      "trace": [
        {
          "step": 1,
          "tool": "search_rules",
          "arguments": {
            "section": "§2"
          },
          "result": "Projects must be genuinely agentic: they use one or more LLMs and implement real agent logic (reasoning, decision-making, orchestration of actions).",
          "ok": true
        },
        {
          "step": 2,
          "tool": "propose_action",
          "arguments": {
            "action_type": "SEND_MESSAGE"
          },
          "result": "Curated sample; organizer approval required",
          "ok": true
        }
      ]
    }
  },
  "bulk_replies": {
    "hackathon:message:m02": {
      "action": {
        "id": "hackathon:message:m02",
        "event_id": "hackathon",
        "issue_id": "message:m02",
        "action_type": "SEND_MESSAGE",
        "title": "Explain the existing-project rule",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§7",
            "description": "Impact 30%, innovation 20%, execution quality 20%, user experience 15%, demo and pitch clarity 15%. Building on an existing project is allowed if declared at submission; only the part created during the hackathon is evaluated."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§7",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "julien.morel@gmail.example",
          "text": "You may build on an existing project if you declare it at submission. Only work created during the hackathon will be evaluated.\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§7"
            },
            "result": "Impact 30%, innovation 20%, execution quality 20%, user experience 15%, demo and pitch clarity 15%. Building on an existing project is allowed if declared at submission; only the part created during the hackathon is evaluated.",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
        "id": "message:m02",
        "kind": "unprocessed_message",
        "blocking": false,
        "title": "New email message from julien.morel@gmail.example",
        "subject_ids": [
          "m02"
        ],
        "details": {
          "text": "Hi, my team already started a RAG agent project. Can we keep working on it during the hackathon?"
        },
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m02",
        "title": "Explain the existing-project rule",
        "to": "julien.morel@gmail.example",
        "text": "You may build on an existing project if you declare it at submission. Only work created during the hackathon will be evaluated.\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§7"
        ],
        "revision": "7aa279d55c6d5fc6df4b0d658c99df4a2f7eb30579d72b6fc57c8729d780f019"
      }
    },
    "hackathon:message:m03": {
      "action": {
        "id": "hackathon:message:m03",
        "event_id": "hackathon",
        "issue_id": "message:m03",
        "action_type": "SEND_MESSAGE",
        "title": "Clarify the final date",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§4",
            "description": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October)."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§4",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "orbit_hugo",
          "text": "La finale a été déplacée du 15 octobre à novembre, lors d'un événement X-IA. La date précise doit être confirmée par les organisateurs.\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§4"
            },
            "result": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October).",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
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
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m03",
        "title": "Clarify the final date",
        "to": "orbit_hugo",
        "text": "La finale a été déplacée du 15 octobre à novembre, lors d'un événement X-IA. La date précise doit être confirmée par les organisateurs.\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§4"
        ],
        "revision": "396a22c066e82f8c2359756d148cc69cb0bea5ea15980ec84a6ea3233336b131"
      }
    },
    "hackathon:message:m07": {
      "action": {
        "id": "hackathon:message:m07",
        "event_id": "hackathon",
        "issue_id": "message:m07",
        "action_type": "SEND_MESSAGE",
        "title": "Share the submission checklist",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§6",
            "description": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§6",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "noah.belcourt@participants.example",
          "text": "Please submit a demo video of at most two minutes, a short project description, a repository link with testing instructions, and the names of your team members.\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§6"
            },
            "result": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted.",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
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
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m07",
        "title": "Share the submission checklist",
        "to": "noah.belcourt@participants.example",
        "text": "Please submit a demo video of at most two minutes, a short project description, a repository link with testing instructions, and the names of your team members.\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§6"
        ],
        "revision": "b84073436fab080b0eeea36b5165e9fe9946db59f20f382daba3a6e98b897373"
      }
    },
    "hackathon:message:m18": {
      "action": {
        "id": "hackathon:message:m18",
        "event_id": "hackathon",
        "issue_id": "message:m18",
        "action_type": "SEND_MESSAGE",
        "title": "Confirm the submission deadline",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§4",
            "description": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October)."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§4",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "adam.solvier@participants.example",
          "text": "La phase de réalisation se termine le dimanche 27 septembre 2026 à 23 h 59, heure de Paris (UTC+02:00).\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§4"
            },
            "result": "Coding phase from 25/09/26 09:00 to 27/09/26 23:59. Pre-selection of finalists in October. The final takes place in November, at an X-IA event (it was moved from 15 October).",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
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
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m18",
        "title": "Confirm the submission deadline",
        "to": "adam.solvier@participants.example",
        "text": "La phase de réalisation se termine le dimanche 27 septembre 2026 à 23 h 59, heure de Paris (UTC+02:00).\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§4"
        ],
        "revision": "c1c85220c7e093f2e17c36b2e1519d005444cc73acc0e178a925220548a50abb"
      }
    },
    "hackathon:message:m19": {
      "action": {
        "id": "hackathon:message:m19",
        "event_id": "hackathon",
        "issue_id": "message:m19",
        "action_type": "SEND_MESSAGE",
        "title": "Explain the deadline policy",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§6",
            "description": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§6",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "sarah.meriel@participants.example",
          "text": "The sample rules do not allow late submissions. Please allow time for the upload and submit the complete package before the deadline.\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§6"
            },
            "result": "Before the deadline: a demo video of 2 minutes maximum, a short description, a repository link with test instructions in the README, and team member names. Late submissions are not accepted.",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
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
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m19",
        "title": "Explain the deadline policy",
        "to": "sarah.meriel@participants.example",
        "text": "The sample rules do not allow late submissions. Please allow time for the upload and submit the complete package before the deadline.\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§6"
        ],
        "revision": "736545a26f564c1fa6b433eeee71c55f19d42543b123549269e8b26c28d7fd73"
      }
    },
    "hackathon:message:m25": {
      "action": {
        "id": "hackathon:message:m25",
        "event_id": "hackathon",
        "issue_id": "message:m25",
        "action_type": "SEND_MESSAGE",
        "title": "Explain the agentic-project requirement",
        "description": "Saved sample proposal; review before approval.",
        "evidence": [
          {
            "source_type": "rule",
            "source_id": "§2",
            "description": "Projects must be genuinely agentic: they use one or more LLMs and implement real agent logic (reasoning, decision-making, orchestration of actions)."
          }
        ],
        "checks": [
          {
            "name": "Saved rule reference exists",
            "passed": true,
            "detail": "§2",
            "verified": true
          }
        ],
        "confidence": null,
        "requires_approval": true,
        "payload": {
          "to": "kenji.aster@participants.example",
          "text": "The project must use one or more LLMs and implement real agent logic. A dashboard containing only fixed scripts would not meet that requirement.\n— Drafted with AI assistance, approved by the organizers."
        },
        "trace": [
          {
            "step": 1,
            "tool": "search_rules",
            "arguments": {
              "section": "§2"
            },
            "result": "Projects must be genuinely agentic: they use one or more LLMs and implement real agent logic (reasoning, decision-making, orchestration of actions).",
            "ok": true
          },
          {
            "step": 2,
            "tool": "propose_action",
            "arguments": {
              "action_type": "SEND_MESSAGE"
            },
            "result": "Curated sample; organizer approval required",
            "ok": true
          }
        ]
      },
      "issue": {
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
        "status": "proposed",
        "depends_on": [],
        "resolved_by_action_id": null
      },
      "preview": {
        "id": "hackathon:message:m25",
        "title": "Explain the agentic-project requirement",
        "to": "kenji.aster@participants.example",
        "text": "The project must use one or more LLMs and implement real agent logic. A dashboard containing only fixed scripts would not meet that requirement.\n— Drafted with AI assistance, approved by the organizers.",
        "rules": [
          "§2"
        ],
        "revision": "1a7f7e823745b65a48ca3476f2b1dc65d80e9333b442d9159ff0090ca986e5b3"
      }
    }
  },
  "bulk_limit": 100,
  "revision": "308ab3cfe9dc3226"
};

Voilà le récap complet à copier-coller dans le prochain chat :

---

# Contexte — Suite système Caisses/Stickers Jungle Gap

## ✅ Étape 1 — DB & Modèles (DONE)

**Migrations SQL appliquées en local** (PAS en prod) :
- `user_cards` : ajout `quantity INTEGER NOT NULL DEFAULT 1` + `equipped_slot VARCHAR(10)` (NULL | left | center | right)
- Contrainte CHECK + index unique partiel `uq_user_cards_user_slot` (user_id, equipped_slot) WHERE equipped_slot IS NOT NULL
- Contrainte UNIQUE existante `(user_id, card_id)` conservée → exploitée pour `INSERT ... ON CONFLICT DO UPDATE`
- Nouvelle table `lootbox_types` : config admin des types de caisses (drop rates par rareté, pool_types CSV, price_coins, is_active)
- Nouvelle table `lootboxes` : caisses possédées par user (opened_at + opened_card_id pour l'historique)
- `promo_codes` : ajout `lootbox_type_id` + `lootbox_quantity`

**Modèles SQLAlchemy créés/modifiés** :
- `backend/models/user_card.py` : ajout colonnes + CheckConstraint
- `backend/models/lootbox.py` : nouveau fichier (LootBoxType + LootBox)
- `backend/models/promo.py` : ajout des 2 colonnes + relationship lootbox_type

## ✅ Étape 2A — Backend base caisses (DONE)

**Fichiers créés** :
- `backend/services/lootbox_service.py` : `pick_card_from_box()` (tirage rareté pondéré + fallback rareté si pool vide) + `grant_card_to_user()` (atomique via ON CONFLICT)
- `backend/routers/lootbox.py` : router `/lootbox`

**Endpoints implémentés** :
- `GET /lootbox/my-boxes` : caisses non-ouvertes de l'user
- `GET /lootbox/types` : catalogue des caisses actives (pour shop)
- `POST /lootbox/{box_id}/open` : ouverture (vérifie ownership + not opened + appelle pick_card)
- `POST /lootbox/admin/types` : création type de caisse (admin only, validation drop_rates total = 100)
- `POST /lootbox/admin/grant/{user_id}/{box_type_id}?quantity=N` : grant manuel

**Tests effectués** :
- Création caisse "Basique" OK (id=1, prix 500 coins)
- Grant + listing OK
- Ouverture impossible car DB locale n'a aucune carte → à régler avec Jérémy au prochain test (soit créer des cartes via AdminCards, soit injecter en SQL)
- ⚠️ Pas encore testé : la distribution des raretés sur 20+ ouvertures + l'incrément de `quantity` sur doublons

**Constantes définies (pas encore utilisées)** :
```python
RESALE_PRICES = {"common": 50, "rare": 200, "epic": 800, "legendary": 3000}
```

---

## 🎯 Étape suivante — 2B : Achat / Revente / Promo

À implémenter **dans cet ordre** :

1. **`POST /lootbox/buy/{box_type_id}`** : 
   - Vérifie que le type est `is_active` et a un `price_coins` non NULL
   - Vérifie que l'user a assez de coins
   - Débite + crée 1 LootBox
   - Renvoie `{success, coins_remaining, lootbox_id}`

2. **`POST /cards/{user_card_id}/sell`** (dans `routers/cards.py`) :
   - Vérifie ownership
   - Empêche revente si `equipped=true` ou `equipped_slot IS NOT NULL`
   - Si `quantity > 1` → décrémente
   - Si `quantity == 1` → DELETE la ligne
   - Crédite `RESALE_PRICES[card.rarity]` coins
   - Renvoie `{success, coins_gained, coins_total, remaining_quantity}`

3. **Intégration `/promo/redeem`** :
   - Si `promo.lootbox_type_id` non NULL et `promo.lootbox_quantity > 0` → créer N LootBox pour l'user
   - Ajouter `lootbox` dans le `rewards` dict renvoyé : `{"lootbox": {"name": "...", "quantity": N}}`

4. **Admin endpoints complémentaires** :
   - `GET /lootbox/admin/types` : liste TOUS les types (actifs + inactifs)
   - `PATCH /lootbox/admin/types/{id}` : édition
   - `DELETE /lootbox/admin/types/{id}` : suppression (uniquement si pas de LootBox liée, sinon `is_active=false`)

## 🎯 Étape 3 — Frontend ouverture

- Page "Mes caisses" : soit nouvelle page `/lootbox`, soit onglet dans Profile (à voir avec Jérémy)
- Page shop "Acheter une caisse" (`GET /lootbox/types`)
- Animation d'ouverture : carte qui flip avec couleur selon rarité, effet de glow/shimmer (s'inspirer du composant `TcgCard` existant)
- Bouton "Revendre" sur les cartes en doublon dans le tab "Cartes" du Profile

## 🎯 Étape 4 — Bannière Stickers (le but originel)

**Backend** :
- `POST /cards/equip-slot` body `{user_card_id, slot}` : valide que `card.type == 'sticker'`, contrainte unique gère le slot déjà pris (DELETE puis INSERT, ou UPDATE)
- `DELETE /cards/equip-slot/{slot}` : retire le sticker du slot
- Exposer les 3 stickers équipés dans `/profile/me` et `/user/{id}` : nouveau champ `equipped_stickers: {left, center, right}` avec `{name, image_url, rarity}` ou null

**Frontend** :
- 3 zones cliquables sur `.profile-banner` (positionnées en gauche / centre / droite, avec un emplacement vide qui montre `+` quand on est sur son propre profil)
- Modal "Choisir un sticker" qui filtre `userCards` sur `card.type === 'sticker'`
- Cliquer sur un slot vide ouvre le modal ; cliquer sur un slot rempli propose "Retirer"

## 🎯 Étape 5 — Admin UI (en parallèle / après)

- Page `/admin/lootbox` avec form de création de type + liste éditable
- Ajouter `sticker` (et plus tard `emote`, `frame`) dans le dropdown des types de carte dans `/admin/cards`
- Étendre le form AdminPromo avec champs `lootbox_type_id` + `lootbox_quantity`

## 🎯 Étape 6 — Prod

- Backup DB prod
- Appliquer la migration SQL (même fichier qu'en local)
- Push code
- Restart `junglegap-backend`
- Smoke tests : créer un type de caisse, se grant, ouvrir, vendre, racheter

---

## Setup Jérémy

- macOS, zsh, pyenv Python 3.10.10, projet à `/Users/jdelfino/JungleGap/` (⚠️ certains chemins legacy mentionnent `/Users/jdelfino/JinxIt/jinxit/` — vérifier avant d'utiliser)
- DB locale : `psql -d junglegap` (pas besoin de sudo -u postgres sur sa machine, il a accès direct)
- VM prod = `junglegap` (systemd `junglegap-backend`)
- Domaine : `junglegap.fr` (front Vercel) + `api.junglegap.fr` (back nginx)
- User_id de Jérémy en local = **2** (pas 1 comme on supposait au début)

## Préférences Jérémy

- Étudiant info, veut explications **claires/concises mais extrêmement bien réfléchies**
- Réécritures complètes après accumulation de fixes
- Modifs ligne par ligne quand scope étroit/clair
- Discuter l'approche avant de coder quand ambigu
- Code copy-pasteable dans le chat (pas en fichier)
- CSS : une règle par ligne, groupé par catégorie avec commentaires de section
- Composants : `frontend/src/pages/[Name]/index.jsx` + `Name.css` séparés
- `api` client centralisé (`import api from '../../api/client'`), JAMAIS axios brut
- Auth store : default export (`import useAuthStore from '../../store/auth'`)
- Design : `#171717` bg, `#65BD62` vert, `#c89b3c` gold, Outfit (heading 800-900) + Inter (body)

## Décisions architecturales clés (à ne pas remettre en cause)

- **Tout passe par la table `cards`** (pas de table `stickers` séparée). Le champ `type` distingue (champion / pro_player / meme / cosmetic / sticker / etc.). Extensible facilement pour emote / frame / title plus tard
- **Drop rates globaux** : common 60% / rare 25% / epic 12% / legendary 3%. Stockés sur `lootbox_types` pour permettre des caisses spéciales plus tard, mais on garde les mêmes par défaut
- **Doublons stockés en quantity** sur `user_cards` (1 ligne par carte, +1 à chaque drop) via `ON CONFLICT DO UPDATE`
- **Revente manuelle** par l'user (pas automatique). Prix par rareté : 50/200/800/3000
- **Caisses obtenues via** : achat coins + code promo (pas de daily, pas de drop sur paris pour l'instant)

## Première action attendue

Demander à Jérémy s'il veut **(A) finir l'étape 2B (achat/revente/promo) backend**, **(B) sauter directement à l'étape 4 (bannière stickers) qui est le but originel**, ou **(C) faire l'admin UI étape 5 d'abord** pour pouvoir créer des cartes/caisses sans curl.

Si A : commencer par implémenter `POST /lootbox/buy/{box_type_id}` puis `POST /cards/{user_card_id}/sell`, puis l'intégration promo. Tests via curl.

Si B : il faudra d'abord que Jérémy ait créé au moins quelques cartes de type `sticker` (via SQL ou via AdminCards si le type est ajouté au dropdown).

---

Bon courage pour le prochain chat 🚀
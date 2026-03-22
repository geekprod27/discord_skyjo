import random

ROWS = 3
COLS = 4
HIDDEN_ESTIMATE = 5


class SkyjoIA:
    def __init__(self, niveau: str = "hard"):
        assert niveau in ("easy", "hard"), "niveau doit être 'easy' ou 'hard'"
        self.niveau = niveau

    def turn(self, game, id) -> dict:
        if self.niveau == "easy":
            return self._tour_easy(game, id)
        else:
            return self._tour_hard(game, id)

    # ─────────────────────────────────────────
    # NIVEAU easy
    # ─────────────────────────────────────────
    def _tour_easy(self, game, id) -> dict:
        if game.defausse <= 2:
            pos = self._pire_carte(game.game[id], inclure_cachees=True)
            if pos:
                self.change_card(game, id, pos[0], pos[1], game.defausse)
                return

        carte_piochee = game.cartes.pop(0)

        if carte_piochee <= 4:
            pos = self._pire_carte(game.game[id], inclure_cachees=True)
            if pos:
                self.change_card(game, id, pos[0], pos[1], carte_piochee)
                return

        cachees = self._cartes_cachees(game.game[id])
        if cachees:
            pos = random.choice(cachees)
            game.defausse = carte_piochee
            game.game[id][pos[0]][pos[1]].visible = True
            return

        pos = self._pire_carte(game.game[id], inclure_cachees=False)
        if pos:
            self.change_card(game, id, pos[0], pos[y], carte_piochee)
            return

        print("pas senser etre la")
        return

    # ─────────────────────────────────────────
    # NIVEAU hard
    # ─────────────────────────────────────────
    def _tour_hard(self, game, id):
        grille = game.game[id]

        pos_def, gain_def = self._meilleur_placement(grille, game.defausse)
        if gain_def >= 5 and pos_def:
            self.change_card(game, id, pos_def[0], pos_def[1], game.defausse)
            return

        carte_piochee = game.cartes.pop(0)
        pos_pio, gain_pio = self._meilleur_placement(grille, carte_piochee)

        if gain_pio >= 3 and pos_pio:
            self.change_card(game, id, pos_pio[0], pos_pio[1], carte_piochee)
            return

        cachees = self._cartes_cachees(grille)

        col_dangereuse = self._colonne_avec_doublons_hauts(grille)
        if col_dangereuse is not None and cachees:
            cibles = [(r, col_dangereuse) for r in range(3)
                    if not grille[r][col_dangereuse].visible and not grille[r][col_dangereuse].deleted]
            if cibles:
                self.change_card(game, id, cibles[0][0], cibles[0][1], carte_piochee)
                return

        if cachees and len(cachees) >= 4:
            pos = self._meilleure_carte_a_reveiller(grille, cachees)
            game.game[id][pos[0]][pos[1]].visible = True
            game.defausse = carte_piochee
            return

        if pos_pio:
            self.change_card(game, id, pos_pio[0], pos_pio[1], carte_piochee)
            return

        print("pas ici ou probleme")

    # ─────────────────────────────────────────
    # CALCUL DU MEILLEUR PLACEMENT
    # ─────────────────────────────────────────
    def _meilleur_placement(self, grille, valeur_carte):
        """
        Retourne (position, gain) du meilleur endroit où poser `valeur_carte`.
        Gain = valeur_actuelle_estimée - valeur_carte
        Bonus si compléter une colonne identique (élimination).
        """
        best_pos = None
        best_gain = -999

        for r in range(ROWS):
            for c in range(COLS):
                carte = grille[r][c]
                if carte.deleted:
                    continue

                valeur_actuelle = carte.valeur if carte.visible else HIDDEN_ESTIMATE
                gain = valeur_actuelle - valeur_carte

                # Bonus colonne : si les 2 autres cartes de la colonne sont
                # visibles et égales à valeur_carte → on éliminerait la colonne
                autres = [grille[rr][c] for rr in range(ROWS) if rr != r and not grille[rr][c].deleted]
                if (len(autres) == ROWS - 1
                        and all(a.visible and a.valeur == valeur_carte for a in autres)):
                    gain += 20  # gros bonus : éliminer une colonne vaut beaucoup

                if gain > best_gain:
                    best_gain = gain
                    best_pos = (r, c)

        return best_pos, best_gain

    # ─────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────
    def _cartes_cachees(self, grille):
        """Liste des positions (r, c) des cartes cachées et non supprimées."""
        return [
            (r, c)
            for r in range(ROWS)
            for c in range(COLS)
            if not grille[r][c].visible and not grille[r][c].deleted
        ]

    def _pire_carte(self, grille, inclure_cachees: bool):
        """
        Position de la carte avec la valeur estimée la plus haute.
        Si inclure_cachees=True, les cartes cachées sont estimées à HIDDEN_ESTIMATE.
        """
        best_pos = None
        best_val = -999

        for r in range(ROWS):
            for c in range(COLS):
                carte = grille[r][c]
                if carte.deleted:
                    continue
                if not carte.visible and not inclure_cachees:
                    continue
                val = carte.valeur if carte.visible else HIDDEN_ESTIMATE
                if val > best_val:
                    best_val = val
                    best_pos = (r, c)

        return best_pos

    def _meilleure_carte_a_reveiller(self, grille, cachees):
        """
        Parmi les cartes cachées, choisit celle dans la colonne
        où les cartes visibles ont les valeurs les plus hautes
        (= colonne la plus risquée à garder cachée).
        """
        best_pos = cachees[0]
        best_score = -999

        for r, c in cachees:
            score_col = sum(
                grille[rr][c].valeur
                for rr in range(ROWS)
                if grille[rr][c].visible and not grille[rr][c].deleted
            )
            if score_col > best_score:
                best_score = score_col
                best_pos = (r, c)

        return best_pos

    def _colonne_avec_doublons_hauts(self, grille, seuil=7):
        for c in range(4):
            vals = [grille[r][c].valeur for r in range(3)
                    if grille[r][c].visible and not grille[r][c].deleted]
            cachees_col = [r for r in range(3)
                        if not grille[r][c].visible and not grille[r][c].deleted]
            if len(vals) >= 2 and sum(vals) >= seuil * len(vals) and cachees_col:
                return c
        return None

    def change_card(self, game, id, x, y, card):
        game.defausse = game.game[id][x][y].valeur
        game.game[id][x][y].valeur = card
        game.game[id][x][y].visible = True


async def turn(game, id):
    ia = SkyjoIA()
    ia.turn(game, id)

    game.check_colone(id)
    await game.channel.send(content=f"{id}\n{game.show_game(id)}", delete_after=60)
    if game.lastturn is None and game.check_if_last(id):
        game.lastturn = id
        await game.channel.send(content=f"# {id} a revelé sa derniere carte le dernier tour commence !")


def first_turn(game, id):
    game.game[id][0][0].visible = True
    game.game[id][0][1].visible = True

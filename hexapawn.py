import tkinter as tk
from tkinter import messagebox
import random
import json
import os


FICHIER_SAUVEGARDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "melvine_cerveau.json")


class CerveauIA:
    def __init__(self):
        self.boites = {}
        self.parties_jouees = 0
        self.victoires = 0
        self.defaites = 0
        self.historique_taux = []
        self.charger()

    def obtenir_cle(self, plateau):
        return ''.join(str(c) for ligne in plateau for c in ligne)

    def initialiser_etat(self, cle_etat, mouvements_valides):
        if cle_etat not in self.boites:
            self.boites[cle_etat] = {}
        for mouvement in mouvements_valides:
            cle_m = f"{mouvement[0][0]},{mouvement[0][1]}-{mouvement[1][0]},{mouvement[1][1]}"
            if cle_m not in self.boites[cle_etat]:
                self.boites[cle_etat][cle_m] = 3

    def choisir_mouvement(self, cle_etat, mouvements_valides):
        self.initialiser_etat(cle_etat, mouvements_valides)

        poids_et_mouvements = []
        for mouvement in mouvements_valides:
            cle_m = f"{mouvement[0][0]},{mouvement[0][1]}-{mouvement[1][0]},{mouvement[1][1]}"
            poids = self.boites[cle_etat].get(cle_m, 3)
            if poids > 0:
                poids_et_mouvements.append((mouvement, poids))

        if not poids_et_mouvements:
            return random.choice(mouvements_valides)

        total = sum(p for _, p in poids_et_mouvements)
        r = random.uniform(0, total)
        cumul = 0
        for mouvement, poids in poids_et_mouvements:
            cumul += poids
            if r <= cumul:
                return mouvement
        return poids_et_mouvements[-1][0]

    def recompenser(self, historique_coups, resultat):
        for cle_etat, mouvement in historique_coups:
            cle_m = f"{mouvement[0][0]},{mouvement[0][1]}-{mouvement[1][0]},{mouvement[1][1]}"
            if cle_etat in self.boites and cle_m in self.boites[cle_etat]:
                if resultat == "victoire":
                    self.boites[cle_etat][cle_m] += 3
                elif resultat == "defaite":
                    self.boites[cle_etat][cle_m] = max(0, self.boites[cle_etat][cle_m] - 1)

        self.parties_jouees += 1
        if resultat == "victoire":
            self.victoires += 1
        elif resultat == "defaite":
            self.defaites += 1

        if self.parties_jouees > 0:
            taux = self.victoires / self.parties_jouees * 100
            self.historique_taux.append(taux)

    def obtenir_stats(self):
        if self.parties_jouees == 0:
            return "Aucune partie jouée"
        taux = self.victoires / self.parties_jouees * 100
        etats_connus = len(self.boites)
        return (f"Parties: {self.parties_jouees} | "
                f"V: {self.victoires} D: {self.defaites} | "
                f"Taux: {taux:.0f}% | "
                f"États appris: {etats_connus}")

    def obtenir_niveau(self):
        if self.parties_jouees < 5:
            return "Débutante", "#ff6b6b"
        elif self.parties_jouees < 15:
            taux = self.victoires / self.parties_jouees * 100
            if taux < 40:
                return "Apprentie", "#ffaa6b"
            else:
                return "Apprentie+", "#ffcc6b"
        elif self.parties_jouees < 30:
            taux = self.victoires / self.parties_jouees * 100
            if taux < 50:
                return "Intermédiaire", "#ffe76b"
            else:
                return "Intermédiaire+", "#d4ff6b"
        else:
            taux = self.victoires / self.parties_jouees * 100
            if taux >= 70:
                return "Experte", "#6bff6b"
            elif taux >= 50:
                return "Avancée", "#90ee90"
            else:
                return "En progression", "#ccff6b"

    def sauvegarder(self):
        donnees = {
            "boites": self.boites,
            "parties_jouees": self.parties_jouees,
            "victoires": self.victoires,
            "defaites": self.defaites,
            "historique_taux": self.historique_taux
        }
        try:
            with open(FICHIER_SAUVEGARDE, 'w') as f:
                json.dump(donnees, f)
        except Exception:
            pass

    def charger(self):
        try:
            if os.path.exists(FICHIER_SAUVEGARDE):
                with open(FICHIER_SAUVEGARDE, 'r') as f:
                    donnees = json.load(f)
                self.boites = donnees.get("boites", {})
                self.parties_jouees = donnees.get("parties_jouees", 0)
                self.victoires = donnees.get("victoires", 0)
                self.defaites = donnees.get("defaites", 0)
                self.historique_taux = donnees.get("historique_taux", [])
        except Exception:
            self.boites = {}
            self.parties_jouees = 0
            self.victoires = 0
            self.defaites = 0
            self.historique_taux = []

    def reinitialiser(self):
        self.boites = {}
        self.parties_jouees = 0
        self.victoires = 0
        self.defaites = 0
        self.historique_taux = []
        self.sauvegarder()


class Hexapawn:
    def __init__(self, racine, nom_joueur):
        self.racine = racine
        self.racine.title("Hexapawn - Melvine IA")
        self.racine.configure(bg="#2c2c2c")
        self.racine.resizable(False, False)

        self.nom_joueur = nom_joueur
        self.score_joueur = 0
        self.score_ia = 0

        self.taille_plateau = 3
        self.taille_canvas = 150
        self.plateau = [[0 for _ in range(self.taille_plateau)] for _ in range(self.taille_plateau)]
        self.tour = 1
        self.selectionne = None

        self.cerveau = CerveauIA()
        self.historique_coups_ia = []

        self.creer_interface()

        for col in range(self.taille_plateau):
            self.plateau[0][col] = 2
            self.plateau[2][col] = 1

        self.mettre_a_jour_plateau()
        self.mettre_a_jour_stats()

    def creer_interface(self):
        cadre_haut = tk.Frame(self.racine, bg="#2c2c2c")
        cadre_haut.grid(row=0, column=0, columnspan=3, pady=(10, 5))

        self.etiquette_score_joueur = tk.Label(
            cadre_haut,
            text=f"{self.nom_joueur}: {self.score_joueur}",
            font=("Helvetica", 14, "bold"),
            fg="white", bg="#2c2c2c"
        )
        self.etiquette_score_joueur.grid(row=0, column=0, padx=20)

        tk.Label(
            cadre_haut, text="VS",
            font=("Helvetica", 12, "bold"),
            fg="#ff6b6b", bg="#2c2c2c"
        ).grid(row=0, column=1, padx=10)

        self.etiquette_score_ia = tk.Label(
            cadre_haut,
            text=f"Melvine_IA: {self.score_ia}",
            font=("Helvetica", 14, "bold"),
            fg="white", bg="#2c2c2c"
        )
        self.etiquette_score_ia.grid(row=0, column=2, padx=20)

        cadre_ia_info = tk.Frame(self.racine, bg="#2c2c2c")
        cadre_ia_info.grid(row=1, column=0, columnspan=3, pady=2)

        self.etiquette_niveau = tk.Label(
            cadre_ia_info,
            text="Niveau: Débutante",
            font=("Helvetica", 11, "bold"),
            fg="#ff6b6b", bg="#2c2c2c"
        )
        self.etiquette_niveau.pack()

        self.etiquette_stats = tk.Label(
            cadre_ia_info,
            text="",
            font=("Helvetica", 9),
            fg="#aaaaaa", bg="#2c2c2c"
        )
        self.etiquette_stats.pack()

        self.etiquette_tour = tk.Label(
            self.racine,
            text=f"Tour de {self.nom_joueur}",
            font=("Helvetica", 12),
            fg="#90ee90", bg="#2c2c2c"
        )
        self.etiquette_tour.grid(row=2, column=0, columnspan=3, pady=5)

        cadre_plateau = tk.Frame(self.racine, bg="#2c2c2c")
        cadre_plateau.grid(row=3, column=0, columnspan=3, padx=20, pady=10)

        self.toiles = []
        for row in range(self.taille_plateau):
            ligne = []
            for col in range(self.taille_plateau):
                couleur_fond = "#d4a574" if (row + col) % 2 == 0 else "#8b6914"
                toile = tk.Canvas(
                    cadre_plateau,
                    width=self.taille_canvas,
                    height=self.taille_canvas,
                    bg=couleur_fond,
                    highlightthickness=2,
                    highlightbackground="#1a1a1a"
                )
                toile.grid(row=row, column=col, padx=1, pady=1)
                toile.bind("<Button-1>", lambda event, r=row, c=col: self.sur_clic(r, c))
                ligne.append(toile)
            self.toiles.append(ligne)

        cadre_boutons = tk.Frame(self.racine, bg="#2c2c2c")
        cadre_boutons.grid(row=4, column=0, columnspan=3, pady=10)

        tk.Button(
            cadre_boutons,
            text="Réinitialiser le cerveau",
            font=("Helvetica", 10),
            bg="#cc4444", fg="white",
            activebackground="#aa3333",
            relief="flat", padx=15, pady=3,
            command=self.reinitialiser_cerveau
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            cadre_boutons,
            text="Voir l'évolution",
            font=("Helvetica", 10),
            bg="#4488cc", fg="white",
            activebackground="#3377bb",
            relief="flat", padx=15, pady=3,
            command=self.afficher_evolution
        ).pack(side=tk.LEFT, padx=5)

        self.etiquette_dernier_resultat = tk.Label(
            self.racine,
            text="",
            font=("Helvetica", 10, "italic"),
            fg="#888888", bg="#2c2c2c"
        )
        self.etiquette_dernier_resultat.grid(row=5, column=0, columnspan=3, pady=(0, 10))

    def mettre_a_jour_stats(self):
        self.etiquette_stats.config(text=self.cerveau.obtenir_stats())
        niveau, couleur = self.cerveau.obtenir_niveau()
        self.etiquette_niveau.config(text=f"Melvine_IA — Niveau: {niveau}", fg=couleur)
        self.etiquette_score_joueur.config(text=f"{self.nom_joueur}: {self.score_joueur}")
        self.etiquette_score_ia.config(text=f"Melvine_IA: {self.score_ia}")

    def reinitialiser_cerveau(self):
        if messagebox.askyesno("Confirmation",
                               "Effacer toute la mémoire de Melvine_IA ?\n"
                               "Elle repartira de zéro et devra tout réapprendre."):
            self.cerveau.reinitialiser()
            self.score_joueur = 0
            self.score_ia = 0
            self.mettre_a_jour_stats()
            self.etiquette_dernier_resultat.config(
                text="Mémoire effacée. L'IA repart de zéro !",
                fg="#ff6b6b"
            )

    def afficher_evolution(self):
        if not self.cerveau.historique_taux:
            messagebox.showinfo("Évolution", "Pas encore de données.\nJouez quelques parties d'abord !")
            return

        fen = tk.Toplevel(self.racine)
        fen.title("Évolution de Melvine_IA")
        fen.configure(bg="#2c2c2c")
        fen.resizable(False, False)

        largeur = 500
        hauteur = 300
        marge_g = 50
        marge_d = 20
        marge_h = 30
        marge_b = 40

        canvas = tk.Canvas(fen, width=largeur, height=hauteur, bg="#1a1a1a",
                           highlightthickness=0)
        canvas.pack(padx=10, pady=10)

        canvas.create_text(
            largeur // 2, 15,
            text="Taux de victoire de l'IA au fil des parties",
            fill="white", font=("Helvetica", 11, "bold")
        )

        zone_l = largeur - marge_g - marge_d
        zone_h = hauteur - marge_h - marge_b

        for i in range(5):
            y = marge_h + i * zone_h / 4
            val = 100 - i * 25
            canvas.create_line(marge_g, y, largeur - marge_d, y, fill="#333333", dash=(2, 4))
            canvas.create_text(marge_g - 5, y, text=f"{val}%", fill="#888888",
                               font=("Helvetica", 8), anchor="e")

        canvas.create_line(marge_g, hauteur - marge_b, largeur - marge_d, hauteur - marge_b,
                           fill="#888888")
        canvas.create_text(largeur // 2, hauteur - 10, text="Nombre de parties",
                           fill="#888888", font=("Helvetica", 9))

        taux = self.cerveau.historique_taux
        n = len(taux)

        if n >= 2:
            pas_x = zone_l / (n - 1) if n > 1 else zone_l
            points = []
            for i, t in enumerate(taux):
                x = marge_g + i * pas_x
                y = marge_h + zone_h - (t / 100) * zone_h
                points.append((x, y))

            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                progres = i / max(len(points) - 1, 1)
                r = int(255 * (1 - progres))
                g = int(255 * progres)
                couleur = f"#{r:02x}{g:02x}6b"
                canvas.create_line(x1, y1, x2, y2, fill=couleur, width=2)

            for x, y in points:
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#ffffff", outline="")

            canvas.create_text(marge_g + 5, marge_h + zone_h + 15,
                               text="1", fill="#888888", font=("Helvetica", 8))
            canvas.create_text(largeur - marge_d, marge_h + zone_h + 15,
                               text=str(n), fill="#888888", font=("Helvetica", 8))

        cadre_stats = tk.Frame(fen, bg="#2c2c2c")
        cadre_stats.pack(pady=5)

        etats = len(self.cerveau.boites)
        total_poids = sum(
            sum(v for v in mouvements.values())
            for mouvements in self.cerveau.boites.values()
        )

        tk.Label(cadre_stats,
                 text=f"États mémorisés: {etats} | Poids total: {total_poids}",
                 font=("Helvetica", 10), fg="#aaaaaa", bg="#2c2c2c").pack()

        if self.cerveau.parties_jouees >= 5:
            recents = taux[-5:]
            moy = sum(recents) / len(recents)
            anciens = taux[:5] if len(taux) >= 10 else taux[:max(1, len(taux) // 2)]
            moy_ancien = sum(anciens) / len(anciens)
            diff = moy - moy_ancien

            if diff > 5:
                msg = f"L'IA s'améliore ! (+{diff:.0f}% sur les 5 dernières parties)"
                couleur_msg = "#6bff6b"
            elif diff < -5:
                msg = f"L'IA régresse ({diff:.0f}% sur les 5 dernières parties)"
                couleur_msg = "#ff6b6b"
            else:
                msg = "L'IA se stabilise"
                couleur_msg = "#ffcc6b"

            tk.Label(cadre_stats, text=msg,
                     font=("Helvetica", 10, "bold"),
                     fg=couleur_msg, bg="#2c2c2c").pack(pady=5)

    def dessiner_pion(self, toile, couleur):
        toile.delete("all")
        if couleur:
            marge = 25
            x1, y1 = marge, marge
            x2, y2 = self.taille_canvas - marge, self.taille_canvas - marge

            if couleur == "white":
                toile.create_oval(x1, y1, x2, y2, fill="#f0f0f0", outline="#333333", width=3)
                toile.create_oval(x1 + 15, y1 + 15, x2 - 15, y2 - 15,
                                  fill="#ffffff", outline="#aaaaaa", width=1)
            else:
                toile.create_oval(x1, y1, x2, y2, fill="#1a1a1a", outline="#555555", width=3)
                toile.create_oval(x1 + 15, y1 + 15, x2 - 15, y2 - 15,
                                  fill="#333333", outline="#555555", width=1)

    def obtenir_mouvements_valides(self, plateau, joueur):
        mouvements = []
        direction = 1 if joueur == 2 else -1
        adversaire = 3 - joueur

        for row in range(self.taille_plateau):
            for col in range(self.taille_plateau):
                if plateau[row][col] == joueur:
                    nr = row + direction
                    if 0 <= nr < self.taille_plateau:
                        if plateau[nr][col] == 0:
                            mouvements.append(((row, col), (nr, col)))
                        if col - 1 >= 0 and plateau[nr][col - 1] == adversaire:
                            mouvements.append(((row, col), (nr, col - 1)))
                        if col + 1 < self.taille_plateau and plateau[nr][col + 1] == adversaire:
                            mouvements.append(((row, col), (nr, col + 1)))
        return mouvements

    def est_mouvement_valide(self, de_pos, vers_pos):
        de_row, de_col = de_pos
        vers_row, vers_col = vers_pos
        direction = 1 if self.tour == 2 else -1

        if de_col == vers_col and de_row + direction == vers_row and self.plateau[vers_row][vers_col] == 0:
            return True
        if (de_row + direction == vers_row and abs(de_col - vers_col) == 1
                and self.plateau[vers_row][vers_col] != 0
                and self.plateau[vers_row][vers_col] != self.tour):
            return True
        return False

    def sur_clic(self, row, col):
        if self.tour != 1:
            return

        if self.selectionne:
            if self.selectionne == (row, col):
                self.selectionne = None
            elif self.est_mouvement_valide(self.selectionne, (row, col)):
                self.deplacer_pion(self.selectionne, (row, col))
                self.selectionne = None
                if self.verifier_fin_jeu():
                    return
                self.changer_tour()
                if self.tour == 2:
                    self.racine.after(400, self.mouvement_ia)
            else:
                if self.plateau[row][col] == self.tour:
                    self.selectionne = (row, col)
                else:
                    self.selectionne = None
        elif self.plateau[row][col] == self.tour:
            self.selectionne = (row, col)

        self.mettre_a_jour_plateau()

    def deplacer_pion(self, de_pos, vers_pos):
        de_row, de_col = de_pos
        vers_row, vers_col = vers_pos
        self.plateau[vers_row][vers_col] = self.plateau[de_row][de_col]
        self.plateau[de_row][de_col] = 0
        self.mettre_a_jour_plateau()

    def changer_tour(self):
        self.tour = 2 if self.tour == 1 else 1
        if self.tour == 1:
            self.etiquette_tour.config(text=f"Tour de {self.nom_joueur}", fg="#90ee90")
        else:
            self.etiquette_tour.config(text="Melvine_IA réfléchit...", fg="#ff6b6b")
        self.mettre_a_jour_plateau()

    def verifier_fin_jeu(self):
        message = ""
        resultat_ia = None

        if any(self.plateau[0][col] == 1 for col in range(self.taille_plateau)):
            message = f"{self.nom_joueur} gagne en atteignant le côté opposé !"
            self.score_joueur += 1
            resultat_ia = "defaite"

        elif any(self.plateau[2][col] == 2 for col in range(self.taille_plateau)):
            message = "Melvine_IA gagne en atteignant le côté opposé !"
            self.score_ia += 1
            resultat_ia = "victoire"

        elif not any(1 in row for row in self.plateau):
            message = "Melvine_IA gagne ! Tous les pions du joueur sont capturés !"
            self.score_ia += 1
            resultat_ia = "victoire"

        elif not any(2 in row for row in self.plateau):
            message = f"{self.nom_joueur} gagne ! Tous les pions de l'IA sont capturés !"
            self.score_joueur += 1
            resultat_ia = "defaite"

        elif len(self.obtenir_mouvements_valides(self.plateau, self.tour)) == 0:
            if self.tour == 1:
                message = f"{self.nom_joueur} est bloqué ! Melvine_IA gagne !"
                self.score_ia += 1
                resultat_ia = "victoire"
            else:
                message = f"Melvine_IA est bloquée ! {self.nom_joueur} gagne !"
                self.score_joueur += 1
                resultat_ia = "defaite"

        if message:
            self.cerveau.recompenser(self.historique_coups_ia, resultat_ia)
            self.cerveau.sauvegarder()

            self.mettre_a_jour_stats()
            self.mettre_a_jour_plateau()

            if resultat_ia == "defaite":
                self.etiquette_dernier_resultat.config(
                    text="L'IA a appris de cette défaite. Elle évitera ces erreurs.",
                    fg="#ffaa6b"
                )
            elif resultat_ia == "victoire":
                self.etiquette_dernier_resultat.config(
                    text="L'IA renforce sa stratégie gagnante !",
                    fg="#6bff6b"
                )

            messagebox.showinfo("Fin de la partie", message)
            self.reinitialiser_jeu()
            return True
        return False

    def mouvement_ia(self):
        if self.tour != 2:
            return

        mouvements = self.obtenir_mouvements_valides(self.plateau, 2)

        if not mouvements:
            if not self.verifier_fin_jeu():
                self.changer_tour()
            return

        cle_etat = self.cerveau.obtenir_cle(self.plateau)
        mouvement = self.cerveau.choisir_mouvement(cle_etat, mouvements)

        self.historique_coups_ia.append((cle_etat, mouvement))

        self.deplacer_pion(mouvement[0], mouvement[1])

        if not self.verifier_fin_jeu():
            self.changer_tour()

    def reinitialiser_jeu(self):
        self.plateau = [[0 for _ in range(self.taille_plateau)] for _ in range(self.taille_plateau)]
        for col in range(self.taille_plateau):
            self.plateau[0][col] = 2
            self.plateau[2][col] = 1
        self.tour = 1
        self.selectionne = None
        self.historique_coups_ia = []
        self.etiquette_tour.config(text=f"Tour de {self.nom_joueur}", fg="#90ee90")
        self.mettre_a_jour_plateau()

    def mettre_a_jour_plateau(self):
        for row in range(self.taille_plateau):
            for col in range(self.taille_plateau):
                couleur_fond = "#d4a574" if (row + col) % 2 == 0 else "#8b6914"
                couleur_pion = ''
                if self.plateau[row][col] == 1:
                    couleur_pion = 'white'
                elif self.plateau[row][col] == 2:
                    couleur_pion = 'black'

                if self.selectionne == (row, col):
                    couleur_fond = "#5cb85c"
                elif self.selectionne:
                    if self.est_mouvement_valide(self.selectionne, (row, col)):
                        if self.plateau[row][col] == 0:
                            couleur_fond = "#a8d8a8"
                        elif self.plateau[row][col] != self.tour:
                            couleur_fond = "#ff9999"

                self.toiles[row][col].config(bg=couleur_fond)
                self.dessiner_pion(self.toiles[row][col], couleur_pion)


def demander_nom_joueur():
    fenetre_nom = tk.Tk()
    fenetre_nom.title("Hexapawn - Melvine IA")
    fenetre_nom.configure(bg="#2c2c2c")
    fenetre_nom.resizable(False, False)

    cadre = tk.Frame(fenetre_nom, bg="#2c2c2c", padx=40, pady=30)
    cadre.pack()

    tk.Label(
        cadre, text="HEXAPAWN",
        font=("Helvetica", 24, "bold"),
        fg="#ff6b6b", bg="#2c2c2c"
    ).pack(pady=(0, 5))

    tk.Label(
        cadre, text="Melvine IA — Apprentissage par renforcement",
        font=("Helvetica", 11),
        fg="#aaaaaa", bg="#2c2c2c"
    ).pack(pady=(0, 5))

    tk.Label(
        cadre,
        text="L'IA commence nulle et apprend de chaque partie.\n"
             "Plus vous jouez, plus elle devient forte !",
        font=("Helvetica", 9, "italic"),
        fg="#888888", bg="#2c2c2c", justify="center"
    ).pack(pady=(0, 20))

    tk.Label(
        cadre, text="Entrez votre nom :",
        font=("Helvetica", 12),
        fg="white", bg="#2c2c2c"
    ).pack(pady=(0, 10))

    entree_nom = tk.Entry(
        cadre,
        font=("Helvetica", 14),
        justify="center",
        bg="#3c3c3c", fg="white",
        insertbackground="white",
        relief="flat",
        highlightthickness=2,
        highlightcolor="#ff6b6b",
        highlightbackground="#555555"
    )
    entree_nom.pack(pady=(0, 20), ipady=5)
    entree_nom.focus_set()

    def demarrer_jeu(event=None):
        nom = entree_nom.get().strip()
        if not nom:
            nom = "Joueur"
        fenetre_nom.destroy()
        jeu_principal(nom)

    entree_nom.bind("<Return>", demarrer_jeu)

    tk.Button(
        cadre, text="Jouer",
        font=("Helvetica", 14, "bold"),
        bg="#ff6b6b", fg="white",
        activebackground="#ff4444",
        activeforeground="white",
        relief="flat", padx=30, pady=5,
        command=demarrer_jeu
    ).pack()

    fenetre_nom.mainloop()


def jeu_principal(nom_joueur):
    racine = tk.Tk()
    Hexapawn(racine, nom_joueur)
    racine.mainloop()


demander_nom_joueur()

import json
import os
import random
from datetime import datetime

from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "quiz-binaire-bts-ms23-secret"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dec_to_bcd(n):
    """Convertit un entier décimal en chaîne BCD (sans espaces)."""
    return "".join(f"{int(d):04b}" for d in str(n))


def format_bin(val):
    """Formate en binaire 8 bits avec espace : '1011 0010'."""
    b = f"{val:08b}"
    return f"{b[:4]} {b[4:]}"


def format_bcd(val):
    """Formate en BCD avec espaces entre nibbles : '0101 0110'."""
    return " ".join(f"{int(d):04b}" for d in str(val))


def formater_donnee(val, col):
    """Formate une valeur donnée pour affichage dans le tableau exercice 2."""
    if col == "dec":
        return str(val)
    if col == "hex":
        return f"{val:02X}"
    if col == "bin":
        return format_bin(val)
    if col == "bcd":
        return format_bcd(val)


# ---------------------------------------------------------------------------
# Génération aléatoire des énoncés
# ---------------------------------------------------------------------------

def generer_exercice2():
    """Génère 8 lignes aléatoires pour l'exercice 2."""
    structure = [
        (1, "hex"), (2, "bin"), (3, "bcd"), (4, "bin"),
        (5, "dec"), (6, "hex"), (7, "bcd"), (8, "dec"),
    ]
    data = []
    for num, given_col in structure:
        if given_col == "bcd":
            val = random.randint(10, 99)
        else:
            val = random.randint(33, 254)
        data.append([num, given_col, val])
    return data


def generer_exercice3():
    """Génère 2 opérandes 8 bits aléatoires pour l'exercice 3."""
    return {"a": random.randint(1, 254), "b": random.randint(1, 254)}


# ---------------------------------------------------------------------------
# Correction automatique
# ---------------------------------------------------------------------------

def construire_corrections(ex2_data, ex3_operands):
    """Construit le dictionnaire de corrections pour un étudiant donné."""
    c = {}

    # --- Exercice 1 : identique pour tous ---
    for i in range(16):
        c[f"ex1_bin_{i}"] = ("bin", i)
        c[f"ex1_hex_{i}"] = ("hex", i)
        if i < 10:
            c[f"ex1_bcd_{i}"] = ("bcd", dec_to_bcd(i))

    # --- Exercice 2 : valeurs aléatoires ---
    for row, given_col, dec_val in ex2_data:
        if given_col != "dec":
            c[f"ex2_dec_{row}"] = ("dec", dec_val)
        if given_col != "bin":
            c[f"ex2_bin_{row}"] = ("bin", dec_val)
        if given_col != "hex":
            c[f"ex2_hex_{row}"] = ("hex", dec_val)
        if given_col != "bcd":
            c[f"ex2_bcd_{row}"] = ("bcd", dec_to_bcd(dec_val))

    # --- Exercice 3 : tables de vérité et Karnaugh (identiques pour tous) ---
    tt = {
        "not": {"0": "1", "1": "0"},
        "and":  {"00": "0", "01": "0", "10": "0", "11": "1"},
        "or":   {"00": "0", "01": "1", "10": "1", "11": "1"},
        "xor":  {"00": "0", "01": "1", "10": "1", "11": "0"},
        "nand": {"00": "1", "01": "1", "10": "1", "11": "0"},
        "nor":  {"00": "1", "01": "0", "10": "0", "11": "0"},
    }
    for op, table in tt.items():
        for inputs, output in table.items():
            c[f"ex3_tt_{op}_{inputs}"] = ("bit", output)
    for op in ("and", "or", "xor", "nand", "nor"):
        for inputs, output in tt[op].items():
            c[f"ex3_kn_{op}_{inputs}"] = ("bit", output)

    # --- Exercice 3 : opérations bit à bit (aléatoires) ---
    a = ex3_operands["a"]
    b = ex3_operands["b"]
    c["ex3_bw_not"]  = ("bw", f"{(~b & 0xFF):08b}")
    c["ex3_bw_and"]  = ("bw", f"{(a & b):08b}")
    c["ex3_bw_or"]   = ("bw", f"{(a | b):08b}")
    c["ex3_bw_xor"]  = ("bw", f"{(a ^ b):08b}")
    c["ex3_bw_nand"] = ("bw", f"{(~(a & b) & 0xFF):08b}")
    c["ex3_bw_nor"]  = ("bw", f"{(~(a | b) & 0xFF):08b}")

    return c


RESULTATS_JSON = os.path.join(os.path.dirname(__file__), "resultats.json")


def charger_resultats():
    """Charge les résultats existants depuis le fichier JSON."""
    if os.path.exists(RESULTATS_JSON):
        with open(RESULTATS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def generer_code():
    """Génère un code unique de 6 chiffres."""
    existants = {r["code"] for r in charger_resultats()}
    while True:
        code = f"{random.randint(0, 999999):06d}"
        if code not in existants:
            return code


NOMS_COLONNES = {"dec": "décimal", "bin": "binaire", "hex": "hexadécimal", "bcd": "BCD"}


def structurer_resultat(enonce, reponses, scores, total_c, total_q):
    """Restructure les données brutes en format JSON lisible."""

    # --- Exercice 1 ---
    ex1 = {}
    for i in range(16):
        ex1[str(i)] = {
            "binaire": reponses.get(f"ex1_bin_{i}", ""),
            "hexadécimal": reponses.get(f"ex1_hex_{i}", ""),
            "BCD": reponses.get(f"ex1_bcd_{i}", ""),
        }

    # --- Exercice 2 ---
    ex2_enonce = []
    ex2_rep = {}
    for row, col, val in enonce["ex2_data"]:
        ex2_enonce.append({
            "ligne": row,
            "colonne_donnée": NOMS_COLONNES[col],
            "valeur_décimale": val,
            "valeur_affichée": formater_donnee(val, col),
        })
        ligne = {}
        for c in ("dec", "bin", "hex", "bcd"):
            if c != col:
                ligne[NOMS_COLONNES[c]] = reponses.get(f"ex2_{c}_{row}", "")
        ex2_rep[str(row)] = ligne

    # --- Exercice 3 ---
    op = enonce["ex3_operands"]

    ex3_tt = {}
    for nom_op in ("not", "and", "or", "xor", "nand", "nor"):
        if nom_op == "not":
            ex3_tt[nom_op.upper()] = {
                "0": reponses.get("ex3_tt_not_0", ""),
                "1": reponses.get("ex3_tt_not_1", ""),
            }
        else:
            ex3_tt[nom_op.upper()] = {
                f"{a}{b}": reponses.get(f"ex3_tt_{nom_op}_{a}{b}", "")
                for a in "01" for b in "01"
            }

    ex3_kn = {}
    for nom_op in ("and", "or", "xor", "nand", "nor"):
        ex3_kn[nom_op.upper()] = {
            f"{a}{b}": reponses.get(f"ex3_kn_{nom_op}_{a}{b}", "")
            for a in "01" for b in "01"
        }

    ex3_bw = {}
    for nom_op in ("not", "and", "or", "xor", "nand", "nor"):
        ex3_bw[nom_op.upper()] = reponses.get(f"ex3_bw_{nom_op}", "")

    return {
        "exercice1": {
            "score": {"correct": scores[1][0], "total": scores[1][1]},
            "réponses": ex1,
        },
        "exercice2": {
            "score": {"correct": scores[2][0], "total": scores[2][1]},
            "énoncé": ex2_enonce,
            "réponses": ex2_rep,
        },
        "exercice3": {
            "score": {"correct": scores[3][0], "total": scores[3][1]},
            "énoncé": {
                "opérande_a": format_bin(op["a"]),
                "opérande_b": format_bin(op["b"]),
            },
            "réponses": {
                "tables_vérité": ex3_tt,
                "karnaugh": ex3_kn,
                "bit_à_bit": ex3_bw,
            },
        },
        "score_total": {"correct": total_c, "total": total_q},
    }


def sauvegarder_resultat(nom, prenom, enonce, reponses, scores, total_c, total_q):
    """Sauvegarde une soumission dans le fichier JSON. Retourne le code généré."""
    resultats = charger_resultats()
    code = generer_code()
    entree = {
        "code": code,
        "nom": nom,
        "prenom": prenom,
        "date": datetime.now().isoformat(timespec="seconds"),
    }
    entree.update(structurer_resultat(enonce, reponses, scores, total_c, total_q))
    resultats.append(entree)
    with open(RESULTATS_JSON, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    return code


def normaliser(valeur, type_champ):
    """Normalise une réponse pour comparaison. Retourne None si invalide/vide."""
    s = valeur.strip().replace(" ", "")
    if not s:
        return None
    try:
        if type_champ == "dec":
            return int(s)
        elif type_champ == "hex":
            return int(s, 16)
        elif type_champ == "bin":
            return int(s, 2)
        elif type_champ in ("bcd", "bw", "bit"):
            return s
    except ValueError:
        return None
    return None


def corriger(reponses, ex2_data, ex3_operands):
    """Corrige les réponses d'un étudiant."""
    corrections = construire_corrections(ex2_data, ex3_operands)
    scores = {1: [0, 0], 2: [0, 0], 3: [0, 0]}

    for champ, (type_champ, valeur_correcte) in corrections.items():
        exo = int(champ[2])

        scores[exo][1] += 1  # total

        reponse = reponses.get(champ, "")
        norm = normaliser(reponse, type_champ)
        if norm is not None and norm == valeur_correcte:
            scores[exo][0] += 1  # correct

    total_c = sum(s[0] for s in scores.values())
    total_q = sum(s[1] for s in scores.values())
    return scores, total_c, total_q


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def accueil():
    return render_template("accueil.html")


@app.route("/start", methods=["POST"])
def start():
    session.clear()
    session["nom"] = request.form.get("nom", "").strip()
    session["prenom"] = request.form.get("prenom", "").strip()
    session["ex2_data"] = generer_exercice2()
    session["ex3_operands"] = generer_exercice3()
    return redirect(url_for("exercice", n=1))


@app.route("/exercice/<int:n>", methods=["GET", "POST"])
def exercice(n):
    if n not in (1, 2, 3):
        return redirect(url_for("accueil"))

    if "nom" not in session:
        return redirect(url_for("accueil"))

    if request.method == "POST":
        # Sauvegarder les réponses en session
        reponses = session.get("reponses", {})
        for key, value in request.form.items():
            if key != "direction":
                reponses[key] = value
        session["reponses"] = reponses

        if request.form.get("direction") == "prev" and n > 1:
            return redirect(url_for("exercice", n=n - 1))
        elif n < 3:
            return redirect(url_for("exercice", n=n + 1))
        else:
            return redirect(url_for("confirmation"))

    reponses = session.get("reponses", {})
    kwargs = {"n": n, "reponses": reponses}

    if n == 2:
        ex2_data = session.get("ex2_data", [])
        kwargs["lignes"] = [
            (row, col, formater_donnee(val, col)) for row, col, val in ex2_data
        ]
    elif n == 3:
        op = session.get("ex3_operands", {})
        kwargs["ex3_a"] = format_bin(op.get("a", 0))
        kwargs["ex3_b"] = format_bin(op.get("b", 0))

    return render_template(f"exercice{n}.html", **kwargs)


@app.route("/confirmation")
def confirmation():
    if "nom" not in session:
        return redirect(url_for("accueil"))

    # Éviter les double soumissions : si déjà un code, le réafficher
    if "code" in session:
        return render_template("confirmation.html", code=session["code"])

    reponses = session.get("reponses", {})
    ex2_data = session.get("ex2_data", [])
    ex3_operands = session.get("ex3_operands", {})

    scores, total_c, total_q = corriger(reponses, ex2_data, ex3_operands)

    enonce = {"ex2_data": ex2_data, "ex3_operands": ex3_operands}
    code = sauvegarder_resultat(
        session["nom"], session["prenom"], enonce, reponses, scores, total_c, total_q
    )
    session["code"] = code

    return render_template("confirmation.html", code=code)


@app.route("/resultats")
def resultats():
    tous = charger_resultats()
    return render_template("resultats.html", resultats=tous)


if __name__ == "__main__":
    app.run(debug=True)

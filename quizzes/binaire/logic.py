import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from db import get_db, generer_code


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


def sauvegarder_resultat(nom, prenom, enonce, reponses, scores, total_c, total_q):
    """Sauvegarde une soumission dans la base SQLite. Retourne le code généré."""
    conn = get_db()
    code = generer_code(conn, "binaire")
    entree = {
        "code": code,
        "nom": nom,
        "prenom": prenom,
        "date": datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    entree.update(structurer_resultat(enonce, reponses, scores, total_c, total_q))
    conn.execute(
        "INSERT INTO resultats (quiz_id, code, nom, prenom, date, score_total_correct, score_total_total, donnees) VALUES (?,?,?,?,?,?,?,?)",
        ("binaire", code, nom, prenom, entree["date"], total_c, total_q, json.dumps(entree, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return code


def charger_resultats():
    """Charge tous les résultats du quiz binaire."""
    conn = get_db()
    rows = conn.execute(
        "SELECT donnees FROM resultats WHERE quiz_id='binaire' ORDER BY date"
    ).fetchall()
    conn.close()
    return [json.loads(row["donnees"]) for row in rows]

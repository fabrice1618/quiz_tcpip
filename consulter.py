#!/usr/bin/env python3
"""Consulter les réponses d'un étudiant à partir de son code de soumission."""

import argparse
import json
import os
import re
import sqlite3
import sys


# ── Couleurs ANSI ──────────────────────────────────────────────────────────

VERT = "\033[32m"
ROUGE = "\033[31m"
GRAS = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def marque(correct):
    return f"{VERT}✓{RESET}" if correct else f"{ROUGE}✗{RESET}"


def visible_len(s):
    """Longueur visible d'une chaîne (sans codes ANSI)."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def pad(s, width):
    """Complète à droite pour atteindre width caractères visibles."""
    return s + " " * max(0, width - visible_len(s))


def rpad(s, width):
    """Complète à gauche pour atteindre width caractères visibles."""
    return " " * max(0, width - visible_len(s)) + s


def vide(val):
    """Retourne la valeur ou '·' si vide."""
    if not val:
        return f"{DIM}·{RESET}"
    return str(val)


# ── Helpers de conversion (quiz_binaire/app.py) ───────────────────────────

def dec_to_bcd(n):
    return "".join(f"{int(d):04b}" for d in str(n))


def format_bin(val):
    b = f"{val:08b}"
    return f"{b[:4]} {b[4:]}"


def format_bcd(val):
    return " ".join(f"{int(d):04b}" for d in str(val))


# ── Helpers réseau (quiz_reseau/app.py) ───────────────────────────────────

MACHINES = [
    {"id": "ordi1",  "nom": "Ordinateur 1",  "ip": "10.1.201.37",   "masque": "255.255.224.0"},
    {"id": "ordi2",  "nom": "Ordinateur 2",  "ip": "192.168.11.3",  "masque": "255.255.0.0"},
    {"id": "ordi3",  "nom": "Ordinateur 3",  "ip": "10.1.188.37",   "masque": "255.255.224.0"},
    {"id": "rect1",  "nom": "Rectifieuse 1", "ip": "192.168.35.4",  "masque": "255.255.0.0"},
    {"id": "frais1", "nom": "Fraiseuse 1",   "ip": "10.1.214.1",    "masque": "255.255.224.0"},
]

EX2_DEVICES = [
    {"id": "routeur_lan", "nom": "Routeur interface LAN", "subnet": 1},
    {"id": "routeur_wan", "nom": "Routeur interface WAN", "subnet": 2, "given": True},
    {"id": "ex2_ordi1",   "nom": "Ordinateur 1",         "subnet": 1, "given": True},
    {"id": "ex2_ordi2",   "nom": "Ordinateur 2",         "subnet": 1},
    {"id": "ex2_ordi3",   "nom": "Ordinateur 3",         "subnet": 2},
    {"id": "ex2_ordi4",   "nom": "Ordinateur 4",         "subnet": 2},
]

SUBNET_RANGES = {1: (2, 126), 2: (129, 253)}
SUBNET_EXCLUSIONS = {1: {"192.168.0.1"}, 2: {"192.168.0.254"}}


def calculer_adresse_reseau(ip_str, masque_str):
    ip = [int(x) for x in ip_str.split(".")]
    masque = [int(x) for x in masque_str.split(".")]
    return ".".join(str(ip[i] & masque[i]) for i in range(4))


def calculer_communications():
    reseaux = {}
    for m in MACHINES:
        adr = calculer_adresse_reseau(m["ip"], m["masque"])
        cle = (adr, m["masque"])
        reseaux.setdefault(cle, []).append(m["id"])
    comm = {m["id"]: set() for m in MACHINES}
    for membres in reseaux.values():
        for i, mid in enumerate(membres):
            for j, other in enumerate(membres):
                if i != j:
                    comm[mid].add(other)
    return comm


def normaliser_ip(s):
    parts = s.strip().split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return None
    if all(0 <= o <= 255 for o in octets):
        return ".".join(str(o) for o in octets)
    return None


def parse_ip(s):
    parts = s.strip().split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return None
    if all(0 <= o <= 255 for o in octets):
        return octets
    return None


# ── Normalisation pour comparaison ────────────────────────────────────────

def norm_bin(s):
    s = s.strip().replace(" ", "")
    if not s:
        return None
    try:
        return int(s, 2)
    except ValueError:
        return None


def norm_hex(s):
    s = s.strip().replace(" ", "")
    if not s:
        return None
    try:
        return int(s, 16)
    except ValueError:
        return None


def norm_dec(s):
    s = s.strip().replace(" ", "")
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def norm_bcd(s):
    s = s.strip().replace(" ", "")
    return s if s else None


# ── Chargement ────────────────────────────────────────────────────────────

def charger_soumission(quiz, code):
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, f"quiz_{quiz}", "resultats.db")
    if not os.path.exists(db_path):
        print(f"Base introuvable : {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT donnees FROM resultats WHERE code=?", (code,)).fetchone()
    conn.close()
    if row:
        return json.loads(row["donnees"])
    return None


# ── Affichage commun ──────────────────────────────────────────────────────

def titre(texte):
    w = max(visible_len(texte) + 4, 60)
    print(f"\n{'─' * w}")
    print(f"  {GRAS}{texte}{RESET}")
    print(f"{'─' * w}")


def entete(r):
    print()
    print(f"{'═' * 60}")
    print(f"  Nom : {GRAS}{r['nom']}{RESET}    Prénom : {GRAS}{r['prenom']}{RESET}")
    print(f"  Date : {r['date']}    Code : {GRAS}{r['code']}{RESET}")
    sc = r["score_total"]
    print(f"  Score total : {GRAS}{sc['correct']}/{sc['total']}{RESET}")
    print(f"{'═' * 60}")


# ── Quiz Binaire ──────────────────────────────────────────────────────────

def afficher_binaire(r):
    entete(r)
    afficher_binaire_ex1(r)
    afficher_binaire_ex2(r)
    afficher_binaire_ex3(r)


def afficher_binaire_ex1(r):
    ex = r["exercice1"]
    sc = ex["score"]
    titre(f"Exercice 1 : Conversions 0–15  ({sc['correct']}/{sc['total']})")

    rep = ex["réponses"]
    W_ATT, W_REP = 7, 9

    print()
    h = f"  {'Déc':>3}  "
    h += f"  {pad('Attendu', W_ATT)} {pad('Réponse', W_REP)}  "
    h += f"  {pad('Att.', 3)} {pad('Rép.', W_REP-4)}  "
    h += f"  {pad('Attendu', W_ATT)} {pad('Réponse', W_REP)}  "
    print(h)
    s = f"  {'':>3}  "
    s += f"  {'── Binaire ──':^{W_ATT + W_REP + 1}}  "
    s += f"  {'── Hex ──':^{3 + W_REP - 4 + 1}}  "
    s += f"  {'──── BCD ────':^{W_ATT + W_REP + 1}}  "
    print(s)
    print(f"  {'─'*3}  {'─'*(W_ATT + W_REP + 3)}  {'─'*(3 + W_REP - 4 + 3)}  {'─'*(W_ATT + W_REP + 3)}")

    for i in range(16):
        si = str(i)
        r_bin = rep[si]["binaire"]
        r_hex = rep[si]["hexadécimal"]
        r_bcd = rep[si].get("BCD", "")

        att_bin = f"{i:04b}"
        att_hex = f"{i:X}"

        ok_bin = norm_bin(r_bin) == i if norm_bin(r_bin) is not None else False
        ok_hex = norm_hex(r_hex) == i if norm_hex(r_hex) is not None else False

        line = f"  {i:>3}  "
        line += f"  {pad(att_bin, W_ATT)} {pad(vide(r_bin), W_REP)} {marque(ok_bin)}"
        line += f"  {pad(att_hex, 3)} {pad(vide(r_hex), W_REP-4)} {marque(ok_hex)}"

        if i <= 9:
            att_bcd = dec_to_bcd(i)
            ok_bcd = norm_bcd(r_bcd) == att_bcd if norm_bcd(r_bcd) is not None else False
            line += f"  {pad(att_bcd, W_ATT)} {pad(vide(r_bcd), W_REP)} {marque(ok_bcd)}"

        print(line)


def afficher_binaire_ex2(r):
    ex = r["exercice2"]
    sc = ex["score"]
    titre(f"Exercice 2 : Conversions aléatoires  ({sc['correct']}/{sc['total']})")

    enonce = ex["énoncé"]
    rep = ex["réponses"]

    NOM_COL = {"décimal": "dec", "binaire": "bin", "hexadécimal": "hex", "BCD": "bcd"}

    for item in enonce:
        ligne = item["ligne"]
        col_donnee = item["colonne_donnée"]
        val_dec = item["valeur_décimale"]
        val_aff = item["valeur_affichée"]

        print(f"\n  Ligne {ligne}  │  {col_donnee} donné : {GRAS}{val_aff}{RESET}  (décimal = {val_dec})")

        ligne_rep = rep.get(str(ligne), {})

        for col_nom, col_code in NOM_COL.items():
            if col_nom == col_donnee:
                continue
            if col_nom not in ligne_rep:
                continue

            student = ligne_rep[col_nom]

            if col_code == "dec":
                attendu = str(val_dec)
                ok = norm_dec(student) == val_dec if norm_dec(student) is not None else False
            elif col_code == "bin":
                attendu = format_bin(val_dec)
                ok = norm_bin(student) == val_dec if norm_bin(student) is not None else False
            elif col_code == "hex":
                attendu = f"{val_dec:02X}"
                ok = norm_hex(student) == val_dec if norm_hex(student) is not None else False
            elif col_code == "bcd":
                attendu = format_bcd(val_dec)
                ok = norm_bcd(student) == dec_to_bcd(val_dec) if norm_bcd(student) is not None else False

            print(f"    {pad(col_nom, 13)} : {pad(vide(student), 12)}  attendu : {pad(attendu, 12)} {marque(ok)}")


def afficher_binaire_ex3(r):
    ex = r["exercice3"]
    sc = ex["score"]
    titre(f"Exercice 3 : Logique  ({sc['correct']}/{sc['total']})")

    rep = ex["réponses"]
    eno = ex["énoncé"]

    a = int(eno["opérande_a"].replace(" ", ""), 2)
    b = int(eno["opérande_b"].replace(" ", ""), 2)

    print(f"\n  Opérandes : A = {eno['opérande_a']} ({a})   B = {eno['opérande_b']} ({b})")

    # Tables de vérité attendues
    tt = {
        "NOT":  {"0": "1", "1": "0"},
        "AND":  {"00": "0", "01": "0", "10": "0", "11": "1"},
        "OR":   {"00": "0", "01": "1", "10": "1", "11": "1"},
        "XOR":  {"00": "0", "01": "1", "10": "1", "11": "0"},
        "NAND": {"00": "1", "01": "1", "10": "1", "11": "0"},
        "NOR":  {"00": "1", "01": "0", "10": "0", "11": "0"},
    }

    # Tables de vérité
    print(f"\n  {GRAS}Tables de vérité{RESET}")
    tt_rep = rep["tables_vérité"]
    for op, table in tt.items():
        errs = []
        for inputs, expected in table.items():
            student = tt_rep.get(op, {}).get(inputs, "")
            if student.strip() != expected:
                errs.append(f"{inputs}→{student.strip() or '·'}(att:{expected})")
        n = len(table)
        c = n - len(errs)
        if errs:
            print(f"    {op:<5} {c}/{n} {marque(False)}  {', '.join(errs)}")
        else:
            print(f"    {op:<5} {c}/{n} {marque(True)}")

    # Karnaugh
    print(f"\n  {GRAS}Tableaux de Karnaugh{RESET}")
    kn_rep = rep["karnaugh"]
    for op in ("AND", "OR", "XOR", "NAND", "NOR"):
        table = tt[op]
        errs = []
        for inputs, expected in table.items():
            student = kn_rep.get(op, {}).get(inputs, "")
            if student.strip() != expected:
                errs.append(f"{inputs}→{student.strip() or '·'}(att:{expected})")
        n = len(table)
        c = n - len(errs)
        if errs:
            print(f"    {op:<5} {c}/{n} {marque(False)}  {', '.join(errs)}")
        else:
            print(f"    {op:<5} {c}/{n} {marque(True)}")

    # Bit à bit
    print(f"\n  {GRAS}Opérations bit à bit{RESET}")
    bw_rep = rep["bit_à_bit"]
    bw_expected = {
        "NOT":  f"{(~b & 0xFF):08b}",
        "AND":  f"{(a & b):08b}",
        "OR":   f"{(a | b):08b}",
        "XOR":  f"{(a ^ b):08b}",
        "NAND": f"{(~(a & b) & 0xFF):08b}",
        "NOR":  f"{(~(a | b) & 0xFF):08b}",
    }
    for op, expected in bw_expected.items():
        student = bw_rep.get(op, "")
        student_norm = student.strip().replace(" ", "")
        ok = student_norm == expected
        label = "NOT B" if op == "NOT" else f"A {op} B"
        exp_fmt = f"{expected[:4]} {expected[4:]}"
        print(f"    {pad(label, 10)} : {pad(vide(student), 12)}  attendu : {exp_fmt}  {marque(ok)}")


# ── Quiz Réseau ───────────────────────────────────────────────────────────

def afficher_reseau(r):
    entete(r)
    afficher_reseau_ex1(r)
    afficher_reseau_ex2(r)


def afficher_reseau_ex1(r):
    ex = r["exercice1"]
    s_adr = ex["score_adresses"]
    s_comm = ex["score_communication"]
    total_c = s_adr["correct"] + s_comm["correct"]
    total_t = s_adr["total"] + s_comm["total"]
    titre(f"Exercice 1 : Adressage réseau  ({total_c}/{total_t})")

    communications = calculer_communications()
    id_to_nom = {m["id"]: m["nom"] for m in MACHINES}

    # 1.1 Adresses réseau
    W = (16, 16, 16, 14, 14)

    print(f"\n  {GRAS}1.1 Adresses réseau{RESET}  ({s_adr['correct']}/{s_adr['total']})\n")
    print(f"  {pad('Machine', W[0])} {pad('IP', W[1])} {pad('Masque', W[2])} {pad('Attendu', W[3])} Réponse")
    print(f"  {'─'*W[0]} {'─'*W[1]} {'─'*W[2]} {'─'*W[3]} {'─'*W[4]}")

    rep_adr = ex["réponses_adresses"]
    for m in MACHINES:
        attendu = calculer_adresse_reseau(m["ip"], m["masque"])
        student = rep_adr.get(m["nom"], "")
        ok = normaliser_ip(student) == attendu if student.strip() else False
        print(
            f"  {pad(m['nom'], W[0])} {pad(m['ip'], W[1])} {pad(m['masque'], W[2])} "
            f"{pad(attendu, W[3])} {pad(vide(student), W[4])} {marque(ok)}"
        )

    # 1.2 Communication
    print(f"\n  {GRAS}1.2 Communication{RESET}  ({s_comm['correct']}/{s_comm['total']})\n")

    rep_comm = ex["réponses_communication"]
    for m in MACHINES:
        attendu_ids = communications[m["id"]]
        attendu_noms = sorted(id_to_nom[mid] for mid in attendu_ids)
        student_noms = sorted(rep_comm.get(m["nom"], []))
        ok = set(student_noms) == set(attendu_noms)

        att_str = ", ".join(attendu_noms) if attendu_noms else "(aucun)"
        stu_str = ", ".join(student_noms) if student_noms else "(aucun)"

        print(f"  {pad(m['nom'], 16)} {marque(ok)}")
        print(f"    Attendu : {att_str}")
        print(f"    Réponse : {stu_str}")

    # 1.3 Diagnostic
    print(f"\n  {GRAS}1.3 Diagnostic{RESET}\n")
    diag = ex.get("diagnostic", "")
    print(f"    {diag if diag else f'{DIM}(vide){RESET}'}")


def afficher_reseau_ex2(r):
    ex = r["exercice2"]
    sc = ex["score"]
    titre(f"Exercice 2 : Plan d'adressage  ({sc['correct']}/{sc['total']})")

    rep = ex["réponses"]

    dev_map = {}
    for d in EX2_DEVICES:
        if not d.get("given"):
            dev_map[d["nom"]] = d

    W_NOM, W_IP, W_MSQ = 24, 18, 18

    print()
    print(f"  {pad('Appareil', W_NOM)} {pad('IP élève', W_IP)} {pad('Masque élève', W_MSQ)} IP  Msq")
    print(f"  {'─'*W_NOM} {'─'*W_IP} {'─'*W_MSQ} {'─'*3} {'─'*3}")

    for nom, dev_rep in rep.items():
        dev = dev_map.get(nom)

        rep_ip = dev_rep.get("ip", "")
        rep_masque = dev_rep.get("masque", "")

        ok_masque = rep_masque.strip() == "255.255.255.128"

        ok_ip = False
        if dev:
            subnet = dev["subnet"]
            lo, hi = SUBNET_RANGES[subnet]
            exclusions = SUBNET_EXCLUSIONS[subnet]
            norm = normaliser_ip(rep_ip)
            if norm is not None:
                octets = parse_ip(rep_ip)
                if (octets[0] == 192 and octets[1] == 168 and octets[2] == 0
                        and lo <= octets[3] <= hi
                        and norm not in exclusions):
                    ok_ip = True

        print(
            f"  {pad(nom, W_NOM)} {pad(vide(rep_ip), W_IP)} "
            f"{pad(vide(rep_masque), W_MSQ)} {marque(ok_ip)}   {marque(ok_masque)}"
        )

    print(f"\n  {DIM}Sous-réseau 1 : 192.168.0.0/25   (hôtes .1 – .126,  masque 255.255.255.128){RESET}")
    print(f"  {DIM}Sous-réseau 2 : 192.168.0.128/25 (hôtes .129 – .254, masque 255.255.255.128){RESET}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Consulter les réponses d'un étudiant."
    )
    parser.add_argument("quiz", choices=["binaire", "reseau"],
                        help="Type de quiz (binaire ou reseau)")
    parser.add_argument("code", help="Code de soumission (6 chiffres)")
    args = parser.parse_args()

    if not args.code.isdigit() or len(args.code) != 6:
        print("Erreur : le code doit être composé de 6 chiffres.", file=sys.stderr)
        sys.exit(1)

    r = charger_soumission(args.quiz, args.code)
    if r is None:
        print(
            f"Aucune soumission trouvée pour le code {args.code} "
            f"dans quiz_{args.quiz}.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.quiz == "binaire":
        afficher_binaire(r)
    else:
        afficher_reseau(r)

    print()


if __name__ == "__main__":
    main()

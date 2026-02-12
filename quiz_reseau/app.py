import json
import os
import random
from datetime import datetime

from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "quiz-reseau-bts-ms23-secret"


# ---------------------------------------------------------------------------
# Données fixes — Exercice 1
# ---------------------------------------------------------------------------

MACHINES = [
    {"id": "ordi1",  "nom": "Ordinateur 1",  "ip": "10.1.201.37",   "masque": "255.255.224.0"},
    {"id": "ordi2",  "nom": "Ordinateur 2",  "ip": "192.168.11.3",  "masque": "255.255.0.0"},
    {"id": "ordi3",  "nom": "Ordinateur 3",  "ip": "10.1.188.37",   "masque": "255.255.224.0"},
    {"id": "rect1",  "nom": "Rectifieuse 1", "ip": "192.168.35.4",  "masque": "255.255.0.0"},
    {"id": "frais1", "nom": "Fraiseuse 1",   "ip": "10.1.214.1",    "masque": "255.255.224.0"},
]

# Données fixes — Exercice 2
EX2_GIVEN = {
    "routeur_wan": {"ip": "192.168.0.254", "masque": "255.255.255.128"},
    "ordi1":       {"ip": "192.168.0.1",   "masque": "255.255.255.128"},
}

EX2_DEVICES = [
    {"id": "routeur_lan", "nom": "Routeur interface LAN", "subnet": 1},
    {"id": "routeur_wan", "nom": "Routeur interface WAN", "subnet": 2, "given": True},
    {"id": "ex2_ordi1",   "nom": "Ordinateur 1",         "subnet": 1, "given": True},
    {"id": "ex2_ordi2",   "nom": "Ordinateur 2",         "subnet": 1},
    {"id": "ex2_ordi3",   "nom": "Ordinateur 3",         "subnet": 2},
    {"id": "ex2_ordi4",   "nom": "Ordinateur 4",         "subnet": 2},
]

# Sous-réseau LAN : 192.168.0.0/25   → hôtes .1 à .126
# Sous-réseau WAN : 192.168.0.128/25 → hôtes .129 à .254
SUBNET_RANGES = {
    1: (2, 126),    # .1 déjà pris par Ordinateur 1
    2: (129, 253),  # .254 déjà pris par Routeur WAN
}

SUBNET_EXCLUSIONS = {
    1: {"192.168.0.1"},       # Ordinateur 1
    2: {"192.168.0.254"},     # Routeur WAN
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def calculer_adresse_reseau(ip_str, masque_str):
    """Calcule l'adresse réseau (IP AND masque)."""
    ip = [int(x) for x in ip_str.split(".")]
    masque = [int(x) for x in masque_str.split(".")]
    return ".".join(str(ip[i] & masque[i]) for i in range(4))


def calculer_communications():
    """Retourne un dict {machine_id: set(machine_ids qui communiquent)}."""
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


def parse_ip(s):
    """Parse une adresse IP. Retourne une liste de 4 entiers ou None."""
    s = s.strip()
    parts = s.split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return None
    if all(0 <= o <= 255 for o in octets):
        return octets
    return None


def normaliser_ip(s):
    """Normalise une IP en supprimant les zéros en tête."""
    octets = parse_ip(s)
    if octets is None:
        return None
    return ".".join(str(o) for o in octets)


# ---------------------------------------------------------------------------
# Correction
# ---------------------------------------------------------------------------

def corriger_ex1(reponses):
    """Corrige l'exercice 1. Retourne (score_1_1, score_1_2, total_1_1, total_1_2)."""
    communications = calculer_communications()

    # 1.1 — Adresses réseau
    score_11 = 0
    for m in MACHINES:
        attendu = calculer_adresse_reseau(m["ip"], m["masque"])
        reponse = reponses.get(f"ex1_reseau_{m['id']}", "")
        norm = normaliser_ip(reponse)
        if norm == attendu:
            score_11 += 1

    # 1.2 — Communication
    score_12 = 0
    for m in MACHINES:
        attendu = communications[m["id"]]
        reponse_set = set()
        for other in MACHINES:
            if other["id"] == m["id"]:
                continue
            if reponses.get(f"ex1_comm_{m['id']}_{other['id']}") == "on":
                reponse_set.add(other["id"])
        if reponse_set == attendu:
            score_12 += 1

    return score_11, score_12, 5, 5


def corriger_ex2(reponses):
    """Corrige l'exercice 2. Retourne (score, total)."""
    score = 0
    total = 8  # 4 IP + 4 masques

    # Collecter les IPs données par l'élève pour vérification
    for dev in EX2_DEVICES:
        if dev.get("given"):
            continue

        subnet = dev["subnet"]
        lo, hi = SUBNET_RANGES[subnet]
        exclusions = SUBNET_EXCLUSIONS[subnet]

        # Vérifier le masque
        rep_masque = reponses.get(f"ex2_masque_{dev['id']}", "").strip()
        if rep_masque == "255.255.255.128":
            score += 1

        # Vérifier l'IP
        rep_ip = reponses.get(f"ex2_ip_{dev['id']}", "").strip()
        norm_ip = normaliser_ip(rep_ip)
        if norm_ip is not None:
            octets = parse_ip(rep_ip)
            if (octets[0] == 192 and octets[1] == 168 and octets[2] == 0
                    and lo <= octets[3] <= hi
                    and norm_ip not in exclusions):
                score += 1

    return score, total


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


def structurer_resultat(reponses, scores):
    """Restructure les données brutes en format JSON lisible."""
    s11, s12, t11, t12 = scores["ex1"]
    s2, t2 = scores["ex2"]

    # Exercice 1.1
    ex1_reseaux = {}
    for m in MACHINES:
        ex1_reseaux[m["nom"]] = reponses.get(f"ex1_reseau_{m['id']}", "")

    # Exercice 1.2
    ex1_comm = {}
    for m in MACHINES:
        comm_list = []
        for other in MACHINES:
            if other["id"] == m["id"]:
                continue
            if reponses.get(f"ex1_comm_{m['id']}_{other['id']}") == "on":
                comm_list.append(other["nom"])
        ex1_comm[m["nom"]] = comm_list

    # Exercice 1.3
    ex1_diag = reponses.get("ex1_diagnostic", "")

    # Exercice 2
    ex2_rep = {}
    for dev in EX2_DEVICES:
        if dev.get("given"):
            continue
        ex2_rep[dev["nom"]] = {
            "ip": reponses.get(f"ex2_ip_{dev['id']}", ""),
            "masque": reponses.get(f"ex2_masque_{dev['id']}", ""),
        }

    return {
        "exercice1": {
            "score_adresses": {"correct": s11, "total": t11},
            "score_communication": {"correct": s12, "total": t12},
            "réponses_adresses": ex1_reseaux,
            "réponses_communication": ex1_comm,
            "diagnostic": ex1_diag,
        },
        "exercice2": {
            "score": {"correct": s2, "total": t2},
            "réponses": ex2_rep,
        },
        "score_total": {"correct": s11 + s12 + s2, "total": t11 + t12 + t2},
    }


def sauvegarder_resultat(nom, prenom, reponses, scores):
    """Sauvegarde une soumission dans le fichier JSON. Retourne le code généré."""
    resultats = charger_resultats()
    code = generer_code()
    entree = {
        "code": code,
        "nom": nom,
        "prenom": prenom,
        "date": datetime.now().isoformat(timespec="seconds"),
    }
    entree.update(structurer_resultat(reponses, scores))
    resultats.append(entree)
    with open(RESULTATS_JSON, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    return code


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
    return redirect(url_for("exercice", n=1))


@app.route("/exercice/<int:n>", methods=["GET", "POST"])
def exercice(n):
    if n not in (1, 2):
        return redirect(url_for("accueil"))

    if "nom" not in session:
        return redirect(url_for("accueil"))

    if request.method == "POST":
        reponses = session.get("reponses", {})
        for key, value in request.form.items():
            reponses[key] = value
        session["reponses"] = reponses

        if n < 2:
            return redirect(url_for("exercice", n=n + 1))
        else:
            return redirect(url_for("confirmation"))

    reponses = session.get("reponses", {})
    kwargs = {"n": n, "reponses": reponses, "total_exercices": 2}

    if n == 1:
        kwargs["machines"] = MACHINES
    elif n == 2:
        kwargs["devices"] = EX2_DEVICES
        kwargs["given"] = EX2_GIVEN

    return render_template(f"exercice{n}.html", **kwargs)


@app.route("/confirmation")
def confirmation():
    if "nom" not in session:
        return redirect(url_for("accueil"))

    if "code" in session:
        return render_template("confirmation.html", code=session["code"])

    reponses = session.get("reponses", {})

    scores_ex1 = corriger_ex1(reponses)
    scores_ex2 = corriger_ex2(reponses)

    scores = {"ex1": scores_ex1, "ex2": scores_ex2}
    code = sauvegarder_resultat(session["nom"], session["prenom"], reponses, scores)
    session["code"] = code

    return render_template("confirmation.html", code=code)


@app.route("/resultats")
def resultats():
    tous = charger_resultats()
    return render_template("resultats.html", resultats=tous)


if __name__ == "__main__":
    app.run(debug=True, port=5001)

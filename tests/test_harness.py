"""Tests du harnais : tri de cascade, gouverneur de budget, prison fichiers."""

import pytest

from sigi.budget import Budget
from sigi.cascade import classify
from sigi.skills import DEFAULT_LEDGER, Skill
from sigi.tools.files import FileTools


def test_tache_triviale_part_en_local():
    assert classify("résume ce fichier") == "local"


def test_tache_critique_declaree_part_en_frontiere():
    assert classify("migration critique de la base de production") == "frontier"


def test_par_defaut_le_tier_bon_marche():
    assert classify("rédige un email de relance") == "cheap"


def test_budget_degrade_au_dela_du_plafond():
    budget = Budget(ceiling=100)
    budget.charge("frontier", 60, 60)
    assert budget.degrade("frontier") == "cheap"
    assert budget.degrade("cheap") == "local"


def test_taux_escalade_est_un_slo():
    budget = Budget(ceiling=1000)
    budget.charge("local", 1, 1)
    budget.charge("local", 1, 1)
    assert budget.escalation_rate == 0.0


def test_fichiers_enfermes_dans_la_racine(tmp_path):
    files = FileTools(root=str(tmp_path))
    files.write("a.txt", "bonjour")
    assert files.read("a.txt") == "bonjour"
    with pytest.raises(ValueError):
        files.read("../secret.txt")


def test_skill_mature_au_meilleur_ratio():
    mature = Skill("a", ledger={"calls": 10, "tokens": 1000, "failures": 0})
    jeune = Skill("b", ledger=dict(DEFAULT_LEDGER))
    assert mature.mature and not jeune.mature
    assert mature.cost_quality_ratio == 100.0

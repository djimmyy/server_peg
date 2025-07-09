from datetime import date
from ninja import Schema
from typing import Optional, List

# ------------------- DÉTAIL DE FACTURE -------------------

class DetailFactureIn(Schema):
    description: str
    date_debut_periode: Optional[date] = None
    date_fin_periode: Optional[date] = None
    montant: float

class DetailFactureOut(Schema):
    id: int
    description: str
    date_debut_periode: Optional[date] = None
    date_fin_periode: Optional[date] = None
    montant: float

# ------------------- FACTURE -------------------

class FactureIn(Schema):
    id_inscription: Optional[int] = None
    id_cours_prive: Optional[int] = None
    id_eleve: Optional[int] = None
    details_facture: List[DetailFactureIn]

class FacturesOut(Schema):
    id: int
    date_emission: date
    montant_total: float
    montant_restant: float

class FactureOut(Schema):
    id: int
    date_emission: date
    montant_total: float
    montant_restant: float
    eleve_nom: str
    eleve_prenom: str

# ------------------- PAIEMENT -------------------

class PaiementIn(Schema):
    montant: float
    mode_paiement: str
    methode_paiement: Optional[str] = None
    id_facture: int

class PaiementOut(Schema):
    id: int
    date_paiement: date
    montant: float
    mode_paiement: str
    methode_paiement: Optional[str] = None

import calendar
from datetime import date, timedelta
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import models
from ninja import Router
from typing import Optional, List  # <-- Ajout pour compatibilité 3.9
from .models import (
    Cours,
    Enseignant,
    Presence,
    Session,
    CoursPrive,
    Inscription,
    FichePresences,
    StatutPresenceChoices,
)
from eleves.models import Eleve
from eleves.schemas import ElevesOut
from django.db.models import Q
from .schemas import (
    CoursIn,
    CoursOut,
    EnseignantIn,
    EnseignantOut,
    FichePresencesOut,
    FichesPresencesOut,
    PresenceIn,
    SessionIn,
    SessionOut,
    CoursPriveIn,
    CoursPriveOut,
    InscriptionIn,
    InscriptionUpdateIn,
    FichePresencesIn,
)
from django.db import transaction
from django.core.paginator import Paginator

router = Router()

# ------------------- COURS -------------------

@router.get("/cours/")
def get_cours(request):
    cours = Cours.objects.all()
    return [CoursOut.from_orm(c) for c in cours]

@router.get("/cours/{cours_id}/")
def get_cours_specifique(request, cours_id: int):
    cours = get_object_or_404(Cours, id=cours_id)
    return CoursOut.from_orm(cours)

@router.post("/cour/")
def create_cours(request, cours: CoursIn):
    try:
        with transaction.atomic():
            cours_obj = Cours(**cours.dict())
            cours_obj.full_clean()
            cours_obj.save()
            return {"id": cours_obj.id}
    except ValidationError as e:
        return {"message": "Erreurs de validation.", "erreurs": e.message_dict}

@router.put("/cours/{cours_id}/")
def update_cours(request, cours_id: int, cours: CoursIn):
    try:
        with transaction.atomic():
            cours_obj = get_object_or_404(Cours, id=cours_id)
            for attr, value in cours.dict().items():
                setattr(cours_obj, attr, value)
            cours_obj.full_clean()
            cours_obj.save()
            return {"id": cours_obj.id}
    except ValidationError as e:
        return {"message": "Erreurs de validation.", "erreurs": e.message_dict}

@router.delete("/cours/{cours_id}/")
def delete_cours(request, cours_id: int):
    with transaction.atomic():
        cours = get_object_or_404(Cours, id=cours_id)
        cours.delete()

# ------------------- ENSEIGNANT -------------------
@router.get("/enseignants/")
def list_enseignants(request, search: Optional[str] = None):  # Correction ici
    enseignants = Enseignant.objects.all()
    if search:
        enseignants = enseignants.filter(
            Q(nom__icontains=search) | Q(prenom__icontains=search)
        )
    return [EnseignantOut.from_orm(e) for e in enseignants]

@router.post("/enseignant/")
def create_enseignant(request, enseignant: EnseignantIn):
    try:
        with transaction.atomic():
            enseignant_obj = Enseignant(**enseignant.dict())
            enseignant_obj.full_clean()
            enseignant_obj.save()
            return {"id": enseignant_obj.id}
    except ValidationError as e:
        return {"message": "Erreurs de validation.", "erreurs": e.message_dict}

@router.put("/enseignants/{enseignant_id}/")
def update_enseignant(request, enseignant_id: int, enseignant: EnseignantIn):
    try:
        with transaction.atomic():
            enseignant_obj = get_object_or_404(Enseignant, id=enseignant_id)
            for attr, value in enseignant.dict().items():
                setattr(enseignant_obj, attr, value)
            enseignant_obj.full_clean()
            enseignant_obj.save()
            return {"id": enseignant_obj.id}
    except ValidationError as e:
        return {"message": "Erreurs de validation.", "erreurs": e.message_dict}

@router.delete("/enseignants/{enseignant_id}/")
def delete_enseignant(request, enseignant_id: int):
    with transaction.atomic():
        enseignant = get_object_or_404(Enseignant, id=enseignant_id)
        enseignant.delete()

# ------------------- SESSION -------------------
@router.get("/sessions/")
def sessions(
    request,
    page: int = 1,
    taille: int = 10,
    type: Optional[str] = None,     # Correction ici
    niveau: Optional[str] = None,   # Correction ici
    statut: Optional[str] = None,   # Correction ici
):
    sessions_qs = (
        Session.objects.select_related("cours", "enseignant")
        .annotate(
            id_cours=models.F("cours_id"),
            id_enseignant=models.F("enseignant_id"),
            enseignant__nom=models.F("enseignant__nom"),
            enseignant__prenom=models.F("enseignant__prenom"),
            cours__nom=models.F("cours__nom"),
            cours__type_cours=models.F("cours__type_cours"),
            cours__niveau=models.F("cours__niveau"),
        )
        .order_by("date_debut")
    )

    if type and type != "tous":
        sessions_qs = sessions_qs.filter(cours__type_cours=type)
    if niveau and niveau != "tous":
        sessions_qs = sessions_qs.filter(cours__niveau=niveau)
    if statut and statut != "tous":
        sessions_qs = sessions_qs.filter(statut=statut)

    paginator = Paginator(sessions_qs, taille)
    page_obj = paginator.get_page(page)

    return {
        "sessions": [SessionOut.from_orm(s) for s in page_obj.object_list],
        "nombre_total": paginator.count,
    }

@router.get("/sessions/{id_session}/", response=SessionOut)
def rechercher_session(request, id_session: int):
    session = get_object_or_404(
        Session.objects.select_related("cours", "enseignant").annotate(
            cours__nom=models.F("cours__nom"),
            cours__type_cours=models.F("cours__type_cours"),
            cours__niveau=models.F("cours__niveau"),
            id_cours=models.F("cours__id"),
            id_enseignant=models.F("enseignant__id"),
            enseignant__nom=models.F("enseignant__nom"),
            enseignant__prenom=models.F("enseignant__prenom"),
        ),
        id=id_session,
    )
    return SessionOut.from_orm(session)

# (Le reste du fichier ne contient pas de syntaxe incompatible 3.9)

# Pour les fonctions où il y a des `list[...]`, sur Python 3.9, mieux vaut utiliser List[...] :

@router.get("/eleves/{eleve_id}/cours_prives/", response=List[CoursPriveOut])  # Correction ici
def get_cours_prives_by_eleve(request, eleve_id: int):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    cours_prives = eleve.cours_prives.select_related("enseignant").all()
    return [
        CoursPriveOut(
            id=cours_prive.id,
            date_cours_prive=cours_prive.date_cours_prive,
            heure_debut=cours_prive.heure_debut,
            heure_fin=cours_prive.heure_fin,
            tarif=cours_prive.tarif,
            lieu=cours_prive.lieu,
            enseignant=cours_prive.enseignant.id,
            enseignant__nom=cours_prive.enseignant.nom,
            enseignant__prenom=cours_prive.enseignant.prenom,
            eleves=[
                f"{eleve.nom} {eleve.prenom}" for eleve in cours_prive.eleves.all()
            ],
            eleves_ids=[eleve.id for eleve in cours_prive.eleves.all()],
        )
        for cours_prive in cours_prives
    ]

@router.put("/fiche_presences/{id_fiche_presences}/")
def modifier_fiche_presences(
    request, id_fiche_presences: int, payload: List[PresenceIn]   # Correction ici
):
    fiche = get_object_or_404(FichePresences, id=id_fiche_presences)

    ids_presences = [presence.id for presence in payload]

    qs = Presence.objects.filter(fiche_presences=fiche, id__in=ids_presences)

    map_presences = {presence.id: presence for presence in qs}

    a_modifier = []

    for entree in payload:
        presence = map_presences.get(entree.id)

        if not presence:
            raise Http404(f"Présence {entree.id} not found in fiche {fiche.id}")

        presence.statut = entree.statut
        presence.full_clean()

        a_modifier.append(presence)

    with transaction.atomic():
        if a_modifier:
            Presence.objects.bulk_update(a_modifier, ["statut"])

    return {"success": True}

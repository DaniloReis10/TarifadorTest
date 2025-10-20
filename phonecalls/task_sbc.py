
# task_sbc.py
# Pipeline SBC: processa registros da tabela sbc_phonecall e gera Phonecall
# sem conflitar com o pipeline MD (usa md_phonecall_id negativo).
from __future__ import annotations

from celery import shared_task

from core.utils import batch_qs
from voip.models import Phonecall
from .models import SbcPhonecall

# Reuso do pipeline original
from .constants import (
    IN_CALL, OUT_CALL, IN_ABANDONED, INTERNAL, CONFERENCE, TRANSFER,
    INTERNAL_ABANDONED, OUT_ABANDONED, BUSY, VACANT, UNCLASSIFIED, PABX,
    VC1, VC2, VC3, LOCAL, LDN, LDI, FREE, UNKNOWN, ADDEDVALUE
)
from .tasks import extension_number_analysis, get_extension, check_extension, phonecall_fixsave

BATCH_SIZE = 20000
NEGATE = True  # usa ids negativos no Phonecall.md_phonecall_id para SBC

def _phonecall_from_sbc(sbc: SbcPhonecall) -> Phonecall:
    """Cria um Phonecall a partir de um registro da SBC."""
    ph = Phonecall()
    ph.md_phonecall_id = -int(sbc.id) if NEGATE else int(sbc.id)
    ph.hostid_id = sbc.hostid if sbc.hostid is not None else None
    ph.startdate = sbc.startdate
    ph.starttime = sbc.starttime
    ph.stopdate = sbc.stopdate
    ph.stoptime = sbc.stoptime
    ph.duration = sbc.duration or 0
    ph.dialednumber = sbc.dialednumber or ""
    ph.connectednumber = sbc.connectednumber or ""
    ph.chargednumber = sbc.chargednumber or (sbc.connectednumber or "")
    ph.conditioncode = sbc.conditioncode or 0
    ph.callcasedata = sbc.callcasedata or 0
    ph.seqnumber = sbc.seqnumber or 0
    ph.seqlim = sbc.seqlim or 0
    ph.callid = sbc.callid or ""
    ph.callidass1 = sbc.callidass1 or ""
    ph.callidass2 = sbc.callidass2 or ""
    return ph

def _is_extension(md_phonecall_id: int, number: str, field_name: str) -> bool:
    if not number:
        return False
    return check_extension(md_phonecall_id, number, field_name) is not None

def _sbc_extension_calltype_analysis(sbc_qs, phonecall_map=None, reanalysis=False):
    phonecall_map = phonecall_map or {}
    for sbc in sbc_qs:
        if reanalysis:
            phonecall = phonecall_map.get(-int(sbc.id)) if NEGATE else phonecall_map.get(int(sbc.id))
            if phonecall is None:
                phonecall = _phonecall_from_sbc(sbc)
        else:
            phonecall = _phonecall_from_sbc(sbc)

        chargednumber = phonecall.chargednumber
        dialednumber = phonecall.dialednumber
        cc = int(sbc.conditioncode or 0)

        if cc in PABX[IN_CALL]:
            phonecall.pabx = IN_CALL
            phonecall = extension_number_analysis(phonecall, chargednumber)
            phonecall.inbound = True

        elif cc in PABX[OUT_CALL]:
            phonecall.pabx = OUT_CALL
            phonecall = extension_number_analysis(phonecall, dialednumber, False)
            phonecall.inbound = False

        elif cc in PABX[IN_ABANDONED]:
            phonecall.pabx = IN_ABANDONED
            phonecall.calltype = FREE
            phonecall.description = "Chamada entrante abandonada"

        elif cc in PABX[INTERNAL]:
            phonecall.pabx = INTERNAL
            phonecall.calltype = FREE
            phonecall.description = "Chamada entre ramais"
            phonecall.internal = True

        elif cc in PABX[CONFERENCE]:
            phonecall.pabx = CONFERENCE
            if (len(dialednumber) == 0 or (len(dialednumber) not in [5, 8] and (dialednumber[:1] not in ["3","8","9"])) 
                    or not _is_extension(sbc.id, dialednumber, "dialed")):
                phonecall = extension_number_analysis(phonecall, dialednumber, False)
                phonecall.inbound = False
            elif (len(chargednumber) == 0 or (len(chargednumber) not in [5, 8] and (chargednumber[:1] not in ["3","8","9"])) 
                    or not _is_extension(sbc.id, chargednumber, "charged")):
                phonecall = extension_number_analysis(phonecall, chargednumber)
                phonecall.inbound = True
            else:
                phonecall.calltype = FREE
                phonecall.internal = True

        elif cc in PABX[TRANSFER]:
            phonecall.pabx = TRANSFER
            if (len(dialednumber) == 0 or (len(dialednumber) not in [5, 8] and (dialednumber[:1] not in ["3","8","9"])) 
                    or not _is_extension(sbc.id, dialednumber, "dialed")):
                phonecall = extension_number_analysis(phonecall, dialednumber, False)
                phonecall.inbound = False
            elif (len(chargednumber) == 0 or (len(chargednumber) not in [5, 8] and (chargednumber[:1] not in ["3","8","9"])) 
                    or not _is_extension(sbc.id, chargednumber, "charged")):
                phonecall = extension_number_analysis(phonecall, chargednumber)
                phonecall.inbound = True
            else:
                phonecall.calltype = FREE
                phonecall.internal = True

        elif cc in PABX[INTERNAL_ABANDONED]:
            phonecall.pabx = INTERNAL_ABANDONED
            phonecall.calltype = FREE
            phonecall.description = "Chamada entre ramais abandonada"

        elif cc in PABX[OUT_ABANDONED]:
            phonecall.pabx = OUT_ABANDONED
            phonecall.calltype = FREE
            phonecall.description = "Chamada externa abandonada"

        elif cc in PABX[BUSY]:
            phonecall.pabx = BUSY
            phonecall.calltype = FREE
            phonecall.description = "Número ocupado"

        elif cc in PABX[VACANT]:
            phonecall.pabx = VACANT
            phonecall.calltype = FREE
            phonecall.description = "Número não existe"

        else:
            phonecall.pabx = UNCLASSIFIED
            phonecall.calltype = FREE
            phonecall.description = f"Ainda não implementado: {cc}"

        # Resolve ramal e salva
        phonecall.extension = get_extension(sbc.id, chargednumber, dialednumber, getattr(phonecall, "inbound", False))
        phonecall_fixsave(phonecall)
        phonecall.save()

@shared_task
def sbc_extension_analysis():
    """Processa todas as ligações SBC que ainda não viraram Phonecall."""
    if NEGATE:
        existing = set(Phonecall.objects.filter(md_phonecall_id__lt=0).values_list("md_phonecall_id", flat=True))
        pending_qs = SbcPhonecall.objects.exclude(id__in=[-x for x in existing])
    else:
        existing = set(Phonecall.objects.filter(md_phonecall_id__gte=0).values_list("md_phonecall_id", flat=True))
        pending_qs = SbcPhonecall.objects.exclude(id__in=list(existing))

    total = pending_qs.count()
    for start, end, total, qs in batch_qs(pending_qs.order_by("id"), batch_size=BATCH_SIZE):
        _sbc_extension_calltype_analysis(qs)
    return f"{total} SBC analisadas"

@shared_task
def sbc_extension_analysis_with_date(liststartdate):
    for startdate in liststartdate:
        day_qs = SbcPhonecall.objects.filter(startdate=startdate)
        if NEGATE:
            done = set(Phonecall.objects.filter(md_phonecall_id__lt=0).values_list("md_phonecall_id", flat=True))
            day_qs = day_qs.exclude(id__in=[-x for x in done])
        else:
            done = set(Phonecall.objects.filter(md_phonecall_id__gte=0).values_list("md_phonecall_id", flat=True))
            day_qs = day_qs.exclude(id__in=list(done))
        _sbc_extension_calltype_analysis(day_qs.order_by("id"))
    return "Datas SBC analisadas"

@shared_task
def sbc_extension_reanalysis():
    if NEGATE:
        phonecall_list = Phonecall.objects.filter(company__isnull=True, md_phonecall_id__lt=0)
    else:
        phonecall_list = Phonecall.objects.filter(company__isnull=True, md_phonecall_id__gte=0)
    for start, end, total, qs in batch_qs(phonecall_list, batch_size=BATCH_SIZE):
        phonecall_map = {pc.md_phonecall_id: pc for pc in qs}
        sbc_ids = [-mid for mid in phonecall_map.keys()] if NEGATE else list(phonecall_map.keys())
        sbc_qs = SbcPhonecall.objects.filter(id__in=sbc_ids)
        _sbc_extension_calltype_analysis(sbc_qs, phonecall_map=phonecall_map, reanalysis=True)
    return f"{phonecall_list.count()} SBC reanalisadas"

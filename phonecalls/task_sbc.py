# task_sbc.py — SBC: classificação com condição + fallback por números controlados
# Fonte dos números controlados:
#   1) Tabela controlled_number_clients (armazenando DDD+número; ex: 85 31001234)
#   2) Tabela controlled_number_ranges (armazenando DDD e faixas locais; ex: DDD=85, 31065600–31065644)
#
# Assumimos DDD brasileiro com 2 dígitos. Normalizamos removendo tudo que não é dígito.
# Para checagem por faixa, separamos: DDD = dois primeiros dígitos; local = restante.

from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

try:
    from celery import shared_task
except ModuleNotFoundError:
    def shared_task(func=None, **_kwargs):
        if func is None:
            def decorator(inner): return inner
            return decorator
        return func

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from django.db import connection  # >>> NOVO: para consultas diretas
except ModuleNotFoundError as exc:  # pragma: no cover - falha visível só em runtime manual
    raise ModuleNotFoundError(
        "Django não está instalado. Ative o ambiente virtual do projeto e "
        "execute 'pip install -r requirements.txt' antes de rodar task_sbc.py."
    ) from exc
from core.utils import batch_qs
from voip.models import Phonecall
from .models import SbcPhonecall

from .constants import (
    IN_CALL, OUT_CALL, IN_ABANDONED, INTERNAL, CONFERENCE, TRANSFER,
    INTERNAL_ABANDONED, OUT_ABANDONED, BUSY, VACANT, UNCLASSIFIED,
    PABX, VC1, VC2, VC3, LOCAL, LDN, LDI, FREE, UNKNOWN, ADDEDVALUE
)
from .tasks import extension_number_analysis, get_extension, check_extension, phonecall_fixsave

# ------------------------------------------------------------------------------
# NOVO: Cache em memória dos números controlados e faixas
# ------------------------------------------------------------------------------
_CONTROLLED_NUMBERS_SET: Optional[Set[str]] = None            # ex.: {"8531065600", "85999991234", ...}
_CONTROLLED_RANGES_LIST: Optional[List[Tuple[str, int, int]]] = None  # ex.: [("85", 31065600, 31065644), ...]

DDD_LEN = 2  # >>> NOVO: DDD brasileiro com 2 dígitos (ajuste aqui se precisar)

def _normalize_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def _split_ddd_local(normalized: str) -> Tuple[str, str]:
    """Separa DDD (2 dígitos) e parte local. Ex.: '8531065600' -> ('85','31065600')."""
    if len(normalized) <= DDD_LEN:
        return "", normalized
    return normalized[:DDD_LEN], normalized[DDD_LEN:]

def _load_controlled_from_db() -> Tuple[Set[str], List[Tuple[str, int, int]]]:
    """
    Lê:
      - controlled_number_clients: colunas esperadas (ddd VARCHAR, number_local VARCHAR) ou (full_number VARCHAR)
      - controlled_number_ranges : colunas esperadas (ddd VARCHAR, start_local INT, end_local INT)
    Observação: toleramos dois esquemas para 'clients':
      A) (ddd, number_local)
      B) (full_number) -> string já com DDD+local (sem país)
    """
    global _CONTROLLED_NUMBERS_SET, _CONTROLLED_RANGES_LIST
    if _CONTROLLED_NUMBERS_SET is not None and _CONTROLLED_RANGES_LIST is not None:
        return _CONTROLLED_NUMBERS_SET, _CONTROLLED_RANGES_LIST

    nums: Set[str] = set()
    ranges: List[Tuple[str, int, int]] = []

    with connection.cursor() as cur:
        # --- controlled_number_clients ---
        # Tentativa A: (ddd, number_local)
        try:
            cur.execute("""
                SELECT ddd, number_local
                FROM controlled_number_clients
            """)
            rows = cur.fetchall()
            if rows:
                for ddd, local in rows:
                    d = _normalize_digits(str(ddd))
                    l = _normalize_digits(str(local))
                    if d and l:
                        nums.add(d + l)
            else:
                # Sem linhas — não há o que fazer aqui
                pass
        except Exception:
            # Tentativa B: (full_number)
            try:
                cur.execute("""SELECT full_number FROM controlled_number_clients""")
                rows = cur.fetchall()
                for (full_number,) in rows:
                    f = _normalize_digits(str(full_number))
                    if f:
                        nums.add(f)
            except Exception:
                # Se a tabela não existir, seguimos com conjunto vazio
                pass

        # --- controlled_number_ranges (ddd, start_local, end_local) ---
        try:
            cur.execute("""
                SELECT ddd, start_local, end_local
                FROM controlled_number_ranges
            """)
            rows = cur.fetchall()
            for ddd, start_local, end_local in rows:
                d = _normalize_digits(str(ddd))
                try:
                    s = int(_normalize_digits(str(start_local)))
                    e = int(_normalize_digits(str(end_local)))
                except ValueError:
                    continue
                if d and s <= e:
                    ranges.append((d, s, e))
        except Exception:
            # Sem tabela de faixas — segue só com números explícitos
            pass

    _CONTROLLED_NUMBERS_SET = nums
    _CONTROLLED_RANGES_LIST = ranges
    return nums, ranges

def _is_in_ranges(normalized: str, ranges: List[Tuple[str, int, int]]) -> bool:
    ddd, local = _split_ddd_local(normalized)
    if not (ddd and local.isdigit()):
        return False
    try:
        nlocal = int(local)
    except ValueError:
        return False
    # Checa faixas do mesmo DDD
    for r_ddd, start, end in ranges:
        if r_ddd == ddd and start <= nlocal <= end:
            return True
    return False

def _is_controlled_number(number: str) -> bool:
    """Controlado se:
       1) DDD+local ∈ controlled_number_clients; ou
       2) DDD coincide com a faixa e local ∈ [start_local, end_local]
    """
    normalized = _normalize_digits(number)
    if not normalized:
        return False
    nums, ranges = _load_controlled_from_db()
    if normalized in nums:
        return True
    return _is_in_ranges(normalized, ranges)

def _classify_by_controlled_numbers(chargednumber: str, dialednumber: str) -> Tuple[Optional[int], Optional[bool], str]:
    charged_is_ours = _is_controlled_number(chargednumber)  # >>> NOVO
    dialed_is_ours  = _is_controlled_number(dialednumber)   # >>> NOVO
    if charged_is_ours and not dialed_is_ours:
        return OUT_CALL, False, "fallback: charged ∈ controlados, dialed ∉ controlados — OUT_CALL"
    if dialed_is_ours and not charged_is_ours:
        return IN_CALL, True, "fallback: dialed ∈ controlados, charged ∉ controlados — IN_CALL"
    if charged_is_ours and dialed_is_ours:
        return INTERNAL, None, "fallback: ambos controlados — INTERNAL"
    return UNCLASSIFIED, None, "fallback: nenhum controlado — UNCLASSIFIED"

# ------------------------------------------------------------------------------
# Restante do pipeline (inalterado exceto onde comentado como NOVO)
# ------------------------------------------------------------------------------
BATCH_SIZE = 20000
NEGATE = True
CALL_END_EVENT_TYPE = "CALL_END"

def _phonecall_from_sbc(sbc: SbcPhonecall) -> Phonecall:
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
            phonecall = (phonecall_map.get(-int(sbc.id)) if NEGATE else phonecall_map.get(int(sbc.id)))
            if phonecall is None:
                phonecall = _phonecall_from_sbc(sbc)
        else:
            phonecall = _phonecall_from_sbc(sbc)

        chargednumber = phonecall.chargednumber or ""
        dialednumber = phonecall.dialednumber or ""
        cc = int(sbc.conditioncode or 0)

        # Caminho A: mantém classificação por condition code quando conhecido
        if cc in PABX[IN_CALL]:
            phonecall.pabx = IN_CALL
            phonecall = extension_number_analysis(phonecall, chargednumber)
            phonecall.inbound = True
            phonecall.description = (phonecall.description or "") + " (cc→IN_CALL)"
        elif cc in PABX[OUT_CALL]:
            phonecall.pabx = OUT_CALL
            phonecall = extension_number_analysis(phonecall, dialednumber, False)
            phonecall.inbound = False
            phonecall.description = (phonecall.description or "") + " (cc→OUT_CALL)"
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
            if (len(dialednumber) == 0 or (len(dialednumber) not in [5, 8] and (dialednumber[:1] not in ["3", "8", "9"])) or not _is_extension(sbc.id, dialednumber, "dialed")):
                phonecall = extension_number_analysis(phonecall, dialednumber, False)
                phonecall.inbound = False
            elif (len(chargednumber) == 0 or (len(chargednumber) not in [5, 8] and (chargednumber[:1] not in ["3", "8", "9"])) or not _is_extension(sbc.id, chargednumber, "charged")):
                phonecall = extension_number_analysis(phonecall, chargednumber)
                phonecall.inbound = True
            else:
                phonecall.calltype = FREE
                phonecall.internal = True
        elif cc in PABX[TRANSFER]:
            phonecall.pabx = TRANSFER
            if (len(dialednumber) == 0 or (len(dialednumber) not in [5, 8] and (dialednumber[:1] not in ["3", "8", "9"])) or not _is_extension(sbc.id, dialednumber, "dialed")):
                phonecall = extension_number_analysis(phonecall, dialednumber, False)
                phonecall.inbound = False
            elif (len(chargednumber) == 0 or (len(chargednumber) not in [5, 8] and (chargednumber[:1] not in ["3", "8", "9"])) or not _is_extension(sbc.id, chargednumber, "charged")):
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
            # Caminho B: fallback por números controlados (clientes + faixas) — >>> NOVO
            pabx_guess, inbound_guess, why = _classify_by_controlled_numbers(chargednumber, dialednumber)
            phonecall.pabx = pabx_guess
            if inbound_guess is True:
                phonecall = extension_number_analysis(phonecall, chargednumber)
                phonecall.inbound = True
            elif inbound_guess is False:
                phonecall = extension_number_analysis(phonecall, dialednumber, False)
                phonecall.inbound = False
            else:
                phonecall.calltype = FREE
            phonecall.description = f"Ainda não implementado por cc: {cc} — {why}"

        phonecall.extension = get_extension(sbc.id, chargednumber, dialednumber, getattr(phonecall, "inbound", False))
        phonecall_fixsave(phonecall)
        phonecall.save()

def _pending_sbc_qs():
    base_qs = SbcPhonecall.objects.filter(event_type=CALL_END_EVENT_TYPE)
    if NEGATE:
        existing = set(Phonecall.objects.filter(md_phonecall_id__lt=0).values_list("md_phonecall_id", flat=True))
        pending_qs = base_qs.exclude(id__in=[-x for x in existing])
    else:
        existing = set(Phonecall.objects.filter(md_phonecall_id__gte=0).values_list("md_phonecall_id", flat=True))
        pending_qs = base_qs.exclude(id__in=list(existing))
    return pending_qs

def run_sbc_extension_analysis() -> str:
    # >>> NOVO: aquece o cache (falha cedo se tabela não existe)
    _load_controlled_from_db()
    pending_qs = _pending_sbc_qs()
    total = pending_qs.count()
    for start, end, total, qs in batch_qs(pending_qs.order_by("id"), batch_size=BATCH_SIZE):
        _sbc_extension_calltype_analysis(qs)
    return f"{total} SBC analisadas"

@shared_task
def sbc_extension_analysis():
    return run_sbc_extension_analysis()

def run_sbc_extension_analysis_with_date(liststartdate: Iterable) -> str:
    _load_controlled_from_db()  # >>> NOVO
    for startdate in liststartdate:
        day_qs = SbcPhonecall.objects.filter(startdate=startdate, event_type=CALL_END_EVENT_TYPE)
        if NEGATE:
            done = set(Phonecall.objects.filter(md_phonecall_id__lt=0).values_list("md_phonecall_id", flat=True))
            day_qs = day_qs.exclude(id__in=[-x for x in done])
        else:
            done = set(Phonecall.objects.filter(md_phonecall_id__gte=0).values_list("md_phonecall_id", flat=True))
            day_qs = day_qs.exclude(id__in=list(done))
        _sbc_extension_calltype_analysis(day_qs.order_by("id"))
    return "Datas SBC analisadas"

@shared_task
def sbc_extension_analysis_with_date(liststartdate):
    return run_sbc_extension_analysis_with_date(liststartdate)

def run_sbc_extension_reanalysis() -> str:
    _load_controlled_from_db()  # >>> NOVO
    if NEGATE:
        phonecall_list = Phonecall.objects.filter(company__isnull=True, md_phonecall_id__lt=0)
    else:
        phonecall_list = Phonecall.objects.filter(company__isnull=True, md_phonecall_id__gte=0)
    for start, end, total, qs in batch_qs(phonecall_list, batch_size=BATCH_SIZE):
        phonecall_map = {pc.md_phonecall_id: pc for pc in qs}
        sbc_ids = [-mid for mid in phonecall_map.keys()] if NEGATE else list(phonecall_map.keys())
        sbc_qs = SbcPhonecall.objects.filter(id__in=sbc_ids, event_type=CALL_END_EVENT_TYPE)
        _sbc_extension_calltype_analysis(sbc_qs, phonecall_map=phonecall_map, reanalysis=True)
    return f"{phonecall_list.count()} SBC reanalisadas"

@shared_task
def sbc_extension_reanalysis():
    return run_sbc_extension_reanalysis()

def _parse_dates(date_strings: List[str]) -> List:
    parsed: List = []
    for value in date_strings:
        try:
            from datetime import date
            parsed.append(date.fromisoformat(value))
        except ValueError:
            parsed.append(value)
    return parsed

def _configure_django(settings_module: str) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    import django
    django.setup()

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa os pipelines SBC fora do ambiente Celery")
    parser.add_argument("command", choices=("analysis", "analysis-with-date", "reanalysis"),
                        help="Tipo de processamento SBC a ser executado.")
    parser.add_argument("--dates", nargs="+", default=None,
                        help="Lista de datas YYYY-MM-DD (para analysis-with-date).")
    parser.add_argument("--settings", default="TestDjango2.settings",
                        help="Módulo de settings Django (default: TestDjango2.settings).")
    return parser

def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_django(args.settings)
    # aquece o cache para falhar cedo se o schema estiver faltando
    _load_controlled_from_db()
    if args.command == "analysis":
        result = run_sbc_extension_analysis()
    elif args.command == "analysis-with-date":
        if not args.dates:
            parser.error("--dates é obrigatório para analysis-with-date")
        result = run_sbc_extension_analysis_with_date(_parse_dates(args.dates))
    elif args.command == "reanalysis":
        result = run_sbc_extension_reanalysis()
    else:
        parser.error("Comando desconhecido"); return 2
    print(result)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

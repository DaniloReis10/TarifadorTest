#!/usr/bin/env python3
"""Ferramentas de ETL para importar linhas CALL_END do syslog do SBC.

O script conecta-se diretamente a duas bases de dados:

* lê os registros do syslog armazenados em uma tabela PostgreSQL
  (``syslog_events``);
* grava os dados tarifados diretamente na tabela ``phonecalls_phonecall``
  do banco de dados SQLite utilizado pelo Tarifador;
* gera uma planilha Excel por empresa com o detalhamento e a tarifação das
  ligações importadas.

Assim, é possível processar os eventos que o SBC entregou para o
PostgreSQL e aplicar as mesmas regras de cálculo de tarifação utilizadas
pelo modelo ``Phonecall`` (cálculo de tempo faturado, busca de preços nas
``PriceTable`` e cálculo do valor faturado) sem carregar o Django.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import re
from pathlib import Path
import sqlite3
import sys
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
import zipfile
from zoneinfo import ZoneInfo
import zlib

try:  # pragma: no cover - import guard depende do ambiente do cliente
    import psycopg  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback para psycopg2
    psycopg = None  # type: ignore[assignment]

try:  # pragma: no cover - import guard depende do ambiente do cliente
    import psycopg2  # type: ignore[import]
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore[assignment]

# --- Constantes principais -------------------------------------------------

# Identificadores que reproduzem as escolhas do campo ``pabx`` do modelo
# ``Phonecall``. O valor ``1`` representa chamadas recebidas (IN_CALL) e ``3``
# representa chamadas originadas (OUT_CALL). Eles são gravados diretamente na
# coluna ``pabx`` ao inserir o registro na tabela ``phonecalls_phonecall``.
IN_CALL = 1
OUT_CALL = 3

VC1 = 1
VC2 = 2
VC3 = 3
LOCAL = 4
LDN = 5
LDI = 6
FREE = 7
UNKNOWN = 8
ADDEDVALUE = 9

ACTIVE_STATUS = 1

# Mapeamento dos rótulos utilizados pelo SBC para os códigos inteiros que o
# Tarifador espera no campo ``calltype``. Isso permite manter o cálculo de
# tarifação compatível com o restante do sistema.
CALLTYPE_LABEL_MAP: Dict[str, int] = {
    "LCL": LOCAL,
    "LOCAL": LOCAL,
    "NATIONAL": LDN,
    "LDN": LDN,
    "LD": LDN,
    "LDI": LDI,
    "INTL": LDI,
    "INT": LDI,
    "INTERNATIONAL": LDI,
    "FREE": FREE,
    "TOLLFREE": FREE,
    "ADDVAL": ADDEDVALUE,
    "ADDEDVALUE": ADDEDVALUE,
    "MOBILE": VC3,
}

# Conversão inversa para exibição em planilhas: traduze o código inteiro de
# ``calltype`` de volta para um rótulo amigável.
CALLTYPE_DISPLAY: Dict[int, str] = {
    VC1: "VC1",
    VC2: "VC2",
    VC3: "VC3",
    LOCAL: "LOCAL",
    LDN: "LDN",
    LDI: "LDI",
    FREE: "FREE",
    UNKNOWN: "UNKNOWN",
    ADDEDVALUE: "ADDEDVALUE",
}

# Os registros podem vir com ou sem o identificador de fuso horário. Guardamos
# os dois formatos para tentar as conversões na função ``parse_datetime``.
DATETIME_FORMAT_WITH_TZ = "%H:%M:%S.%f %Z %a %b %d %Y"
DATETIME_FORMAT_NO_TZ = "%H:%M:%S.%f %a %b %d %Y"

# --- Estruturas de dados ---------------------------------------------------


@dataclass
class SbcCallRecord:
    """Representa um registro CALL_END extraído do syslog."""

    call_id: str
    session_id: str
    leg: str
    from_uri: str
    to_uri: str
    orig_from_uri: str
    orig_to_uri: str
    calltype_label: str
    cause_code: Optional[int]
    release_cause: str
    release_text: str
    start_time: Optional[datetime]
    connect_time: Optional[datetime]
    end_time: Optional[datetime]
    sequence: Optional[int]
    sip_method: str

    @property
    def from_number(self) -> str:
        # Extrai apenas o usuário/número do campo SIP ``From``.
        return extract_user(self.from_uri)

    @property
    def to_number(self) -> str:
        return extract_user(self.to_uri)

    @property
    def orig_from_number(self) -> str:
        return extract_user(self.orig_from_uri)

    @property
    def orig_to_number(self) -> str:
        return extract_user(self.orig_to_uri)

    @property
    def numbers(self) -> Tuple[str, str, str, str]:
        # Retorna todos os números envolvidos na chamada para facilitar a
        # resolução do ramal e do telefone remoto.
        return (
            self.from_number,
            self.to_number,
            self.orig_from_number,
            self.orig_to_number,
        )


@dataclass
class ExtensionInfo:
    """Informações necessárias de um ramal para tarifação."""

    id: int
    number: str
    organization_id: Optional[int]
    company_id: Optional[int]
    center_id: Optional[int]
    sector_id: Optional[int]
    company_pricetable_id: Optional[int]
    organization_pricetable_id: Optional[int]


@dataclass
class ImportStats:
    created: int = 0
    duplicates: int = 0
    missing_extension: int = 0
    invalid: int = 0

    def as_message(self) -> str:
        return (
            "Importação finalizada: "
            f"{self.created} chamadas criadas, "
            f"{self.duplicates} ignoradas por já existirem, "
            f"{self.missing_extension} sem ramal cadastrado e "
            f"{self.invalid} registros inválidos."
        )


@dataclass
class ExcelReportRow:
    """Linha com os dados que serão exportados para a planilha."""

    company_id: Optional[int]
    company_name: str
    extension_number: str
    remote_number: str
    dialed_number: str
    direction: str
    calltype_label: str
    start: datetime
    end: datetime
    duration: int
    billedtime: int
    price: Decimal
    billedamount: Decimal
    org_price: Decimal
    org_billedamount: Decimal
    description: str
    release_info: str
    call_id: str


# --- Funções utilitárias ---------------------------------------------------


def normalize_digits(number: str) -> str:
    """Remove qualquer caractere não numérico do valor informado."""
    return "".join(ch for ch in (number or "") if ch.isdigit())


def sanitize_filename(value: str) -> str:
    """Converte um texto livre em um nome de arquivo seguro."""

    value = (value or "").strip()
    if not value:
        return "empresa"
    safe = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    return safe.strip("._") or "empresa"


def column_letter(index: int) -> str:
    """Converte o índice da coluna (1-based) para a notação Excel (A, B...)."""

    if index <= 0:
        raise ValueError("O índice de coluna deve ser positivo.")
    letters = []
    while index:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def xlsx_escape(value: str) -> str:
    """Escapa caracteres especiais para inclusão nos XMLs do Excel."""

    value = value.replace("\r", "")
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    value = value.replace('"', "&quot;")
    value = value.replace("'", "&apos;")
    value = value.replace("\n", "&#10;")
    return value


def build_sheet_xml(rows: Sequence[Sequence[str]]) -> str:
    """Cria o conteúdo XML da planilha com as linhas fornecidas."""

    xml_rows: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: List[str] = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{column_letter(column_index)}{row_index}"
            text = xlsx_escape(value)
            cell_xml = (
                f'<c r="{ref}" t="inlineStr">'
                f"<is><t xml:space='preserve'>{text}</t></is>"
                "</c>"
            )
            cells.append(cell_xml)
        xml_rows.append(f"<row r='{row_index}'>{''.join(cells)}</row>")

    body = "".join(xml_rows)
    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>"
        f"<sheetData>{body}</sheetData>"
        "</worksheet>"
    )


def write_basic_xlsx(path: Path, rows: Sequence[Sequence[str]], sheet_name: str = "Chamadas") -> None:
    """Escreve um arquivo XLSX mínimo com uma única planilha."""

    sheet_xml = build_sheet_xml(rows)

    safe_sheet_name = re.sub(r"[\\/:*?\[\]]", "_", sheet_name).strip() or "Planilha"
    safe_sheet_name = safe_sheet_name[:31]
    sheet_name_attr = xlsx_escape(safe_sheet_name)

    workbook_xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' "
        "xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>"
        "<sheets>"
        f"<sheet name='{sheet_name_attr}' sheetId='1' r:id='rId1'/>"
        "</sheets>"
        "</workbook>"
    )

    root_rels = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"
        "<Relationship Id='rId1' "
        "Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' "
        "Target='xl/workbook.xml'/>"
        "</Relationships>"
    )

    workbook_rels = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"
        "<Relationship Id='rId1' "
        "Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' "
        "Target='worksheets/sheet1.xml'/>"
        "</Relationships>"
    )

    content_types = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"
        "<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>"
        "<Default Extension='xml' ContentType='application/xml'/>"
        "<Override PartName='/xl/workbook.xml' "
        "ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'/>"
        "<Override PartName='/xl/worksheets/sheet1.xml' "
        "ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'/>"
        "</Types>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def extract_user(uri: str) -> str:
    """Extrai a porção do usuário (antes do @) de um URI SIP/TEL."""
    if not uri:
        return ""
    value = uri.strip().strip("<>").strip('"').strip()
    if not value:
        return ""
    if "@" in value:
        value = value.split("@", 1)[0]
    if ";" in value:
        value = value.split(";", 1)[0]
    if ":" in value:
        prefix, rest = value.split(":", 1)
        if prefix.lower() in {"sip", "sips", "tel"}:
            value = rest
    return value.strip()


def parse_datetime(value: str, tz: ZoneInfo) -> Optional[datetime]:
    """Converte a string fornecida pelo SBC para ``datetime`` no fuso alvo."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        naive = datetime.strptime(value, DATETIME_FORMAT_WITH_TZ)
    except ValueError:
        try:
            naive = datetime.strptime(value, DATETIME_FORMAT_NO_TZ)
        except ValueError:
            return None
    aware = naive.replace(tzinfo=timezone.utc)
    return aware.astimezone(tz)


def parse_call_end_line(line: str, tz: ZoneInfo) -> Optional[SbcCallRecord]:
    """Interpreta uma linha do syslog e devolve um ``SbcCallRecord``.

    A linha é dividida pelos pipes (``|``) e cada coluna é normalizada. Somente
    os registros que realmente correspondem ao evento ``CALL_END`` são
    retornados; os demais são descartados com ``None``.
    """
    parts = line.rstrip("\n").split("|")
    if len(parts) < 22:
        return None
    if parts[1].strip().upper() != "CALL_END":
        return None

    # O identificador de sequência ``[S=xxxx]`` aparece no prefixo da linha e é
    # utilizado para identificar a ordem do evento dentro do syslog.
    prefix = parts[0]
    sequence = None
    seq_start = prefix.find("[S=")
    if seq_start != -1:
        seq_start += 3
        seq_end = prefix.find("]", seq_start)
        if seq_end != -1:
            seq_value = prefix[seq_start:seq_end].strip()
            if seq_value.isdigit():
                sequence = int(seq_value)

    def _field(index: int) -> str:
        # Função auxiliar que protege contra linhas truncadas.
        if index >= len(parts):
            return ""
        return parts[index].strip()

    call_id = _field(3)
    session_id = _field(4)
    leg = _field(5).upper()
    from_uri = _field(11)
    to_uri = _field(12)
    orig_from_uri = _field(13)
    orig_to_uri = _field(14)

    cause_code = None
    cause_str = _field(15)
    if cause_str:
        try:
            cause_code = int(cause_str)
        except ValueError:
            cause_code = None

    # Construímos o ``SbcCallRecord`` normalizando cada coluna relevante.
    record = SbcCallRecord(
        call_id=call_id,
        session_id=session_id,
        leg=leg,
        from_uri=from_uri,
        to_uri=to_uri,
        orig_from_uri=orig_from_uri,
        orig_to_uri=orig_to_uri,
        calltype_label=_field(16).upper(),
        cause_code=cause_code,
        release_cause=_field(17),
        release_text=_field(18),
        start_time=parse_datetime(_field(19), tz),
        connect_time=parse_datetime(_field(20), tz),
        end_time=parse_datetime(_field(21), tz),
        sequence=sequence,
        sip_method=_field(33),
    )
    return record


def calltype_from_label(label: str) -> int:
    """Traduz o rótulo textual do SBC para o código de tarifação do sistema."""
    if not label:
        return UNKNOWN
    return CALLTYPE_LABEL_MAP.get(label.upper(), UNKNOWN)


def make_billedtime(duration: int) -> int:
    """Aplica as regras de arredondamento do Tarifador para tempo faturado."""
    if duration <= 0:
        return 0
    billed = 60
    if duration > 60:
        remainder = duration - 60
        increments = (remainder + 5) // 6
        billed += increments * 6
    return billed


def decimal_from(value: Optional[Decimal]) -> str:
    """Padroniza o formato decimal usado nas colunas monetárias."""
    if value is None:
        value = Decimal("0")
    return str(value.quantize(Decimal("0.0001")))


def compute_billed_amount(price: Decimal, billedtime: int) -> Decimal:
    """Calcula o valor faturado proporcional ao tempo tarifado."""
    if price <= 0 or billedtime <= 0:
        return Decimal("0")
    amount = (price / Decimal(60)) * Decimal(billedtime)
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_currency(value: Decimal) -> str:
    """Formata valores monetários com duas casas decimais."""

    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# --- Integração com PostgreSQL --------------------------------------------


def _validate_identifier(name: str) -> str:
    """Garante que o nome informado contenha apenas caracteres seguros."""
    if not name:
        raise ValueError("Nome de tabela não pode ser vazio.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(
            "O nome da tabela só pode conter letras, números e underscores e "
            "não pode começar com número."
        )
    return name


def connect_postgres(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
):
    """Abre conexão com o PostgreSQL usando ``psycopg`` ou ``psycopg2``."""

    if psycopg is not None:  # type: ignore[attr-defined]
        conn = psycopg.connect(  # type: ignore[call-arg]
            host=host,
            port=port,
            dbname=database,
            user=user,
            password=password,
        )
        try:
            conn.autocommit = True  # type: ignore[assignment]
        except AttributeError:
            pass
        return conn

    if psycopg2 is not None:  # type: ignore[attr-defined]
        conn = psycopg2.connect(  # type: ignore[call-arg]
            host=host,
            port=port,
            dbname=database,
            user=user,
            password=password,
        )
        conn.autocommit = True
        return conn

    raise RuntimeError(
        "É necessário instalar o pacote 'psycopg' ou 'psycopg2' para ler o "
        "syslog a partir do PostgreSQL."
    )


def iter_call_end_from_postgres(
    conn,
    table: str,
    min_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> Iterator[str]:
    """Consulta a tabela de syslog e produz somente as linhas CALL_END."""

    safe_table = _validate_identifier(table)

    clauses = ["raw IS NOT NULL", "raw <> ''", "raw ILIKE %s"]
    params: list[object] = ["%|CALL_END%"]

    if min_id is not None:
        clauses.append("id > %s")
        params.append(min_id)

    where = " AND ".join(clauses)

    query = [f"SELECT id, raw FROM {safe_table}", f"WHERE {where}", "ORDER BY id"]
    if limit is not None:
        query.append("LIMIT %s")
        params.append(limit)

    sql = " ".join(query)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        for row in cur:
            if isinstance(row, dict):  # psycopg com row_factory dict
                raw_value = row.get("raw")
            else:
                try:
                    raw_value = row[1]
                except (TypeError, IndexError):
                    raw_value = None

            if raw_value is None:
                continue

            if isinstance(raw_value, memoryview):
                raw_value = raw_value.tobytes().decode("utf-8", errors="ignore")

            if isinstance(raw_value, bytes):
                raw_value = raw_value.decode("utf-8", errors="ignore")

            line = str(raw_value).strip()
            if not line:
                continue

            yield line


# --- Camada de acesso a dados ----------------------------------------------


def load_extension_info(conn: sqlite3.Connection) -> Sequence[ExtensionInfo]:
    """Lê os metadados dos ramais que alimentam a tarifação."""
    cur = conn.cursor()

    # Mapeia previamente as tabelas de preço configuradas por organização.
    cur.execute(
        "SELECT organization_id, call_pricetable_id FROM accounts_organizationsetting"
        " WHERE call_pricetable_id IS NOT NULL"
    )
    org_price_tables = {
        row[0]: row[1]
        for row in cur.fetchall()
    }

    # Idem para as empresas, evitando múltiplas consultas posteriores.
    cur.execute(
        "SELECT id, call_pricetable_id FROM centers_company"
        " WHERE call_pricetable_id IS NOT NULL"
    )
    company_price_tables = {
        row[0]: row[1]
        for row in cur.fetchall()
    }

    # Por fim carregamos os próprios ramais.
    cur.execute(
        "SELECT id, extension, organization_id, company_id, center_id, sector_id"
        " FROM extensions_extensionline"
    )

    extensions = []
    for row in cur.fetchall():
        ext = ExtensionInfo(
            id=row[0],
            number=row[1] or "",
            organization_id=row[2],
            company_id=row[3],
            center_id=row[4],
            sector_id=row[5],
            company_pricetable_id=company_price_tables.get(row[3]),
            organization_pricetable_id=org_price_tables.get(row[2]),
        )
        extensions.append(ext)
    return extensions


def load_price_index(conn: sqlite3.Connection) -> Dict[Tuple[int, int], Decimal]:
    """Constroi um índice ``(tabela, calltype)`` -> ``valor``."""
    cur = conn.cursor()
    cur.execute(
        "SELECT table_id, calltype, value FROM phonecalls_price"
        " WHERE status = ? AND calltype IS NOT NULL",
        (ACTIVE_STATUS,),
    )
    prices: Dict[Tuple[int, int], Decimal] = {}
    for table_id, calltype, value in cur.fetchall():
        prices[(table_id, calltype)] = Decimal(str(value))
    return prices


def load_company_names(conn: sqlite3.Connection) -> Dict[Optional[int], str]:
    """Retorna um dicionário ``empresa_id -> nome`` para rótulos das planilhas."""

    cur = conn.cursor()
    cur.execute("SELECT id, name FROM centers_company")
    mapping: Dict[Optional[int], str] = {}
    for company_id, name in cur.fetchall():
        label = (name or "").strip() or f"Empresa {company_id}"
        mapping[company_id] = label

    # Também adicionamos uma chave para chamadas sem empresa associada, a fim de
    # agrupar corretamente eventuais ramais órfãos.
    mapping.setdefault(None, "Sem Empresa")
    return mapping


class ExtensionResolver:
    """Resolve números de telefone para um ramal conhecido."""

    def __init__(self, extensions: Sequence[ExtensionInfo], default_ddd: Optional[str]):
        self.extensions = extensions
        self.default_ddd = (default_ddd or "").strip()
        self._index: Dict[str, ExtensionInfo] = {}
        # Pré-calculamos as chaves possíveis para cada ramal (com e sem DDD,
        # prefixos 0/55 etc.) para facilitar a resolução durante a importação.
        for extension in extensions:
            for candidate in self._generate_candidates(extension.number):
                self._index.setdefault(candidate, extension)

    def resolve(self, number: str) -> Optional[ExtensionInfo]:
        # Tenta encontrar o ramal correspondente em todas as variações
        # possíveis do número informado no log.
        for candidate in self._generate_candidates(number):
            extension = self._index.get(candidate)
            if extension:
                return extension
        return None

    def _generate_candidates(self, number: str) -> Iterator[str]:
        # Normaliza o número e gera diversas formas equivalentes para cruzar com
        # o banco: apenas dígitos, com DDD padrão, com código do país etc.
        if not number:
            return iter(())
        value = str(number).strip()
        digits = normalize_digits(value)
        candidates = {value, digits}

        if digits.startswith("55"):
            candidates.add(digits[2:])
            if self.default_ddd and digits.startswith(f"55{self.default_ddd}"):
                candidates.add(digits[2 + len(self.default_ddd):])
        if digits.startswith("0"):
            candidates.add(digits.lstrip("0"))

        if self.default_ddd:
            if digits.startswith(self.default_ddd):
                candidates.add(digits[len(self.default_ddd):])
            if len(digits) in {8, 9}:
                candidates.add(f"{self.default_ddd}{digits}")
                candidates.add(f"55{self.default_ddd}{digits}")

        return iter(candidate for candidate in candidates if candidate)


# --- Núcleo da importação --------------------------------------------------


class SyslogImporter:
    def __init__(
        self,
        conn: sqlite3.Connection,
        default_ddd: Optional[str],
        timezone_name: str,
    ) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.default_ddd = default_ddd
        self.tz = ZoneInfo(timezone_name)
        # Carregamos todo o material necessário antes de iterar as linhas para
        # evitar reconsultas a cada chamada processada.
        self.extensions = load_extension_info(conn)
        self.resolver = ExtensionResolver(self.extensions, default_ddd)
        self.price_index = load_price_index(conn)
        self.company_names = load_company_names(conn)

    # -- Métodos públicos -------------------------------------------------

    def import_lines(
        self,
        lines: Iterable[str],
        target_leg: str,
        dry_run: bool,
    ) -> Tuple[ImportStats, List[ExcelReportRow]]:
        stats = ImportStats()
        seen_call_ids = set()
        cursor = self.conn.cursor()
        report_rows: List[ExcelReportRow] = []

        for line in lines:
            # Converte a linha em um ``SbcCallRecord``; se não for CALL_END,
            # ``parse_call_end_line`` devolve ``None``.
            record = parse_call_end_line(line, self.tz)
            if not record:
                continue
            # Permite importar apenas um dos legs (RMT/LCL) conforme parâmetro.
            if target_leg != "ANY" and record.leg != target_leg:
                continue

            # Deduplicação básica dentro do próprio arquivo.
            if record.call_id in seen_call_ids:
                stats.duplicates += 1
                continue

            phonecall_data = self._build_phonecall(record)
            if phonecall_data is None:
                stats.missing_extension += 1
                continue

            if phonecall_data.duration < 0:
                stats.invalid += 1
                continue

            seen_call_ids.add(record.call_id)
            # Reproduz o hash ``md_phonecall_id`` utilizado no Django para
            # identificar ligações.
            md_phonecall_id = zlib.crc32(record.call_id.encode("utf-8")) & 0xFFFFFFFF

            cursor.execute(
                "SELECT 1 FROM phonecalls_phonecall WHERE md_phonecall_id = ?",
                (md_phonecall_id,),
            )
            if cursor.fetchone():
                stats.duplicates += 1
                continue

            report_rows.append(self._build_report_row(record, phonecall_data))

            if dry_run:
                stats.created += 1
                continue

            # Finalmente insere a nova chamada no banco.
            self._insert_phonecall(cursor, phonecall_data, md_phonecall_id)
            stats.created += 1

        if not dry_run:
            self.conn.commit()
        return stats, report_rows

    # -- Métodos auxiliares ------------------------------------------------

    def _build_phonecall(self, record: SbcCallRecord) -> Optional["PhonecallData"]:
        # Resolve o ramal e o número remoto, além de identificar se é inbound.
        extension, remote_number, inbound, internal = self._resolve_numbers(record)
        if not extension:
            return None

        # O Tarifador usa a hora de conexão; se não houver, usamos o início.
        start = record.connect_time or record.start_time
        end = record.end_time or start
        if not start or not end:
            return None

        duration = int(round((end - start).total_seconds()))
        description = (
            f"Call-ID {record.call_id} | {record.release_cause} - {record.release_text}"
        ).strip()
        calltype = calltype_from_label(record.calltype_label)
        conditioncode = record.cause_code or 0

        billedtime = make_billedtime(duration)

        price_table_id = extension.company_pricetable_id
        org_price_table_id = extension.organization_pricetable_id

        # Busca o valor da tarifa para a empresa e para a organização.
        price = self._lookup_price(price_table_id, calltype)
        org_price = self._lookup_price(org_price_table_id, calltype)

        billedamount = compute_billed_amount(price, billedtime)
        org_billedamount = compute_billed_amount(org_price, billedtime)

        now = datetime.now(timezone.utc)

        return PhonecallData(
            created=now,
            modified=now,
            pabx=IN_CALL if inbound else OUT_CALL,
            inbound=inbound,
            internal=internal,
            calltype=calltype,
            service=None,
            description=description[:600],
            price=price,
            org_price=org_price,
            billedamount=billedamount,
            org_billedamount=org_billedamount,
            billedtime=billedtime,
            start=start,
            end=end,
            duration=max(0, duration),
            chargednumber=extension.number,
            connectednumber=remote_number,
            dialednumber=remote_number,
            conditioncode=conditioncode,
            extension_id=extension.id,
            organization_id=extension.organization_id,
            company_id=extension.company_id,
            center_id=extension.center_id,
            sector_id=extension.sector_id,
            price_table_id=price_table_id,
            org_price_table_id=org_price_table_id,
        )

    def _lookup_price(self, table_id: Optional[int], calltype: int) -> Decimal:
        if table_id is None:
            return Decimal("0")
        return self.price_index.get((table_id, calltype), Decimal("0"))

    def _resolve_numbers(
        self, record: SbcCallRecord
    ) -> Tuple[Optional[ExtensionInfo], str, bool, bool]:
        candidates = list(record.numbers)
        extension = None
        # Procura qual dos números citados corresponde a um ramal conhecido.
        for candidate in candidates:
            extension = self.resolver.resolve(candidate)
            if extension:
                break
        if not extension:
            return None, "", False, False

        extension_digits = normalize_digits(extension.number)

        def _is_extension(number: str) -> bool:
            return (
                extension_digits != ""
                and normalize_digits(number) == extension_digits
            )

        def _pick_remote(*numbers: str) -> str:
            # Escolhe o primeiro número diferente do ramal para ser tratado
            # como telefone remoto.
            for candidate in numbers:
                if candidate and not _is_extension(candidate):
                    return candidate.strip()
            return ""

        remote_number = ""
        inbound = False

        # Identifica se o ramal aparece como origem ou destino para definir o
        # sentido da chamada. Cada bloco tenta uma das combinações do log.
        if _is_extension(record.orig_from_number):
            remote_number = _pick_remote(
                record.orig_to_number, record.to_number, record.from_number
            )
            inbound = False
        elif _is_extension(record.orig_to_number):
            remote_number = _pick_remote(
                record.orig_from_number, record.from_number, record.to_number
            )
            inbound = True
        elif _is_extension(record.from_number):
            remote_number = _pick_remote(
                record.to_number, record.orig_to_number, record.orig_from_number
            )
            inbound = False
        elif _is_extension(record.to_number):
            remote_number = _pick_remote(
                record.from_number, record.orig_from_number, record.orig_to_number
            )
            inbound = True
        else:
            for candidate in candidates:
                if candidate and not _is_extension(candidate):
                    remote_number = candidate
                    break

        remote_number = (remote_number or "").strip()
        internal = (
            extension_digits != ""
            and normalize_digits(remote_number) == extension_digits
        )

        return extension, remote_number, inbound, internal

    def _insert_phonecall(
        self,
        cursor: sqlite3.Cursor,
        phonecall: "PhonecallData",
        md_phonecall_id: int,
    ) -> None:
        # Converte datas para o fuso configurado antes de gravar.
        start_local = phonecall.start.astimezone(self.tz)
        end_local = phonecall.end.astimezone(self.tz)

        cursor.execute(
            """
            INSERT INTO phonecalls_phonecall (
                created, modified, pabx, inbound, internal, calltype, service,
                description, price, org_price, billedamount, org_billedamount,
                billedtime, md_phonecall_id, startdate, starttime, stopdate,
                stoptime, duration, chargednumber, connectednumber,
                dialednumber, conditioncode, center_id, company_id,
                extension_id, org_price_table_id, organization_id,
                price_table_id, sector_id
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                phonecall.created.isoformat(sep=" "),
                phonecall.modified.isoformat(sep=" "),
                phonecall.pabx,
                int(phonecall.inbound),
                int(phonecall.internal),
                phonecall.calltype,
                phonecall.service,
                phonecall.description,
                decimal_from(phonecall.price),
                decimal_from(phonecall.org_price),
                decimal_from(phonecall.billedamount),
                decimal_from(phonecall.org_billedamount),
                phonecall.billedtime,
                md_phonecall_id,
                start_local.date().isoformat(),
                start_local.time().isoformat(timespec="seconds"),
                end_local.date().isoformat(),
                end_local.time().isoformat(timespec="seconds"),
                phonecall.duration,
                phonecall.chargednumber,
                phonecall.connectednumber,
                phonecall.dialednumber,
                phonecall.conditioncode,
                phonecall.center_id,
                phonecall.company_id,
                phonecall.extension_id,
                phonecall.org_price_table_id,
                phonecall.organization_id,
                phonecall.price_table_id,
                phonecall.sector_id,
            ),
        )

    def _build_report_row(
        self,
        record: SbcCallRecord,
        phonecall: "PhonecallData",
    ) -> ExcelReportRow:
        """Monta a linha com os dados exibidos na planilha da empresa."""

        start_local = phonecall.start.astimezone(self.tz)
        end_local = phonecall.end.astimezone(self.tz)
        company_name = self.company_names.get(
            phonecall.company_id,
            self.company_names.get(None, "Sem Empresa"),
        )
        release_parts = [record.release_cause.strip(), record.release_text.strip()]
        release_info = " - ".join(filter(None, release_parts)) or "-"

        return ExcelReportRow(
            company_id=phonecall.company_id,
            company_name=company_name,
            extension_number=phonecall.chargednumber,
            remote_number=phonecall.connectednumber,
            dialed_number=phonecall.dialednumber,
            direction="Entrada" if phonecall.inbound else "Saída",
            calltype_label=CALLTYPE_DISPLAY.get(
                phonecall.calltype,
                (record.calltype_label or "DESCONHECIDO") or "DESCONHECIDO",
            ),
            start=start_local,
            end=end_local,
            duration=phonecall.duration,
            billedtime=phonecall.billedtime,
            price=phonecall.price,
            billedamount=phonecall.billedamount,
            org_price=phonecall.org_price,
            org_billedamount=phonecall.org_billedamount,
            description=phonecall.description,
            release_info=release_info,
            call_id=record.call_id,
        )


@dataclass
class PhonecallData:
    created: datetime
    modified: datetime
    pabx: int
    inbound: bool
    internal: bool
    calltype: int
    service: Optional[int]
    description: str
    price: Decimal
    org_price: Decimal
    billedamount: Decimal
    org_billedamount: Decimal
    billedtime: int
    start: datetime
    end: datetime
    duration: int
    chargednumber: str
    connectednumber: str
    dialednumber: str
    conditioncode: int
    extension_id: int
    organization_id: Optional[int]
    company_id: Optional[int]
    center_id: Optional[int]
    sector_id: Optional[int]
    price_table_id: Optional[int]
    org_price_table_id: Optional[int]


# --- Interface de linha de comando ----------------------------------------


def export_company_workbooks(
    rows: Sequence[ExcelReportRow],
    output_dir: Path,
    dry_run: bool,
) -> List[Path]:
    """Gera uma planilha ``.xlsx`` com o detalhamento por empresa."""

    if not rows:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    grouped: Dict[Optional[int], List[ExcelReportRow]] = {}
    for row in rows:
        grouped.setdefault(row.company_id, []).append(row)

    saved_files: List[Path] = []
    headers = [
        "Ramal",
        "Número remoto",
        "Número discado",
        "Sentido",
        "Tipo",
        "Início",
        "Fim",
        "Duração (s)",
        "Tempo faturado (s)",
        "Tarifa empresa",
        "Valor empresa",
        "Tarifa organização",
        "Valor organização",
        "Descrição",
        "Motivo liberação",
        "Call-ID",
    ]

    for company_id, company_rows in grouped.items():
        # Ordenamos as linhas pelo horário de início e Call-ID para facilitar a leitura.
        ordered_rows = sorted(company_rows, key=lambda item: (item.start, item.call_id))
        company_label = ordered_rows[0].company_name
        id_suffix = company_id if company_id is not None else "sem_empresa"
        filename = f"{sanitize_filename(company_label)}_{id_suffix}.xlsx"
        workbook_path = output_dir / filename

        table: List[List[str]] = [headers]
        for entry in ordered_rows:
            start_str = entry.start.strftime("%Y-%m-%d %H:%M:%S")
            end_str = entry.end.strftime("%Y-%m-%d %H:%M:%S")
            table.append(
                [
                    entry.extension_number or "",
                    entry.remote_number or "",
                    entry.dialed_number or "",
                    entry.direction,
                    entry.calltype_label,
                    start_str,
                    end_str,
                    str(entry.duration),
                    str(entry.billedtime),
                    format_currency(entry.price),
                    format_currency(entry.billedamount),
                    format_currency(entry.org_price),
                    format_currency(entry.org_billedamount),
                    entry.description or "",
                    entry.release_info or "",
                    entry.call_id,
                ]
            )

        write_basic_xlsx(workbook_path, table)
        saved_files.append(workbook_path)

    if dry_run:
        # Em modo dry-run informamos explicitamente onde as planilhas foram gravadas,
        # já que nenhuma alteração foi persistida no SQLite.
        print(
            "Planilhas geradas apenas para conferência (dry-run):",
            ", ".join(str(path) for path in saved_files),
        )

    return saved_files


def iter_lines_from_path(path: Path, encoding: str) -> Iterator[str]:
    """Itera pelas linhas de um arquivo ou ``stdin``."""
    if str(path) == "-":
        for line in sys.stdin:
            yield line
        return

    with path.open("r", encoding=encoding) as handle:
        for line in handle:
            yield line


def build_argument_parser() -> argparse.ArgumentParser:
    """Configura a interface de linha de comando da ferramenta."""
    parser = argparse.ArgumentParser(
        description="Importa registros CALL_END do syslog do SBC para o banco do Tarifador.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--database",
        default="db.sqlite3",
        help="Caminho do banco de dados SQLite onde os Phonecalls serão inseridos.",
    )
    parser.add_argument(
        "--syslog-file",
        help=(
            "Arquivo texto com as linhas do syslog. Quando omitido, os eventos"
            " são lidos diretamente da tabela PostgreSQL."
        ),
    )
    parser.add_argument(
        "--default-ddd",
        dest="default_ddd",
        help="DDD padrão utilizado para normalizar ramais (ex.: 85).",
    )
    parser.add_argument(
        "--leg",
        choices=["RMT", "LCL", "ANY"],
        default="RMT",
        help="Leg do SBC que deve ser importada.",
    )
    parser.add_argument(
        "--timezone",
        default="UTC",
        help="Fuso horário utilizado para converter as datas de início/fim.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Codificação do arquivo de entrada.",
    )
    parser.add_argument(
        "--pg-host",
        default="localhost",
        help="Servidor PostgreSQL de onde os eventos serão lidos.",
    )
    parser.add_argument(
        "--pg-port",
        type=int,
        default=5432,
        help="Porta do PostgreSQL.",
    )
    parser.add_argument(
        "--pg-database",
        default="syslogdb",
        help="Nome do banco que armazena os eventos do SBC.",
    )
    parser.add_argument(
        "--pg-user",
        default="sysloguser",
        help="Usuário utilizado para acessar a base de syslog.",
    )
    parser.add_argument(
        "--pg-password",
        default="1234",
        help="Senha do usuário do PostgreSQL.",
    )
    parser.add_argument(
        "--pg-table",
        default="syslog_events",
        help="Tabela que contém os eventos do SBC.",
    )
    parser.add_argument(
        "--pg-min-id",
        type=int,
        help="Importa apenas registros com id superior ao informado.",
    )
    parser.add_argument(
        "--pg-limit",
        type=int,
        help="Limita a quantidade máxima de linhas lidas do PostgreSQL.",
    )
    parser.add_argument(
        "--excel-dir",
        default="relatorios_excel",
        help="Diretório onde as planilhas por empresa serão salvas.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa a leitura sem gravar no banco de dados.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Ponto de entrada do script quando executado pelo terminal."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    database_path = Path(args.database)
    if not database_path.exists():
        parser.error(f"Banco de dados {database_path} não encontrado")

    conn = sqlite3.connect(str(database_path))
    pg_conn = None
    generated_files: List[Path] = []
    stats = ImportStats()
    try:
        importer = SyslogImporter(conn, args.default_ddd, args.timezone)

        if args.syslog_file:
            lines = iter_lines_from_path(Path(args.syslog_file), args.encoding)
        else:
            try:
                pg_conn = connect_postgres(
                    host=args.pg_host,
                    port=args.pg_port,
                    database=args.pg_database,
                    user=args.pg_user,
                    password=args.pg_password,
                )
            except (ValueError, RuntimeError) as exc:
                parser.error(str(exc))
            lines = iter_call_end_from_postgres(
                pg_conn,
                args.pg_table,
                min_id=args.pg_min_id,
                limit=args.pg_limit,
            )

        stats, report_rows = importer.import_lines(lines, args.leg.upper(), args.dry_run)
        generated_files = export_company_workbooks(
            report_rows,
            Path(args.excel_dir),
            args.dry_run,
        )
    finally:
        if pg_conn is not None:
            pg_conn.close()
        conn.close()

    print(stats.as_message())
    if generated_files:
        print(
            "Planilhas geradas:",
            ", ".join(str(path) for path in generated_files),
        )
    if args.dry_run:
        print("Nenhum registro foi gravado (modo dry-run).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

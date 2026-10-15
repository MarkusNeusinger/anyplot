"""File conversion for the renderer's convert mode: a binary data file becomes CSV text for the paste route.

The harness (`harness.py --convert input.bin`) loads this module by its path, calls
`preload()` before it arms its audit-hook guard (every import and every `open` is refused
after that), and then `convert(data, sheet)` on the bytes it read, with the guard armed.
Like the harness it is a standalone module with no anyplot import, because it runs inside
the sandbox with the isolated interpreter; the renderer image copies it next to the
harness (`/opt/anyplot/convert.py`). The tests import it directly.

The format comes from the first bytes, never from the file's name or type:

* **Excel and OpenDocument** (`.xlsx`, `.xlsm`, `.xlsb`, `.xls`, `.ods`) through
  calamine, which reads the values the file stored and nothing else: no formula is
  evaluated, no external link followed, no macro or DDE run. A formula cell the file
  saved without its value is empty, and the cells are counted (`formulas_without_value`,
  xlsx and xlsm only: the other formats do not say). An encrypted workbook (an OLE
  container with an `EncryptedPackage` stream) is refused with "remove the password".
  The sheet goes out as its raw cell grid (`csv.writer`): dates ISO, numbers in their
  shortest form, booleans `TRUE`/`FALSE`, empty for nothing, so the parser's
  `table_block` finds a header below row 1 and keeps a title or a footnote as a note.
  Merged cells keep their value in the top-left cell only, which is how calamine reads
  them. Hidden sheets are skipped and counted, very hidden ones are never named, chart
  and macro sheets are skipped. Without a chosen sheet the first visible sheet with a
  cell in it is read; the answer names the visible sheets (at most `MAX_SHEETS_LISTED`)
  so the page can offer the others.
* **Parquet, Feather (v1 and v2) and Arrow IPC** (file and stream) through pyarrow. The
  row count comes from the Parquet footer before any data page is read, and at most
  `MAX_ROWS` + 1 rows are ever read, batch by batch, whatever a footer claims. Struct
  columns are flattened to dotted names, dictionary columns decoded, time-zone-aware
  timestamps written in UTC with `+00:00`; map, binary and union columns are dropped and
  counted (`dropped_columns`). A table with a list column goes out as JSON records, one
  per line, instead of CSV: the paste route's parser expands list fields into long format
  (one row per value, a `record_id` column, thinning to its row cap), the owner's list
  rule of 2026-10-15 (#12191), so there is one implementation of it (`list_columns`).
* **NumPy** `.npy` and `.npz` with `allow_pickle=False`: an object array (a pickle
  inside) is refused, and so is any array that is neither 2-D nor a structured 1-D
  array. The header's shape is checked against the bytes that are there before an
  array is allocated. An `.npz` is a zip of `.npy` members, each a "sheet".
* **Never**: pickle and joblib (loading one runs code) and HDF5; anything else is
  `unsupported`.

Every zip (xlsx, xlsm, xlsb, ods, npz) passes `check_archive` first: at most
`MAX_ZIP_ENTRIES` entries, `MAX_ZIP_UNCOMPRESSED` bytes declared uncompressed in all, at
most `MAX_ZIP_RATIO` times the archive's own size, no encrypted member.

The caps are the computed-data caps of the harness's data mode for rows and columns
(`MAX_ROWS`, `MAX_COLUMNS`), with `ROW_SLACK` more raw rows for a spreadsheet's titles
and notes, and the paste cap (`MAX_CSV_BYTES`, 1 MiB) for the text: the text goes into
the paste box, and a paste over it is refused. A file over a cap is refused with the
measured value and the cap, never cut.
"""

import csv
import datetime
import decimal
import io
import math
import re
import zipfile


MAX_INPUT_BYTES = 5 * 1024 * 1024
"""The largest file converted: the BFF's and the agents service's raw cap (base64 in JSON, about 6.7 MB)."""
MAX_ROWS = 20_000  # agents/anyplot/schemas.py MAX_ROWS (the harness's DATA_MAX_ROWS)
MAX_COLUMNS = 50  # agents/anyplot/schemas.py MAX_COLUMNS
ROW_SLACK = 200
"""Raw spreadsheet rows past `MAX_ROWS`: a title, notes and a header above the table, totals and footnotes below."""
MAX_GRID_ROWS = MAX_ROWS + ROW_SLACK
MAX_CSV_BYTES = 1024 * 1024  # agents/anyplot/data/parse.py MAX_INPUT_BYTES: the text goes through the paste route
MAX_ZIP_ENTRIES = 2_000
MAX_ZIP_UNCOMPRESSED = 100 * 1024 * 1024
MAX_ZIP_RATIO = 250
"""Declared uncompressed bytes per byte of archive: an xlsx of repeated rows packs about 20 to 1, a zip bomb 1,000 to 1."""
MAX_FORMULA_SCAN_BYTES = 32 * 1024 * 1024
"""The largest sheet part whose formula cells are counted; a larger one is read without the count."""
MAX_SHEETS_LISTED = 10
MAX_SHEET_NAME_CHARS = 100
NPY_MAX_HEADER = 10_000  # numpy's own `_MAX_HEADER_SIZE`

REFUSALS = (
    "unsupported",
    "encrypted",
    "pickle",
    "hdf5",
    "corrupt",
    "archive_limits",
    "too_many_rows",
    "too_many_columns",
    "too_large",
    "empty",
    "sheet_not_found",
    "array_shape",
    "object_array",
)
"""Why a file is not converted. The harness exits with `REFUSAL_EXIT_BASE` plus the index (`harness.CONVERT_EXIT`),
and the renderer maps the code back (`wire.CONVERT_REASONS`); a test pins the three together."""
REFUSAL_EXIT_BASE = 10

OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_MAGICS = (b"PK\x03\x04", b"PK\x05\x06")
ODS_MIMETYPE = b"application/vnd.oasis.opendocument.spreadsheet"
SPREADSHEET_KINDS = ("xlsx", "xlsm", "xlsb", "xls", "ods")
_CONTROLS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


class Refused(Exception):
    """A file this module does not convert: `reason` is one of `REFUSALS`, with the measured value and the cap."""

    def __init__(self, reason, measured=None, limit=None):
        super().__init__(reason)
        self.reason = reason
        self.measured = measured
        self.limit = limit


class Conversion:
    """The CSV text of one table and what the page shows next to it."""

    def __init__(self, csv_text, kind, rows, columns, sheet=None, sheets=(), sheet_count=0, warnings=None):
        self.csv_text = csv_text
        self.kind = kind
        self.rows = rows
        self.columns = columns
        self.sheet = sheet
        self.sheets = list(sheets)
        self.sheet_count = sheet_count
        self.warnings = dict(warnings or {})
        self.text_format = "csv"

    def meta(self):
        """`meta.json` for the host (`wire.ConvertMeta`)."""
        return {
            "kind": self.kind,
            "format": self.text_format,
            "rows": self.rows,
            "columns": self.columns,
            "sheet": self.sheet,
            "sheets": self.sheets,
            "sheet_count": self.sheet_count,
            "warnings": {key: value for key, value in self.warnings.items() if value},
        }


def preload():
    """Import everything a conversion needs, before the harness's guard refuses every import and `open`.

    pyarrow and numpy import some of their modules on first use (`pyarrow.compute` for a
    cast, `numpy.lib.format` for a load); a module missing here (a machine without the
    `convert` extra) is skipped, and a conversion that needs it fails as `error`.
    """
    import importlib

    for name in (
        "numpy",
        "numpy.lib.format",
        "pyarrow",
        "pyarrow.compute",
        "pyarrow.ipc",
        "pyarrow.feather",
        "pyarrow.parquet",
        "python_calamine",
        "ast",
        "html",
    ):
        try:
            importlib.import_module(name)
        except ImportError:
            continue
    # `zipfile` decodes member names as cp437, which the codec registry imports on first use; a round trip through
    # an in-memory zip loads that and the deflate path once.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("warm.npy", b"warm")
    with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
        archive.read("warm.npy")
    "warm".encode("cp437").decode("cp437")


# --- Sniffing -------------------------------------------------------------------------------


def sniff(data):
    """The format the first bytes name: one of the converted kinds, or a `Refused` for anything else."""
    head = bytes(data[:16])
    if head.startswith(ZIP_MAGICS):
        return _zip_kind(data)
    if head.startswith(OLE_MAGIC):
        return _ole_kind(data)
    if head.startswith(b"PAR1"):
        return "parquet"
    if head.startswith((b"ARROW1", b"FEA1")):
        return "feather"
    if head.startswith(b"\xff\xff\xff\xff"):
        return "arrow"
    if head.startswith(b"\x93NUMPY"):
        return "npy"
    if head.startswith(b"\x89HDF\r\n\x1a\n"):
        raise Refused("hdf5")
    if len(head) >= 2 and head[0] == 0x80 and 2 <= head[1] <= 5:
        raise Refused("pickle")
    raise Refused("unsupported")


def _open_zip(data):
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, ValueError, OSError, EOFError):
        raise Refused("corrupt") from None


def check_archive(archive, size):
    """Refuse a zip whose central directory announces too much: entries, uncompressed bytes, ratio, encryption.

    The sizes are the declared ones; Python's `zipfile` never inflates a member past its
    declared size (a longer stream fails its CRC), and the sandbox's address-space limit
    and the host's timeout stand behind calamine's own reader.
    """
    infos = archive.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        raise Refused("archive_limits", len(infos), MAX_ZIP_ENTRIES)
    if any(info.flag_bits & 0x1 for info in infos):
        raise Refused("encrypted")
    total = sum(info.file_size for info in infos)
    if total > MAX_ZIP_UNCOMPRESSED:
        raise Refused("archive_limits", total, MAX_ZIP_UNCOMPRESSED)
    if total > MAX_ZIP_RATIO * max(size, 1):
        raise Refused("archive_limits", total // max(size, 1), MAX_ZIP_RATIO)


def _zip_kind(data):
    with _open_zip(data) as archive:
        check_archive(archive, len(data))
        names = set(archive.namelist())
        if "mimetype" in names:
            try:
                mimetype = archive.read("mimetype")[:200].strip()
            except (zipfile.BadZipFile, OSError, ValueError, EOFError):
                raise Refused("corrupt") from None
            if mimetype == ODS_MIMETYPE:
                return "ods"
        if "[Content_Types].xml" in names:
            if "xl/workbook.bin" in names:
                return "xlsb"
            if "xl/workbook.xml" in names:
                try:
                    types = archive.read("[Content_Types].xml")
                except (zipfile.BadZipFile, OSError, ValueError, EOFError):
                    raise Refused("corrupt") from None
                return "xlsm" if b"macroEnabled" in types else "xlsx"
        if names and all(name.endswith(".npy") for name in names):
            return "npz"
    raise Refused("unsupported")


def _ole_kind(data):
    """An OLE compound file: a legacy `.xls` (a `Workbook` or `Book` stream), an encrypted OOXML workbook
    (`EncryptedPackage`), or something else (a `.doc`). The directory names are UTF-16LE."""
    if "EncryptedPackage".encode("utf-16-le") in data:
        raise Refused("encrypted")
    if "Workbook".encode("utf-16-le") in data or "Book".encode("utf-16-le") in data:
        return "xls"
    raise Refused("unsupported")


# --- Cells ----------------------------------------------------------------------------------


def cell_text(value):
    """One cell as CSV text: ISO dates, the shortest number, `TRUE`/`FALSE`, empty for nothing."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return repr(value)
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None and value.time() == datetime.time(0):
            return value.date().isoformat()
        return value.isoformat(sep=" ", timespec="microseconds" if value.microsecond else "seconds")
    if isinstance(value, datetime.date | datetime.time):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value)
    if isinstance(value, decimal.Decimal):
        return str(value) if value.is_finite() else ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = str(value)
    # The parser refuses control characters other than tab and line breaks: they become spaces here.
    return _CONTROLS.sub(" ", text)


def grid_csv(rows):
    """The rows (lists of cell texts, `[]` for an empty row) as CSV text, refused over `MAX_CSV_BYTES`."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    text = buffer.getvalue()
    size = len(text.encode("utf-8", errors="surrogatepass"))
    if size > MAX_CSV_BYTES:
        raise Refused("too_large", size, MAX_CSV_BYTES)
    return text


def _table(names, columns, kind, warnings, sheet=None, sheets=(), sheet_count=0):
    """Named columns of cell texts, all the same length, as a `Conversion` with a header row."""
    if not names:
        raise Refused("empty")
    if len(names) > MAX_COLUMNS:
        raise Refused("too_many_columns", len(names), MAX_COLUMNS)
    count = len(columns[0]) if columns else 0
    if count > MAX_ROWS:
        raise Refused("too_many_rows", count, MAX_ROWS)
    rows = [[cell_text(name) for name in names]]
    rows.extend([column[index] for column in columns] for index in range(count))
    return Conversion(grid_csv(rows), kind, count, len(names), sheet, sheets, sheet_count, warnings)


# --- Spreadsheets ---------------------------------------------------------------------------


def read_grid(sheet):
    """The sheet's cells row by row: trailing empty cells and rows trimmed, the caps checked while it is read.

    Only rows up to the last one with a cell count, so formatted empty rows below a table
    do not; a cell past `MAX_GRID_ROWS` rows or `MAX_COLUMNS` columns refuses the sheet,
    whatever dimension the file declares.
    """
    rows = []
    blank = 0
    width = 0
    for index, row in enumerate(sheet.iter_rows()):
        cells = [cell_text(value) for value in row]
        while cells and cells[-1] == "":
            cells.pop()
        if not cells:
            blank += 1
            continue
        if index >= MAX_GRID_ROWS:
            raise Refused("too_many_rows", max(index + 1, sheet.height), MAX_ROWS)
        if len(cells) > MAX_COLUMNS:
            raise Refused("too_many_columns", max(len(cells), sheet.width), MAX_COLUMNS)
        if rows:
            rows.extend([] for _ in range(blank))
        blank = 0
        width = max(width, len(cells))
        rows.append(cells)
    return rows, width


def _visible_sheets(workbook, warnings):
    from python_calamine import SheetTypeEnum, SheetVisibleEnum

    visible = []
    hidden = 0
    for meta in workbook.sheets_metadata:
        if meta.typ != SheetTypeEnum.WorkSheet:
            continue
        if meta.visible == SheetVisibleEnum.Visible:
            visible.append(meta.name)
        elif meta.visible == SheetVisibleEnum.Hidden:
            hidden += 1
    if hidden:
        warnings["hidden_sheets"] = hidden
    return visible


def read_workbook(data, kind, sheet_name, warnings):
    """The chosen sheet, or the first visible one with a cell, as a raw-grid `Conversion`."""
    from python_calamine import CalamineWorkbook, PasswordError

    try:
        workbook = CalamineWorkbook.from_filelike(io.BytesIO(data))
    except PasswordError:
        raise Refused("encrypted") from None
    except Exception:  # calamine's errors (zip, XML, a broken record) and anything its reader raises
        raise Refused("corrupt") from None
    with workbook:
        visible = _visible_sheets(workbook, warnings)
        if sheet_name is not None:
            if sheet_name not in visible:
                raise Refused("sheet_not_found")
            candidates = [sheet_name]
        else:
            candidates = visible
        for name in candidates:
            try:
                sheet = workbook.get_sheet_by_name(name)
            except Exception:
                raise Refused("corrupt") from None
            rows, width = read_grid(sheet)
            if rows:
                if kind in ("xlsx", "xlsm"):
                    missing = formulas_without_value(data, name)
                    if missing:
                        warnings["formulas_without_value"] = missing
                listed = [_short(item) for item in visible[:MAX_SHEETS_LISTED]]
                return Conversion(grid_csv(rows), kind, len(rows), width, _short(name), listed, len(visible), warnings)
        raise Refused("empty")


def _short(name):
    return name if len(name) <= MAX_SHEET_NAME_CHARS else name[: MAX_SHEET_NAME_CHARS - 1] + "…"


_SHEET_TAG = re.compile(rb"<(?:\w+:)?sheet\b([^>]*)/?>")
_RELATIONSHIP_TAG = re.compile(rb"<(?:\w+:)?Relationship\b([^>]*)/?>")
_ATTRIBUTE = re.compile(rb"([\w:]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
_CELL = re.compile(rb"<(?:\w+:)?c\b[^>]*?(?:/>|>(.*?)</(?:\w+:)?c>)", re.DOTALL)
_FORMULA = re.compile(rb"<(?:\w+:)?f\b")
_VALUE = re.compile(rb"<(?:\w+:)?v\b[^>]*>[^<]")


def _attributes(raw):
    import html

    return {
        key.decode("ascii", "replace"): html.unescape(value[1:-1].decode("utf-8", "replace"))
        for key, value in _ATTRIBUTE.findall(raw)
    }


def formulas_without_value(data, sheet_name):
    """How many formula cells of an xlsx sheet the file saved without a value (calamine reads them as empty).

    Read from the workbook's own parts with plain patterns, no XML parser: the sheet's
    relationship id in `xl/workbook.xml`, its part in `xl/_rels/workbook.xml.rels`, then
    every `<c>` with an `<f>` and no non-empty `<v>`. 0 when a part is missing or too large.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            workbook = archive.read("xl/workbook.xml")
            relations = archive.read("xl/_rels/workbook.xml.rels")
            target = None
            for raw in _SHEET_TAG.findall(workbook):
                attributes = _attributes(raw)
                if attributes.get("name") == sheet_name:
                    target = next((value for key, value in attributes.items() if key.endswith(":id")), None)
                    break
            if target is None:
                return 0
            part = None
            for raw in _RELATIONSHIP_TAG.findall(relations):
                attributes = _attributes(raw)
                if attributes.get("Id") == target:
                    part = attributes.get("Target")
                    break
            if not part:
                return 0
            path = part.lstrip("/") if part.startswith("/") else "xl/" + part
            info = archive.getinfo(path)
            if info.file_size > MAX_FORMULA_SCAN_BYTES:
                return 0
            xml = archive.read(path)
    except (KeyError, zipfile.BadZipFile, OSError, ValueError, EOFError):
        return 0
    return sum(
        1
        for match in _CELL.finditer(xml)
        if match.group(1) and _FORMULA.search(match.group(1)) and not _VALUE.search(match.group(1))
    )


# --- Parquet, Feather, Arrow ----------------------------------------------------------------


def read_arrow(data, kind, warnings):
    """A Parquet, Feather or Arrow IPC table, at most `MAX_ROWS` + 1 rows read, as a `Conversion`."""
    import pyarrow as pa

    try:
        table = _arrow_table(pa, data, kind)
    except Refused:
        raise
    except Exception:  # pyarrow's ArrowInvalid, OSError and kin for a broken or hostile file
        raise Refused("corrupt") from None
    names, columns, lists = _arrow_columns(pa, table, warnings)
    if lists:
        return _records(names, columns, kind, warnings)
    return _table(names, columns, kind, warnings)


def json_value(value):
    """One value for a JSON record: numbers, text, booleans and null as they are, lists and objects element by
    element, everything else (dates, times, decimals) as its cell text."""
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return _CONTROLS.sub(" ", value)
    if isinstance(value, list | tuple):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    return cell_text(value)


def _records(names, columns, kind, warnings):
    """A table with list columns as JSON records, one per line: the paste route's parser expands list fields into
    long format (one row per value, `record_id`, thinning to its row cap: `data/parse.py` `_records`), the owner's
    list rule of 2026-10-15, so the conversion does not expand them a second way."""
    import json

    if len(names) > MAX_COLUMNS:
        raise Refused("too_many_columns", len(names), MAX_COLUMNS)
    count = len(columns[0]) if columns else 0
    lines = [
        json.dumps({name: column[index] for name, column in zip(names, columns, strict=True)}, ensure_ascii=False)
        for index in range(count)
    ]
    text = "[\n" + ",\n".join(lines) + "\n]\n"
    size = len(text.encode("utf-8", errors="surrogatepass"))
    if size > MAX_CSV_BYTES:
        raise Refused("too_large", size, MAX_CSV_BYTES)
    conversion = Conversion(text, kind, count, len(names), warnings=warnings)
    conversion.text_format = "json"
    return conversion


def _arrow_table(pa, data, kind):
    """Every read is single-threaded (`use_threads=False`): the sandbox's process limit counts threads, and a
    decompression pool that cannot start its workers fails the read."""
    batches = []
    count = 0

    def take(batch):
        nonlocal count
        count += batch.num_rows
        if count > MAX_ROWS:
            raise Refused("too_many_rows", count, MAX_ROWS)
        batches.append(batch)

    source = pa.BufferReader(pa.py_buffer(data))
    if kind == "parquet":
        import pyarrow.parquet as pq

        parquet = pq.ParquetFile(source)
        if parquet.metadata.num_rows > MAX_ROWS:
            raise Refused("too_many_rows", parquet.metadata.num_rows, MAX_ROWS)
        schema = parquet.schema_arrow
        _leaf_count(pa, schema)
        for batch in parquet.iter_batches(batch_size=4096, use_threads=False):
            take(batch)
    elif data[:4] == b"FEA1":
        import pyarrow.feather as feather

        table = feather.read_table(source, use_threads=False)
        if table.num_rows > MAX_ROWS:
            raise Refused("too_many_rows", table.num_rows, MAX_ROWS)
        return table
    elif kind == "feather":
        reader = pa.ipc.open_file(source, options=pa.ipc.IpcReadOptions(use_threads=False))
        schema = reader.schema
        _leaf_count(pa, schema)
        for index in range(reader.num_record_batches):
            take(reader.get_batch(index))
    else:
        stream = pa.ipc.open_stream(source, options=pa.ipc.IpcReadOptions(use_threads=False))
        schema = stream.schema
        _leaf_count(pa, schema)
        for batch in stream:
            take(batch)
    return pa.Table.from_batches(batches, schema=schema)


def _leaf_count(pa, schema):
    """Refuse a schema with more than `MAX_COLUMNS` columns once its structs are flattened, before any row is read."""
    count = 0
    pending = [field.type for field in schema]
    while pending:
        kind = pending.pop()
        if pa.types.is_struct(kind):
            pending.extend(kind.field(index).type for index in range(kind.num_fields))
        else:
            count += 1
        if count > 10 * MAX_COLUMNS:
            break
    if count > MAX_COLUMNS:
        raise Refused("too_many_columns", count, MAX_COLUMNS)


def _arrow_columns(pa, table, warnings):
    """The table's columns: structs flattened, unsupported types dropped and counted.

    Scalar columns become cell texts. List columns (`list`, `large_list`, `fixed_size_list`) are
    kept as lists of JSON values, and the third value says there is one: the table then goes
    out as JSON records (`_records`), whose list fields the parser expands.
    """
    import pyarrow.compute as pc

    while any(pa.types.is_struct(field.type) for field in table.schema):
        table = table.flatten()
    names = []
    columns = []
    lists = False
    list_types = (pa.types.is_list, pa.types.is_large_list, pa.types.is_fixed_size_list)
    lists_ahead = any(
        any(check(field.type.value_type if pa.types.is_dictionary(field.type) else field.type) for check in list_types)
        for field in table.schema
    )
    for name, column in zip(table.column_names, table.columns, strict=True):
        kind = column.type
        if pa.types.is_dictionary(kind):
            column = pa.chunked_array([chunk.dictionary_decode() for chunk in column.chunks], type=kind.value_type)
            kind = column.type
        if pa.types.is_list(kind) or pa.types.is_large_list(kind) or pa.types.is_fixed_size_list(kind):
            lists = True
            warnings["list_columns"] = warnings.get("list_columns", 0) + 1
            names.append(str(name))
            columns.append([json_value(value) for value in column.to_pylist()])
            continue
        if (
            pa.types.is_map(kind)
            or pa.types.is_binary(kind)
            or pa.types.is_large_binary(kind)
            or pa.types.is_fixed_size_binary(kind)
            or pa.types.is_union(kind)
            or pa.types.is_dictionary(kind)
        ):
            warnings["dropped_columns"] = warnings.get("dropped_columns", 0) + 1
            continue
        utc = False
        if pa.types.is_timestamp(kind):
            utc = kind.tz is not None
            # Microseconds: a Python datetime holds no nanoseconds, and a cast drops the zone (values are UTC).
            column = pc.cast(column, pa.timestamp("us"), safe=False)
        elif pa.types.is_duration(kind):
            column = pc.cast(column, pa.duration("us"), safe=False)
        elif pa.types.is_time64(kind):
            column = pc.cast(column, pa.time64("us"), safe=False)
        elif pa.types.is_float16(kind):
            column = pc.cast(column, pa.float32())
        values = column.to_pylist()
        texts = [_utc(value) for value in values] if utc else [cell_text(value) for value in values]
        names.append(str(name))
        # A JSON record keeps a number a number and a missing value null; anything else is its cell text.
        columns.append(
            [
                json_value(value) if value is None or isinstance(value, bool | int | float) else text
                for value, text in zip(values, texts, strict=True)
            ]
            if lists_ahead
            else texts
        )
    return names, columns, lists


def _utc(value):
    if value is None:
        return ""
    return value.isoformat(sep=" ", timespec="microseconds" if value.microsecond else "seconds") + "+00:00"


# --- NumPy ----------------------------------------------------------------------------------


def _npy_array(raw):
    """One `.npy` image as an array, its header checked before the data is allocated."""
    import numpy as np

    format_ = np.lib.format
    handle = io.BytesIO(raw)
    try:
        version = format_.read_magic(handle)
        if version == (1, 0):
            shape, fortran, dtype = format_.read_array_header_1_0(handle, max_header_size=NPY_MAX_HEADER)
        else:
            shape, fortran, dtype = format_.read_array_header_2_0(handle, max_header_size=NPY_MAX_HEADER)
    except ValueError:
        raise Refused("corrupt") from None
    if dtype.hasobject:
        raise Refused("object_array")
    count = math.prod(shape) if shape else 1
    if count * max(dtype.itemsize, 1) > len(raw):
        raise Refused("corrupt")
    handle.seek(0)
    try:
        return format_.read_array(handle, allow_pickle=False, max_header_size=NPY_MAX_HEADER)
    except ValueError:
        raise Refused("corrupt") from None


def _array_shape_ok(array):
    return array.ndim == 2 and array.dtype.names is None or array.ndim == 1 and array.dtype.names is not None


def _array_columns(array, warnings):
    """A 2-D array's columns (`column_1`, ...) or a structured array's fields, as cell texts."""
    import numpy as np

    if array.dtype.names is None:
        if array.shape[0] > MAX_ROWS:
            raise Refused("too_many_rows", array.shape[0], MAX_ROWS)
        if array.shape[1] > MAX_COLUMNS:
            raise Refused("too_many_columns", array.shape[1], MAX_COLUMNS)
        fields = [(f"column_{index + 1}", array[:, index]) for index in range(array.shape[1])]
    else:
        if array.shape[0] > MAX_ROWS:
            raise Refused("too_many_rows", array.shape[0], MAX_ROWS)
        fields = []
        for name in array.dtype.names:
            field = array[name]
            if field.ndim != 1 or field.dtype.names is not None:
                warnings["dropped_columns"] = warnings.get("dropped_columns", 0) + 1
                continue
            fields.append((name, field))
    names = []
    columns = []
    for name, values in fields:
        if values.dtype.kind == "M":
            texts = ["" if np.isnat(value) else str(np.datetime_as_string(value)) for value in values]
        elif values.dtype.kind == "m":
            texts = ["" if np.isnat(value) else str(value) for value in values]
        else:
            texts = [cell_text(value) for value in values.tolist()]
        names.append(name)
        columns.append(texts)
    return names, columns


def read_numpy(data, kind, sheet_name, warnings):
    """An `.npy` array, or one array of an `.npz` (the chosen one, else the first 2-D or structured one)."""
    if kind == "npy":
        array = _npy_array(data)
        if not _array_shape_ok(array):
            raise Refused("array_shape", array.ndim, 2)
        names, columns = _array_columns(array, warnings)
        return _table(names, columns, kind, warnings)
    with _open_zip(data) as archive:
        members = [info.filename for info in archive.infolist()]
        labels = [member[: -len(".npy")] for member in members]
        if sheet_name is not None:
            if sheet_name not in labels:
                raise Refused("sheet_not_found")
            candidates = [sheet_name]
        else:
            candidates = labels
        refused = None
        for label in candidates:
            try:
                raw = archive.read(label + ".npy")
            except (zipfile.BadZipFile, OSError, ValueError, EOFError, KeyError):
                raise Refused("corrupt") from None
            try:
                array = _npy_array(raw)
            except Refused as exc:
                if exc.reason != "object_array" or sheet_name is not None:
                    raise
                refused = exc  # never read: the first array that is no pickle is
                continue
            if not _array_shape_ok(array):
                refused = refused or Refused("array_shape", array.ndim, 2)
                continue
            names, columns = _array_columns(array, warnings)
            listed = [_short(item) for item in labels[:MAX_SHEETS_LISTED]]
            return _table(names, columns, kind, warnings, _short(label), listed, len(labels))
    raise refused or Refused("empty")


# --- Entry ----------------------------------------------------------------------------------


def convert(data, sheet=None):
    """The CSV text of the file in `data` (bytes), or `Refused`; `sheet` names a sheet or an `.npz` array."""
    data = bytes(data)
    if len(data) > MAX_INPUT_BYTES:
        raise Refused("too_large", len(data), MAX_INPUT_BYTES)
    if not data:
        raise Refused("empty")
    kind = sniff(data)
    warnings = {}
    if kind in SPREADSHEET_KINDS:
        return read_workbook(data, kind, sheet, warnings)
    if kind in ("parquet", "feather", "arrow"):
        return read_arrow(data, kind, warnings)
    return read_numpy(data, kind, sheet, warnings)

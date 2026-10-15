"""Binary data files for the convert-mode tests, built in memory: no binary fixture is committed.

The xlsx and ods builders write the few parts calamine reads (the content types, the
workbook and its relationships, one part per sheet; the ODS `mimetype` and `content.xml`),
so a test can state exactly what a hostile file declares: a spoofed dimension, a formula
without its value, an entity expansion, a very hidden sheet.
"""

import io
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from xml.sax.saxutils import escape, quoteattr


Cell = str | int | float | None


@dataclass
class Sheet:
    name: str
    rows: Sequence[Sequence[Cell]] = ()
    state: str | None = None  # "hidden" or "veryHidden"
    formulas: dict[str, tuple[str, str | None]] = field(default_factory=dict)
    """Cell reference -> (formula, cached value or None)."""
    merged: Sequence[str] = ()
    dimension: str | None = None
    prolog: str = ""
    """Text before the root element of the sheet part (a DOCTYPE with entities, for the expansion test)."""


def column_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _cell_xml(reference: str, value: Cell) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    return f'<c r="{reference}"><v>{value}</v></c>'


def _sheet_xml(sheet: Sheet) -> str:
    rows = []
    for row_index, row in enumerate(sheet.rows, start=1):
        cells = "".join(
            _cell_xml(f"{column_letter(col)}{row_index}", value) for col, value in enumerate(row) if value is not None
        )
        rows.append(f'<row r="{row_index}">{cells}</row>')
    for reference, (formula, cached) in sheet.formulas.items():
        row_number = int("".join(ch for ch in reference if ch.isdigit()))
        value = f"<v>{cached}</v>" if cached is not None else ""
        rows.append(f'<row r="{row_number}"><c r="{reference}"><f>{escape(formula)}</f>{value}</c></row>')
    dimension = f'<dimension ref="{sheet.dimension}"/>' if sheet.dimension else ""
    merged = ""
    if sheet.merged:
        merged = (
            f'<mergeCells count="{len(sheet.merged)}">'
            + "".join(f'<mergeCell ref="{ref}"/>' for ref in sheet.merged)
            + "</mergeCells>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + sheet.prolog
        + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{dimension}<sheetData>{''.join(rows)}</sheetData>{merged}</worksheet>"
    )


def xlsx(sheets: Sequence[Sheet], *, macro: bool = False) -> bytes:
    """A minimal workbook calamine reads: inline strings and numbers, formulas, merged cells, sheet states."""
    main = (
        "application/vnd.ms-excel.sheet.macroEnabled.main+xml"
        if macro
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
    )
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, len(sheets) + 1)
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/xl/workbook.xml" ContentType="{main}"/>{overrides}</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    sheet_tags = "".join(
        f'<sheet name={quoteattr(sheet.name)} sheetId="{index}" r:id="rId{index}"'
        + (f' state="{sheet.state}"' if sheet.state else "")
        + "/>"
        for index, sheet in enumerate(sheets, start=1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheet_tags}</sheets></workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, len(sheets) + 1)
        )
        + "</Relationships>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        for index, sheet in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(sheet))
    return buffer.getvalue()


def ods(tables: dict[str, Sequence[Sequence[Cell]]]) -> bytes:
    """A minimal OpenDocument spreadsheet: `mimetype` first and stored, then `content.xml`."""
    body = []
    for name, rows in tables.items():
        xml_rows = []
        for row in rows:
            cells = []
            for value in row:
                if value is None:
                    cells.append("<table:table-cell/>")
                elif isinstance(value, str):
                    cells.append(
                        f'<table:table-cell office:value-type="string"><text:p>{escape(value)}</text:p>'
                        "</table:table-cell>"
                    )
                else:
                    cells.append(
                        f'<table:table-cell office:value-type="float" office:value="{value}">'
                        f"<text:p>{value}</text:p></table:table-cell>"
                    )
            xml_rows.append(f"<table:table-row>{''.join(cells)}</table:table-row>")
        body.append(f"<table:table table:name={quoteattr(name)}>{''.join(xml_rows)}</table:table>")
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">'
        f"<office:body><office:spreadsheet>{''.join(body)}</office:spreadsheet></office:body>"
        "</office:document-content>"
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
        '<manifest:file-entry manifest:full-path="/" '
        'manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.spreadsheet")
        archive.writestr("META-INF/manifest.xml", manifest, zipfile.ZIP_DEFLATED)
        archive.writestr("content.xml", content, zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def zip_bomb(member: str = "xl/worksheets/sheet1.xml", size: int = 200 * 1024 * 1024) -> bytes:
    """A zip whose one member inflates to `size` bytes of zeros (about 200 KB on disk for the default)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        with archive.open(member, "w", force_zip64=True) as handle:
            chunk = b"\0" * (1024 * 1024)
            for _ in range(size // len(chunk)):
                handle.write(chunk)
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
    return buffer.getvalue()


def ole(*stream_names: str) -> bytes:
    """The first bytes of an OLE compound file with `stream_names` in its directory (UTF-16LE), for the sniffer."""
    directory = b"".join(name.encode("utf-16-le").ljust(64, b"\0") for name in stream_names)
    return b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 504 + directory.ljust(512, b"\0")

"""The renderer's file conversion: `convert.py` in-process, then the harness's convert mode under its guard.

The fixtures are built in memory (`convert_fixtures.py`); no binary file is committed. The
in-process cases cover the formats and the hostile files (a zip bomb, an entity expansion, a
spoofed sheet dimension, an encrypted workbook, a broken Parquet footer, a pickled NumPy
array); the subprocess cases run the real harness with the guard armed, because an audit hook
can never be removed from the process that arms it.
"""

import base64
import decimal
import io
import json
import os
import pickle
import struct
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq
import pytest

from agents.anyplot.data.parse import MAX_INPUT_BYTES, parse_dataset
from agents.anyplot.render import convert, harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE
from agents.anyplot.schemas import MAX_COLUMNS, MAX_ROWS
from agents.renderer import wire

from .convert_fixtures import Sheet, ods, ole, xlsx, zip_bomb


def refused(data: bytes, sheet: str | None = None) -> convert.Refused:
    with pytest.raises(convert.Refused) as caught:
        convert.convert(data, sheet)
    return caught.value


def parquet(table: pa.Table) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()


def npy(array: np.ndarray, *, allow_pickle: bool = False) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, array, allow_pickle=allow_pickle)
    return buffer.getvalue()


class TestPins:
    def test_refusals_and_caps_agree_across_converter_harness_and_wire(self) -> None:
        assert convert.REFUSALS == harness.CONVERT_REFUSALS == wire.CONVERT_REASONS
        assert convert.REFUSAL_EXIT_BASE == wire.CONVERT_REFUSAL_BASE == 10
        for index, reason in enumerate(convert.REFUSALS):
            assert harness.CONVERT_EXIT[reason] == 10 + index
            assert wire.convert_refusal(10 + index) == reason
        assert wire.convert_refusal(1) is None and wire.convert_refusal(None) is None
        assert len(set(harness.CONVERT_EXIT.values())) == len(harness.CONVERT_EXIT)
        assert set(harness.CONVERT_EXIT.values()) == wire.CONVERT_HARNESS_EXITS

    def test_the_bffs_refusal_codes_name_every_refusal(self) -> None:
        from api.routers.agent import CONVERT_REFUSAL_CODES

        assert {f"file_{reason}" for reason in convert.REFUSALS} <= CONVERT_REFUSAL_CODES

    def test_caps_are_the_parsers_and_the_wires(self) -> None:
        assert convert.MAX_ROWS == MAX_ROWS and convert.MAX_COLUMNS == MAX_COLUMNS
        assert convert.MAX_CSV_BYTES == MAX_INPUT_BYTES == wire.MAX_CONVERT_TEXT_BYTES
        assert convert.MAX_INPUT_BYTES == harness.CONVERT_MAX_INPUT_BYTES == wire.MAX_CONVERT_INPUT_BYTES
        assert harness.CONVERT_REQUEST_FILE == wire.CONVERT_REQUEST_FILE
        assert harness.CONVERT_META_FILE == wire.CONVERT_META_FILE


class TestSpreadsheets:
    def test_a_title_above_the_header_stays_a_note_for_the_parser(self) -> None:
        data = xlsx([Sheet("Bericht", [["Umsatz 2024"], [], ["month", "revenue"], ["Jan", 120], ["Feb", 135.5]])])
        result = convert.convert(data)
        assert result.csv_text == "Umsatz 2024\n\nmonth,revenue\nJan,120\nFeb,135.5\n"
        assert (result.kind, result.sheet, result.sheets) == ("xlsx", "Bericht", ["Bericht"])
        parsed = parse_dataset(result.csv_text)
        assert [column.name for column in parsed.profile.columns] == ["month", "revenue"]
        assert parsed.context_lines == ["Umsatz 2024"]

    def test_rows_with_empty_trailing_cells_stay_data_rows(self) -> None:
        rows = [["Bericht"], [], ["category", "value"], ["A", 1], ["B", 2], ["C", None], ["D", None], [], ["Quelle: X"]]
        result = convert.convert(xlsx([Sheet("S", rows)]))
        assert result.csv_text == "Bericht\n\ncategory,value\nA,1\nB,2\nC,\nD,\n\nQuelle: X\n"
        parsed = parse_dataset(result.csv_text)
        assert parsed.profile.rows == 4 and parsed.context_lines == ["Bericht", "Quelle: X"]

    def test_long_sheet_names_are_sent_whole_or_not_listed(self) -> None:
        long = "x" * 150
        data = ods({long: [["a"], [1]], "y" * 300: [["b"]]})
        result = convert.convert(data)
        assert result.sheet == long and result.sheets == [long] and result.sheet_count == 2
        assert convert.convert(data, long).csv_text == "a\n1\n"

    def test_merged_cells_keep_their_value_in_the_top_left_cell_only(self) -> None:
        data = xlsx([Sheet("S", [["Region", None, "Sales"], ["North", None, 5]], merged=["A1:B1", "A2:B2"])])
        assert convert.convert(data).csv_text == "Region,,Sales\nNorth,,5\n"

    def test_formula_cells_without_a_saved_value_are_empty_and_counted(self) -> None:
        sheet = Sheet("S", [["a", "b"], [1, None], [2, None]], formulas={"B2": ("A2*2", None), "B3": ("A3*2", "4")})
        result = convert.convert(xlsx([sheet]))
        assert result.csv_text == "a,b\n1,\n2,4\n"
        assert result.warnings == {"formulas_without_value": 1}

    def test_the_first_visible_sheet_with_a_cell_is_read_and_the_visible_ones_are_named(self) -> None:
        sheets = [
            Sheet("Cover"),
            Sheet("Secret", [["x"]], state="veryHidden"),
            Sheet("Old", [["y"]], state="hidden"),
            Sheet("2024", [["a"], [1]]),
            Sheet("2025", [["b"], [2]]),
        ]
        result = convert.convert(xlsx(sheets))
        assert result.sheet == "2024" and result.csv_text == "a\n1\n"
        assert result.sheets == ["2024", "2025"] and result.sheet_count == 2  # the empty cover is not offered
        assert result.warnings == {"hidden_sheets": 1}
        assert "Secret" not in json.dumps(result.meta())

    def test_a_chosen_sheet_is_read_and_a_hidden_or_unknown_one_is_refused(self) -> None:
        data = xlsx([Sheet("A", [["a"]]), Sheet("B", [["b"], [2]]), Sheet("H", [["h"]], state="veryHidden")])
        assert convert.convert(data, "B").csv_text == "b\n2\n"
        assert refused(data, "H").reason == "sheet_not_found"
        assert refused(data, "Z").reason == "sheet_not_found"

    def test_a_workbook_without_cells_is_empty(self) -> None:
        assert refused(xlsx([Sheet("A"), Sheet("B")])).reason == "empty"

    def test_more_sheets_than_listed_are_counted(self) -> None:
        result = convert.convert(xlsx([Sheet(f"S{index}", [[index]]) for index in range(14)]))
        assert len(result.sheets) == convert.MAX_SHEETS_LISTED and result.sheet_count == 14

    def test_a_spoofed_dimension_reads_the_cells_that_are_there(self) -> None:
        data = xlsx([Sheet("S", [["a"], [1]], dimension="A1:XFD1048576")])
        assert convert.convert(data).csv_text == "a\n1\n"

    def test_rows_past_the_cap_and_slack_are_refused_while_reading(self) -> None:
        rows = [["n"], *([index] for index in range(convert.MAX_GRID_ROWS))]
        error = refused(xlsx([Sheet("S", rows)]))
        assert (error.reason, error.limit) == ("too_many_rows", MAX_ROWS)
        assert error.measured is not None and error.measured > convert.MAX_GRID_ROWS

    def test_a_sheet_wider_than_the_column_cap_is_refused(self) -> None:
        error = refused(xlsx([Sheet("S", [list(range(MAX_COLUMNS + 1))])]))
        assert (error.reason, error.measured, error.limit) == ("too_many_columns", MAX_COLUMNS + 1, MAX_COLUMNS)

    def test_text_over_the_paste_cap_is_refused_with_its_size(self) -> None:
        rows = [["x" * 120] * 10 for _ in range(1_000)]
        error = refused(xlsx([Sheet("S", rows)]))
        assert error.reason == "too_large" and error.limit == convert.MAX_CSV_BYTES
        assert error.measured is not None and error.measured > convert.MAX_CSV_BYTES

    def test_an_entity_expansion_is_never_expanded(self) -> None:
        laughs = (
            '<!DOCTYPE worksheet [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">'
            '<!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;"><!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">]>'
        )
        sheet = Sheet("S", [["x"]], prolog=laughs)
        try:
            result = convert.convert(xlsx([sheet]))
        except convert.Refused as error:
            assert error.reason in ("corrupt", "empty")
        else:
            assert "aaaaaaaaaa" not in result.csv_text

    def test_ods_is_read_with_its_sheets(self) -> None:
        result = convert.convert(ods({"Data": [["x", "y"], [1, 2]], "More": [["z"], [3]]}))
        assert (result.kind, result.csv_text, result.sheets) == ("ods", "x,y\n1,2\n", ["Data", "More"])

    def test_control_characters_in_cells_become_spaces(self) -> None:
        assert convert.convert(xlsx([Sheet("S", [["a\x07b"]])])).csv_text == "a b\n"


class TestContainers:
    def test_a_zip_bomb_is_refused_from_its_directory(self) -> None:
        error = refused(zip_bomb())
        assert error.reason == "archive_limits" and error.limit == convert.MAX_ZIP_UNCOMPRESSED

    def test_an_encrypted_workbook_is_refused_with_its_own_reason(self) -> None:
        assert refused(ole("Root Entry", "EncryptionInfo", "EncryptedPackage")).reason == "encrypted"

    def test_an_xls_container_goes_to_calamine_and_a_broken_one_is_corrupt(self) -> None:
        assert convert.sniff(ole("Root Entry", "Workbook")) == "xls"
        assert refused(ole("Root Entry", "Workbook")).reason == "corrupt"

    def test_other_ole_files_and_zips_are_unsupported(self) -> None:
        assert refused(ole("Root Entry", "WordDocument")).reason == "unsupported"
        buffer = io.BytesIO()
        with __import__("zipfile").ZipFile(buffer, "w") as archive:
            archive.writestr("notes.txt", "hello")
        assert refused(buffer.getvalue()).reason == "unsupported"

    @pytest.mark.parametrize(
        ("data", "reason"),
        [
            (pickle.dumps({"a": 1}, protocol=4), "pickle"),
            (b"\x89HDF\r\n\x1a\n" + b"\0" * 32, "hdf5"),
            (b"%PDF-1.7\n", "unsupported"),
            (b"month,revenue\n", "unsupported"),
            (b"", "empty"),
        ],
    )
    def test_never_read_formats(self, data: bytes, reason: str) -> None:
        assert refused(data).reason == reason

    def test_a_file_over_the_input_cap_is_refused(self) -> None:
        error = refused(b"PAR1" + b"\0" * convert.MAX_INPUT_BYTES)
        assert (error.reason, error.limit) == ("too_large", convert.MAX_INPUT_BYTES)


class TestArrow:
    TABLE = pa.table(
        {
            "id": [1, 2],
            "point": pa.array([{"x": 1.5, "y": "a"}, None]),
            "label": pa.array(["u", "v"]).dictionary_encode(),
            "at": pa.array([0, 3_600_000_000], type=pa.timestamp("us", tz="Europe/Berlin")),
            "blob": [b"x", b"y"],
        }
    )

    def test_parquet_flattens_structs_decodes_dictionaries_and_keeps_the_zone(self) -> None:
        result = convert.convert(parquet(self.TABLE))
        assert result.csv_text == (
            "id,point.x,point.y,label,at\n1,1.5,a,u,1970-01-01 01:00:00+0100\n2,,,v,1970-01-01 02:00:00+0100\n"
        )
        assert result.warnings == {"dropped_columns": 1} and result.dropped == ["blob"] and result.kind == "parquet"

    def test_utc_timestamps_are_dates_to_the_parser(self) -> None:
        table = pa.table(
            {"at": pa.array([3_600 * 10**9, 7_200 * 10**9], type=pa.timestamp("ns", tz="UTC")), "v": [1, 2]}
        )
        parsed = parse_dataset(convert.convert(parquet(table)).csv_text)
        assert parsed.profile.columns[0].dtype == "datetime"

    def test_a_repeated_flattened_name_is_renamed_and_counted(self) -> None:
        table = pa.table({"point.x": [1], "point": pa.array([{"x": 2}]), "l": [[1, 2]]})
        result = convert.convert(parquet(table))
        assert result.warnings["renamed_columns"] == 1
        assert '"point.x": 1' in result.csv_text and '"point.x_2": 2' in result.csv_text

    def test_feather_v2_and_an_arrow_stream(self) -> None:
        buffer = io.BytesIO()
        feather.write_feather(self.TABLE, buffer)
        assert convert.convert(buffer.getvalue()).kind == "feather"
        buffer = io.BytesIO()
        with pa.ipc.new_stream(buffer, self.TABLE.schema) as writer:
            writer.write_table(self.TABLE)
        assert convert.convert(buffer.getvalue()).csv_text.startswith("id,point.x")

    def test_list_columns_go_out_as_records_the_parser_expands(self) -> None:
        table = pa.table({"sample": ["A", "B"], "x": [[1, 2, 3], [4, 5, 6]], "y": [[0.1, 0.2, 0.3], [1.0, 2.0, 3.0]]})
        result = convert.convert(parquet(table))
        assert result.text_format == "json" and result.warnings == {"list_columns": 2}
        parsed = parse_dataset(result.csv_text)
        assert parsed.profile.rows == 6
        assert [column.name for column in parsed.profile.columns] == ["sample", "x", "y"]

    def test_the_footer_row_count_refuses_before_any_page_is_read(self) -> None:
        error = refused(parquet(pa.table({"a": range(MAX_ROWS + 1)})))
        assert (error.reason, error.measured, error.limit) == ("too_many_rows", MAX_ROWS + 1, MAX_ROWS)

    def test_a_schema_wider_than_the_cap_is_refused_from_the_footer(self) -> None:
        table = pa.table({f"c{index}": [index] for index in range(MAX_COLUMNS + 1)})
        assert refused(parquet(table)).reason == "too_many_columns"

    @pytest.mark.parametrize(
        "data",
        [
            b"PAR1" + b"\x00" * 16 + (2**31 - 1).to_bytes(4, "little") + b"PAR1",
            b"PAR1garbagePAR1",
            b"ARROW1\x00\x00" + b"\xff" * 64,
            b"\xff\xff\xff\xff" + b"\x7f\xff\xff\xff" + b"\x00" * 16,
        ],
    )
    def test_a_hostile_footer_or_stream_is_corrupt(self, data: bytes) -> None:
        assert refused(data).reason == "corrupt"


class TestNumpy:
    def test_a_2d_array_becomes_numbered_columns(self) -> None:
        result = convert.convert(npy(np.arange(6).reshape(3, 2)))
        assert result.csv_text == "column_1,column_2\n0,1\n2,3\n4,5\n"

    def test_a_structured_array_keeps_its_field_names(self) -> None:
        array = np.zeros(2, dtype=[("t", "datetime64[s]"), ("v", "f8")])
        assert convert.convert(npy(array)).csv_text.startswith("t,v\n1970-01-01T00:00:00,0\n")

    def test_a_1d_array_is_refused(self) -> None:
        assert refused(npy(np.arange(3))).reason == "array_shape"

    def test_an_object_array_is_never_unpickled(self) -> None:
        assert refused(npy(np.array([1, "a"], dtype=object), allow_pickle=True)).reason == "object_array"

    def test_a_header_that_claims_more_data_than_there_is_is_refused_before_allocating(self) -> None:
        raw = bytearray(npy(np.zeros((2, 2))))
        raw = raw.replace(b"(2, 2)", b"(9999999, 9999)", 1)
        assert refused(bytes(raw)).reason == "corrupt"

    def test_npz_arrays_are_sheets_and_a_pickled_member_is_skipped_or_refused(self) -> None:
        buffer = io.BytesIO()
        np.savez(buffer, obj=np.array([None], dtype=object), flat=np.arange(3), grid=np.ones((2, 2)))
        data = buffer.getvalue()
        result = convert.convert(data)
        assert (result.kind, result.sheet, result.sheets) == ("npz", "grid", ["obj", "flat", "grid"])
        assert refused(data, "obj").reason == "object_array"
        only = io.BytesIO()
        np.savez(only, obj=np.array([None], dtype=object))
        assert refused(only.getvalue()).reason == "object_array"


def run_harness(tmp_path: Path, data: bytes, sheet: str | None = None) -> tuple[int, dict[str, object], str | None]:
    """Exit code, `status.json` and `out.csv` of one convert-mode run of the real harness."""
    (tmp_path / "input.bin").write_bytes(data)
    if sheet is not None:
        (tmp_path / "request.json").write_text(json.dumps({"sheet": sheet}), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", str(HARNESS_SOURCE), harness.CONVERT_FLAG, "input.bin"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "ANYPLOT_RLIMIT_CPU_S": "60",
            "ANYPLOT_RLIMIT_AS_MB": "2048",
            "ARROW_DEFAULT_MEMORY_POOL": "system",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
        },
    )
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    out = tmp_path / "out.csv"
    text = out.read_text(encoding="utf-8") if out.exists() and done.returncode == 0 else None
    return done.returncode, status, text


class TestHarness:
    """Each format read once by the real harness with `ConvertGuard` armed: every import and `open` it needs
    happens in the preload, and NumPy's header reader is the one `compile` it lets through."""

    @pytest.mark.parametrize(
        ("label", "data"),
        [
            ("xlsx", xlsx([Sheet("S", [["a", "b"], [1, 2]])])),
            ("ods", ods({"S": [["a", "b"], [1, 2]]})),
            ("parquet", parquet(pa.table({"a": [1], "b": [2]}))),
            ("npy", npy(np.array([[1, 2]]))),
        ],
        ids=[
            "xlsx",
            "ods",
            "parquet",
            "npy",
        ],  # not the bytes: a zip carries its write time, which xdist workers differ on
    )
    def test_formats_convert_under_the_guard(self, tmp_path: Path, label: str, data: bytes) -> None:
        code, status, text = run_harness(tmp_path, data)
        assert (code, status["exit"]) == (0, 0), label
        assert text == "a,b\n1,2\n" or text == "column_1,column_2\n1,2\n"
        meta = wire.ConvertMeta.model_validate_json((tmp_path / "meta.json").read_text(encoding="utf-8"))
        assert meta.rows >= 1

    def test_npz_and_feather_under_the_guard(self, tmp_path: Path) -> None:
        buffer = io.BytesIO()
        np.savez_compressed(buffer, grid=np.ones((1, 2)))
        assert run_harness(tmp_path, buffer.getvalue())[0] == 0
        other = tmp_path / "feather"
        other.mkdir()
        buffer = io.BytesIO()
        feather.write_feather(pa.table({"a": [1], "l": [[1, 2]]}), buffer)
        code, _, text = run_harness(other, buffer.getvalue())
        assert code == 0 and text is not None and text.startswith("[\n")

    def test_a_refusal_writes_its_code_and_numbers_to_status(self, tmp_path: Path) -> None:
        code, status, text = run_harness(tmp_path, zip_bomb())
        assert code == harness.CONVERT_EXIT["archive_limits"] and text is None
        assert status["reason"] == "archive_limits" and status["limit"] == convert.MAX_ZIP_UNCOMPRESSED

    def test_a_zone_aware_timestamp_keeps_its_zone_or_says_utc_under_the_guard(self, tmp_path: Path) -> None:
        stamps = pa.array([1_700_000_000_123_456_789], type=pa.timestamp("ns", "Europe/Berlin"))
        code, _, text = run_harness(tmp_path, parquet(pa.table({"t": stamps})))
        meta = wire.ConvertMeta.model_validate_json((tmp_path / "meta.json").read_text(encoding="utf-8"))
        assert code == 0 and text is not None
        # The zone comes from the system's time-zone database; without one the times are UTC and the meta says so.
        assert text == "t\n2023-11-14 23:13:20.123456789+0100\n" or (
            text == "t\n2023-11-14 22:13:20.123456789Z\n" and meta.warnings == {"utc_timestamps": 1}
        )

    def test_an_encrypted_workbook_is_named_under_the_guard(self, tmp_path: Path) -> None:
        """The OLE sniffer's UTF-16 codec loads lazily: without the preload the guard refused it (`blocked`)."""
        code, status, _ = run_harness(tmp_path, ole("Root Entry", "EncryptedPackage"))
        assert (code, status["reason"]) == (harness.CONVERT_EXIT["encrypted"], "encrypted")

    def test_a_chosen_sheet_travels_in_the_request_file(self, tmp_path: Path) -> None:
        data = xlsx([Sheet("A", [["a"]]), Sheet("B", [["b"]])])
        assert run_harness(tmp_path, data, "B")[2] == "b\n"

    @pytest.mark.parametrize(
        ("data", "request_text", "code", "out"),
        [
            (xlsx([Sheet("A", [["a"]]), Sheet("B", [["b"]])]), '{"sheet": "B"}', 0, "b\n"),
            (zip_bomb(), None, harness.CONVERT_EXIT["archive_limits"], ""),
            (b"\x80\x04K\x01.", '{"sheet": 3}', harness.CONVERT_EXIT["usage"], None),
            (b"\x80\x04K\x01.", "not json", harness.CONVERT_EXIT["usage"], None),
        ],
        ids=["chosen sheet", "refusal", "a sheet that is no text", "a broken request"],
    )
    def test_main_convert_in_process_with_an_inert_guard(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        data: bytes,
        request_text: str | None,
        code: int,
        out: str | None,
    ) -> None:
        """The same code path as the subprocess runs, with a guard that never arms: an audit hook cannot be removed
        from the test process. The subprocess cases above prove the real guard lets each format through."""

        class Inert(harness.DataGuard):
            def arm(self, entry: object = None) -> None:
                self.entry = entry

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        (tmp_path / "input.bin").write_bytes(data)
        if request_text is not None:
            (tmp_path / "request.json").write_text(request_text, encoding="utf-8")

        assert harness.main_convert("input.bin", Inert()) == code
        status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
        assert status["exit"] == code
        written = tmp_path / "out.csv"
        assert (written.read_text(encoding="utf-8") if written.exists() else None) == out

    def test_an_oversized_input_is_refused_before_the_converter_loads(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        (tmp_path / "input.bin").write_bytes(b"\0" * (harness.CONVERT_MAX_INPUT_BYTES + 1))
        assert harness.main_convert("input.bin", harness.DataGuard()) == harness.CONVERT_EXIT["too_large"]
        assert harness.main(["harness.py", "--convert", "missing.bin"]) == harness.CONVERT_EXIT["usage"]

    def test_the_guard_keeps_none_of_the_data_modes_code_builders(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`namedtuple` is one of `CODE_BUILDERS`, which data mode lets compile and exec; convert mode does not."""
        guard = harness.ConvertGuard()
        builder = harness.DataGuard()
        frame = sys._getframe()
        monkeypatch.setattr(harness, "builds_code", lambda caller: True)  # as if `namedtuple` were the caller
        monkeypatch.setattr(guard, "caller", lambda: frame)
        monkeypatch.setattr(builder, "caller", lambda: frame)
        assert not builder.refuses("exec", (compile("1", "<x>", "eval"),))
        assert guard.refuses("exec", (compile("1", "<x>", "eval"),))
        assert guard.refuses("compile", (b"1", "<x>"))

    def test_the_meta_of_ten_long_cjk_sheet_names_fits_the_hosts_cap(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        names = {chr(0x4E00 + index) * 255: [["a"], [index]] for index in range(10)}

        class Inert(harness.DataGuard):
            def arm(self, entry: object = None) -> None:
                self.entry = entry

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        (tmp_path / "input.bin").write_bytes(ods(names))

        assert harness.main_convert("input.bin", Inert()) == 0
        raw = (tmp_path / "meta.json").read_bytes()
        assert len(raw) <= wire.MAX_CONVERT_META_BYTES
        assert wire.ConvertMeta.model_validate_json(raw, strict=True).sheets == list(names)

    def test_the_guard_refuses_code_and_files_while_converting(self) -> None:
        guard = harness.ConvertGuard()
        assert guard.refuses("open", ("/etc/passwd", "r", 0))
        assert guard.refuses("import", ("socket", None, None, None, None))
        assert guard.refuses("exec", (compile("1", "<x>", "eval"),))
        assert guard.refuses("compile", (b"1", "<x>"))  # not called from NumPy's header reader


def zip_with_declared_size(members: dict[str, bytes], liar: str, declared: int) -> bytes:
    """A zip whose member `liar` declares `declared` uncompressed bytes in both headers, whatever it holds."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    data = bytearray(buffer.getvalue())
    with zipfile.ZipFile(io.BytesIO(bytes(data))) as archive:
        info = archive.getinfo(liar)
    struct.pack_into("<I", data, info.header_offset + 22, declared)  # local header: uncompressed size
    position = data.find(b"PK\x01\x02")
    while position != -1:
        name_length = struct.unpack_from("<H", data, position + 28)[0]
        if bytes(data[position + 46 : position + 46 + name_length]) == liar.encode():
            struct.pack_into("<I", data, position + 24, declared)  # central directory: uncompressed size
        position = data.find(b"PK\x01\x02", position + 4)
    return bytes(data)


class TestSecurityReview:
    """The security review of #12194 (Fable with crafted files through the real harness, Gemini by reading)."""

    def test_a_run_of_open_cell_tags_is_scanned_in_linear_time(self) -> None:
        xml = b"<x><!--" + b"<c " * 10_000_000 + b"--></x>"  # 30 MB, the review's crafted comment
        started = time.perf_counter()
        found = convert.scan_sheet_xml(xml)
        assert found.cells == 0 and time.perf_counter() - started < 1.0

    def test_the_crafted_workbook_converts_in_well_under_a_second(self) -> None:
        comment = "<!--" + "".join(f"<c {index % 9973} " for index in range(600_000)) + "-->"
        data = xlsx([Sheet("S", [["a"], [1]], prolog=comment)])
        started = time.perf_counter()
        assert convert.convert(data).csv_text == "a\n1\n"
        assert time.perf_counter() - started < 1.0

    def test_a_cell_far_out_is_refused_before_calamine_allocates_the_box(self) -> None:
        far_row = xlsx([Sheet("S", [["a"]], formulas={"A1048576": ("1", "1")})])
        error = refused(far_row)
        assert (error.reason, error.measured, error.limit) == ("too_many_rows", 1_048_576, MAX_ROWS)
        far_column = xlsx([Sheet("S", [["a"]], formulas={"XFD1": ("1", "1")})])
        assert refused(far_column).reason == "too_many_columns"

    def test_a_member_that_inflates_past_its_declared_size_is_corrupt(self) -> None:
        good = xlsx([Sheet("S", [["a"], [1]])])
        with zipfile.ZipFile(io.BytesIO(good)) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        part = "xl/worksheets/sheet1.xml"
        # Incompressible, so the archive's ratio stays far below its cap: only the declared size lies.
        members[part] = members[part] + b"<!--" + base64.b64encode(os.urandom(1_500_000)) + b"-->"
        assert refused(zip_with_declared_size(members, part, 1024)).reason == "corrupt"
        assert convert.convert(zip_with_declared_size(members, part, len(members[part]))).csv_text == "a\n1\n"

    def test_a_footer_total_that_disagrees_with_its_row_groups_is_corrupt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        data = parquet(pa.table({"a": [1, 2]}))
        real = pq.ParquetFile

        class Forged:
            def __init__(self, source: object) -> None:
                self._file = real(source)

            def __getattr__(self, name: str) -> object:
                return getattr(self._file, name)

            @property
            def metadata(self) -> object:
                metadata = self._file.metadata

                class Footer:
                    num_rows = 1
                    num_row_groups = metadata.num_row_groups
                    row_group = staticmethod(metadata.row_group)

                return Footer()

        monkeypatch.setattr(pq, "ParquetFile", Forged)
        assert refused(data).reason == "corrupt"

    def test_row_groups_are_added_up_before_any_page_is_read(self) -> None:
        buffer = io.BytesIO()
        pq.write_table(pa.table({"a": range(MAX_ROWS + 10)}), buffer, row_group_size=5_000)
        error = refused(buffer.getvalue())
        assert (error.reason, error.measured) == ("too_many_rows", MAX_ROWS + 10)

    def test_running_out_of_memory_is_too_complex(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def exhausted(*args: object) -> object:
            raise MemoryError

        monkeypatch.setattr(convert, "_arrow_table", exhausted)
        assert refused(parquet(pa.table({"a": [1]}))).reason == "too_complex"

    def test_npz_names_with_controls_or_paths_are_never_offered(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name in ("../evil", "bell\x07", "grid"):
                member = io.BytesIO()
                np.save(member, np.ones((1, 2)))
                archive.writestr(name + ".npy", member.getvalue())
        result = convert.convert(buffer.getvalue())
        assert result.sheet == "../evil" or result.sheet is None
        assert result.sheets == ["grid"] and result.sheet_count == 3

    def test_a_broken_npy_header_is_corrupt(self) -> None:
        raw = bytearray(npy(np.zeros((2, 2))))
        end = raw.index(b"}")
        raw[end] = ord("(")  # an unclosed literal: tokenize's error, not a ValueError
        assert refused(bytes(raw)).reason == "corrupt"

    def test_durations_and_intervals_are_dropped_and_named(self) -> None:
        table = pa.table(
            {
                "v": [1],
                "span": pa.array([5], type=pa.duration("s")),
                "every": pa.array([pa.MonthDayNano([1, 2, 3])], type=pa.month_day_nano_interval()),
            }
        )
        buffer = io.BytesIO()
        feather.write_feather(table, buffer)  # Parquet holds no interval
        result = convert.convert(buffer.getvalue())
        assert result.csv_text == "v\n1\n"
        assert result.warnings == {"dropped_columns": 2} and result.dropped == ["span", "every"]
        assert result.meta()["dropped"] == ["span", "every"]

    def test_a_sheet_of_formulas_without_values_is_refused_with_its_count(self) -> None:
        sheet = Sheet("S", formulas={"A1": ("1+1", None), "A2": ("2+2", None)})
        error = refused(xlsx([sheet]))
        assert (error.reason, error.measured) == ("formulas_only", 2)


class TestExactValues:
    """Owner rule of 2026-10-15: data keeps exactly the precision it came in with, through the converter and the
    parser."""

    def test_nanosecond_timestamps_keep_every_digit_and_their_zone(self) -> None:
        stamps = pa.array(
            [1_700_000_000_123_456_789, 1_700_000_001_000_000_000], type=pa.timestamp("ns", "Europe/Berlin")
        )
        text = convert.convert(parquet(pa.table({"t": stamps}))).csv_text
        assert text == "t\n2023-11-14 23:13:20.123456789+0100\n2023-11-14 23:13:21+0100\n"
        parsed = parse_dataset(text)
        assert parsed.column_dtypes["t"] == "datetime"
        assert parsed.csv.splitlines()[1:] == [
            "2023-11-14T23:13:20.123456789+01:00",
            "2023-11-14T23:13:21.000000000+01:00",
        ]

    def test_decimals_and_large_integers_are_written_exactly(self) -> None:
        table = pa.table(
            {
                "d": pa.array([decimal.Decimal("12345678901234567890.123456789"), decimal.Decimal("1.230")]),
                "n": pa.array([2**63 - 1, -(2**62) - 1], type=pa.int64()),
                "u": pa.array([2**64 - 1, 0], type=pa.uint64()),
            }
        )
        text = convert.convert(parquet(table)).csv_text
        assert text.splitlines()[1:] == [
            f"12345678901234567890.123456789,{2**63 - 1},{2**64 - 1}",
            f"1.230000000,{-(2**62) - 1},0",  # the column's decimal(29, 9) holds nine places, all written
        ]
        assert parse_dataset(text).csv.splitlines()[1].split(",")[1] == str(2**63 - 1)

    def test_floats_keep_their_shortest_exact_text(self) -> None:
        table = pa.table({"f": pa.array([0.1], type=pa.float32()), "g": [0.1 + 0.2]})
        assert convert.convert(parquet(table)).csv_text == "f,g\n0.1,0.30000000000000004\n"
        sheet = Sheet("S", [["x"], [0.1 + 0.2], [1e-300]])
        assert convert.convert(xlsx([sheet])).csv_text == "x\n0.30000000000000004\n1e-300\n"
        assert convert.convert(npy(np.array([[0.1]], dtype=np.float32))).csv_text == "column_1\n0.1\n"

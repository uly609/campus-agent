from __future__ import annotations

import base64
import csv
import io

import pdfplumber
import pytest

from app.multimodal import document_parser


def _xlsx_bytes(sheet_name: str = "课程表", rows: list[tuple[str, str]] | None = None) -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(["课程", "时间"])
    for row in rows or [("数据结构", "周一"), ("操作系统", "周三")]:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def test_xlsx_parse_splits_sheets_into_markdown_tables() -> None:
    content = _xlsx_bytes()
    result = document_parser._parse_xlsx("课表.xlsx", content)
    assert result
    assert result[0].kind == "table"
    assert "| 课程 | 时间 |" in result[0].text
    assert "数据结构" in result[0].text
    assert result[0].metadata["sheet_name"] == "课程表"


def test_csv_parse_splits_rows() -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["姓名", "班级"])
    writer.writerow(["张三", "计科2401"])
    writer.writerow(["李四", "计科2402"])
    result = document_parser._parse_csv("名单.csv", buffer.getvalue().encode("utf-8"))
    assert len(result) == 1
    assert result[0].kind == "table"
    assert "计科2402" in result[0].text


def test_text_parse_keeps_paragraphs() -> None:
    content = "第一条校园通知\n\n第二条校园通知内容".encode("utf-8")
    result = document_parser._parse_text("通知.txt", content)
    assert result
    assert "第一条校园通知" in result[0].text


def test_pdf_parse_extracts_text_and_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self) -> str:
            return "测试校园 PDF"

        def extract_tables(self) -> list[list[list[str]]]:
            return [[["编号", "名称"], ["1", "图书馆"]]]

    class FakePDF:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(pdfplumber, "open", lambda _buffer: FakePDF())
    chunks, warnings = document_parser._parse_pdf("手册.pdf", b"%PDF-1.4")
    assert chunks and chunks[0].kind == "table"
    assert "| 编号 | 名称 |" in chunks[0].text
    assert not warnings


@pytest.mark.asyncio
async def test_image_parse_uses_vision_model() -> None:
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    result = await document_parser.parse_document_file("物品.png", png)
    assert result.kind == "image"
    assert result.chunks[0].kind == "image"
    assert "图片解析结果" in result.chunks[0].text
    assert any("演示" in warning or "离线" in warning for warning in result.warnings)


def test_unsupported_extension_rejected() -> None:
    with pytest.raises(ValueError, match="不支持的文件类型"):
        document_parser._validate_input("恶意.exe", b"MZ")


def test_file_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(document_parser, "MAX_FILE_BYTES", 100)
    with pytest.raises(ValueError, match="超过 10MB"):
        document_parser._validate_input("大文件.txt", b"x" * 101)

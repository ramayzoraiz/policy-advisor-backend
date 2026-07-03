"""Markdown splitter that keeps tables intact across chunks.

RecursiveCharacterTextSplitter breaks markdown pipe-tables mid-row because a
table is just one long paragraph to it.  MarkdownTableSplitter instead:

1. Splits the text into alternating *text* and *table* blocks.
2. Text blocks are split with a normal RecursiveCharacterTextSplitter.
3. Table blocks are split row-wise; every chunk of a table gets the header
   row + separator row repeated, plus the nearest markdown heading found
   above the table on the same page (if any).  Caption / description
   paragraphs are NOT copied — they already live in their own text chunk,
   and copying them would just reassemble the page we set out to split.
4. If a single row is still too big for one chunk, the row is split
   column-wise into sub-tables (each keeping its own header cells).
5. If even a single cell is too big, the cell text itself is split and each
   piece is emitted as a one-column table under the same header cell.

Only tables whose rows start with ``|`` and that have a ``|---|``-style
separator as the second line are recognised (the common GFM form, and what
docling & friends emit).
"""

import re
from copy import deepcopy
from typing import Iterable, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
_SEP_CELL_RE = re.compile(r":?-+:?")


def _split_cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in _CELL_SPLIT_RE.split(line)]


def _is_separator_row(line: str) -> bool:
    line = line.strip()
    if not line.startswith("|") or "-" not in line:
        return False
    cells = _split_cells(line)
    return bool(cells) and all(_SEP_CELL_RE.fullmatch(c) for c in cells if c)


def _parse_blocks(text: str) -> list[tuple[str, list[str]]]:
    """Return [('text', lines), ('table', lines), ...] preserving order."""
    lines = text.split("\n")
    blocks: list[tuple[str, list[str]]] = []
    text_buf: list[str] = []
    i = 0
    while i < len(lines):
        starts_table = (
            lines[i].lstrip().startswith("|")
            and i + 1 < len(lines)
            and _is_separator_row(lines[i + 1])
        )
        if starts_table:
            if text_buf:
                blocks.append(("text", text_buf))
                text_buf = []
            table = [lines[i], lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                table.append(lines[i])
                i += 1
            blocks.append(("table", table))
        else:
            text_buf.append(lines[i])
            i += 1
    if text_buf:
        blocks.append(("text", text_buf))
    return blocks


class MarkdownTableSplitter:
    """Drop-in replacement for RecursiveCharacterTextSplitter on markdown
    containing pipe-tables.

    Args:
        chunk_size: max characters per chunk (tables included).
        chunk_overlap: overlap for the plain-text parts.
        include_heading: copy the nearest markdown heading (``#``/``##``/...)
            found above the table into every chunk of that table.  Only the
            heading line is copied — caption/description paragraphs are not,
            they stay in their own text chunk.
        row_overlap: number of data rows repeated between consecutive
            chunks of the same table.
        normalize_cells: strip the column-alignment padding inside cells.
            Converted documents often pad every cell to the widest column,
            which can double or triple a table's size without adding any
            information.  Rendering is unchanged.
        text_splitter: optional pre-configured splitter for the non-table
            text; by default a RecursiveCharacterTextSplitter with the
            given chunk_size/chunk_overlap is used.
    """

    def __init__(
        self,
        chunk_size: int = 3000,
        chunk_overlap: int = 600,
        include_heading: bool = True,
        row_overlap: int = 0,
        normalize_cells: bool = True,
        text_splitter: Optional[RecursiveCharacterTextSplitter] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.include_heading = include_heading
        self.row_overlap = row_overlap
        self.normalize_cells = normalize_cells
        self.text_splitter = text_splitter or RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
        )

    # ------------------------------------------------------------------ API

    def split_text(self, text: str) -> list[str]:
        return [chunk for chunk, _ in self._split_text_tagged(text)]

    def split_documents(self, documents: Iterable[Document]) -> list[Document]:
        out: list[Document] = []
        for doc in documents:
            for chunk, is_table in self._split_text_tagged(doc.page_content):
                metadata = deepcopy(doc.metadata)
                metadata["contains_table"] = is_table
                out.append(Document(page_content=chunk, metadata=metadata))
        return out

    # ------------------------------------------------------------ internals

    def _split_text_tagged(self, text: str) -> list[tuple[str, bool]]:
        """Split into chunks, tagging each with whether it holds table rows."""
        chunks: list[tuple[str, bool]] = []
        prev_text_lines: list[str] = []
        for kind, block_lines in _parse_blocks(text):
            if kind == "text":
                block_text = "\n".join(block_lines).strip("\n")
                if block_text.strip():
                    chunks.extend(
                        (c, False) for c in self.text_splitter.split_text(block_text)
                    )
                prev_text_lines = block_lines
            else:
                context = self._heading_above(prev_text_lines)
                chunks.extend((c, True) for c in self._split_table(block_lines, context))
                prev_text_lines = []
        return [(c, t) for c, t in chunks if c.strip()]

    def _heading_above(self, prev_text_lines: list[str]) -> str:
        """Nearest markdown heading above the table, or '' if there is none."""
        if not self.include_heading:
            return ""
        for line in reversed(prev_text_lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped
        return ""

    def _split_table(self, table_lines: list[str], context: str) -> list[str]:
        header_raw, _sep_raw, *row_lines = table_lines
        header_cells = _split_cells(header_raw)
        n_cols = len(header_cells)

        if self.normalize_cells:
            rows = []
            for line in row_lines:
                cells = [re.sub(r"\s+", " ", c) for c in _split_cells(line)]
                rows.append("| " + " | ".join(cells) + " |")
            header = "| " + " | ".join(header_cells) + " |"
        else:
            rows = [line.rstrip() for line in row_lines]
            header = header_raw.rstrip()
        sep = "|" + "---|" * n_cols

        prefix = (context + "\n\n" if context else "") + header + "\n" + sep + "\n"

        chunks: list[str] = []
        current: list[str] = []

        def flush():
            if current:
                chunks.append(prefix + "\n".join(current))

        for row in rows:
            fits_alone = len(prefix) + len(row) <= self.chunk_size
            if not fits_alone:
                flush()
                current = []
                chunks.extend(self._split_wide_row(header_cells, row, context))
                continue
            size = len(prefix) + sum(len(r) + 1 for r in current) + len(row)
            if current and size > self.chunk_size:
                flush()
                carry = current[-self.row_overlap:] if self.row_overlap else []
                current = list(carry)
                if len(prefix) + sum(len(r) + 1 for r in current) + len(row) > self.chunk_size:
                    current = []
            current.append(row)
        flush()

        if not rows:  # header-only table, keep it whole
            chunks.append(prefix.rstrip("\n"))
        return chunks

    def _split_wide_row(
        self, header_cells: list[str], row: str, context: str
    ) -> list[str]:
        """Row too big for one chunk: split column-wise, then cell-wise."""
        row_cells = _split_cells(row)
        if self.normalize_cells:
            row_cells = [re.sub(r"\s+", " ", c) for c in row_cells]
        # tolerate ragged rows
        while len(row_cells) < len(header_cells):
            row_cells.append("")

        chunks: list[str] = []
        grp_h: list[str] = []
        grp_c: list[str] = []

        def make(hs: list[str], cs: list[str]) -> str:
            body = (
                "| " + " | ".join(hs) + " |\n"
                + "|" + "---|" * len(hs) + "\n"
                + "| " + " | ".join(cs) + " |"
            )
            return (context + "\n\n" + body) if context else body

        def flush_group():
            if grp_h:
                chunks.append(make(grp_h, grp_c))

        for h, c in zip(header_cells, row_cells):
            if len(make([h], [c])) > self.chunk_size:
                flush_group()
                grp_h, grp_c = [], []
                chunks.extend(self._split_wide_cell(h, c, context))
                continue
            if grp_h and len(make(grp_h + [h], grp_c + [c])) > self.chunk_size:
                flush_group()
                grp_h, grp_c = [], []
            grp_h.append(h)
            grp_c.append(c)
        flush_group()
        return chunks

    def _split_wide_cell(self, header_cell: str, cell: str, context: str) -> list[str]:
        """Single cell too big for one chunk: split its text, one table each."""
        overhead = len(
            ((context + "\n\n") if context else "")
            + "| " + header_cell + " |\n|---|\n|  |"
        )
        budget = max(self.chunk_size - overhead, 200)
        cell_splitter = RecursiveCharacterTextSplitter(
            chunk_size=budget,
            chunk_overlap=min(self.chunk_overlap, budget // 4),
            separators=["<br>", ". ", "; ", ", ", " ", ""],
        )
        pieces = cell_splitter.split_text(cell)
        out = []
        for piece in pieces:
            body = "| " + header_cell + " |\n|---|\n| " + piece.strip() + " |"
            out.append((context + "\n\n" + body) if context else body)
        return out

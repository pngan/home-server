#!/usr/bin/env python3
"""Generate the weekly CMYK nozzle maintenance page as an A4 PDF.

Page content: full-strength solid CMYK ink blocks plus horizontal and vertical
line grids for every ink - nothing else.

Usage:  python3 generate-nozzle-check.py [output.pdf] [--date STAMP|--no-date]
        [--ink-scale 1.0]

Pure stdlib so it can be re-run anywhere the page needs tweaking. Output is
deterministic (no timestamps) so regenerating does not dirty the repo.
"""

import argparse
import sys
import zlib
from datetime import datetime

PAGE_W = 595.276
PAGE_H = 841.89
MARGIN = 36.0
CONTENT_W = PAGE_W - 2 * MARGIN

INK_SCALE = 1.0

CYAN = (1.0, 0.0, 0.0, 0.0)
MAGENTA = (0.0, 1.0, 0.0, 0.0)
YELLOW = (0.0, 0.0, 1.0, 0.0)
BLACK = (0.0, 0.0, 0.0, 1.0)
NO_INK = (0.0, 0.0, 0.0, 0.0)

INKS = (
    ("C", "CYAN", CYAN),
    ("M", "MAGENTA", MAGENTA),
    ("Y", "YELLOW", YELLOW),
    ("K", "BLACK", BLACK),
)

GRID_WIDTHS = (1.0, 0.75, 0.5, 0.3, 0.2)


def num(*values):
    return " ".join(f"{v:.3f}".rstrip("0").rstrip(".") if v == int(v) else f"{v:.3f}" for v in values)


def y_from_top(top_offset):
    return PAGE_H - top_offset


def escape(text):
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class Content:
    def __init__(self, ink_scale=INK_SCALE):
        self.ops = []
        self.ink_scale = ink_scale

    def emit(self, op):
        self.ops.append(op)

    def fill(self, colour):
        scaled = tuple(v * self.ink_scale for v in colour)
        self.emit(f"/DeviceCMYK cs {num(*scaled)} k\n")

    def box(self, x, top_offset, width, height, colour):
        baseline = y_from_top(top_offset) - height
        self.emit(f"{num(x, baseline, width, height)} re\n")
        self.fill(colour)
        self.emit("f\n")

    def text(self, x, top_offset, size, text, colour=BLACK, bold=False):
        baseline = y_from_top(top_offset)
        self.fill(colour)
        self.emit(
            f"BT /{'F2' if bold else 'F1'} {num(size)} Tf "
            f"1 0 0 1 {num(x, baseline)} Tm ({escape(text)}) Tj ET\n"
        )

    def rule(self, x, top_offset, width, height, colour):
        self.box(x, top_offset, width, height, colour)

    def stroke(self, colour):
        scaled = tuple(v * self.ink_scale for v in colour)
        self.emit(f"/DeviceCMYK CS {num(*scaled)} K\n")

    def hairline(self, top_offset, colour=BLACK, dash="3 3", width=0.4):
        y = y_from_top(top_offset)
        self.emit(f"[{dash}] 0 d {num(width)} w\n")
        self.stroke(colour)
        self.emit(f"{num(MARGIN, y)} m {num(MARGIN + CONTENT_W, y)} l S [] 0 d\n")

    def to_bytes(self):
        return zlib.compress("".join(self.ops).encode("latin-1"), 9)


def draw_header(c, y, stamp=""):
    pct = round(c.ink_scale * 100)
    line = stamp if stamp else ""
    if pct < 100:
        line = f"{line} - {pct}% ink volume".strip(" -")
    c.text(MARGIN, y + 12, 14, "Epson EcoTank ET-16600 - nozzle maintenance page", bold=True)
    if line:
        c.text(MARGIN, y + 26, 9, line, BLACK, bold=True)
    c.box(MARGIN, y + 32, CONTENT_W, 0.8, BLACK)
    return y + 44


def draw_solid_patches(c, y, height=30.0, gap=6.0):
    c.text(MARGIN, y + 10, 8, "SOLID INK BLOCKS")
    y += 14
    col_w = (CONTENT_W - gap * 3) / 4
    for index, (code, name, colour) in enumerate(INKS):
        x = MARGIN + index * (col_w + gap)
        c.box(x, y, col_w, height, colour)
        label_colour = BLACK if colour is YELLOW else NO_INK
        c.text(x + 8, y + 13, 10, f"{code} - {name}", label_colour, bold=True)
        c.text(x + 8, y + 25, 7, f"{round(c.ink_scale * 100)}% ink", label_colour)
    return y + height + 10


def draw_horizontal_lines(c, y):
    c.text(MARGIN, y + 10, 8, "HORIZONTAL LINES - missing nozzles show as gaps along the line")
    y += 12
    label_w = 26.0
    for code, _name, colour in INKS:
        c.text(MARGIN, y + 8, 8, code, BLACK, bold=True)
        for offset, width in enumerate(GRID_WIDTHS):
            top = y + 2 + offset * 5
            c.rule(MARGIN + label_w, top, CONTENT_W - label_w, width, colour)
        y += len(GRID_WIDTHS) * 5 + 6
    return y + 2


def draw_vertical_lines(c, y, spacing=5.5, row_height=12.0):
    c.text(MARGIN, y + 10, 8, "VERTICAL LINE GRIDS - missing or deflected nozzles show as absent or ragged lines")
    y += 12
    group_gap = 8.0
    group_w = (CONTENT_W - group_gap * (len(GRID_WIDTHS) - 1)) / len(GRID_WIDTHS)
    lines_per_group = int(group_w / spacing)
    for code, _name, colour in INKS:
        c.text(MARGIN, y + 9, 8, code, BLACK, bold=True)
        row_top = y + 12
        for group_index, width in enumerate(GRID_WIDTHS):
            group_x = MARGIN + group_index * (group_w + group_gap)
            cursor = group_x
            for _ in range(lines_per_group):
                c.rule(cursor, row_top, width, row_height, colour)
                cursor += spacing
        y += 12 + row_height + 5
    return y + 2


def draw_cut_guide(c):
    c.text(MARGIN, PAGE_H / 2 - 11, 7, "cut here - bottom half is blank for reuse", BLACK)
    c.hairline(PAGE_H / 2)


def build_pdf(stamp="", ink_scale=INK_SCALE):
    c = Content(ink_scale)
    y = MARGIN
    y = draw_header(c, y, stamp)
    y = draw_solid_patches(c, y)
    y = draw_horizontal_lines(c, y)
    y = draw_vertical_lines(c, y)
    draw_cut_guide(c)

    contents = c.to_bytes()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.3f} {PAGE_H:.3f}] "
            f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"
        ).encode("latin-1"),
        b"<< /Length "
        + str(len(contents)).encode()
        + b" /Filter /FlateDecode >>\nstream\n"
        + contents
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Title (Epson ET-16600 nozzle maintenance page) /Creator (home-server) >>",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(number).encode() + b" 0 obj\n" + body + b"\nendobj\n"

    xref_offset = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode()
        + b" /Root 1 0 R /Info "
        + str(len(objects)).encode()
        + b" 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF\n"
    )
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="nozzle-check.pdf")
    parser.add_argument(
        "--date",
        default="now",
        help="printed-on stamp; 'now' uses the current local time (honours TZ), "
        "'' or --no-date leaves the stamp out",
    )
    parser.add_argument("--no-date", action="store_true", help="omit the printed-on stamp")
    parser.add_argument(
        "--ink-scale",
        type=float,
        default=INK_SCALE,
        help="ink volume for every element, 1.0 = full strength (default: %(default)s)",
    )
    args = parser.parse_args()

    if args.no_date or args.date == "":
        stamp = ""
    elif args.date == "now":
        stamp = f"Printed: {datetime.now().strftime('%a %Y-%m-%d %H:%M')}"
    else:
        stamp = f"Printed: {args.date}"

    with open(args.output, "wb") as handle:
        handle.write(build_pdf(stamp, args.ink_scale))
    print(f"wrote {args.output} ({len(stamp.encode())} byte stamp)")


if __name__ == "__main__":
    main()

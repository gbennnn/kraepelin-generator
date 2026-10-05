from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
import random
import io
import math

app = Flask(__name__)

# ---------- Helpers ----------

def validate_settings(data):
    rows = int(data.get("rows", 50))
    columns = int(data.get("columns", 20))
    min_num = int(data.get("min_num", 0))
    max_num = int(data.get("max_num", 9))
    font_size = float(data.get("font_size", 14))
    margin = float(data.get("margin", 10))
    row_spacing = float(data.get("row_spacing", 7))
    col_spacing = float(data.get("col_spacing", 10))
    title = str(data.get("title", "KRAEPELIN TEST")).strip()[:100]
    orientation = data.get("orientation", "portrait")

    if not 1 <= rows <= 200:
        raise ValueError("Jumlah baris harus 1-200.")
    if not 1 <= columns <= 60:
        raise ValueError("Jumlah kolom harus 1-60.")
    if not 0 <= min_num <= 9 or not 0 <= max_num <= 9:
        raise ValueError("Angka harus berada pada rentang 0-9.")
    if min_num > max_num:
        raise ValueError("Angka minimum tidak boleh lebih besar dari maksimum.")
    if not 6 <= font_size <= 30:
        raise ValueError("Ukuran font harus 6-30 pt.")
    if not 3 <= margin <= 30:
        raise ValueError("Margin harus 3-30 mm.")
    if not 3 <= row_spacing <= 20:
        raise ValueError("Jarak baris harus 3-20 mm.")
    if not 5 <= col_spacing <= 40:
        raise ValueError("Jarak kolom harus 5-40 mm.")
    if orientation not in ("portrait", "landscape"):
        raise ValueError("Orientasi tidak valid.")

    return {
        "rows": rows,
        "columns": columns,
        "min_num": min_num,
        "max_num": max_num,
        "font_size": font_size,
        "margin": margin,
        "row_spacing": row_spacing,
        "col_spacing": col_spacing,
        "title": title or "KRAEPELIN TEST",
        "orientation": orientation,
    }


def generate_numbers(rows, columns, min_num, max_num, seed=None):
    rng = random.Random(seed) if seed not in (None, "") else random.SystemRandom()
    return [
        [rng.randint(min_num, max_num) for _ in range(columns)]
        for _ in range(rows)
    ]


def make_pdf(settings, numbers):
    page_size = A4 if settings["orientation"] == "portrait" else landscape(A4)
    page_width, page_height = page_size

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)
    c.setTitle(settings["title"])

    margin = settings["margin"] * mm
    row_spacing = settings["row_spacing"] * mm
    col_spacing = settings["col_spacing"] * mm
    font_size = settings["font_size"]

    # Keep a small header area.
    header_height = 18 * mm
    usable_top = page_height - margin - header_height
    usable_bottom = margin

    rows = settings["rows"]
    cols = settings["columns"]

    # Automatic fallback if the requested grid does not fit.
    actual_row_spacing = row_spacing
    actual_col_spacing = col_spacing
    available_height = usable_top - usable_bottom
    available_width = page_width - (2 * margin)

    if rows > 1:
        max_row_step = available_height / (rows - 1)
        actual_row_spacing = min(row_spacing, max_row_step)

    if cols > 1:
        max_col_step = available_width / (cols - 1)
        actual_col_spacing = min(col_spacing, max_col_step)

    # Reduce font size only when necessary to fit.
    actual_font_size = font_size
    if rows > 1:
        estimated_height = (rows - 1) * actual_row_spacing + actual_font_size
        if estimated_height > available_height:
            actual_font_size = max(6, available_height / max(rows, 1) * 0.75)

    # Center columns on the page.
    grid_width = (cols - 1) * actual_col_spacing if cols > 1 else 0
    start_x = (page_width - grid_width) / 2

    # Center each page vertically within available area.
    grid_height = (rows - 1) * actual_row_spacing if rows > 1 else 0
    start_y = usable_top - max(0, (available_height - grid_height) / 2)

    # Header
    c.setFont("Helvetica-Bold", min(16, max(10, actual_font_size + 2)))
    title_width = stringWidth(settings["title"], "Helvetica-Bold",
                              min(16, max(10, actual_font_size + 2)))
    c.drawString((page_width - title_width) / 2, page_height - margin - 8 * mm, settings["title"])

    c.setFont("Helvetica", 7.5)
    meta = f"Range: {settings['min_num']}-{settings['max_num']}   |   {rows} baris × {cols} kolom"
    c.drawCentredString(page_width / 2, page_height - margin - 13 * mm, meta)

    # Numbers
    c.setFont("Helvetica-Bold", actual_font_size)
    for r in range(rows):
        y = start_y - r * actual_row_spacing
        for col in range(cols):
            x = start_x + col * actual_col_spacing
            value = str(numbers[r][col])
            text_width = stringWidth(value, "Helvetica-Bold", actual_font_size)
            c.drawString(x - text_width / 2, y, value)

    # Light footer
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(page_width / 2, 5 * mm, "Kraepelin Test Generator (https://kraepelin-generator.vercel.app/)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# ---------- Routes ----------

@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/generate")
def api_generate():
    try:
        settings = validate_settings(request.get_json(force=True))
        seed = request.get_json(force=True).get("seed")
        numbers = generate_numbers(
            settings["rows"],
            settings["columns"],
            settings["min_num"],
            settings["max_num"],
            seed
        )
        return jsonify({
            "success": True,
            "settings": settings,
            "numbers": numbers
        })
    except (ValueError, TypeError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@app.post("/api/pdf")
def api_pdf():
    try:
        data = request.get_json(force=True)
        settings = validate_settings(data)

        numbers = data.get("numbers")
        if not numbers:
            numbers = generate_numbers(
                settings["rows"],
                settings["columns"],
                settings["min_num"],
                settings["max_num"],
                data.get("seed")
            )

        # Basic dimension check to avoid malformed requests.
        if len(numbers) != settings["rows"] or any(
            len(row) != settings["columns"] for row in numbers
        ):
            raise ValueError("Data angka tidak sesuai dengan jumlah baris/kolom.")

        pdf = make_pdf(settings, numbers)

        safe_name = "".join(
            ch if ch.isalnum() or ch in " _-" else "_"
            for ch in settings["title"]
        ).strip() or "kraepelin_test"

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{safe_name}.pdf"
        )
    except (ValueError, TypeError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

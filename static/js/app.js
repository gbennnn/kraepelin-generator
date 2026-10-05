let currentNumbers = null;

const $ = (id) => document.getElementById(id);

function getSettings() {
    return {
        title: $("title").value,
        rows: Number($("rows").value),
        columns: Number($("columns").value),
        min_num: Number($("minNum").value),
        max_num: Number($("maxNum").value),
        font_size: Number($("fontSize").value),
        margin: Number($("margin").value),
        row_spacing: Number($("rowSpacing").value),
        col_spacing: Number($("colSpacing").value),
        orientation: $("orientation").value
    };
}

function showError(message) {
    const box = $("alertBox");
    box.textContent = message;
    box.classList.remove("d-none");
}

function hideError() {
    $("alertBox").classList.add("d-none");
}

function updateStats(settings) {
    $("statRows").textContent = settings.rows;
    $("statCols").textContent = settings.columns;
    $("statTotal").textContent = (settings.rows * settings.columns).toLocaleString("id-ID");
}

function renderPreview(numbers, settings) {
    $("emptyPreview").classList.add("d-none");
    $("previewWrapper").classList.remove("d-none");

    $("previewTitle").textContent = settings.title;
    $("previewMeta").textContent =
        `Range ${settings.min_num}–${settings.max_num} • ` +
        `${settings.rows} baris × ${settings.columns} kolom`;

    const grid = $("numberGrid");
    grid.innerHTML = "";

    // On screen preview, cap font for very large grids.
    const previewFont = Math.max(
        9,
        Math.min(20, 360 / Math.max(settings.columns, 10))
    );

    grid.style.gridTemplateColumns =
        `repeat(${settings.columns}, minmax(${Math.max(22, previewFont * 1.8)}px, 1fr))`;
    grid.style.fontSize = `${previewFont}px`;

    numbers.forEach(row => {
        row.forEach(value => {
            const cell = document.createElement("div");
            cell.className = "number-cell";
            cell.textContent = value;
            grid.appendChild(cell);
        });
    });

    $("statusBadge").className = "badge text-bg-success";
    $("statusBadge").textContent = "Siap";
    $("pdfBtn").disabled = false;

    updateStats(settings);
}

async function generateNumbers() {
    hideError();
    const settings = getSettings();

    $("generateBtn").disabled = true;
    $("generateBtn").textContent = "Generating...";

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Gagal membuat angka.");
        }

        currentNumbers = data.numbers;
        renderPreview(currentNumbers, data.settings);
    } catch (error) {
        showError(error.message);
        currentNumbers = null;
        $("pdfBtn").disabled = true;
    } finally {
        $("generateBtn").disabled = false;
        $("generateBtn").textContent = "Generate Angka";
    }
}

async function downloadPdf() {
    hideError();

    if (!currentNumbers) {
        showError("Silakan generate angka terlebih dahulu.");
        return;
    }

    const settings = getSettings();

    $("pdfBtn").disabled = true;
    $("pdfBtn").textContent = "Membuat PDF...";

    try {
        const response = await fetch("/api/pdf", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                ...settings,
                numbers: currentNumbers
            })
        });

        if (!response.ok) {
            let message = "Gagal membuat PDF.";
            try {
                const data = await response.json();
                message = data.message || message;
            } catch (_) {}
            throw new Error(message);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const anchor = document.createElement("a");
        anchor.href = url;

        const safeTitle = (settings.title || "kraepelin_test")
            .replace(/[^\w\s-]/g, "_")
            .trim();

        anchor.download = `${safeTitle || "kraepelin_test"}.pdf`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();

        URL.revokeObjectURL(url);
    } catch (error) {
        showError(error.message);
    } finally {
        $("pdfBtn").disabled = false;
        $("pdfBtn").textContent = "Download PDF A4";
    }
}

document.querySelectorAll(".preset").forEach(button => {
    button.addEventListener("click", () => {
        $("minNum").value = button.dataset.min;
        $("maxNum").value = button.dataset.max;
    });
});

$("generateBtn").addEventListener("click", generateNumbers);
$("pdfBtn").addEventListener("click", downloadPdf);

$("settingsForm").addEventListener("submit", (event) => {
    event.preventDefault();
    generateNumbers();
});

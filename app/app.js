(() => {
  "use strict";

  const DATA_PATHS = {
    municipalities: "../data/master/01_municipalities_master.csv",
    municipalityResearch: "../data/research/04_municipalities_research.csv",
    categories: "../data/research/02_categories_master.csv"
  };

  const select = document.getElementById("municipalitySelect");
  const presentationButton = document.getElementById("presentationButton");
  const municipalityName = document.getElementById("municipalityName");
  const statusText = document.getElementById("statusText");
  const bucketGrid = document.getElementById("bucketGrid");

  let municipalitiesById = new Map();
  let bucketsByMunicipality = new Map();

  function parseCsv(text) {
    const rows = [];
    let row = [];
    let field = "";
    let quoted = false;

    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      const next = text[i + 1];

      if (quoted) {
        if (char === '"' && next === '"') {
          field += '"';
          i += 1;
        } else if (char === '"') {
          quoted = false;
        } else {
          field += char;
        }
        continue;
      }

      if (char === '"') {
        quoted = true;
      } else if (char === ',') {
        row.push(field);
        field = "";
      } else if (char === '\n') {
        row.push(field.replace(/\r$/, ""));
        rows.push(row);
        row = [];
        field = "";
      } else {
        field += char;
      }
    }

    if (field.length > 0 || row.length > 0) {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
    }

    if (rows.length === 0) return [];

    const headers = rows[0].map((value, index) => {
      const clean = value.trim();
      return index === 0 ? clean.replace(/^\uFEFF/, "") : clean;
    });

    return rows.slice(1)
      .filter((values) => values.some((value) => value.trim() !== ""))
      .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
  }

  function numericOrder(value) {
    const number = Number.parseFloat(value);
    return Number.isFinite(number) ? number : Number.MAX_SAFE_INTEGER;
  }

  function displayColumns(count) {
    if (count <= 2) return count || 1;
    if (count <= 4) return 2;
    if (count <= 6) return 3;
    if (count <= 8) return 4;
    if (count <= 12) return 4;
    return 5;
  }

  function buildData(municipalities, municipalityResearch, categories) {
    municipalitiesById = new Map(
      municipalities.map((row) => [row.municipality_id.trim(), row])
    );

    const qaPassedIds = new Set(
      municipalityResearch
        .filter((row) => row["確認ステータス"]?.trim() === "QA_PASSED")
        .map((row) => row.municipality_id?.trim())
        .filter(Boolean)
    );

    const eligible = categories.filter((row) => {
      const id = row.municipality_id?.trim();
      return id &&
        qaPassedIds.has(id) &&
        row.category_id?.trim() &&
        row["自治体正式名称"]?.trim() &&
        row.ui_role?.trim() === "SORT_BUCKET" &&
        row.rule_status?.trim() === "CURRENT";
    });

    bucketsByMunicipality = new Map();
    for (const row of eligible) {
      const id = row.municipality_id.trim();
      if (!bucketsByMunicipality.has(id)) bucketsByMunicipality.set(id, []);
      bucketsByMunicipality.get(id).push(row);
    }

    for (const rows of bucketsByMunicipality.values()) {
      rows.sort((a, b) => {
        const byOrder = numericOrder(a["表示順"]) - numericOrder(b["表示順"]);
        if (byOrder !== 0) return byOrder;
        return a.category_id.localeCompare(b.category_id, "ja");
      });
    }
  }

  function municipalityLabel(id) {
    const row = municipalitiesById.get(id);
    if (!row) return id;
    return `${row["都道府県"] ?? ""} ${row["市町村"] ?? ""}`.trim();
  }

  function populateMunicipalitySelect() {
    const ids = [...bucketsByMunicipality.keys()]
      .filter((id) => municipalitiesById.has(id))
      .sort((a, b) => {
        const aa = municipalitiesById.get(a);
        const bb = municipalitiesById.get(b);
        const prefecture = (aa["都道府県"] ?? "").localeCompare(bb["都道府県"] ?? "", "ja");
        if (prefecture !== 0) return prefecture;
        return (aa["市町村"] ?? "").localeCompare(bb["市町村"] ?? "", "ja");
      });

    select.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "自治体を選択";
    select.appendChild(placeholder);

    for (const id of ids) {
      const option = document.createElement("option");
      option.value = id;
      option.textContent = municipalityLabel(id);
      select.appendChild(option);
    }

    select.disabled = false;
    statusText.textContent = `${ids.length}自治体を選択できます。`;
  }

  function renderBuckets(id) {
    bucketGrid.replaceChildren();

    if (!id) {
      municipalityName.textContent = "自治体を選択してください";
      statusText.textContent = "選択すると、その自治体の仕分け用ボックスだけを表示します。";
      presentationButton.disabled = true;
      return;
    }

    const rows = bucketsByMunicipality.get(id) ?? [];
    municipalityName.textContent = municipalityLabel(id);
    statusText.textContent = `${rows.length}区分`;
    presentationButton.disabled = rows.length === 0;
    document.documentElement.style.setProperty("--bucket-columns", String(displayColumns(rows.length)));

    if (rows.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "投影できる分別区分がありません。";
      bucketGrid.appendChild(empty);
      return;
    }

    for (const row of rows) {
      const box = document.createElement("div");
      box.className = "bucket";
      box.dataset.categoryId = row.category_id;
      box.textContent = row["自治体正式名称"].trim();
      bucketGrid.appendChild(box);
    }
  }

  async function enterPresentation() {
    if (!select.value) return;
    try {
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      } else {
        document.body.classList.add("presentation-mode");
      }
    } catch (error) {
      console.warn("Fullscreen API unavailable; using presentation layout only.", error);
      document.body.classList.add("presentation-mode");
    }
  }

  async function load() {
    try {
      const [municipalityResponse, researchResponse, categoryResponse] = await Promise.all([
        fetch(DATA_PATHS.municipalities, { cache: "no-store" }),
        fetch(DATA_PATHS.municipalityResearch, { cache: "no-store" }),
        fetch(DATA_PATHS.categories, { cache: "no-store" })
      ]);

      if (!municipalityResponse.ok || !researchResponse.ok || !categoryResponse.ok) {
        throw new Error(
          `data load failed: municipalities=${municipalityResponse.status}, ` +
          `research=${researchResponse.status}, categories=${categoryResponse.status}`
        );
      }

      const [municipalityText, researchText, categoryText] = await Promise.all([
        municipalityResponse.text(),
        researchResponse.text(),
        categoryResponse.text()
      ]);

      buildData(
        parseCsv(municipalityText),
        parseCsv(researchText),
        parseCsv(categoryText)
      );
      populateMunicipalitySelect();
      renderBuckets("");
    } catch (error) {
      console.error(error);
      select.disabled = true;
      presentationButton.disabled = true;
      municipalityName.textContent = "データを読み込めませんでした";
      statusText.textContent = "CSVの配置と公開パスを確認してください。";
    }
  }

  select.addEventListener("change", () => renderBuckets(select.value));
  presentationButton.addEventListener("click", enterPresentation);

  document.addEventListener("fullscreenchange", () => {
    document.body.classList.toggle("presentation-mode", Boolean(document.fullscreenElement));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !document.fullscreenElement) {
      document.body.classList.remove("presentation-mode");
    }
  });

  load();
})();

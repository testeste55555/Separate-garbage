(() => {
  "use strict";

  const DATA_PATHS = {
    companyMapping: "../data/app/company_municipality_mapping.csv",
    lessonScope: "../data/app/lesson_mode_app_ready_scope.csv"
  };

  const APP_READY = "APP_READY";
  const selectionModeSelect = document.getElementById("selectionModeSelect");
  const companyControl = document.getElementById("companyControl");
  const companySelect = document.getElementById("companySelect");
  const companySiteControl = document.getElementById("companySiteControl");
  const companySiteSelect = document.getElementById("companySiteSelect");
  const municipalityControl = document.getElementById("municipalityControl");
  const municipalitySelect = document.getElementById("municipalitySelect");
  const lessonVariantGroup = document.getElementById("lessonVariantGroup");

  if (!selectionModeSelect || !companyControl || !companySelect || !companySiteControl ||
      !companySiteSelect || !municipalityControl || !municipalitySelect || !lessonVariantGroup) {
    console.warn("Company selector controls are unavailable.");
    return;
  }

  let companyRows = [];
  let appReadyMunicipalities = new Set();
  let companiesById = new Map();

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
      if (char === '"') quoted = true;
      else if (char === ",") {
        row.push(field);
        field = "";
      } else if (char === "\n") {
        row.push(field.replace(/\r$/, ""));
        rows.push(row);
        row = [];
        field = "";
      } else field += char;
    }
    if (field.length > 0 || row.length > 0) {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
    }
    if (!rows.length) return [];
    const headers = rows[0].map((value, index) => {
      const clean = value.trim();
      return index === 0 ? clean.replace(/^\uFEFF/, "") : clean;
    });
    return rows.slice(1)
      .filter((values) => values.some((value) => value.trim() !== ""))
      .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
  }

  function isTrue(value) {
    return value?.trim().toUpperCase() === "TRUE";
  }

  function rowAvailable(row) {
    return row.mapping_status?.trim() === "CONFIRMED" && isTrue(row.active) &&
      appReadyMunicipalities.has(row.municipality_id?.trim());
  }

  function companySortName(row) {
    return (row.company_normalized_name?.trim() || row.company_display_name?.trim() || row.company_id?.trim() || "");
  }

  function companyOptionLabel(rows) {
    const row = rows[0];
    const base = row.company_display_name?.trim() || row.company_id?.trim();
    if (rows.length === 1) {
      const site = row.site_display_name?.trim();
      if (site && !["本社", "本店"].includes(site)) return `${base}（${site}）`;
    }
    return base;
  }

  function clearSiteControl() {
    companySiteSelect.replaceChildren();
    companySiteControl.hidden = true;
    companySiteSelect.disabled = true;
  }

  function applyCompanySite(row) {
    const municipalityId = row?.municipality_id?.trim();
    if (!municipalityId || !rowAvailable(row)) return;
    const municipalityOption = [...municipalitySelect.options].find((option) => option.value === municipalityId);
    if (!municipalityOption) {
      console.warn("Company mapping points to a municipality unavailable in the app.", municipalityId);
      return;
    }

    municipalitySelect.value = municipalityId;
    municipalitySelect.dispatchEvent(new Event("change", { bubbles: true }));

    const variantGroupId = row.lesson_variant_group_id?.trim();
    if (variantGroupId) {
      const variantOption = [...lessonVariantGroup.options].find((option) => option.value === variantGroupId);
      if (variantOption) {
        lessonVariantGroup.value = variantGroupId;
        lessonVariantGroup.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  }

  function populateSiteSelect(rows) {
    clearSiteControl();
    if (rows.length <= 1) {
      if (rows.length === 1) applyCompanySite(rows[0]);
      return;
    }

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "拠点を選択";
    companySiteSelect.appendChild(placeholder);

    for (const row of rows) {
      const option = document.createElement("option");
      option.value = row.site_id.trim();
      option.textContent = rowAvailable(row)
        ? row.site_display_name.trim()
        : `${row.site_display_name.trim()}（準備中）`;
      option.disabled = !rowAvailable(row);
      companySiteSelect.appendChild(option);
    }
    companySiteControl.hidden = false;
    companySiteSelect.disabled = false;
  }

  function populateCompanySelect() {
    companySelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "会社を選択";
    companySelect.appendChild(placeholder);

    const groups = [...companiesById.entries()].sort(([, aRows], [, bRows]) =>
      companySortName(aRows[0]).localeCompare(companySortName(bRows[0]), "ja")
    );

    for (const [companyId, rows] of groups) {
      const option = document.createElement("option");
      const available = rows.some(rowAvailable);
      option.value = companyId;
      option.textContent = available ? companyOptionLabel(rows) : `${companyOptionLabel(rows)}（準備中）`;
      option.disabled = !available;
      companySelect.appendChild(option);
    }
    companySelect.disabled = false;
  }

  function setSelectionMode(mode) {
    const companyMode = mode === "COMPANY";
    companyControl.hidden = !companyMode;
    municipalityControl.hidden = companyMode;
    if (!companyMode) clearSiteControl();
  }

  async function fetchText(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`company selector data load failed: ${path} (${response.status})`);
    return response.text();
  }

  function enableWhenMunicipalityReady() {
    const ready = () => !municipalitySelect.disabled && municipalitySelect.options.length > 1;
    if (ready()) {
      selectionModeSelect.disabled = false;
      return;
    }
    const observer = new MutationObserver(() => {
      if (!ready()) return;
      observer.disconnect();
      selectionModeSelect.disabled = false;
    });
    observer.observe(municipalitySelect, { childList: true, attributes: true, attributeFilter: ["disabled"] });
  }

  async function load() {
    try {
      const [companyText, scopeText] = await Promise.all([
        fetchText(DATA_PATHS.companyMapping),
        fetchText(DATA_PATHS.lessonScope)
      ]);
      companyRows = parseCsv(companyText)
        .filter((row) => row.company_id?.trim() && row.site_id?.trim() && row.mapping_status?.trim() === "CONFIRMED");
      appReadyMunicipalities = new Set(
        parseCsv(scopeText)
          .filter((row) => row.scoring_status?.trim() === APP_READY)
          .map((row) => row.municipality_id?.trim())
          .filter(Boolean)
      );
      companiesById = new Map();
      for (const row of companyRows) {
        const companyId = row.company_id.trim();
        if (!companiesById.has(companyId)) companiesById.set(companyId, []);
        companiesById.get(companyId).push(row);
      }
      for (const rows of companiesById.values()) {
        rows.sort((a, b) => Number(a.display_order || 9999) - Number(b.display_order || 9999));
      }
      populateCompanySelect();
      enableWhenMunicipalityReady();
    } catch (error) {
      console.error(error);
      companySelect.disabled = true;
      selectionModeSelect.disabled = false;
    }
  }

  selectionModeSelect.addEventListener("change", () => {
    setSelectionMode(selectionModeSelect.value);
    if (selectionModeSelect.value === "COMPANY") {
      municipalitySelect.value = "";
      municipalitySelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });

  companySelect.addEventListener("change", () => {
    clearSiteControl();
    const rows = companiesById.get(companySelect.value) ?? [];
    if (!rows.length) return;
    populateSiteSelect(rows);
  });

  companySiteSelect.addEventListener("change", () => {
    const rows = companiesById.get(companySelect.value) ?? [];
    const row = rows.find((candidate) => candidate.site_id?.trim() === companySiteSelect.value);
    if (row) applyCompanySite(row);
  });

  setSelectionMode("MUNICIPALITY");
  load();
})();

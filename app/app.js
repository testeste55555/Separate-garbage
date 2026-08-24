(() => {
  "use strict";

  const DATA_PATHS = {
    municipalities: "../data/master/01_municipalities_master.csv",
    municipalityResearch: "../data/research/04_municipalities_research.csv",
    categories: "../data/research/02_categories_master.csv",
    styleProjection: "../data/style_research/08_style_ui_projection.csv",
    itemAssets: "../data/app/item_image_assets.csv",
    itemMappingPilot: "../data/app/item_image_mapping_pilot_top8.csv"
  };

  const MUNICIPAL_SCOPE = "MUNICIPALITY_WIDE";
  const OFFICIAL_STYLE_STATUSES = new Set(["OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"]);
  const HEX_RE = /^#[0-9A-Fa-f]{6}$/;
  const SAFE_ID_RE = /^[A-Za-z0-9_-]+$/;
  const SAFE_IMAGE_RE = /^I\d{3}_[A-Za-z0-9_]+\.png$/;
  const ONLINE_CLASS_MODE = "ONLINE_CLASS";
  const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS";

  const lessonModeSelect = document.getElementById("lessonModeSelect");
  const select = document.getElementById("municipalitySelect");
  const presentationButton = document.getElementById("presentationButton");
  const municipalityName = document.getElementById("municipalityName");
  const statusText = document.getElementById("statusText");
  const bucketGrid = document.getElementById("bucketGrid");
  const practicePanel = document.getElementById("practicePanel");
  const practiceUnavailable = document.getElementById("practiceUnavailable");
  const practiceProgress = document.getElementById("practiceProgress");
  const itemCard = document.getElementById("itemCard");
  const itemImage = document.getElementById("itemImage");
  const practiceInstruction = document.getElementById("practiceInstruction");
  const answerFeedback = document.getElementById("answerFeedback");
  const nextItemButton = document.getElementById("nextItemButton");

  let municipalitiesById = new Map();
  let categoryByKey = new Map();
  let bucketsByMunicipality = new Map();
  let stylesByBucket = new Map();
  let assetsByItem = new Map();
  let itemsByMunicipality = new Map();
  let unresolvedByMunicipality = new Map();
  let activeItems = [];
  let activeItemIndex = 0;
  let practiceFinished = false;

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
      } else if (char === ",") {
        row.push(field);
        field = "";
      } else if (char === "\n") {
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
    if (count <= 12) return 4;
    return 5;
  }

  function categoryKey(municipalityId, categoryId) {
    return `${municipalityId}::${categoryId}`;
  }

  function styleKey(municipalityId, categoryId, scope = MUNICIPAL_SCOPE) {
    return `${municipalityId}::${scope}::${categoryId}`;
  }

  function buildData(municipalities, municipalityResearch, categories) {
    municipalitiesById = new Map(municipalities.map((row) => [row.municipality_id.trim(), row]));
    categoryByKey = new Map(
      categories
        .filter((row) => row.municipality_id?.trim() && row.category_id?.trim())
        .map((row) => [categoryKey(row.municipality_id.trim(), row.category_id.trim()), row])
    );

    const qaPassedIds = new Set(
      municipalityResearch
        .filter((row) => row["確認ステータス"]?.trim() === "QA_PASSED")
        .map((row) => row.municipality_id?.trim())
        .filter(Boolean)
    );

    const eligible = categories.filter((row) => {
      const id = row.municipality_id?.trim();
      return id && qaPassedIds.has(id) && row.category_id?.trim() && row["自治体正式名称"]?.trim() &&
        row.ui_role?.trim() === "SORT_BUCKET" && row.rule_status?.trim() === "CURRENT";
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
        return byOrder || a.category_id.localeCompare(b.category_id, "ja");
      });
    }
  }

  function buildStyleData(styleRows) {
    stylesByBucket = new Map();
    for (const row of styleRows) {
      const municipalityId = row.municipality_id?.trim();
      const categoryId = row.category_id?.trim();
      const scope = row.district_scope?.trim();
      if (!municipalityId || !categoryId || scope !== MUNICIPAL_SCOPE) continue;
      stylesByBucket.set(styleKey(municipalityId, categoryId, scope), row);
    }
  }

  function findSortBucket(municipalityId, categoryId) {
    let currentId = categoryId;
    const visited = new Set();
    while (currentId && !visited.has(currentId)) {
      visited.add(currentId);
      const row = categoryByKey.get(categoryKey(municipalityId, currentId));
      if (!row || row.rule_status?.trim() !== "CURRENT") return null;
      if (row.ui_role?.trim() === "SORT_BUCKET") return row;
      currentId = row.parent_category_id?.trim();
    }
    return null;
  }

  function buildItemData(assetRows, mappingRows) {
    assetsByItem = new Map(
      assetRows
        .filter((row) => row.asset_status?.trim() === "CONFIRMED")
        .map((row) => [row.internal_item_id?.trim(), row])
    );
    itemsByMunicipality = new Map();
    unresolvedByMunicipality = new Map();

    for (const row of mappingRows) {
      const municipalityId = row.municipality_id?.trim();
      if (!municipalityId) continue;
      if (row.review_status?.trim() !== "VERIFIED") {
        unresolvedByMunicipality.set(municipalityId, (unresolvedByMunicipality.get(municipalityId) ?? 0) + 1);
        continue;
      }

      const itemId = row.internal_item_id?.trim();
      const asset = assetsByItem.get(itemId);
      const sortBucket = findSortBucket(municipalityId, row.category_id?.trim());
      const imageFile = asset?.image_file?.trim();
      if (!asset || !sortBucket || !SAFE_IMAGE_RE.test(imageFile ?? "") || !imageFile.startsWith(`${itemId}_`)) {
        console.warn("A verified Pilot row could not be projected safely.", municipalityId, itemId);
        continue;
      }

      const item = {
        ...row,
        imageFile,
        uiCategoryId: sortBucket.category_id.trim(),
        uiCategoryName: sortBucket["自治体正式名称"].trim()
      };
      if (!itemsByMunicipality.has(municipalityId)) itemsByMunicipality.set(municipalityId, []);
      itemsByMunicipality.get(municipalityId).push(item);
    }
    for (const rows of itemsByMunicipality.values()) {
      rows.sort((a, b) => numericOrder(a.pair_order) - numericOrder(b.pair_order));
    }
  }

  function findAppStyleSheet() {
    return [...document.styleSheets].find((sheet) => {
      if (!sheet.href) return false;
      try {
        const url = new URL(sheet.href, window.location.href);
        return url.origin === window.location.origin && url.pathname.endsWith("/styles.css");
      } catch (_error) {
        return false;
      }
    });
  }

  function installOfficialStyleRules() {
    const sheet = findAppStyleSheet();
    if (!sheet) return;
    for (const row of stylesByBucket.values()) {
      const status = row.color_status?.trim();
      const municipalityId = row.municipality_id?.trim();
      const categoryId = row.category_id?.trim();
      const background = row.display_color?.trim();
      const border = row.border_color?.trim();
      const text = row.text_color?.trim();
      if (!OFFICIAL_STYLE_STATUSES.has(status)) continue;
      if (!SAFE_ID_RE.test(municipalityId ?? "") || !SAFE_ID_RE.test(categoryId ?? "")) continue;
      if (!HEX_RE.test(background ?? "") || !HEX_RE.test(border ?? "") || !HEX_RE.test(text ?? "")) continue;
      const selector = `.bucket[data-municipality-id="${municipalityId}"][data-category-id="${categoryId}"]`;
      try {
        sheet.insertRule(`${selector} { background-color: ${background}; border-color: ${border}; color: ${text}; }`, sheet.cssRules.length);
      } catch (error) {
        console.warn("Could not install municipality style rule.", error);
      }
    }
  }

  function municipalityLabel(id) {
    const row = municipalitiesById.get(id);
    return row ? `${row["都道府県"] ?? ""} ${row["市町村"] ?? ""}`.trim() : id;
  }

  function populateLessonModeSelect() {
    lessonModeSelect.replaceChildren();
    const modes = [
      ["", "授業モードを選択"],
      [ONLINE_CLASS_MODE, "オンライン授業"],
      [IN_PERSON_CLASS_MODE, "対面授業"]
    ];
    for (const [value, label] of modes) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      lessonModeSelect.appendChild(option);
    }
    lessonModeSelect.disabled = false;
  }

  function populateMunicipalitySelect() {
    const ids = [...bucketsByMunicipality.keys()]
      .filter((id) => municipalitiesById.has(id))
      .sort((a, b) => {
        const aa = municipalitiesById.get(a);
        const bb = municipalitiesById.get(b);
        return (aa["都道府県"] ?? "").localeCompare(bb["都道府県"] ?? "", "ja") ||
          (aa["市町村"] ?? "").localeCompare(bb["市町村"] ?? "", "ja");
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
    statusText.textContent = `授業モードと自治体を選択してください。${ids.length}自治体を表示できます。`;
  }

  function styleNote(status) {
    if (status === "OFFICIAL_CONFIRMED") return "公式指定色";
    if (status === "OFFICIAL_DERIVED") return "公式資料の色（近似）";
    return "標準表示";
  }

  function clearBucketAnswerState() {
    for (const box of bucketGrid.querySelectorAll(".bucket")) {
      delete box.dataset.answerState;
      if (box instanceof HTMLButtonElement) box.disabled = false;
    }
  }

  function renderBuckets(id) {
    bucketGrid.replaceChildren();
    if (!id) {
      bucketGrid.dataset.columns = "1";
      return;
    }

    const rows = bucketsByMunicipality.get(id) ?? [];
    const interactive = activeItems.length > 0;
    bucketGrid.dataset.columns = String(displayColumns(rows.length));
    if (rows.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "投影できる分別区分がありません。";
      bucketGrid.appendChild(empty);
      return;
    }

    for (const row of rows) {
      const categoryId = row.category_id.trim();
      const label = row["自治体正式名称"].trim();
      const style = stylesByBucket.get(styleKey(id, categoryId));
      const status = style?.color_status?.trim() || "NO_STYLE_RESEARCH";
      const box = document.createElement(interactive ? "button" : "div");
      if (box instanceof HTMLButtonElement) box.type = "button";
      box.className = "bucket";
      box.dataset.municipalityId = id;
      box.dataset.categoryId = categoryId;
      box.dataset.styleStatus = status;
      box.setAttribute("aria-label", `${label}。${styleNote(status)}`);

      const name = document.createElement("span");
      name.className = "bucket__name";
      name.textContent = label;
      box.appendChild(name);

      const length = [...label].length;
      if (length >= 13) box.classList.add("bucket--long");
      else if (length >= 7) box.classList.add("bucket--compact");
      box.classList.add(OFFICIAL_STYLE_STATUSES.has(status) ? "bucket--official-style" : "bucket--neutral-style");
      if (interactive) {
        box.classList.add("bucket--interactive");
        box.addEventListener("click", () => handleBucketChoice(box, categoryId));
      }
      bucketGrid.appendChild(box);
    }
  }

  function resetAnswer() {
    answerFeedback.textContent = "";
    answerFeedback.className = "answer-feedback";
    nextItemButton.hidden = true;
    practiceInstruction.textContent = "画像を見て、下の分別箱から1つ選んでください。";
    clearBucketAnswerState();
  }

  function renderPracticeItem() {
    practiceFinished = false;
    const item = activeItems[activeItemIndex];
    practiceProgress.textContent = `${activeItemIndex + 1} / ${activeItems.length}`;
    itemCard.hidden = false;
    itemImage.hidden = false;
    itemImage.src = `./assets/items/${item.imageFile}`;
    itemImage.alt = "仕分ける品目の画像";
    practicePanel.classList.remove("practice-panel--complete");
    nextItemButton.textContent = activeItemIndex + 1 === activeItems.length ? "結果を見る" : "次の品目";
    resetAnswer();
  }

  function showPracticeCompletion() {
    practiceFinished = true;
    itemCard.hidden = true;
    itemImage.hidden = true;
    practiceProgress.textContent = "完了";
    practiceInstruction.textContent = "";
    answerFeedback.textContent = "すべて正解です。";
    answerFeedback.className = "answer-feedback answer-feedback--correct";
    nextItemButton.textContent = "もう一度";
    nextItemButton.hidden = false;
    practicePanel.classList.add("practice-panel--complete");
    for (const box of bucketGrid.querySelectorAll("button.bucket")) box.disabled = true;
  }

  function handleBucketChoice(box, categoryId) {
    if (practiceFinished || !activeItems.length) return;
    const item = activeItems[activeItemIndex];
    for (const candidate of bucketGrid.querySelectorAll(".bucket")) delete candidate.dataset.answerState;

    if (categoryId !== item.uiCategoryId) {
      box.dataset.answerState = "incorrect";
      answerFeedback.textContent = "ちがいます。もう一度。";
      answerFeedback.className = "answer-feedback answer-feedback--incorrect";
      return;
    }

    box.dataset.answerState = "correct";
    answerFeedback.textContent = "正解です。";
    answerFeedback.className = "answer-feedback answer-feedback--correct";
    nextItemButton.hidden = false;
    practiceInstruction.textContent = "";
    for (const candidate of bucketGrid.querySelectorAll("button.bucket")) candidate.disabled = true;
    nextItemButton.focus();
  }

  function renderMunicipality(id) {
    const lessonMode = lessonModeSelect.value;
    const availableItems = id ? [...(itemsByMunicipality.get(id) ?? [])] : [];
    activeItems = lessonMode === ONLINE_CLASS_MODE ? availableItems : [];
    activeItemIndex = 0;
    practiceFinished = false;
    practicePanel.hidden = activeItems.length === 0;
    practiceUnavailable.hidden = true;

    if (!id) {
      municipalityName.textContent = "自治体を選択してください";
      statusText.textContent = lessonMode
        ? "自治体を選択してください。"
        : "授業モードと自治体を選択してください。";
      presentationButton.disabled = true;
      renderBuckets("");
      return;
    }

    const rows = bucketsByMunicipality.get(id) ?? [];
    const unresolved = unresolvedByMunicipality.get(id) ?? 0;
    municipalityName.textContent = municipalityLabel(id);
    presentationButton.disabled = rows.length === 0 || !lessonMode;

    if (!lessonMode) {
      statusText.textContent = `${rows.length}区分・授業モードを選択してください。`;
      practiceUnavailable.hidden = false;
      practiceUnavailable.textContent = "オンライン授業または対面授業を選択してください。";
      renderBuckets(id);
    } else if (lessonMode === IN_PERSON_CLASS_MODE) {
      statusText.textContent = `${rows.length}区分・対面授業モード`;
      renderBuckets(id);
    } else if (activeItems.length) {
      const holdText = unresolved ? `・確認中${unresolved}品目は出題対象外` : "";
      statusText.textContent = `${rows.length}区分・オンライン授業モード・画像練習${activeItems.length}問${holdText}`;
      renderBuckets(id);
      renderPracticeItem();
    } else {
      statusText.textContent = `${rows.length}区分・オンライン授業モード`;
      practiceUnavailable.hidden = false;
      practiceUnavailable.textContent = "この自治体は画像仕分けPilotの対象外です。";
      renderBuckets(id);
    }
  }

  async function enterPresentation() {
    if (!select.value) return;
    try {
      if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
      else document.body.classList.add("presentation-mode");
    } catch (error) {
      console.warn("Fullscreen API unavailable; using presentation layout only.", error);
      document.body.classList.add("presentation-mode");
    }
  }

  async function load() {
    try {
      const requests = Object.values(DATA_PATHS).map((path) => fetch(path, { cache: "no-store" }));
      const responses = await Promise.all(requests);
      const failed = responses.find((response) => !response.ok);
      if (failed) throw new Error(`data load failed: ${failed.url} (${failed.status})`);
      const [municipalityText, researchText, categoryText, styleText, assetText, mappingText] =
        await Promise.all(responses.map((response) => response.text()));

      buildData(parseCsv(municipalityText), parseCsv(researchText), parseCsv(categoryText));
      buildStyleData(parseCsv(styleText));
      buildItemData(parseCsv(assetText), parseCsv(mappingText));
      installOfficialStyleRules();
      populateLessonModeSelect();
      populateMunicipalitySelect();
      renderMunicipality("");
    } catch (error) {
      console.error(error);
      lessonModeSelect.disabled = true;
      select.disabled = true;
      presentationButton.disabled = true;
      municipalityName.textContent = "データを読み込めませんでした";
      statusText.textContent = "CSVの配置と公開パスを確認してください。";
    }
  }

  lessonModeSelect.addEventListener("change", () => renderMunicipality(select.value));
  select.addEventListener("change", () => renderMunicipality(select.value));
  presentationButton.addEventListener("click", enterPresentation);
  nextItemButton.addEventListener("click", () => {
    if (practiceFinished) {
      activeItemIndex = 0;
      renderPracticeItem();
      return;
    }
    if (activeItemIndex + 1 < activeItems.length) {
      activeItemIndex += 1;
      renderPracticeItem();
    } else {
      showPracticeCompletion();
    }
  });

  document.addEventListener("fullscreenchange", () => {
    document.body.classList.toggle("presentation-mode", Boolean(document.fullscreenElement));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !document.fullscreenElement) document.body.classList.remove("presentation-mode");
  });

  load();
})();

(() => {
  "use strict";

  const DATA_PATHS = {
    municipalities: "../data/master/01_municipalities_master.csv",
    municipalityResearch: "../data/research/04_municipalities_research.csv",
    categories: "../data/research/02_categories_master.csv",
    styleProjection: "../data/style_research/08_style_ui_projection.csv",
    itemAssets: "../data/app/item_image_assets.csv",
    imageMappingPilot: "../data/app/item_image_mapping_pilot_top8.csv",
    lessonScope: "../data/app/lesson_mode_app_ready_scope.csv",
    lessonTeachingBoxes: "../data/app/lesson_teaching_boxes.csv",
    lessonItemScoringProjection: "../data/app/lesson_item_scoring_projection.csv",
    districtScopes: "../data/app/district_scopes.csv",
    lessonVariantGroups: "../data/app/lesson_variant_groups.csv",
    lessonVariantBoxes: "../data/app/lesson_variant_teaching_boxes.csv",
    lessonVariantScoring: "../data/app/lesson_variant_item_scoring.csv",
    lessonSupplementalScoring: "../data/app/lesson_supplemental_item_scoring.csv",
    lessonSupplementalBoxes: "../data/app/lesson_supplemental_teaching_boxes.csv"
  };

  const MUNICIPAL_SCOPE = "MUNICIPALITY_WIDE";
  const OFFICIAL_STYLE_STATUSES = new Set(["OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"]);
  const HEX_RE = /^#[0-9A-Fa-f]{6}$/;
  const SAFE_ID_RE = /^[A-Za-z0-9_-]+$/;
  const SAFE_IMAGE_RE = /^I\d{3}_[A-Za-z0-9_]+\.(?:png|webp)$/;
  const ONLINE_CLASS_MODE = "ONLINE_CLASS";
  const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS";
  const APP_READY_STATUS = "APP_READY";
  const LESSON_READY_STATUS = "LESSON_READY_10";
  const EXPECTED_APP_READY_ITEM_COUNT = 40;
  const EXPECTED_LESSON_READY_ITEM_COUNT = 10;
  const LESSON_IMAGE_ITEM_IDS = new Set([
    "I001", "I004", "I006", "I007", "I013",
    "I014", "I017", "I029", "I031", "I033"
  ]);
  const SUPPLEMENTAL_IMAGE_ITEM_IDS = new Set(["I002", "I003", "I027", "I018", "I010"]);
  const SUPPLEMENTAL_TARGET_MUNICIPALITIES = new Set(["M009", "M020", "M094", "M098", "M099", "M105"]);
  const REVIEW_SOURCE_RE = /^data\/research\/(?:app_readiness|lesson_readiness)\/m\d{3}_item_review\.csv$/;

  const lessonModeSelect = document.getElementById("lessonModeSelect");
  const select = document.getElementById("municipalitySelect");
  const lessonVariantControl = document.getElementById("lessonVariantControl");
  const lessonVariantGroup = document.getElementById("lessonVariantGroup");
  const presentationButton = document.getElementById("presentationButton");
  const municipalityName = document.getElementById("municipalityName");
  const statusText = document.getElementById("statusText");
  const bucketGrid = document.getElementById("bucketGrid");
  const practicePanel = document.getElementById("practicePanel");
  const practiceUnavailable = document.getElementById("practiceUnavailable");
  const practiceProgress = document.getElementById("practiceProgress");
  const itemImage = document.getElementById("itemImage");
  const answerFeedback = document.getElementById("answerFeedback");
  const nextItemButton = document.getElementById("nextItemButton");

  let municipalitiesById = new Map();
  let categoryByKey = new Map();
  let bucketsByMunicipality = new Map();
  let stylesByBucket = new Map();
  let assetsByItem = new Map();
  let scoringReadyPairs = new Set();
  let scoringReadyMunicipalities = new Set();
  let itemsByMunicipality = new Map();
  let lessonBoxesByMunicipalityAndMode = new Map();
  let lessonProjectionByPair = new Map();
  let lessonTeachingMunicipalities = new Set();
  let lessonVariantGroupsByMunicipality = new Map();
  let lessonVariantGroupById = new Map();
  let lessonVariantBoxesByGroupAndMode = new Map();
  let lessonVariantItemsByGroup = new Map();
  let supplementalItemsByMunicipality = new Map();
  let supplementalVariantItemsByGroup = new Map();
  let supplementalBoxesByGroup = new Map();
  let supplementalImageGateReady = false;
  let activeLessonVariantGroupId = "";
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
    if (count <= 9) return 3;
    return 4;
  }

  function categoryKey(municipalityId, categoryId) {
    return `${municipalityId}::${categoryId}`;
  }

  function pairKey(municipalityId, itemId) {
    return `${municipalityId}::${itemId}`;
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
      const scope = row.district_scope?.trim() || MUNICIPAL_SCOPE;
      if (!municipalityId || !categoryId) continue;
      stylesByBucket.set(styleKey(municipalityId, categoryId, scope), row);
    }
  }

  function officialStyleUsable(style) {
    return Boolean(
      style && OFFICIAL_STYLE_STATUSES.has(style.color_status?.trim()) &&
      HEX_RE.test(style.display_color?.trim() ?? "") &&
      HEX_RE.test(style.border_color?.trim() ?? "") &&
      HEX_RE.test(style.text_color?.trim() ?? "")
    );
  }

  function styleSignature(style) {
    return [style.display_color, style.border_color, style.text_color]
      .map((value) => value?.trim().toUpperCase())
      .join("::");
  }

  function fallbackStyle(reason, sourceCategoryIds = []) {
    return {
      provenance: "FALLBACK",
      reason,
      sourceCategoryIds,
      style: null
    };
  }

  function resolveBoxStyle(municipalityId, row, usesTeachingBox) {
    const boxKind = row.box_kind?.trim();
    if (boxKind === "SIMPLIFIED_ACTION") {
      return fallbackStyle("SIMPLIFIED_ACTION");
    }

    const configuredSources = row.style_source_category_ids?.trim();
    const defaultSource = row.category_id?.trim();
    const sourceCategoryIds = (configuredSources || defaultSource || "")
      .split(";")
      .map((value) => value.trim())
      .filter(Boolean);
    if (sourceCategoryIds.length === 0) {
      return fallbackStyle(usesTeachingBox ? "LEARNER_CREATED_BOX" : "NO_SOURCE_CATEGORY");
    }

    const districtScope = row.style_district_scope?.trim() || MUNICIPAL_SCOPE;
    const resolved = [];
    const resolvedScopes = [];
    for (const sourceCategoryId of sourceCategoryIds) {
      const sortBucket = findSortBucket(municipalityId, sourceCategoryId);
      if (!sortBucket) return fallbackStyle("SOURCE_CATEGORY_NOT_SORT_BUCKET", sourceCategoryIds);
      const categoryId = sortBucket.category_id.trim();
      const exact = stylesByBucket.get(styleKey(municipalityId, categoryId, districtScope));
      const municipalityWide = stylesByBucket.get(styleKey(municipalityId, categoryId, MUNICIPAL_SCOPE));
      const usesExactVariant = districtScope !== MUNICIPAL_SCOPE && officialStyleUsable(exact);
      const style = usesExactVariant ? exact : municipalityWide;
      if (!officialStyleUsable(style)) return fallbackStyle("OFFICIAL_STYLE_UNAVAILABLE", sourceCategoryIds);
      resolved.push(style);
      resolvedScopes.push(usesExactVariant ? districtScope : MUNICIPAL_SCOPE);
    }

    if (new Set(resolved.map(styleSignature)).size !== 1) {
      return fallbackStyle("CONFLICTING_OFFICIAL_STYLES", sourceCategoryIds);
    }
    const allConfirmed = resolved.every((style) => style.color_status?.trim() === "OFFICIAL_CONFIRMED");
    const reason = resolvedScopes.some((scope) => scope !== MUNICIPAL_SCOPE)
      ? "VARIANT_OFFICIAL_STYLE"
      : sourceCategoryIds.length === 1
        ? "SINGLE_OFFICIAL_CATEGORY"
        : "SAME_OFFICIAL_STYLE";
    return {
      provenance: allConfirmed ? "OFFICIAL_CONFIRMED" : "OFFICIAL_DERIVED",
      reason,
      sourceCategoryIds,
      style: resolved[0]
    };
  }

  function buildScoringReadyData(scopeRows, reviewRowsByMunicipality) {
    scoringReadyPairs = new Set();
    scoringReadyMunicipalities = new Set();

    for (const scope of scopeRows) {
      const expectedMunicipalityId = scope.municipality_id?.trim();
      const scoringStatus = scope.scoring_status?.trim();
      const requiredItemCount = Number.parseInt(scope.required_item_count?.trim(), 10);
      const rows = reviewRowsByMunicipality.get(expectedMunicipalityId) ?? [];
      const expectedCount = scoringStatus === APP_READY_STATUS
        ? EXPECTED_APP_READY_ITEM_COUNT
        : scoringStatus === LESSON_READY_STATUS
          ? EXPECTED_LESSON_READY_ITEM_COUNT
          : 0;
      const municipalityIds = new Set(rows.map((row) => row.municipality_id?.trim()).filter(Boolean));
      const itemIds = new Set(rows.map((row) => row.internal_item_id?.trim()).filter(Boolean));
      const allComplete = rows.length > 0 && rows.every((row) => row.branch_review_status?.trim() === "COMPLETE");
      const municipalityMatches = municipalityIds.size === 1 && municipalityIds.has(expectedMunicipalityId);
      const fixedLessonItemsMatch = scoringStatus !== LESSON_READY_STATUS ||
        (itemIds.size === LESSON_IMAGE_ITEM_IDS.size && [...itemIds].every((itemId) => LESSON_IMAGE_ITEM_IDS.has(itemId)));
      const completeMunicipality = municipalityMatches && allComplete && expectedCount > 0 &&
        requiredItemCount === expectedCount && itemIds.size === expectedCount && fixedLessonItemsMatch;

      if (!completeMunicipality) {
        console.warn("Scoring review is incomplete and will not enable scoring.", expectedMunicipalityId);
        continue;
      }

      scoringReadyMunicipalities.add(expectedMunicipalityId);
      for (const itemId of itemIds) scoringReadyPairs.add(pairKey(expectedMunicipalityId, itemId));
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
      if (["HIDDEN", "EXCLUDED_NOTICE"].includes(row.ui_role?.trim())) return null;
      currentId = row.parent_category_id?.trim();
    }
    return null;
  }

  function buildLessonTeachingData(boxRows, projectionRows) {
    lessonBoxesByMunicipalityAndMode = new Map();
    lessonProjectionByPair = new Map();
    lessonTeachingMunicipalities = new Set();

    for (const row of boxRows) {
      const municipalityId = row.municipality_id?.trim();
      const boxId = row.teaching_box_id?.trim();
      const classMode = row.class_mode?.trim();
      if (!municipalityId || !boxId || ![ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE].includes(classMode)) continue;
      const key = `${municipalityId}::${classMode}`;
      if (!lessonBoxesByMunicipalityAndMode.has(key)) lessonBoxesByMunicipalityAndMode.set(key, []);
      lessonBoxesByMunicipalityAndMode.get(key).push(row);
      lessonTeachingMunicipalities.add(municipalityId);
    }
    for (const rows of lessonBoxesByMunicipalityAndMode.values()) {
      rows.sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));
    }

    for (const row of projectionRows) {
      const municipalityId = row.municipality_id?.trim();
      const itemId = row.internal_item_id?.trim();
      const boxId = row.teaching_box_id?.trim();
      if (!municipalityId || !itemId || !boxId || row.review_status?.trim() !== "COMPLETE") continue;
      const onlineBoxes = lessonBoxesByMunicipalityAndMode.get(`${municipalityId}::${ONLINE_CLASS_MODE}`) ?? [];
      if (!onlineBoxes.some((box) => box.teaching_box_id?.trim() === boxId)) continue;
      lessonProjectionByPair.set(pairKey(municipalityId, itemId), row);
    }
  }

  function buildItemData(assetRows, imageMappingRows) {
    assetsByItem = new Map(
      assetRows
        .filter((row) => row.asset_status?.trim() === "CONFIRMED")
        .map((row) => [row.internal_item_id?.trim(), row])
    );
    itemsByMunicipality = new Map();

    for (const row of imageMappingRows) {
      const municipalityId = row.municipality_id?.trim();
      const itemId = row.internal_item_id?.trim();
      if (!municipalityId || !itemId) continue;
      if (!scoringReadyMunicipalities.has(municipalityId)) continue;
      if (!scoringReadyPairs.has(pairKey(municipalityId, itemId))) continue;
      if (row.review_status?.trim() !== "VERIFIED") continue;

      const asset = assetsByItem.get(itemId);
      const imageFile = asset?.image_file?.trim();
      const projection = lessonProjectionByPair.get(pairKey(municipalityId, itemId));
      const sortBucket = projection ? null : findSortBucket(municipalityId, row.category_id?.trim());
      const projectionMatches = projection?.category_id?.trim() === row.category_id?.trim();
      const uiCategoryId = projectionMatches ? projection.teaching_box_id.trim() : sortBucket?.category_id?.trim();
      if (!asset || !uiCategoryId || !SAFE_IMAGE_RE.test(imageFile ?? "") || !imageFile.startsWith(`${itemId}_`)) continue;

      const item = {
        municipalityId,
        itemId,
        imageFile,
        pairOrder: numericOrder(row.pair_order),
        uiCategoryId
      };
      if (!itemsByMunicipality.has(municipalityId)) itemsByMunicipality.set(municipalityId, []);
      itemsByMunicipality.get(municipalityId).push(item);
    }

    for (const rows of itemsByMunicipality.values()) {
      rows.sort((a, b) => a.pairOrder - b.pairOrder);
    }
  }

  function buildLessonVariantData(districtScopeRows, groupRows, boxRows, scoringRows) {
    const knownScopeMunicipalities = new Set(
      districtScopeRows.map((row) => row.municipality_id?.trim()).filter(Boolean)
    );
    lessonVariantGroupsByMunicipality = new Map();
    lessonVariantGroupById = new Map();
    lessonVariantBoxesByGroupAndMode = new Map();
    lessonVariantItemsByGroup = new Map();

    for (const row of groupRows) {
      const groupId = row.lesson_variant_group_id?.trim();
      const municipalityId = row.municipality_id?.trim();
      if (!groupId || !municipalityId || !knownScopeMunicipalities.has(municipalityId)) continue;
      if (row.readiness_status?.trim() !== LESSON_READY_STATUS) continue;
      lessonVariantGroupById.set(groupId, row);
      if (!lessonVariantGroupsByMunicipality.has(municipalityId)) {
        lessonVariantGroupsByMunicipality.set(municipalityId, []);
      }
      lessonVariantGroupsByMunicipality.get(municipalityId).push(row);
    }
    for (const rows of lessonVariantGroupsByMunicipality.values()) {
      rows.sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));
    }

    for (const row of boxRows) {
      const groupId = row.lesson_variant_group_id?.trim();
      const boxId = row.teaching_box_id?.trim();
      const classMode = row.class_mode?.trim();
      if (!groupId || !boxId || ![ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE].includes(classMode) ||
          !lessonVariantGroupById.has(groupId)) continue;
      const key = `${groupId}::${classMode}`;
      if (!lessonVariantBoxesByGroupAndMode.has(key)) lessonVariantBoxesByGroupAndMode.set(key, []);
      lessonVariantBoxesByGroupAndMode.get(key).push(row);
    }
    for (const rows of lessonVariantBoxesByGroupAndMode.values()) {
      rows.sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));
    }

    for (const row of scoringRows) {
      const groupId = row.lesson_variant_group_id?.trim();
      const itemId = row.internal_item_id?.trim();
      const boxId = row.teaching_box_id?.trim();
      if (!groupId || !itemId || !boxId || row.review_status?.trim() !== "COMPLETE") continue;
      const group = lessonVariantGroupById.get(groupId);
      if (!group || group.municipality_id?.trim() !== row.municipality_id?.trim()) continue;
      const boxes = lessonVariantBoxesByGroupAndMode.get(`${groupId}::${ONLINE_CLASS_MODE}`) ?? [];
      if (!boxes.some((box) => box.teaching_box_id?.trim() === boxId)) continue;
      const asset = assetsByItem.get(itemId);
      const imageFile = asset?.image_file?.trim();
      if (!asset || !SAFE_IMAGE_RE.test(imageFile ?? "") || !imageFile.startsWith(`${itemId}_`)) continue;
      if (!lessonVariantItemsByGroup.has(groupId)) lessonVariantItemsByGroup.set(groupId, []);
      lessonVariantItemsByGroup.get(groupId).push({
        municipalityId: row.municipality_id.trim(),
        itemId,
        imageFile,
        pairOrder: numericOrder(itemId.slice(1)),
        uiCategoryId: boxId
      });
    }
    for (const rows of lessonVariantItemsByGroup.values()) {
      rows.sort((a, b) => a.pairOrder - b.pairOrder);
    }
  }

  function buildLessonSupplementalData(scoringRows, supplementalBoxRows) {
    supplementalItemsByMunicipality = new Map();
    supplementalVariantItemsByGroup = new Map();
    supplementalBoxesByGroup = new Map();
    supplementalImageGateReady = [...SUPPLEMENTAL_IMAGE_ITEM_IDS].every((itemId) => assetsByItem.has(itemId));
    if (!supplementalImageGateReady) return;

    for (const row of supplementalBoxRows) {
      const groupId = row.lesson_variant_group_id?.trim();
      const boxId = row.teaching_box_id?.trim();
      if (!groupId || !boxId || row.class_mode?.trim() !== ONLINE_CLASS_MODE) continue;
      if (!lessonVariantGroupById.has(groupId)) continue;
      if (!supplementalBoxesByGroup.has(groupId)) supplementalBoxesByGroup.set(groupId, []);
      supplementalBoxesByGroup.get(groupId).push(row);
    }
    for (const rows of supplementalBoxesByGroup.values()) {
      rows.sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));
    }

    for (const row of scoringRows) {
      const municipalityId = row.municipality_id?.trim();
      const groupId = row.lesson_variant_group_id?.trim();
      const itemId = row.internal_item_id?.trim();
      if (!municipalityId || !itemId || row.review_status?.trim() !== "COMPLETE") continue;
      if (!SUPPLEMENTAL_TARGET_MUNICIPALITIES.has(municipalityId) || !SUPPLEMENTAL_IMAGE_ITEM_IDS.has(itemId)) continue;
      const asset = assetsByItem.get(itemId);
      const imageFile = asset?.image_file?.trim();
      if (!asset || !SAFE_IMAGE_RE.test(imageFile ?? "") || !imageFile.startsWith(`${itemId}_`)) continue;

      if (groupId) {
        const group = lessonVariantGroupById.get(groupId);
        if (!group || group.municipality_id?.trim() !== municipalityId) continue;
        const baseBoxes = lessonVariantBoxesByGroupAndMode.get(`${groupId}::${ONLINE_CLASS_MODE}`) ?? [];
        const extraBoxes = supplementalBoxesByGroup.get(groupId) ?? [];
        const boxId = row.teaching_box_id?.trim();
        if (!boxId || ![...baseBoxes, ...extraBoxes].some((box) => box.teaching_box_id?.trim() === boxId)) continue;
        if (!supplementalVariantItemsByGroup.has(groupId)) supplementalVariantItemsByGroup.set(groupId, []);
        supplementalVariantItemsByGroup.get(groupId).push({
          municipalityId, itemId, imageFile, pairOrder: numericOrder(row.display_order), uiCategoryId: boxId
        });
        continue;
      }

      const sortBucket = findSortBucket(municipalityId, row.category_id?.trim());
      if (!sortBucket) continue;
      if (!supplementalItemsByMunicipality.has(municipalityId)) supplementalItemsByMunicipality.set(municipalityId, []);
      supplementalItemsByMunicipality.get(municipalityId).push({
        municipalityId, itemId, imageFile, pairOrder: numericOrder(row.display_order), uiCategoryId: sortBucket.category_id.trim()
      });
    }

    for (const rows of [...supplementalItemsByMunicipality.values(), ...supplementalVariantItemsByGroup.values()]) {
      rows.sort((a, b) => a.pairOrder - b.pairOrder);
    }
  }

  function supplementalSetReady(rows) {
    return supplementalImageGateReady && rows.length === SUPPLEMENTAL_IMAGE_ITEM_IDS.size &&
      new Set(rows.map((row) => row.itemId)).size === SUPPLEMENTAL_IMAGE_ITEM_IDS.size;
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
      const scope = row.district_scope?.trim() || MUNICIPAL_SCOPE;
      const background = row.display_color?.trim();
      const border = row.border_color?.trim();
      const text = row.text_color?.trim();

      if (!OFFICIAL_STYLE_STATUSES.has(status) || scope !== MUNICIPAL_SCOPE) continue;
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
    for (const [value, label] of [
      ["", "授業モードを選択"],
      [ONLINE_CLASS_MODE, "オンライン授業"],
      [IN_PERSON_CLASS_MODE, "対面授業"]
    ]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      lessonModeSelect.appendChild(option);
    }
    lessonModeSelect.disabled = false;
  }

  function populateMunicipalitySelect() {
    const ids = [...new Set([
      ...bucketsByMunicipality.keys(), ...lessonVariantGroupsByMunicipality.keys(), ...lessonTeachingMunicipalities
    ])]
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

  function configureLessonVariantSelection(id) {
    const groups = lessonVariantGroupsByMunicipality.get(id) ?? [];
    lessonVariantGroup.replaceChildren();
    activeLessonVariantGroupId = "";

    if (groups.length === 0) {
      lessonVariantControl.hidden = true;
      lessonVariantGroup.disabled = true;
      return;
    }

    const requiresSelection = groups.some((row) => row.learner_selection_required?.trim() === "TRUE");
    if (groups.length === 1 && !requiresSelection) {
      activeLessonVariantGroupId = groups[0].lesson_variant_group_id.trim();
      lessonVariantControl.hidden = true;
      lessonVariantGroup.disabled = true;
      return;
    }

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "地域を選択";
    lessonVariantGroup.appendChild(placeholder);
    for (const row of groups) {
      const option = document.createElement("option");
      option.value = row.lesson_variant_group_id.trim();
      option.textContent = row.display_name.trim();
      lessonVariantGroup.appendChild(option);
    }
    lessonVariantControl.hidden = false;
    lessonVariantGroup.disabled = false;
  }

  function displayRows(id) {
    if (activeLessonVariantGroupId) {
      const classMode = lessonModeSelect.value;
      if (![ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE].includes(classMode)) return [];
      const baseRows = lessonVariantBoxesByGroupAndMode.get(`${activeLessonVariantGroupId}::${classMode}`) ?? [];
      const supplementalItems = supplementalVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];
      if (classMode !== ONLINE_CLASS_MODE || !supplementalSetReady(supplementalItems)) return baseRows;
      const extraRows = supplementalBoxesByGroup.get(activeLessonVariantGroupId) ?? [];
      const seen = new Set();
      return [...baseRows, ...extraRows]
        .filter((row) => {
          const boxId = row.teaching_box_id?.trim();
          if (!boxId || seen.has(boxId)) return false;
          seen.add(boxId);
          return true;
        })
        .sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));
    }
    const classMode = lessonModeSelect.value;
    const lessonRows = lessonBoxesByMunicipalityAndMode.get(`${id}::${classMode}`) ?? [];
    if (lessonRows.length > 0) return lessonRows;
    return bucketsByMunicipality.get(id) ?? [];
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

    const rows = displayRows(id);
    const interactive = lessonModeSelect.value === ONLINE_CLASS_MODE && activeItems.length > 0;
    bucketGrid.dataset.columns = String(displayColumns(rows.length));

    if (rows.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "投影できる分別区分がありません。";
      bucketGrid.appendChild(empty);
      return;
    }

    for (const [boxIndex, row] of rows.entries()) {
      const usesTeachingBox = Boolean(row.teaching_box_id?.trim());
      const categoryId = usesTeachingBox ? row.teaching_box_id.trim() : row.category_id.trim();
      const label = usesTeachingBox ? row.display_name.trim() : row["自治体正式名称"].trim();
      const resolution = resolveBoxStyle(id, row, usesTeachingBox);
      const status = resolution.provenance;
      const box = document.createElement(interactive ? "button" : "div");
      if (box instanceof HTMLButtonElement) box.type = "button";

      box.className = "bucket";
      box.dataset.municipalityId = id;
      box.dataset.categoryId = categoryId;
      box.dataset.styleStatus = status;
      box.dataset.styleProvenance = status;
      box.dataset.styleReason = resolution.reason;
      box.dataset.sourceCategoryIds = resolution.sourceCategoryIds.join(";");
      box.dataset.boxKind = row.box_kind?.trim() || "OFFICIAL_CATEGORY";
      box.textContent = label;

      if (resolution.style) {
        box.style.backgroundColor = resolution.style.display_color.trim();
        box.style.borderColor = resolution.style.border_color.trim();
        box.style.color = resolution.style.text_color.trim();
      }

      const length = [...label].length;
      if (length >= 13) box.classList.add("bucket--long");
      else if (length >= 7) box.classList.add("bucket--compact");
      if (OFFICIAL_STYLE_STATUSES.has(status)) {
        box.classList.add("bucket--official-style");
      } else {
        box.classList.add("bucket--fallback-style");
        box.dataset.fallbackPalette = String((boxIndex % 8) + 1);
      }

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
    clearBucketAnswerState();
  }

  function renderPracticeItem() {
    practiceFinished = false;
    const item = activeItems[activeItemIndex];
    practiceProgress.textContent = `${activeItemIndex + 1} / ${activeItems.length}`;
    itemImage.hidden = false;
    itemImage.src = `./assets/items/${item.imageFile}`;
    itemImage.alt = "仕分けるごみの画像";
    practicePanel.classList.remove("practice-panel--complete");
    resetAnswer();
  }

  function showPracticeCompletion() {
    practiceFinished = true;
    itemImage.hidden = true;
    practiceProgress.textContent = "完了";
    answerFeedback.textContent = "○";
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
      answerFeedback.textContent = "×";
      answerFeedback.className = "answer-feedback answer-feedback--incorrect";
      return;
    }

    box.dataset.answerState = "correct";
    answerFeedback.textContent = "○";
    answerFeedback.className = "answer-feedback answer-feedback--correct";
    nextItemButton.textContent = activeItemIndex + 1 === activeItems.length ? "結果" : "次へ";
    nextItemButton.hidden = false;
    for (const candidate of bucketGrid.querySelectorAll("button.bucket")) candidate.disabled = true;
    nextItemButton.focus();
  }

  function renderMunicipality(id) {
    const lessonMode = lessonModeSelect.value;
    activeItems = [];
    if (lessonMode === ONLINE_CLASS_MODE && id) {
      if (activeLessonVariantGroupId) {
        const coreItems = lessonVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];
        const supplementalItems = supplementalVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];
        activeItems = supplementalSetReady(supplementalItems) ? [...coreItems, ...supplementalItems] : [...coreItems];
      } else {
        const coreItems = itemsByMunicipality.get(id) ?? [];
        const supplementalItems = supplementalItemsByMunicipality.get(id) ?? [];
        activeItems = SUPPLEMENTAL_TARGET_MUNICIPALITIES.has(id) && supplementalSetReady(supplementalItems)
          ? [...coreItems, ...supplementalItems]
          : [...coreItems];
      }
    }
    activeItemIndex = 0;
    practiceFinished = false;
    practicePanel.hidden = true;
    practiceUnavailable.hidden = true;

    if (!id) {
      municipalityName.textContent = "自治体を選択してください";
      statusText.textContent = lessonMode ? "自治体を選択してください。" : "授業モードと自治体を選択してください。";
      presentationButton.disabled = true;
      renderBuckets("");
      return;
    }

    const variantGroups = lessonVariantGroupsByMunicipality.get(id) ?? [];
    const needsVariantSelection = variantGroups.length > 1 && !activeLessonVariantGroupId;
    const rows = displayRows(id);
    municipalityName.textContent = municipalityLabel(id);
    presentationButton.disabled = rows.length === 0 || !lessonMode || needsVariantSelection;

    if (needsVariantSelection) {
      statusText.textContent = "地域を選択してください。";
      renderBuckets("");
      return;
    }

    if (!lessonMode) {
      statusText.textContent = `${rows.length}区分・授業モードを選択してください。`;
      renderBuckets(id);
      return;
    }

    if (lessonMode === IN_PERSON_CLASS_MODE) {
      statusText.textContent = `${rows.length}区分・対面授業モード`;
      renderBuckets(id);
      return;
    }

    if (activeItems.length > 0) {
      statusText.textContent = `${rows.length}区分・オンライン授業モード・画像練習${activeItems.length}問`;
      practicePanel.hidden = false;
      renderBuckets(id);
      renderPracticeItem();
      return;
    }

    statusText.textContent = `${rows.length}区分・オンライン授業モード`;
    practiceUnavailable.hidden = false;
    practiceUnavailable.textContent = activeLessonVariantGroupId || scoringReadyMunicipalities.has(id)
      ? "この自治体の画像問題はまだ登録されていません。"
      : "この自治体の自動正誤判定は準備中です。";
    renderBuckets(id);
  }

  async function enterPresentation() {
    if (!select.value || !lessonModeSelect.value) return;
    try {
      if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
      else document.body.classList.add("presentation-mode");
    } catch (error) {
      console.warn("Fullscreen API unavailable; using presentation layout only.", error);
      document.body.classList.add("presentation-mode");
    }
  }

  async function fetchText(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`data load failed: ${path} (${response.status})`);
    return response.text();
  }

  async function load() {
    try {
      const requests = [
        fetchText(DATA_PATHS.municipalities),
        fetchText(DATA_PATHS.municipalityResearch),
        fetchText(DATA_PATHS.categories),
        fetchText(DATA_PATHS.styleProjection),
        fetchText(DATA_PATHS.itemAssets),
        fetchText(DATA_PATHS.imageMappingPilot),
        fetchText(DATA_PATHS.lessonScope),
        fetchText(DATA_PATHS.lessonTeachingBoxes),
        fetchText(DATA_PATHS.lessonItemScoringProjection),
        fetchText(DATA_PATHS.districtScopes),
        fetchText(DATA_PATHS.lessonVariantGroups),
        fetchText(DATA_PATHS.lessonVariantBoxes),
        fetchText(DATA_PATHS.lessonVariantScoring),
        fetchText(DATA_PATHS.lessonSupplementalScoring),
        fetchText(DATA_PATHS.lessonSupplementalBoxes)
      ];

      const texts = await Promise.all(requests);
      const [
        municipalityText, researchText, categoryText, styleText, assetText, mappingText, scopeText,
        teachingBoxText, scoringProjectionText,
        districtScopeText, variantGroupText, variantBoxText, variantScoringText,
        supplementalScoringText, supplementalBoxText
      ] = texts;
      const scopeRows = parseCsv(scopeText);
      const reviewEntries = scopeRows.map((row) => {
        const municipalityId = row.municipality_id?.trim();
        const source = row.review_source?.trim();
        if (!municipalityId || !REVIEW_SOURCE_RE.test(source ?? "")) {
          throw new Error(`unsafe scoring review source: ${municipalityId || "UNKNOWN"}`);
        }
        return [municipalityId, `../${source}`];
      });
      const reviewTexts = await Promise.all(reviewEntries.map(([, path]) => fetchText(path)));

      buildData(parseCsv(municipalityText), parseCsv(researchText), parseCsv(categoryText));
      buildStyleData(parseCsv(styleText));
      buildScoringReadyData(
        scopeRows,
        new Map(reviewEntries.map(([municipalityId], index) => [municipalityId, parseCsv(reviewTexts[index])]))
      );
      buildLessonTeachingData(parseCsv(teachingBoxText), parseCsv(scoringProjectionText));
      buildItemData(parseCsv(assetText), parseCsv(mappingText));
      buildLessonVariantData(
        parseCsv(districtScopeText),
        parseCsv(variantGroupText),
        parseCsv(variantBoxText),
        parseCsv(variantScoringText)
      );
      buildLessonSupplementalData(parseCsv(supplementalScoringText), parseCsv(supplementalBoxText));
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
  select.addEventListener("change", () => {
    configureLessonVariantSelection(select.value);
    renderMunicipality(select.value);
  });
  lessonVariantGroup.addEventListener("change", () => {
    activeLessonVariantGroupId = lessonVariantGroup.value;
    renderMunicipality(select.value);
  });
  presentationButton.addEventListener("click", enterPresentation);
  nextItemButton.addEventListener("click", () => {
    if (practiceFinished) {
      activeItemIndex = 0;
      nextItemButton.textContent = "次へ";
      renderBuckets(select.value);
      renderPracticeItem();
      return;
    }

    if (activeItemIndex + 1 < activeItems.length) {
      activeItemIndex += 1;
      nextItemButton.textContent = "次へ";
      renderBuckets(select.value);
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

import { app } from "/scripts/app.js";

/* eslint-disable no-undef */
const EXTENSION_NAME = "Arena.AutoCache.Overlay";
const TARGET_CLASSES = new Set([
  "ArenaAutoCacheAudit",
  "ArenaAutoCacheDashboard",
  "ArenaAutoCacheOps",
]);
const SOCKET_FIELDS = {
  summary_json: "summary",
  warmup_json: "warmup",
  trim_json: "trim",
};
const OUTPUT_FIELD_ALIASES = {
  summary: [
    "summary",
    "summary json",
    "json summary",
    "summary_json",
    "json summary data",
    "json сводка",
    "json сводки",
    "сводка json",
    "сводка",
    "сводки",
    "итог",
    "резюме",
  ],
  warmup: [
    "warmup",
    "warmup json",
    "json warmup",
    "warmup_json",
    "warm up",
    "prewarm",
    "прогрев json",
    "прогрев",
    "разогрев",
    "разминка",
    "подготовка",
  ],
  trim: [
    "trim",
    "trim json",
    "json trim",
    "trim_json",
    "cleanup",
    "clean up",
    "purge",
    "prune",
    "обрезка json",
    "обрезка",
    "очистка",
    "удаление",
    "срез",
  ],
};
// Inject Russian aliases at runtime to avoid encoding issues in source
try {
  OUTPUT_FIELD_ALIASES.summary = (OUTPUT_FIELD_ALIASES.summary || []).concat([
    "сводка",
    "сводка json",
    "json сводки",
    "сводка (json)",
  ]);
  OUTPUT_FIELD_ALIASES.warmup = (OUTPUT_FIELD_ALIASES.warmup || []).concat([
    "прогрев",
    "прогрев json",
    "json прогрева",
    "прогрев (json)",
  ]);
  OUTPUT_FIELD_ALIASES.trim = (OUTPUT_FIELD_ALIASES.trim || []).concat([
    "очистка",
    "очистка json",
    "json очистки",
    "очистка (json)",
  ]);
} catch (e) {
  // no-op
}
const OUTPUT_FIELD_LOOKUP = buildOutputFieldLookup(SOCKET_FIELDS, OUTPUT_FIELD_ALIASES);
const PROGRESS_COLORS = {
  audit: "#42a5f5",
  warmup: "#26a69a",
  trim: "#ff7043",
  capacity: "#7e57c2",
};
const COLOR_PRESETS = {
  idle: null,
  ok: {
    box: "#2e7d32",
    border: "#1b5e20",
    background: "#102915",
    title: "#e8f5e9",
  },
  warn: {
    box: "#f9a825",
    border: "#f57f17",
    background: "#2d2307",
    title: "#fff8e1",
  },
  error: {
    box: "#c62828",
    border: "#8e0000",
    background: "#2b0d0d",
    title: "#ffebee",
  },
};
const ISSUE_LEVEL = {
  WARN: "warn",
  ERROR: "error",
};
const trackedNodes = new WeakMap();
let graphApp = null;
const REGISTRATION_RETRY_DELAY_MS = 50;
let extensionRegistered = false;
let pendingRegistrationTimer = null;
let fallbackExecutionUnsubscribe = null;
let fallbackExecutionGraph = null;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function isTargetNode(node) {
  return (
    !!node &&
    !!node.constructor &&
    typeof node.constructor.comfyClass === "string" &&
    TARGET_CLASSES.has(node.constructor.comfyClass)
  );
}

function ensureState(node) {
  let state = trackedNodes.get(node);
  if (!state) {
    state = {
      summary: null,
      warmup: null,
      trim: null,
      issues: {
        summary: null,
        warmup: null,
        trim: null,
      },
      display: null,
    };
    trackedNodes.set(node, state);
  }
  return state;
}

function rebuildDisplay(node, state) {
  if (!node) {
    return;
  }
  const currentState = state || ensureState(node);
  currentState.display = buildDisplay(currentState);
  applyPalette(node, currentState.display.severity);
  scheduleDraw(node);
}

function decorateNode(node) {
  if (!node || node.__arenaAutoCacheDecorated) {
    return;
  }
  node.__arenaAutoCacheDecorated = true;
  const originalDrawForeground = node.onDrawForeground;
  const originalOnRemoved = node.onRemoved;
  const originalPalette = {
    boxcolor: node.boxcolor,
    bgcolor: node.bgcolor,
    color: node.color,
    title_color: node.title_color,
  };
  node.__arenaAutoCacheOriginalPalette = originalPalette;

  node.onDrawForeground = function arenaAutoCacheDraw(ctx) {
    if (typeof originalDrawForeground === "function") {
      originalDrawForeground.apply(this, arguments);
    }
    drawOverlay(this, ctx);
  };

  node.onRemoved = function arenaAutoCacheRemoved() {
    restorePalette(this);
    trackedNodes.delete(this);
    if (typeof originalOnRemoved === "function") {
      return originalOnRemoved.apply(this, arguments);
    }
    return undefined;
  };
}

function restorePalette(node) {
  const original = node.__arenaAutoCacheOriginalPalette;
  if (!original) {
    return;
  }
  node.boxcolor = original.boxcolor;
  node.bgcolor = original.bgcolor;
  node.color = original.color;
  node.title_color = original.title_color;
}

function applyPalette(node, severity) {
  const preset = COLOR_PRESETS[severity] || null;
  const original = node.__arenaAutoCacheOriginalPalette;
  if (!original) {
    return;
  }
  if (!preset) {
    restorePalette(node);
    return;
  }
  node.boxcolor = preset.box;
  node.color = preset.border;
  node.bgcolor = preset.background;
  node.title_color = preset.title;
}

function scheduleDraw(node) {
  const graph = node?.graph || graphApp?.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

function hasOutputsUpdatedCallback(graph) {
  if (!graph) {
    return false;
  }
  const callback = graph.onNodeOutputsUpdated;
  if (!callback) {
    return false;
  }
  if (typeof callback === "function") {
    return true;
  }
  const potentialMethods = [
    "add",
    "addListener",
    "addEventListener",
    "connect",
    "subscribe",
  ];
  return potentialMethods.some((method) => typeof callback?.[method] === "function");
}

function detachFallbackExecutionListener() {
  if (typeof fallbackExecutionUnsubscribe === "function") {
    try {
      fallbackExecutionUnsubscribe();
    } catch (detachError) {
      console.error("Arena.AutoCache.Overlay failed to detach execution listener:", detachError);
    }
  }
  fallbackExecutionUnsubscribe = null;
  fallbackExecutionGraph = null;
}

function attachListenerToEventSource(context, key, source, handler) {
  if (!source) {
    return null;
  }

  const methodPairs = [
    ["addEventListener", "removeEventListener"],
    ["addListener", "removeListener"],
    ["add", "remove"],
    ["on", "off"],
    ["connect", "disconnect"],
    ["attach", "detach"],
    ["subscribe", "unsubscribe"],
  ];

  for (const [attachName, detachName] of methodPairs) {
    if (typeof source[attachName] === "function" && typeof source[detachName] === "function") {
      try {
        source[attachName](handler);
      } catch (attachError) {
        console.error(`Arena.AutoCache.Overlay failed to attach ${String(key)} listener:`, attachError);
        return null;
      }
      return () => {
        try {
          source[detachName](handler);
        } catch (detachError) {
          console.error(`Arena.AutoCache.Overlay failed to detach ${String(key)} listener:`, detachError);
        }
      };
    }
  }

  if (typeof source === "function" && context && key) {
    const original = source;
    const wrapper = function arenaAutoCacheWrappedExecutionListener() {
      let result;
      if (typeof original === "function") {
        result = original.apply(this, arguments);
      }
      try {
        handler.apply(this, arguments);
      } catch (handlerError) {
        console.error("Arena.AutoCache.Overlay execution listener failed:", handlerError);
      }
      return result;
    };
    context[key] = wrapper;
    return () => {
      if (context[key] === wrapper) {
        context[key] = original;
      }
    };
  }

  return null;
}

function convertCandidateToOutputs(node, candidate) {
  if (candidate == null) {
    return null;
  }

  if (candidate instanceof Map) {
    const mapResult = {};
    let mapHasEntries = false;
    for (const [key, value] of candidate.entries()) {
      if (key == null || value === undefined) {
        continue;
      }
      mapResult[String(key)] = value;
      mapHasEntries = true;
    }
    return mapHasEntries ? mapResult : null;
  }

  if (Array.isArray(candidate)) {
    const outputs = Array.isArray(node?.outputs) ? node.outputs : [];
    const result = {};
    let hasEntries = false;
    for (let index = 0; index < candidate.length; index += 1) {
      const slot = outputs[index];
      const key = typeof slot?.name === "string" ? slot.name : typeof slot?.label === "string" ? slot.label : String(index);
      if (!key) {
        continue;
      }
      const value = candidate[index];
      if (value === undefined) {
        continue;
      }
      result[key] = value;
      hasEntries = true;
    }
    return hasEntries ? result : null;
  }

  if (typeof candidate === "object") {
    if (Array.isArray(candidate.outputData)) {
      const nested = convertCandidateToOutputs(node, candidate.outputData);
      if (nested) {
        return nested;
      }
    }
    if (candidate.outputs && typeof candidate.outputs === "object") {
      const nested = convertCandidateToOutputs(node, candidate.outputs);
      if (nested) {
        return nested;
      }
    }
    const result = {};
    let hasEntries = false;
    for (const [key, value] of Object.entries(candidate)) {
      if (value === undefined) {
        continue;
      }
      result[key] = value;
      hasEntries = true;
    }
    return hasEntries ? result : null;
  }

  return null;
}

function buildOutputsFromNode(node) {
  if (!node || !Array.isArray(node.outputs) || node.outputs.length === 0) {
    return null;
  }
  const result = {};
  let hasEntries = false;
  for (let index = 0; index < node.outputs.length; index += 1) {
    const slot = node.outputs[index];
    const key = typeof slot?.name === "string" ? slot.name : typeof slot?.label === "string" ? slot.label : String(index);
    if (!key) {
      continue;
    }
    let value;
    if (typeof node.getOutputData === "function") {
      try {
        value = node.getOutputData(index);
      } catch (readError) {
        value = undefined;
      }
    } else if (slot && Object.prototype.hasOwnProperty.call(slot, "value")) {
      value = slot.value;
    }
    if (value === undefined) {
      continue;
    }
    result[key] = value;
    hasEntries = true;
  }
  return hasEntries ? result : null;
}

function normalizeExecutionOutputs(node, candidates) {
  if (!node || !Array.isArray(candidates)) {
    return null;
  }
  for (const candidate of candidates) {
    const normalized = convertCandidateToOutputs(node, candidate);
    if (normalized) {
      return normalized;
    }
  }
  return buildOutputsFromNode(node);
}

function extractExecutionPayload(graph, args) {
  if (!graph) {
    return { node: null, candidates: [] };
  }
  if (!Array.isArray(args) || args.length === 0) {
    return { node: null, candidates: [] };
  }
  const [first, ...rest] = args;
  if (first && typeof first === "object" && typeof first.id !== "undefined") {
    return { node: first, candidates: rest };
  }
  if ((typeof first === "number" || typeof first === "string") && typeof graph.getNodeById === "function") {
    const node = graph.getNodeById(first) || null;
    return { node, candidates: rest };
  }
  return { node: null, candidates: args };
}

function subscribeToExecutionEvents(graph) {
  if (!graph) {
    return null;
  }

  const handler = function arenaAutoCacheExecutionListener() {
    const { node, candidates } = extractExecutionPayload(graph, Array.from(arguments));
    if (!node || !isTargetNode(node)) {
      return;
    }
    const outputs = normalizeExecutionOutputs(node, candidates);
    if (outputs && Object.keys(outputs).length > 0) {
      try {
        updateNodeFromOutputs(String(node.id), outputs);
      } catch (updateError) {
        console.error("Arena.AutoCache.Overlay execution update failed:", updateError);
      }
    }
    const state = ensureState(node);
    rebuildDisplay(node, state);
  };

  const candidateKeys = ["onExecuted", "onNodeExecuted", "onAfterExecute"];
  for (const key of candidateKeys) {
    const source = graph[key];
    const unsubscribe = attachListenerToEventSource(graph, key, source, handler);
    if (typeof unsubscribe === "function") {
      return unsubscribe;
    }
  }

  return null;
}

function refreshExecutionSubscription() {
  const graph = graphApp?.graph || null;
  if (!graph) {
    detachFallbackExecutionListener();
    return;
  }
  if (hasOutputsUpdatedCallback(graph)) {
    if (typeof fallbackExecutionUnsubscribe === "function") {
      detachFallbackExecutionListener();
    }
    fallbackExecutionGraph = graph;
    return;
  }
  if (fallbackExecutionGraph !== graph) {
    detachFallbackExecutionListener();
  }
  if (typeof fallbackExecutionUnsubscribe !== "function") {
    const unsubscribe = subscribeToExecutionEvents(graph);
    if (typeof unsubscribe === "function") {
      fallbackExecutionUnsubscribe = unsubscribe;
      fallbackExecutionGraph = graph;
    }
  }
}

function normalizeOutputKeyVariants(name) {
  if (typeof name !== "string") {
    return [];
  }
  const trimmed = name.trim().toLowerCase();
  if (!trimmed) {
    return [];
  }
  const variants = new Set([trimmed]);
  variants.add(trimmed.replace(/[\s_\-]+/g, ""));
  variants.add(trimmed.replace(/[^\p{L}\p{N}]+/gu, ""));
  const withoutJson = trimmed.replace(/\bjson\b/giu, "").trim();
  if (withoutJson) {
    variants.add(withoutJson);
    variants.add(withoutJson.replace(/[\s_\-]+/g, ""));
    variants.add(withoutJson.replace(/[^\p{L}\p{N}]+/gu, ""));
  }
  return Array.from(variants).filter(Boolean);
}

function registerOutputAlias(map, alias, canonical) {
  if (!alias || typeof alias !== "string") {
    return;
  }
  for (const variant of normalizeOutputKeyVariants(alias)) {
    if (!variant || map.has(variant)) {
      continue;
    }
    map.set(variant, canonical);
  }
}

function buildOutputFieldLookup(socketFields, aliasGroups) {
  const lookup = new Map();
  for (const [alias, canonical] of Object.entries(socketFields)) {
    registerOutputAlias(lookup, alias, canonical);
  }
  for (const [canonical, aliases] of Object.entries(aliasGroups)) {
    registerOutputAlias(lookup, canonical, canonical);
    if (!Array.isArray(aliases)) {
      continue;
    }
    for (const alias of aliases) {
      registerOutputAlias(lookup, alias, canonical);
    }
  }
  return lookup;
}

function resolveOutputFieldName(key) {
  if (typeof key !== "string") {
    return null;
  }
  for (const variant of normalizeOutputKeyVariants(key)) {
    if (!variant) {
      continue;
    }
    if (OUTPUT_FIELD_LOOKUP.has(variant)) {
      return OUTPUT_FIELD_LOOKUP.get(variant);
    }
  }
  return null;
}

function extractTextPayload(value) {
  if (value == null) {
    return null;
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    for (const entry of value) {
      if (typeof entry === "string") {
        return entry;
      }
      if (entry && typeof entry === "object") {
        if (typeof entry.text === "string") {
          return entry.text;
        }
        if (typeof entry.value === "string") {
          return entry.value;
        }
      }
    }
  }
  if (typeof value === "object" && typeof value.text === "string") {
    return value.text;
  }
  return null;
}

function safeParseJson(text) {
  if (typeof text !== "string" || !text.trim()) {
    return { data: null, error: null };
  }
  try {
    return { data: JSON.parse(text), error: null };
  } catch (error) {
    return { data: null, error: error instanceof Error ? error.message : String(error) };
  }
}

function getPayload(block) {
  if (!block || typeof block !== "object") {
    return null;
  }
  if (block.payload && typeof block.payload === "object") {
    return block.payload;
  }
  return block;
}

function getCounts(block) {
  const payload = getPayload(block);
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const counts = payload.counts;
  if (counts && typeof counts === "object") {
    return counts;
  }
  return null;
}

function addIssue(list, level, message) {
  if (!message) {
    return;
  }
  list.push({ level, message: String(message) });
}

function addProgress(progressMap, key, label, value, total, colorKey) {
  const numericTotal = Number(total);
  const numericValue = Number(value);
  if (!Number.isFinite(numericTotal) || numericTotal <= 0) {
    return;
  }
  const ratio = clamp(Number.isFinite(numericValue) ? numericValue / numericTotal : 0, 0, 1);
  const color = PROGRESS_COLORS[colorKey] || "#90a4ae";
  const text = `${label} ${Math.round(numericValue)}/${Math.round(numericTotal)}`;
  if (!progressMap.has(key)) {
    progressMap.set(key, { label, ratio, text, color });
  }
}

function buildDisplay(state) {
  const summary = state.summary;
  const warmup = state.warmup;
  const trim = state.trim;
  const issues = [];
  const detailSet = new Set();
  const progressMap = new Map();
  let headline = "Arena AutoCache";
  let severity = summary || warmup || trim ? "ok" : "idle";

  if (summary && typeof summary === "object") {
    const ui = summary.ui;
    if (ui && typeof ui === "object" && typeof ui.headline === "string") {
      headline = ui.headline;
    }
    if (ui && Array.isArray(ui.details)) {
      for (const line of ui.details) {
        if (line != null) {
          detailSet.add(String(line));
        }
      }
    }
    if (summary.ok === false) {
      addIssue(issues, ISSUE_LEVEL.ERROR, "Summary reported a failure");
    }
    const auditMeta = summary.audit_meta;
    if (auditMeta && typeof auditMeta === "object") {
      const missing = Number(auditMeta.missing ?? 0);
      const cached = Number(auditMeta.cached ?? 0);
      const total = Number(auditMeta.total ?? 0);
      if (missing > 0) {
        addIssue(issues, ISSUE_LEVEL.WARN, `Audit missing items: ${missing}`);
      }
      addProgress(progressMap, "audit", "Audit", cached, total, "audit");
    }
    const statsMeta = summary.stats_meta;
    const statsPayload = getPayload(summary.stats);
    const totalGb = Number(statsMeta?.total_gb ?? 0);
    const maxGb = Number(statsPayload?.max_size_gb ?? statsMeta?.max_size_gb ?? 0);
    if (maxGb > 0) {
      const ratio = clamp(totalGb / maxGb, 0, 1);
      const label = "Capacity";
      const text = `${label} ${totalGb.toFixed(1)} / ${maxGb.toFixed(1)} GiB`;
      progressMap.set("capacity", {
        label,
        ratio,
        text,
        color: PROGRESS_COLORS.capacity,
      });
    }
    const warmMeta = summary.warmup_meta;
    if (warmMeta && typeof warmMeta === "object") {
      addProgress(
        progressMap,
        "warmup",
        "Warmup",
        warmMeta.warmed ?? 0,
        warmMeta.total ?? warmMeta.items ?? 0,
        "warmup",
      );
      const missingWarm = Number(warmMeta.missing ?? 0);
      const warmErrors = Number(warmMeta.errors ?? 0);
      if (missingWarm > 0) {
        addIssue(issues, ISSUE_LEVEL.WARN, `Warmup missing items: ${missingWarm}`);
      }
      if (warmErrors > 0) {
        addIssue(issues, ISSUE_LEVEL.ERROR, `Warmup errors: ${warmErrors}`);
      }
    }
  }

  if (!summary && warmup && typeof warmup === "object") {
    const ui = warmup.ui;
    if (ui && typeof ui === "object" && typeof ui.headline === "string") {
      headline = ui.headline;
    }
    if (ui && Array.isArray(ui.details)) {
      for (const line of ui.details) {
        if (line != null) {
          detailSet.add(String(line));
        }
      }
    }
  }

  if (!summary && trim && typeof trim === "object") {
    const ui = trim.ui;
    if (ui && typeof ui === "object" && typeof ui.headline === "string") {
      headline = ui.headline;
    }
    if (ui && Array.isArray(ui.details)) {
      for (const line of ui.details) {
        if (line != null) {
          detailSet.add(String(line));
        }
      }
    }
  }

  const warmCounts = getCounts(warmup);
  if (warmCounts) {
    addProgress(
      progressMap,
      "warmup",
      "Warmup",
      warmCounts.warmed ?? warmCounts.copied ?? 0,
      warmCounts.total ?? warmCounts.items ?? 0,
      "warmup",
    );
    const warmMissing = Number(warmCounts.missing ?? 0);
    const warmErrors = Number(warmCounts.errors ?? 0);
    if (warmMissing > 0) {
      addIssue(issues, ISSUE_LEVEL.WARN, `Warmup missing items: ${warmMissing}`);
    }
    if (warmErrors > 0) {
      addIssue(issues, ISSUE_LEVEL.ERROR, `Warmup errors: ${warmErrors}`);
    }
  }

  const warmPayload = getPayload(warmup);
  if (warmPayload && warmPayload.ok === false) {
    addIssue(issues, ISSUE_LEVEL.ERROR, "Warmup reported a failure");
  }

  const trimPayload = getPayload(trim);
  if (trimPayload) {
    const trimmedList = Array.isArray(trimPayload.trimmed)
      ? trimPayload.trimmed.length
      : Number(trimPayload.trimmed ?? 0);
    const trimTotal = Number(trimPayload.items ?? 0);
    addProgress(progressMap, "trim", "Trim", trimmedList, trimTotal || trimmedList || 1, "trim");
    if (trimPayload.ok === false) {
      addIssue(issues, ISSUE_LEVEL.ERROR, "Trim reported a failure");
    }
    if (typeof trimPayload.note === "string" && trimPayload.note) {
      if (!/trim (skipped|to limit)/i.test(trimPayload.note)) {
        addIssue(issues, ISSUE_LEVEL.WARN, trimPayload.note);
      }
    }
  }

  for (const [key, message] of Object.entries(state.issues)) {
    if (typeof message === "string" && message.trim()) {
      addIssue(
        issues,
        ISSUE_LEVEL.ERROR,
        `${key} parse error: ${message.trim()}`,
      );
    }
  }

  let finalSeverity = severity;
  for (const issue of issues) {
    if (issue.level === ISSUE_LEVEL.ERROR) {
      finalSeverity = "error";
      break;
    }
    if (issue.level === ISSUE_LEVEL.WARN && finalSeverity !== "error") {
      finalSeverity = "warn";
    }
  }

  const details = Array.from(detailSet).slice(0, 4);
  const messages = issues.slice(0, 3);
  const progressBars = Array.from(progressMap.values());

  return {
    severity: finalSeverity,
    headline,
    details,
    issues: messages,
    progressBars,
  };
}

function drawOverlay(node, ctx) {
  const state = trackedNodes.get(node);
  if (!state || !state.display) {
    return;
  }
  const { display } = state;
  const width = Array.isArray(node.size) ? node.size[0] : node.size || node.width || 180;
  const margin = 10;
  const textHeight = 14;
  const progressHeight = 6;
  let cursorY = (typeof LiteGraph !== "undefined" ? LiteGraph.NODE_TITLE_HEIGHT : 24) + margin;

  ctx.save();
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "11px sans-serif";
  ctx.fillStyle = "#ffffff";
  ctx.globalAlpha = 0.95;

  if (display.headline) {
    ctx.fillText(display.headline, margin, cursorY);
    cursorY += textHeight + 2;
  }

  for (const bar of display.progressBars) {
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    ctx.fillRect(margin, cursorY, width - margin * 2, progressHeight);
    ctx.fillStyle = bar.color;
    ctx.fillRect(margin, cursorY, (width - margin * 2) * clamp(bar.ratio, 0, 1), progressHeight);
    cursorY += progressHeight + 2;
    ctx.fillStyle = "#ffffff";
    ctx.fillText(bar.text, margin, cursorY);
    cursorY += textHeight;
  }

  for (const line of display.details) {
    ctx.fillStyle = "#cfd8dc";
    ctx.fillText(line, margin, cursorY);
    cursorY += textHeight;
  }

  for (const issue of display.issues) {
    ctx.fillStyle = issue.level === ISSUE_LEVEL.ERROR ? "#ffab91" : "#ffe082";
    ctx.fillText(`⚠ ${issue.message}`, margin, cursorY);
    cursorY += textHeight;
  }

  ctx.restore();
}

function parseNodeLocatorId(locator) {
  if (typeof locator !== "string" || locator.length === 0) {
    return null;
  }
  const parts = locator.split(":");
  if (parts.length === 1) {
    const local = Number(parts[0]);
    return {
      subgraphUuid: null,
      localNodeId: Number.isFinite(local) ? local : parts[0],
    };
  }
  if (parts.length === 2 && parts[0]) {
    const local = Number(parts[1]);
    return {
      subgraphUuid: parts[0],
      localNodeId: Number.isFinite(local) ? local : parts[1],
    };
  }
  return null;
}

function findSubgraphByUuid(graph, uuid) {
  if (!graph || !Array.isArray(graph._nodes)) {
    return null;
  }
  for (const node of graph._nodes) {
    if (typeof node?.isSubgraphNode === "function" && node.isSubgraphNode() && node.subgraph) {
      if (String(node.subgraph.id) === String(uuid)) {
        return node.subgraph;
      }
      const nested = findSubgraphByUuid(node.subgraph, uuid);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
}

function getNodeFromGraph(graph, localId) {
  if (!graph) {
    return null;
  }
  const numericId = Number(localId);
  if (Number.isFinite(numericId)) {
    return graph.getNodeById(numericId) || null;
  }
  if (Array.isArray(graph._nodes)) {
    return graph._nodes.find((node) => String(node.id) === String(localId)) || null;
  }
  return null;
}

function resolveNode(locatorId) {
  const graph = graphApp?.graph;
  if (!graph) {
    return null;
  }
  const parsed = parseNodeLocatorId(locatorId);
  if (!parsed) {
    return null;
  }
  if (!parsed.subgraphUuid) {
    return getNodeFromGraph(graph, parsed.localNodeId);
  }
  const targetGraph = findSubgraphByUuid(graph, parsed.subgraphUuid);
  if (!targetGraph) {
    return null;
  }
  return getNodeFromGraph(targetGraph, parsed.localNodeId);
}

function updateNodeFromOutputs(locatorId, outputs) {
  const node = resolveNode(locatorId);
  if (!isTargetNode(node)) {
    return;
  }
  decorateNode(node);
  const state = ensureState(node);
  let dirty = false;

  const processedFields = new Set();

  for (const [socket, value] of Object.entries(outputs)) {
    const field = resolveOutputFieldName(socket);
    if (!field || processedFields.has(field)) {
      continue;
    }
    processedFields.add(field);
    const rawText = extractTextPayload(value);
    const parsed = safeParseJson(rawText);
    if (parsed.error) {
      state.issues[field] = parsed.error;
      dirty = true;
      continue;
    }
    state.issues[field] = null;
    if (parsed.data === null) {
      state[field] = null;
      dirty = true;
      continue;
    }
    state[field] = parsed.data;
    dirty = true;
  }

  if (dirty) {
    rebuildDisplay(node, state);
  }
}

function bootstrapExistingNodes() {
  if (!graphApp?.graph || !Array.isArray(graphApp.graph._nodes)) {
    return;
  }
  for (const node of graphApp.graph._nodes) {
    if (isTargetNode(node)) {
      decorateNode(node);
      const state = ensureState(node);
      rebuildDisplay(node, state);
    }
  }
}

const extensionDefinition = {
  name: EXTENSION_NAME,
  init(appInstance) {
    graphApp = appInstance;
    refreshExecutionSubscription();
    bootstrapExistingNodes();
    try { console.info('[Arena.AutoCache.Overlay] init'); } catch {}
  },
  loadedGraph() {
    refreshExecutionSubscription();
    bootstrapExistingNodes();
    try { console.info('[Arena.AutoCache.Overlay] loadedGraph'); } catch {}
  },
  nodeCreated(node) {
    if (!isTargetNode(node)) {
      return;
    }
    decorateNode(node);
    const state = ensureState(node);
    rebuildDisplay(node, state);
    try { console.info('[Arena.AutoCache.Overlay] nodeCreated', node?.title || node?.type || node?.constructor?.name); } catch {}
  },
  onNodeOutputsUpdated(nodeOutputs) {
    if (!nodeOutputs || typeof nodeOutputs !== "object") {
      return;
    }
    for (const [locatorId, outputs] of Object.entries(nodeOutputs)) {
      if (!outputs || typeof outputs !== "object") {
        continue;
      }
      updateNodeFromOutputs(locatorId, outputs);
    }
  },
};

function registerExtensionWith(appInstance) {
  if (extensionRegistered) {
    return;
  }
  if (!appInstance || typeof appInstance.registerExtension !== "function") {
    throw new Error("Invalid ComfyUI app instance");
  }
  appInstance.registerExtension(extensionDefinition);
  extensionRegistered = true;
  console.log("Arena.AutoCache.Overlay loaded …");
}

function resolveComfyAppInstance() {
  const globalScope = typeof globalThis !== "undefined" ? globalThis : window;
  if (!globalScope) {
    return null;
  }
  const directApp = globalScope.app;
  if (directApp && typeof directApp.registerExtension === "function") {
    return directApp;
  }
  const comfyApp = globalScope.ComfyApp?.app;
  if (comfyApp && typeof comfyApp.registerExtension === "function") {
    return comfyApp;
  }
  return null;
}

function scheduleExtensionRegistration() {
  if (extensionRegistered || pendingRegistrationTimer != null) {
    return;
  }
  const globalScope = typeof globalThis !== "undefined" ? globalThis : window;
  if (!globalScope || typeof globalScope.setTimeout !== "function") {
    return;
  }
  pendingRegistrationTimer = globalScope.setTimeout(() => {
    pendingRegistrationTimer = null;
    attemptExtensionRegistration();
  }, REGISTRATION_RETRY_DELAY_MS);
}

function attemptExtensionRegistration() {
  if (extensionRegistered) {
    return;
  }
  const comfyApp = resolveComfyAppInstance();
  if (!comfyApp) {
    scheduleExtensionRegistration();
    return;
  }
  try {
    registerExtensionWith(comfyApp);
  } catch (registrationError) {
    console.error("Arena.AutoCache.Overlay failed to load:", registrationError);
  }
}

function subscribeToComfyUiReadyEvent() {
  const globalScope = typeof globalThis !== "undefined" ? globalThis : window;
  const target = globalScope?.document || globalScope;
  const addEventListener = target?.addEventListener;
  if (typeof addEventListener !== "function") {
    return;
  }
  const handleReady = () => {
    attemptExtensionRegistration();
    if (typeof target.removeEventListener === "function") {
      target.removeEventListener("comfyui:ready", handleReady);
    }
  };
  addEventListener.call(target, "comfyui:ready", handleReady);
}

try {
  registerExtensionWith(app);
} catch (esmError) {
  const fallbackApp =
    (typeof globalThis !== "undefined" && globalThis.app) ||
    (typeof window !== "undefined" && window.app) ||
    null;

  if (fallbackApp) {
    try {
      registerExtensionWith(fallbackApp);
    } catch (fallbackError) {
      console.error("Arena.AutoCache.Overlay failed to load:", fallbackError);
    }
  } else {
    subscribeToComfyUiReadyEvent();
    attemptExtensionRegistration();
    console.error("Arena.AutoCache.Overlay failed to load: app not found");
  }
}

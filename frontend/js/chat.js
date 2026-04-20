import { LANGUAGE_FLAGS, LANGUAGE_LABELS } from "./constants.js";

export function confidenceEmojiForLabel(label) {
    if (!label) return "";
    if (/strong match/i.test(label) || /verified/i.test(label)) return "🟢 ";
    if (/moderate/i.test(label)) return "🟡 ";
    return "🟠 ";
}

export function stripCitationMarkers(text) {
    if (!text) return "";
    return text.replace(/\s*\[\d+\]/g, "").trim();
}

function citationHoverTitle(source) {
    if (!source) return "";
    const scheme = source.scheme || "Scheme";
    const preview = (source.preview_text || "").trim();
    const line = preview ? `${scheme} — ${preview}` : `${scheme} — Official catalogue match`;
    return line.length > 280 ? `${line.slice(0, 278)}…` : line;
}

function renderMessageWithCitations(msgEl, text, sources) {
    msgEl.textContent = "";
    const max = Array.isArray(sources) ? sources.length : 0;
    if (!text || !max) {
        msgEl.textContent = text || "";
        return;
    }
    const re = /\[(\d+)\]/g;
    let last = 0;
    let m;
    while ((m = re.exec(text)) !== null) {
        const chunk = text.slice(last, m.index);
        if (chunk) msgEl.appendChild(document.createTextNode(chunk));
        const n = parseInt(m[1], 10);
        if (n >= 1 && n <= max) {
            const sup = document.createElement("sup");
            sup.className = "cite-ref";
            const a = document.createElement("a");
            a.href = `#src-footnote-${n}`;
            a.className = "cite-ref-link";
            a.textContent = `[${n}]`;
            a.title = citationHoverTitle(sources[n - 1]);
            sup.appendChild(a);
            msgEl.appendChild(sup);
        } else {
            msgEl.appendChild(document.createTextNode(m[0]));
        }
        last = re.lastIndex;
    }
    const tail = text.slice(last);
    if (tail) msgEl.appendChild(document.createTextNode(tail));
}

function appendCitationFootnotes(wrap, sources) {
    if (!Array.isArray(sources) || !sources.length) return;
    let primaryIdx = 0;
    let bestScore = -1;
    sources.forEach((s, i) => {
        const sc = typeof s.score === "number" ? s.score : 0;
        if (sc > bestScore) {
            bestScore = sc;
            primaryIdx = i;
        }
    });
    const block = document.createElement("div");
    block.className = "citation-source-block";
    const title = document.createElement("div");
    title.className = "citation-footnotes-title";
    title.textContent = "Sources";
    block.appendChild(title);
    const hint = document.createElement("p");
    hint.className = "citation-footnotes-hint";
    hint.textContent = "Sources are from official government portals (MyScheme catalogue).";
    block.appendChild(hint);
    const ol = document.createElement("ol");
    ol.className = "citation-footnotes";
    ol.setAttribute("aria-label", "Source references");
    sources.forEach((s, idx) => {
        const num = idx + 1;
        const li = document.createElement("li");
        li.className = "citation-footnote-item";
        li.id = `src-footnote-${num}`;
        const isPrimary = idx === primaryIdx;
        if (isPrimary) {
            li.classList.add("primary-source");
            const lead = document.createElement("strong");
            lead.className = "citation-fn-primary-line";
            lead.textContent = `[${num}] ${s.scheme || "Scheme"} — Official Source`;
            li.appendChild(lead);
            if (s.source) {
                const catalogueLink = document.createElement("a");
                catalogueLink.href = s.source;
                catalogueLink.target = "_blank";
                catalogueLink.rel = "noopener noreferrer";
                catalogueLink.className = "citation-fn-link citation-fn-primary-link";
                catalogueLink.textContent = "MyScheme.gov.in / catalogue";
                li.appendChild(catalogueLink);
            }
        } else {
            const head = document.createElement("span");
            head.className = "citation-fn-label";
            head.textContent = `[${num}] `;
            li.appendChild(head);
            const name = document.createElement("strong");
            name.className = "citation-fn-scheme";
            name.textContent = s.scheme || "Scheme";
            li.appendChild(name);
            li.appendChild(document.createTextNode(" — "));
            if (s.source) {
                const catalogueLink = document.createElement("a");
                catalogueLink.href = s.source;
                catalogueLink.target = "_blank";
                catalogueLink.rel = "noopener noreferrer";
                catalogueLink.className = "citation-fn-link";
                catalogueLink.textContent = "MyScheme / catalogue";
                li.appendChild(catalogueLink);
            } else {
                li.appendChild(document.createTextNode("Retrieved context"));
            }
        }
        ol.appendChild(li);
    });
    block.appendChild(ol);
    wrap.appendChild(block);
}

function appendAssistantSourceLinks(container, sources, headingText) {
    if (!Array.isArray(sources) || !sources.length) return;
    const rows = sources.filter((s) => s.apply_link || s.source);
    if (!rows.length) return;

    const block = document.createElement("div");
    block.className = "source-links-block";
    const heading = document.createElement("div");
    heading.className = "source-links-heading";
    heading.textContent = headingText || "Official portals (verified)";
    block.appendChild(heading);

    rows.forEach((s) => {
        const row = document.createElement("div");
        row.className = "source-links-row";
        const name = document.createElement("div");
        name.className = "source-links-scheme-name";
        name.textContent = s.scheme || "Scheme";
        row.appendChild(name);
        if (s.confidence_label) {
            const tier = document.createElement("div");
            tier.className = "source-links-confidence";
            tier.textContent = `${confidenceEmojiForLabel(s.confidence_label)}${s.confidence_label}`;
            row.appendChild(tier);
        }
        const links = document.createElement("div");
        links.className = "scheme-links";
        if (s.apply_link) {
            const a = document.createElement("a");
            a.href = s.apply_link;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.className = "scheme-link scheme-link-apply";
            const isApply = s.cta_label === "Apply Now";
            a.textContent = isApply ? "🔗 Apply Now" : "🔍 Check Eligibility";
            links.appendChild(a);
        }
        if (s.source) {
            const b = document.createElement("a");
            b.href = s.source;
            b.target = "_blank";
            b.rel = "noopener noreferrer";
            b.className = "scheme-link scheme-link-source";
            b.textContent = "📄 Official Info";
            links.appendChild(b);
        }
        row.appendChild(links);
        block.appendChild(row);
    });

    container.appendChild(block);
}

export function appendMessageToChat(role, content, options = {}) {
    const chat = document.getElementById("conversation");
    if (!chat) return;

    const variant = options.variant || (role === "user" ? "user" : "assistant");
    if (variant === "moderation") {
        const msg = document.createElement("div");
        msg.className = "message assistant moderation-block";
        const cat = options.moderationCategory;
        if (cat === "harmful") {
            const line = document.createElement("div");
            line.className = "moderation-category-headline";
            line.textContent = "We can't assist with that request.";
            msg.appendChild(line);
        } else if (cat === "off_topic") {
            const line = document.createElement("div");
            line.className = "moderation-category-headline";
            line.textContent = "I help with government schemes and civic services.";
            msg.appendChild(line);
        }
        const prefix = document.createElement("span");
        prefix.className = "moderation-prefix";
        prefix.textContent = "🙏 ";
        msg.appendChild(prefix);
        msg.appendChild(document.createTextNode(content || ""));
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    if (variant === "error") {
        const msg = document.createElement("div");
        msg.className = "message error";
        msg.textContent = content || "Something went wrong.";
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    if (role === "user") {
        const msg = document.createElement("div");
        msg.className = "message user";
        msg.textContent = content || "";
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    const wrap = document.createElement("div");
    wrap.className = "assistant-wrap";
    const confidenceMap = {
        high: "Verified match",
        medium: "Possible match",
        low: "Needs more info",
    };
    if (options.confidence && confidenceMap[options.confidence]) {
        const chip = document.createElement("div");
        chip.className = "confidence-label";
        const emoji = options.confidence === "high" ? "🟢 " : options.confidence === "medium" ? "🟡 " : "🔴 ";
        chip.textContent = `${emoji}${confidenceMap[options.confidence]}`;
        wrap.appendChild(chip);
    }
    const msg = document.createElement("div");
    msg.className = "message assistant";

    const srcList = options.sources || [];
    if (srcList.length) {
        renderMessageWithCitations(msg, content || "", srcList);
    } else {
        msg.textContent = content || "No answer provided.";
    }
    wrap.appendChild(msg);

    if (srcList.length) {
        appendCitationFootnotes(wrap, srcList);
    }

    const why = options.reasoningWhy;
    if (why && why.trim()) {
        const panel = document.createElement("div");
        panel.className = "explain-panel";
        const h = document.createElement("div");
        h.className = "explain-panel-title";
        h.textContent = "Why this fits you";
        panel.appendChild(h);
        const body = document.createElement("div");
        body.className = "explain-panel-body";
        body.textContent = why.trim();
        panel.appendChild(body);
        wrap.appendChild(panel);
    }

    const nearText = options.nearMissText;
    const nearSrc = options.nearMissSources || [];
    if ((nearText && nearText.trim()) || nearSrc.length) {
        const panel = document.createElement("div");
        panel.className = "near-miss-panel";
        const h = document.createElement("div");
        h.className = "near-miss-panel-title";
        h.textContent = "Almost eligible";
        panel.appendChild(h);
        if (nearText && nearText.trim()) {
            const body = document.createElement("div");
            body.className = "near-miss-panel-body";
            body.textContent = nearText.trim();
            panel.appendChild(body);
        }
        if (nearSrc.length) {
            appendAssistantSourceLinks(panel, nearSrc, "Reference (lower match)");
        }
        wrap.appendChild(panel);
    }

    const topScore =
        typeof options.topScore === "number"
            ? options.topScore
            : Array.isArray(options.sources) && options.sources.length
              ? Math.max(...options.sources.map((s) => s.score || 0))
              : null;

    if (topScore !== null && !Number.isNaN(topScore)) {
        const sortedSrc = [...(options.sources || [])].sort((a, b) => (b.score || 0) - (a.score || 0));
        const serverLabel = sortedSrc[0]?.confidence_label;
        const meter = document.createElement("div");
        meter.className = "confidence-meter";
        const fill = document.createElement("div");
        fill.className = "confidence-meter-fill";
        const pct = Math.round(Math.min(1, Math.max(0, topScore)) * 100);
        fill.style.width = `${pct}%`;
        let band = "mid";
        let label = "Moderate match";
        if (topScore < 0.4) {
            band = "low";
            label = "Low confidence";
        } else if (topScore > 0.7) {
            band = "high";
            label = "Strong match (based on available data)";
        }
        fill.classList.add(band);
        meter.appendChild(fill);
        const cap = document.createElement("div");
        cap.className = "confidence-label";
        const displayLabel = serverLabel || label;
        cap.textContent = `${confidenceEmojiForLabel(displayLabel)}${displayLabel} · match strength`;
        wrap.appendChild(meter);
        wrap.appendChild(cap);
    }

    appendAssistantSourceLinks(wrap, options.sources || [], "Official portals (verified)");
    if (options.nextStep && options.nextStep.trim()) {
        const step = document.createElement("div");
        step.className = "near-miss-panel";
        const h = document.createElement("div");
        h.className = "near-miss-panel-title";
        h.textContent = "Next step";
        const body = document.createElement("div");
        body.className = "near-miss-panel-body";
        body.textContent = options.nextStep.trim();
        step.appendChild(h);
        step.appendChild(body);
        wrap.appendChild(step);
    }
    chat.appendChild(wrap);
    wrap.scrollIntoView({ behavior: "smooth", block: "end" });
}

export function renderSchemePills(sessionSchemeNames) {
    const host = document.getElementById("schemePills");
    if (!host) return;
    host.innerHTML = "";
    sessionSchemeNames.forEach((name) => {
        const span = document.createElement("span");
        span.className = "scheme-pill";
        span.textContent = name;
        host.appendChild(span);
    });
}

export function showTypingIndicator() {
    const chat = document.getElementById("conversation");
    if (!chat || document.getElementById("typing")) return;
    const t = document.createElement("div");
    t.className = "typing-indicator";
    t.id = "typing";
    t.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    chat.appendChild(t);
}

export function removeTypingIndicator() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}

export function setStatusIndicator(text, colorKey) {
    const st = document.getElementById("statusText") || document.querySelector(".status-text");
    const d = document.getElementById("statusDot") || document.querySelector(".status-dot");
    if (st) st.textContent = text;
    if (d) {
        const colorMap = {
            green: "var(--color-success)",
            orange: "var(--color-accent)",
            red: "var(--color-error)",
            yellow: "var(--color-warn)",
            blue: "#5dade2",
        };
        d.style.background = colorMap[colorKey] || colorMap.green;
        const pulse = text === "Thinking..." || text === "Listening...";
        d.classList.toggle("pulse", pulse);
    }
}

export function updateLanguageUI(lang) {
    const hint = document.getElementById("voiceHint");
    if (hint) hint.textContent = `Listening for: ${LANGUAGE_LABELS[lang] || lang}`;
    const sidebarLang = document.getElementById("sidebarLangDisplay");
    if (sidebarLang) {
        const flag = LANGUAGE_FLAGS[lang] || "🇮🇳";
        sidebarLang.textContent = `${flag} ${LANGUAGE_LABELS[lang] || lang}`;
    }
}

export function downloadConversationTranscript() {
    const chat = document.getElementById("conversation");
    if (!chat) return;
    const lines = [];
    chat.querySelectorAll(".message, .source-links-block, .citation-source-block").forEach((node) => {
        let speaker = "Assistant";
        if (node.classList.contains("user")) speaker = "You";
        if (node.classList.contains("error")) speaker = "System";
        if (node.classList.contains("moderation-block")) speaker = "Notice";
        if (node.classList.contains("source-links-block")) speaker = "Links";
        if (node.classList.contains("citation-source-block")) speaker = "Sources";
        lines.push(`${speaker}: ${node.textContent.trim()}`);
    });
    const blob = new Blob([lines.join("\n\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sahayaksetu-chat.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

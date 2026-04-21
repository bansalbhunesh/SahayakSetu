import { LANGUAGE_FLAGS, LANGUAGE_LABELS } from "./constants.js";

export function confidenceEmojiForLabel(label) {
    if (!label) return "";
    if (/strong match/i.test(label) || /verified/i.test(label)) return "🟢 ";
    if (/moderate/i.test(label)) return "🟡 ";
    return "🟠 ";
}

function confidenceMeta(confidence, score) {
    const bounded = Math.max(0, Math.min(1, typeof score === "number" ? score : 0));
    if (confidence === "high") return { status: "verified", label: "VERIFIED", score: bounded, grounded: "Grounded match" };
    if (confidence === "medium") return { status: "partial", label: "PARTIAL", score: bounded, grounded: "Needs verification" };
    return { status: "unverified", label: "UNVERIFIED", score: bounded, grounded: "Needs more profile info" };
}

function renderConfidenceArc(confidence, score) {
    const meta = confidenceMeta(confidence, score);
    const pct = Math.round(meta.score * 100);
    const host = document.createElement("div");
    host.className = "confidence-arc";
    host.dataset.status = meta.status;
    host.style.setProperty("--pct", String(pct));
    host.innerHTML = `
      <svg viewBox="0 0 64 64" class="arc-svg" aria-hidden="true">
        <path class="arc-bg" d="M 8 44 A 24 24 0 1 1 56 44"></path>
        <path class="arc-fill" d="M 8 44 A 24 24 0 1 1 56 44" pathLength="100"></path>
      </svg>
      <div class="arc-score">${meta.score.toFixed(2)}</div>
      <div class="arc-label">${meta.label}</div>
      <div class="arc-sub">${meta.grounded}</div>
    `;
    return host;
}

function renderQueryUnderstanding(queryDebug) {
    if (!queryDebug || !queryDebug.original || !queryDebug.rewritten) return null;
    const box = document.createElement("div");
    box.className = "query-understanding";
    box.innerHTML = `
      <span class="qu-raw">${queryDebug.original}</span>
      <span class="qu-arrow">→</span>
      <span class="qu-parsed">${queryDebug.rewritten}</span>
    `;
    return box;
}

function renderNextStepPanel(nextStep) {
    if (!nextStep || !nextStep.trim()) return null;
    const panel = document.createElement("section");
    panel.className = "next-step";
    panel.innerHTML = `
      <header class="ns-head">
        <span class="ns-kicker">NEXT STEP</span>
        <span class="ns-est">⏱ quick action</span>
      </header>
      <ol class="ns-track">
        <li class="ns-step">
          <span class="ns-dot">1</span>
          <div><strong>${nextStep.trim()}</strong><p>Use official links below to continue safely.</p></div>
        </li>
      </ol>
    `;
    return panel;
}

function verdictClass(verdict) {
    const v = (verdict || "").toLowerCase();
    if (v === "eligible") return "ap-v-ok";
    if (v === "likely_eligible") return "ap-v-mid";
    if (v === "likely_ineligible") return "ap-v-bad";
    return "ap-v-unknown";
}

function renderPlanPanel(plan) {
    if (!plan || typeof plan !== "object") return null;
    const steps = Array.isArray(plan.steps) ? plan.steps : [];
    const docs = Array.isArray(plan.documents_needed) ? plan.documents_needed : [];
    const eligibility = Array.isArray(plan.eligibility) ? plan.eligibility : [];
    const questions = Array.isArray(plan.clarifying_questions) ? plan.clarifying_questions : [];
    const disclaimer = typeof plan.disclaimer === "string" ? plan.disclaimer.trim() : "";
    const rawStatus = typeof plan.status === "string" ? plan.status : "";
    const statusLabel = rawStatus ? rawStatus.replaceAll("_", " ") : "plan";

    const hasBody =
        steps.length || docs.length || eligibility.length || questions.length || disclaimer;
    if (!hasBody) return null;

    const panel = document.createElement("section");
    panel.className = "action-plan-panel";
    panel.setAttribute("aria-label", "Action plan");

    const head = document.createElement("header");
    head.className = "ap-head";
    const kicker = document.createElement("span");
    kicker.className = "ap-kicker";
    kicker.textContent = "Action plan";
    const badge = document.createElement("span");
    badge.className = `ap-status-badge ap-status-${rawStatus.replace(/_/g, "-") || "unknown"}`;
    badge.textContent = statusLabel;
    head.append(kicker, badge);
    panel.appendChild(head);

    if (eligibility.length) {
        const sub = document.createElement("p");
        sub.className = "ap-subtitle";
        sub.textContent = "Eligibility snapshot";
        panel.appendChild(sub);
        const grid = document.createElement("div");
        grid.className = "ap-eligibility-grid";
        eligibility.slice(0, 6).forEach((row, i) => {
            const card = document.createElement("article");
            card.className = `ap-e-card ap-animate-in ap-delay-${Math.min(i + 1, 6)}`;
            const v = document.createElement("span");
            v.className = `ap-verdict-pill ${verdictClass(row.verdict)}`;
            v.textContent = (row.verdict || "unknown").replaceAll("_", " ");
            const title = document.createElement("h4");
            title.className = "ap-e-title";
            title.textContent = row.scheme || "Scheme";
            const meta = document.createElement("p");
            meta.className = "ap-e-meta";
            meta.textContent = row.source_id ? `Source ${row.source_id}` : "";
            card.append(v, title, meta);
            grid.appendChild(card);
        });
        panel.appendChild(grid);
    }

    if (docs.length) {
        const docTitle = document.createElement("p");
        docTitle.className = "ap-subtitle";
        docTitle.textContent = "Documents to keep ready";
        panel.appendChild(docTitle);
        const chips = document.createElement("div");
        chips.className = "ap-doc-chips";
        docs.slice(0, 10).forEach((d, i) => {
            const span = document.createElement("span");
            span.className = `ap-chip ap-animate-in ap-delay-${Math.min(i + 1, 6)}`;
            span.textContent = d;
            chips.appendChild(span);
        });
        panel.appendChild(chips);
    }

    if (steps.length) {
        const stTitle = document.createElement("p");
        stTitle.className = "ap-subtitle";
        stTitle.textContent = "Steps";
        panel.appendChild(stTitle);
        const track = document.createElement("ol");
        track.className = "ap-track";
        steps.slice(0, 8).forEach((step, idx) => {
            const li = document.createElement("li");
            li.className = `ap-step ap-animate-in ap-delay-${Math.min(idx + 1, 8)}`;
            const dot = document.createElement("span");
            dot.className = "ap-dot";
            dot.textContent = String(step.order || idx + 1);
            const body = document.createElement("div");
            const strong = document.createElement("strong");
            strong.textContent = step.action || "Action";
            const detail = document.createElement("p");
            detail.className = "ap-step-detail";
            const where = (step.where || "").trim();
            const est = (step.estimated_time || "").trim();
            if (where) {
                const w = document.createElement("span");
                w.className = "ap-where";
                w.textContent = where;
                detail.appendChild(w);
            }
            if (est) {
                const t = document.createElement("span");
                t.className = "ap-time";
                t.textContent = est;
                detail.appendChild(t);
            }
            body.append(strong, detail);
            li.append(dot, body);
            track.appendChild(li);
        });
        panel.appendChild(track);
    }

    if (questions.length) {
        const qTitle = document.createElement("p");
        qTitle.className = "ap-subtitle";
        qTitle.textContent = "To tailor this further";
        panel.appendChild(qTitle);
        const ul = document.createElement("ul");
        ul.className = "ap-questions";
        questions.slice(0, 5).forEach((q, i) => {
            const li = document.createElement("li");
            li.className = `ap-animate-in ap-delay-${Math.min(i + 1, 5)}`;
            li.textContent = q;
            ul.appendChild(li);
        });
        panel.appendChild(ul);
    }

    if (disclaimer) {
        const foot = document.createElement("footer");
        foot.className = "ap-disclaimer";
        foot.textContent = disclaimer;
        panel.appendChild(foot);
    }

    return panel;
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

function verdictEmoji(verdict) {
    if (verdict === "likely_eligible") return "✅";
    if (verdict === "likely_ineligible") return "❌";
    return "❓";
}

function renderEligibilityHintsPanel(hints) {
    if (!Array.isArray(hints) || !hints.length) return null;
    const panel = document.createElement("div");
    panel.className = "eligibility-hints-panel";
    const h = document.createElement("div");
    h.className = "eligibility-hints-title";
    h.textContent = "Quick eligibility check (best-effort)";
    panel.appendChild(h);
    hints.forEach((row) => {
        const line = document.createElement("div");
        line.className = "eligibility-hint-row";
        const scheme = row.scheme || "Scheme";
        const reason = row.reason || "";
        line.textContent = `${verdictEmoji(row.verdict)} ${scheme} — ${reason}`;
        panel.appendChild(line);
    });
    return panel;
}

function appendAssistantSourceLinks(container, sources, headingText) {
    if (!Array.isArray(sources) || !sources.length) return;
    const rows = sources.filter((s) => s.apply_link || s.source);
    if (!rows.length) return;

    const block = document.createElement("div");
    block.className = "source-links-block";
    const heading = document.createElement("div");
    heading.className = "source-links-heading";
    heading.textContent = headingText || "Where this answer comes from";
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
    if (options.confidence) wrap.appendChild(renderConfidenceArc(options.confidence, options.topScore));
    const queryPill = renderQueryUnderstanding(options.queryDebug);
    if (queryPill) wrap.appendChild(queryPill);
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
        h.textContent = "How this answer was chosen";
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
        h.textContent = "Possible mismatch (what to check next)";
        panel.appendChild(h);
        if (nearText && nearText.trim()) {
            const body = document.createElement("div");
            body.className = "near-miss-panel-body";
            body.textContent = nearText.trim();
            panel.appendChild(body);
        }
        if (nearSrc.length) {
            appendAssistantSourceLinks(panel, nearSrc, "Related references (lower match)");
        }
        wrap.appendChild(panel);
    }

    const eligPanel = renderEligibilityHintsPanel(options.eligibilityHints);
    if (eligPanel) wrap.appendChild(eligPanel);

    appendAssistantSourceLinks(wrap, options.sources || [], "Where this answer comes from");
    const next = renderNextStepPanel(options.nextStep);
    if (next) wrap.appendChild(next);
    const plan = renderPlanPanel(options.plan);
    if (plan) wrap.appendChild(plan);
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
        const pulse =
            text === "Thinking..." || text === "Listening..." || text === "Speaking...";
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

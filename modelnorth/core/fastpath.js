/**
 * ModelNorth HyperBrowser - Tier 0 In-Browser Heuristic Compiler
 * Copyright 2026 ModelNorth Sovereign AI - Apache 2.0
 */
((instruction) => {
    if (!instruction || typeof instruction !== 'string') {
        return { matched: false, reason: "No instruction provided" };
    }

    const cleanGoal = instruction.trim().toLowerCase();

    function normalizeText(text) {
        return (text || '').toLowerCase().replace(/\s+/g, ' ').trim();
    }

    function findNodeById(root, id) {
        if (!root) return null;
        let el = null;
        try {
            el = root.querySelector(`[data-mn-id="${id}"]`);
        } catch (_) {}
        if (el) return el;

        let allEls = [];
        try {
            allEls = root.querySelectorAll('*');
        } catch (_) {}
        for (const child of allEls) {
            if (child.shadowRoot) {
                const res = findNodeById(child.shadowRoot, id);
                if (res) return res;
            }
            if (child.tagName === 'IFRAME') {
                try {
                    const doc = child.contentDocument || (child.contentWindow && child.contentWindow.document);
                    if (doc) {
                        const res = findNodeById(doc, id);
                        if (res) return res;
                    }
                } catch (_) {}
            }
        }
        return null;
    }

    function getAllTaggedNodes(root) {
        let results = [];
        if (!root) return results;
        try {
            results.push(...root.querySelectorAll('[data-mn-id]'));
        } catch (_) {}
        let allEls = [];
        try {
            allEls = root.querySelectorAll('*');
        } catch (_) {}
        for (const child of allEls) {
            if (child.shadowRoot) {
                results.push(...getAllTaggedNodes(child.shadowRoot));
            }
            if (child.tagName === 'IFRAME') {
                try {
                    const doc = child.contentDocument || (child.contentWindow && child.contentWindow.document);
                    if (doc) results.push(...getAllTaggedNodes(doc));
                } catch (_) {}
            }
        }
        return results;
    }

    const allNodes = getAllTaggedNodes(document);

    // Pattern 1: Keyboard actions e.g. 'press enter', 'hit escape', 'press tab'
    const keyMatch = cleanGoal.match(/^(?:press|hit|send key)\s+([a-z0-9_]+)$/i);
    if (keyMatch) {
        const keyName = keyMatch[1].toLowerCase();
        return {
            matched: true,
            tier: 0,
            action: "KEY_PRESS",
            key: keyName,
            confidence: 1.0
        };
    }

    // Pattern 2: Check / Uncheck checkboxes
    const checkMatch = cleanGoal.match(/(?:check|uncheck|toggle)\s+["']?([^"']+)["']?/i);
    if (checkMatch) {
        const targetLabel = normalizeText(checkMatch[1]);
        for (const node of allNodes) {
            const role = (node.getAttribute('role') || node.type || '').toLowerCase();
            if (role === 'checkbox' || role === 'switch' || role === 'radio') {
                const text = normalizeText(node.innerText || node.textContent || node.getAttribute('aria-label') || '');
                if (text.includes(targetLabel) || targetLabel.includes(text)) {
                    const id = parseInt(node.getAttribute('data-mn-id'), 10);
                    return {
                        matched: true,
                        tier: 0,
                        action: "CLICK",
                        targetId: id,
                        targetName: text,
                        confidence: 0.95
                    };
                }
            }
        }
    }

    // Pattern 3: Select dropdown value e.g. 'select "Economy" from "Class"'
    const selectMatch = cleanGoal.match(/(?:select|choose|pick)\s+["']([^"']+)["'](?:\s+from\s+["']?([^"']+)["']?)?/i);
    if (selectMatch) {
        const optionVal = normalizeText(selectMatch[1]);
        const dropdownLabel = selectMatch[2] ? normalizeText(selectMatch[2]) : null;

        for (const node of allNodes) {
            if (node.tagName === 'SELECT') {
                const label = normalizeText(node.getAttribute('aria-label') || node.name || '');
                if (!dropdownLabel || label.includes(dropdownLabel)) {
                    const id = parseInt(node.getAttribute('data-mn-id'), 10);
                    return {
                        matched: true,
                        tier: 0,
                        action: "SELECT_OPTION",
                        targetId: id,
                        targetName: label || "select",
                        value: optionVal,
                        confidence: 0.95
                    };
                }
            }
        }
    }

    // Pattern 4: Direct text fill e.g. 'type "Zurich" into "Where from?"' or 'enter "test@example.com" in email'
    const typeMatch = cleanGoal.match(/(?:type|enter|write|input)\s+["']([^"']+)["']\s+(?:into|in|to)\s+["']?([^"']+)["']?/i);
    if (typeMatch) {
        const textToType = typeMatch[1];
        const fieldLabel = normalizeText(typeMatch[2]);

        for (const node of allNodes) {
            const tag = node.tagName.toLowerCase();
            const role = (node.getAttribute('role') || '').toLowerCase();
            if (tag === 'input' || tag === 'textarea' || node.isContentEditable || role === 'textbox' || role === 'combobox') {
                const id = parseInt(node.getAttribute('data-mn-id'), 10);
                const label = normalizeText(
                    node.getAttribute('placeholder') ||
                    node.getAttribute('aria-label') ||
                    node.getAttribute('name') ||
                    node.innerText ||
                    ''
                );

                if (label.includes(fieldLabel) || fieldLabel.includes(label)) {
                    return {
                        matched: true,
                        tier: 0,
                        action: "TYPE_TEXT",
                        targetId: id,
                        targetName: label,
                        text: textToType,
                        confidence: 0.95
                    };
                }
            }
        }
    }

    // Pattern 5: Click commands e.g. 'click "Search"', 'tap on Flights', 'press Continue'
    const clickMatch = cleanGoal.match(/(?:click|tap|press|open link)\s+["']?([^"']+)["']?/i);
    if (clickMatch) {
        const targetLabel = normalizeText(clickMatch[1]);
        let exactMatch = null;
        let partialMatches = [];

        for (const node of allNodes) {
            const id = parseInt(node.getAttribute('data-mn-id'), 10);
            const text = normalizeText(node.innerText || node.textContent || node.getAttribute('aria-label') || node.getAttribute('placeholder') || '');
            
            if (text === targetLabel) {
                exactMatch = { id, text };
                break;
            } else if (text.includes(targetLabel) || (targetLabel.length > 3 && targetLabel.includes(text) && text.length > 2)) {
                partialMatches.push({ id, text });
            }
        }

        if (exactMatch) {
            return {
                matched: true,
                tier: 0,
                action: "CLICK",
                targetId: exactMatch.id,
                targetName: exactMatch.text,
                confidence: 1.0
            };
        } else if (partialMatches.length === 1) {
            return {
                matched: true,
                tier: 0,
                action: "CLICK",
                targetId: partialMatches[0].id,
                targetName: partialMatches[0].text,
                confidence: 0.90
            };
        }
    }

    return {
        matched: false,
        reason: "Requires Tier 1 System 1 classification or multi-candidate disambiguation"
    };
})

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

    // Pattern 1: Click commands e.g. 'click "Search"', 'tap on Flights', 'press Continue'
    const clickMatch = cleanGoal.match(/(?:click|tap|press|select button|open link)\s+["']?([^"']+)["']?/i);
    if (clickMatch) {
        const targetLabel = normalizeText(clickMatch[1]);
        const nodes = document.querySelectorAll('[data-mn-id]');
        
        let exactMatch = null;
        let partialMatches = [];

        for (const node of nodes) {
            const id = parseInt(node.getAttribute('data-mn-id'), 10);
            const text = normalizeText(node.innerText || node.textContent || node.getAttribute('aria-label') || node.getAttribute('placeholder') || '');
            
            if (text === targetLabel) {
                exactMatch = { id, text, node };
                break;
            } else if (text.includes(targetLabel) || targetLabel.includes(text)) {
                partialMatches.push({ id, text, node });
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

    // Pattern 2: Direct text fill e.g. 'type "Zurich" into "Where from?"' or 'enter "test@example.com" in email'
    const typeMatch = cleanGoal.match(/(?:type|enter|write|input)\s+["']([^"']+)["']\s+(?:into|in|to)\s+["']?([^"']+)["']?/i);
    if (typeMatch) {
        const textToType = typeMatch[1];
        const fieldLabel = normalizeText(typeMatch[2]);
        const inputs = document.querySelectorAll('input[data-mn-id], textarea[data-mn-id], [contenteditable="true"][data-mn-id]');

        for (const node of inputs) {
            const id = parseInt(node.getAttribute('data-mn-id'), 10);
            const label = normalizeText(
                node.getAttribute('placeholder') ||
                node.getAttribute('aria-label') ||
                node.getAttribute('name') ||
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

    return {
        matched: false,
        reason: "Requires Tier 1 System 1 classification or multi-candidate disambiguation"
    };
})

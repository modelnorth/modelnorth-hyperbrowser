/**
 * ModelNorth HyperBrowser - Atomic DOM Snapshot & Recursive Shadow/iframe Control Indexer
 * Copyright 2026 ModelNorth Sovereign AI - Apache 2.0
 */
(() => {
    const INTERACTIVE_SELECTORS = [
        'button',
        'input:not([type="hidden"])',
        'textarea',
        'select',
        'a[href]',
        '[role="button"]',
        '[role="combobox"]',
        '[role="textbox"]',
        '[role="checkbox"]',
        '[role="radio"]',
        '[role="tab"]',
        '[role="menuitem"]',
        '[role="option"]',
        '[role="switch"]',
        '[contenteditable="true"]',
        '[tabindex]:not([tabindex="-1"])'
    ].join(',');

    const CAPTCHA_SELECTORS = [
        'iframe[src*="captcha" i]',
        'iframe[src*="turnstile" i]',
        'iframe[src*="recaptcha" i]',
        'iframe[src*="hcaptcha" i]',
        '.g-recaptcha',
        '.h-captcha',
        '#cf-challenge-running',
        '#challenge-stage'
    ].join(',');

    const viewportW = window.innerWidth || document.documentElement.clientWidth;
    const viewportH = window.innerHeight || document.documentElement.clientHeight;

    function isVisible(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return false;
        const win = el.ownerDocument ? (el.ownerDocument.defaultView || window) : window;
        const style = win.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        return (
            rect.bottom >= -100 &&
            rect.top <= viewportH + 100 &&
            rect.right >= -100 &&
            rect.left <= viewportW + 100
        );
    }

    function isOccluded(el) {
        const rect = el.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        if (cx < 0 || cx > viewportW || cy < 0 || cy > viewportH) return false;
        const doc = el.ownerDocument || document;
        const topEl = doc.elementFromPoint(cx, cy);
        if (!topEl) return false;
        if (topEl === el || el.contains(topEl) || topEl.contains(el)) return false;

        // In Shadow DOM, elementFromPoint returns host
        const rootNode = el.getRootNode ? el.getRootNode() : null;
        if (rootNode && rootNode.host && (rootNode.host === topEl || rootNode.host.contains(topEl) || topEl.contains(rootNode.host))) {
            return false;
        }

        return true;
    }

    function getAccessibleName(el) {
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const doc = el.ownerDocument || document;
            const labelNode = doc.getElementById(labelledBy);
            if (labelNode && labelNode.textContent.trim()) return labelNode.textContent.trim();
        }

        const placeholder = el.getAttribute('placeholder');
        if (placeholder && placeholder.trim()) return placeholder.trim();

        const title = el.getAttribute('title');
        if (title && title.trim()) return title.trim();

        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            const val = el.value || '';
            if (val.trim()) return val.trim();
        }

        const text = el.innerText || el.textContent || '';
        return text.replace(/\s+/g, ' ').trim().slice(0, 100);
    }

    function getControlRole(el) {
        const explicitRole = el.getAttribute('role');
        if (explicitRole) return explicitRole.toLowerCase();
        const tag = el.tagName.toLowerCase();
        if (tag === 'button') return 'button';
        if (tag === 'select') return 'combobox';
        if (tag === 'textarea') return 'textbox';
        if (tag === 'a') return 'link';
        if (tag === 'input') {
            const type = (el.getAttribute('type') || 'text').toLowerCase();
            if (['button', 'submit', 'reset'].includes(type)) return 'button';
            if (['checkbox', 'radio'].includes(type)) return type;
            return 'textbox';
        }
        return 'clickable';
    }

    // Clean previous tags across all shadow roots
    function cleanPreviousIds(root) {
        if (!root || !root.querySelectorAll) return;
        try {
            root.querySelectorAll('[data-mn-id]').forEach(node => node.removeAttribute('data-mn-id'));
            root.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) cleanPreviousIds(el.shadowRoot);
            });
        } catch (_) {}
    }

    cleanPreviousIds(document);

    const elements = [];
    let counter = { val: 1 };
    let canvasCount = 0;
    let hasCaptcha = false;

    function crawlTree(root) {
        if (!root) return;

        // Check for captcha in current root
        try {
            if (root.querySelectorAll(CAPTCHA_SELECTORS).length > 0) {
                hasCaptcha = true;
            }
            canvasCount += root.querySelectorAll('canvas').length;
        } catch (_) {}

        // Interactive nodes
        let nodes = [];
        try {
            nodes = root.querySelectorAll(INTERACTIVE_SELECTORS);
        } catch (_) {}

        for (let i = 0; i < nodes.length; i++) {
            const el = nodes[i];
            if (!isVisible(el)) continue;
            if (isOccluded(el)) continue;

            const role = getControlRole(el);
            const name = getAccessibleName(el);
            const rect = el.getBoundingClientRect();
            const id = counter.val;
            counter.val++;

            el.setAttribute('data-mn-id', String(id));

            elements.push({
                id: id,
                tag: el.tagName.toLowerCase(),
                role: role,
                name: name,
                value: el.value || null,
                disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                checked: el.checked || el.getAttribute('aria-checked') === 'true' || null,
                selected: el.selected || el.getAttribute('aria-selected') === 'true' || null,
                expanded: el.getAttribute('aria-expanded') === 'true' || null,
                rect: {
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                }
            });
        }

        // Recursively crawl all child shadow roots and iframes
        let allEls = [];
        try {
            allEls = root.querySelectorAll('*');
        } catch (_) {}

        for (let i = 0; i < allEls.length; i++) {
            const el = allEls[i];
            if (el.shadowRoot) {
                crawlTree(el.shadowRoot);
            }
            if (el.tagName === 'IFRAME') {
                try {
                    const doc = el.contentDocument || (el.contentWindow && el.contentWindow.document);
                    if (doc) crawlTree(doc);
                } catch (_) {}
            }
        }
    }

    crawlTree(document);

    const title = document.title || '';
    const url = window.location.href || '';

    return {
        url: url,
        title: title,
        elements: elements,
        visualTriggers: {
            hasCanvas: canvasCount > 0,
            canvasCount: canvasCount,
            hasCaptcha: hasCaptcha,
            viewport: { width: viewportW, height: viewportH }
        }
    };
})();

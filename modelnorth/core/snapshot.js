/**
 * ModelNorth HyperBrowser - Atomic DOM Snapshot & Control Indexer
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
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        // In or reasonably near viewport
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
        const topEl = document.elementFromPoint(cx, cy);
        if (!topEl) return false;
        return topEl !== el && !el.contains(topEl) && !topEl.contains(el);
    }

    function getAccessibleName(el) {
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelNode = document.getElementById(labelledBy);
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

    // Clear previous transient mn-ids
    document.querySelectorAll('[data-mn-id]').forEach(node => node.removeAttribute('data-mn-id'));

    const elements = [];
    const rawNodes = document.querySelectorAll(INTERACTIVE_SELECTORS);
    let index = 1;

    for (let i = 0; i < rawNodes.length; i++) {
        const el = rawNodes[i];
        if (!isVisible(el)) continue;
        if (isOccluded(el)) continue;

        const role = getControlRole(el);
        const name = getAccessibleName(el);
        const rect = el.getBoundingClientRect();

        el.setAttribute('data-mn-id', String(index));

        elements.push({
            id: index,
            tag: el.tagName.toLowerCase(),
            role: role,
            name: name,
            value: el.value || null,
            disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
            rect: {
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        });

        index++;
    }

    // Anomaly & Visual Sentry Triggers
    const canvasCount = document.querySelectorAll('canvas').length;
    const hasCaptcha = document.querySelectorAll(CAPTCHA_SELECTORS).length > 0;
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

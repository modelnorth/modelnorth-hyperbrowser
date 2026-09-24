/**
 * ModelNorth HyperBrowser - Stealth & Anti-Bot Fingerprint Defense
 * Copyright 2026 ModelNorth Sovereign AI - Apache 2.0
 */
(() => {
    'use strict';

    // 1. Mask navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. Mock navigator.languages & platform
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true
    });

    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                description: 'Portable Document Format',
                filename: 'internal-pdf-viewer',
                length: 1,
                name: 'Chrome PDF Plugin'
            },
            {
                0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                description: 'Portable Document Format',
                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                length: 1,
                name: 'Chrome PDF Viewer'
            }
        ],
        configurable: true
    });

    // 3. Mock window.chrome runtime
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
            PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' },
            PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' },
            connect: () => {},
            sendMessage: () => {}
        };
    }

    // 4. WebGL Vendor Spoofing
    const getParameterProto = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return getParameterProto.apply(this, arguments);
    };

    // 5. Spoof permissions query
    if (navigator.permissions && navigator.permissions.query) {
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    }
})();

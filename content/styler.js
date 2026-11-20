/**
 * VISIONFREE — In-Page Styling Engine (content/styler.js)
 * Phase 3: Enhanced Non-Destructive DOM & Content Presentation Engine
 *
 * Responsibilities:
 * 1. Safely injects a scoped, non-destructive stylesheet (#visionfree-engine-style).
 * 2. Applies subtle, readable typographic enhancements via CSS custom properties.
 * 3. Enforces strict exemptions for interactive controls, forms, links, media, and code.
 * 4. Provides ensureAttached() for SPA dynamic route resilience.
 * 5. Completely cleans up all injected styles and root attributes upon deactivation.
 */

(function (global) {
  'use strict';

  const STYLE_ELEMENT_ID = 'visionfree-engine-style';
  const ROOT_ACTIVE_ATTR = 'data-visionfree-active';

  // Cached current settings for re-attachment during SPA route transitions
  let currentActiveSettings = null;

  const VisionFreeStyler = {
    /**
     * Checks if the VISIONFREE styling engine is currently active on the page.
     * @returns {boolean}
     */
    isActive() {
      const hasStyleTag = Boolean(document.getElementById(STYLE_ELEMENT_ID));
      const hasRootAttr = document.documentElement?.hasAttribute(ROOT_ACTIVE_ATTR);
      return hasStyleTag || hasRootAttr;
    },

    /**
     * Returns currently applied settings or null if inactive.
     */
    getCurrentSettings() {
      return currentActiveSettings;
    },

    /**
     * Generates scoped CSS rules using CSS custom properties.
     * @param {Object} settings
     * @returns {string}
     */
    _buildCSS(settings) {
      const lineSpacing = settings.lineSpacing || '1.6';
      const letterSpacing = settings.letterSpacing || '0.02em';
      const fontWeightDelta = settings.fontWeightDelta || '0';
      const highContrastText = Boolean(settings.highContrastText);

      // Compute heading line spacing (proportionate: 1.25x - 1.35x)
      const numSpacing = parseFloat(lineSpacing) || 1.6;
      const headingSpacing = Math.min(1.4, Math.max(1.2, numSpacing * 0.8)).toFixed(2);

      // Font weight adjustment
      let fontWeightCSS = '';
      if (fontWeightDelta === '100') {
        fontWeightCSS = 'font-weight: 500 !important;';
      } else if (fontWeightDelta === '200') {
        fontWeightCSS = 'font-weight: 600 !important;';
      }

      // Micro-contrast accentuation (gentle edge prominence without darkening the background)
      const contrastCSS = highContrastText
        ? 'text-shadow: 0 0 0.5px rgba(0, 0, 0, 0.45) !important;'
        : '';

      return `
        /* ========================================================
           VISIONFREE In-Page Styling Engine (Phase 3)
           Unique ID: ${STYLE_ELEMENT_ID}
           ======================================================== */

        :root[${ROOT_ACTIVE_ATTR}="true"] {
          --vf-line-height: ${lineSpacing};
          --vf-heading-line-height: ${headingSpacing};
          --vf-letter-spacing: ${letterSpacing};
        }

        /* --- A. Reading Content: Paragraphs, Articles & Blockquotes --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] p,
        :root[${ROOT_ACTIVE_ATTR}="true"] article p,
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="article"] p,
        :root[${ROOT_ACTIVE_ATTR}="true"] main p,
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="main"] p,
        :root[${ROOT_ACTIVE_ATTR}="true"] blockquote,
        :root[${ROOT_ACTIVE_ATTR}="true"] dd {
          line-height: var(--vf-line-height, 1.6) !important;
          letter-spacing: var(--vf-letter-spacing, 0.02em) !important;
          ${fontWeightCSS}
          ${contrastCSS}
        }

        /* --- B. Reading Content: Lists & List Items --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] li,
        :root[${ROOT_ACTIVE_ATTR}="true"] dt {
          line-height: var(--vf-line-height, 1.6) !important;
          letter-spacing: var(--vf-letter-spacing, 0.02em) !important;
          ${fontWeightCSS}
        }

        /* --- C. Headings (Proportionate Spacing) --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] h1,
        :root[${ROOT_ACTIVE_ATTR}="true"] h2,
        :root[${ROOT_ACTIVE_ATTR}="true"] h3,
        :root[${ROOT_ACTIVE_ATTR}="true"] h4,
        :root[${ROOT_ACTIVE_ATTR}="true"] h5,
        :root[${ROOT_ACTIVE_ATTR}="true"] h6 {
          line-height: var(--vf-heading-line-height, 1.25) !important;
          letter-spacing: var(--vf-letter-spacing, 0.02em) !important;
          ${contrastCSS}
        }

        /* --- D. Links: Maintain Normal Functionality, Hover & Cursor --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] a {
          letter-spacing: var(--vf-letter-spacing, 0.02em);
          cursor: pointer !important;
        }

        /* --- E. Interactive Elements Preservation (Zero Modification) --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] button,
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="button"],
        :root[${ROOT_ACTIVE_ATTR}="true"] input,
        :root[${ROOT_ACTIVE_ATTR}="true"] textarea,
        :root[${ROOT_ACTIVE_ATTR}="true"] select,
        :root[${ROOT_ACTIVE_ATTR}="true"] option,
        :root[${ROOT_ACTIVE_ATTR}="true"] optgroup,
        :root[${ROOT_ACTIVE_ATTR}="true"] datalist,
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="combobox"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="listbox"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="menu"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="menuitem"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="tab"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [role="switch"] {
          letter-spacing: normal !important;
          line-height: normal;
        }

        /* --- F. Special Content: Code, Math, Embedded Media & Icons --- */
        :root[${ROOT_ACTIVE_ATTR}="true"] pre,
        :root[${ROOT_ACTIVE_ATTR}="true"] code,
        :root[${ROOT_ACTIVE_ATTR}="true"] kbd,
        :root[${ROOT_ACTIVE_ATTR}="true"] samp,
        :root[${ROOT_ACTIVE_ATTR}="true"] math,
        :root[${ROOT_ACTIVE_ATTR}="true"] .katex,
        :root[${ROOT_ACTIVE_ATTR}="true"] .MathJax,
        :root[${ROOT_ACTIVE_ATTR}="true"] mjx-container,
        :root[${ROOT_ACTIVE_ATTR}="true"] svg,
        :root[${ROOT_ACTIVE_ATTR}="true"] svg *,
        :root[${ROOT_ACTIVE_ATTR}="true"] canvas,
        :root[${ROOT_ACTIVE_ATTR}="true"] video,
        :root[${ROOT_ACTIVE_ATTR}="true"] audio,
        :root[${ROOT_ACTIVE_ATTR}="true"] img,
        :root[${ROOT_ACTIVE_ATTR}="true"] picture,
        :root[${ROOT_ACTIVE_ATTR}="true"] iframe,
        :root[${ROOT_ACTIVE_ATTR}="true"] [class*="icon"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [class*="fa-"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [class*="material-icons"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [contenteditable="true"],
        :root[${ROOT_ACTIVE_ATTR}="true"] [contenteditable=""],
        :root[${ROOT_ACTIVE_ATTR}="true"] .monaco-editor,
        :root[${ROOT_ACTIVE_ATTR}="true"] .CodeMirror {
          letter-spacing: normal !important;
          line-height: normal;
        }
      `;
    },

    /**
     * Injects or updates the scoped stylesheet with current user settings.
     * @param {Object} settings
     */
    apply(settings = {}) {
      currentActiveSettings = { ...settings };
      const cssRules = this._buildCSS(currentActiveSettings);

      // Get or create dedicated style tag
      let styleEl = document.getElementById(STYLE_ELEMENT_ID);
      if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = STYLE_ELEMENT_ID;
        styleEl.type = 'text/css';
        (document.head || document.documentElement).appendChild(styleEl);
      }

      styleEl.textContent = cssRules;

      // Mark document root
      if (document.documentElement) {
        document.documentElement.setAttribute(ROOT_ACTIVE_ATTR, 'true');
      }

      return true;
    },

    /**
     * Verifies that the stylesheet and root attribute are present.
     * Used by MutationObserver to restore styles if an SPA wipes head tags during a route change.
     */
    ensureAttached() {
      if (!currentActiveSettings) return false;

      let reattached = false;
      let styleEl = document.getElementById(STYLE_ELEMENT_ID);
      if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = STYLE_ELEMENT_ID;
        styleEl.type = 'text/css';
        styleEl.textContent = this._buildCSS(currentActiveSettings);
        (document.head || document.documentElement).appendChild(styleEl);
        reattached = true;
      }

      if (document.documentElement && !document.documentElement.hasAttribute(ROOT_ACTIVE_ATTR)) {
        document.documentElement.setAttribute(ROOT_ACTIVE_ATTR, 'true');
        reattached = true;
      }

      return reattached;
    },

    /**
     * Completely removes the injected stylesheet and root attribute.
     * Restores the page to its pristine, pre-activation state.
     */
    remove() {
      currentActiveSettings = null;

      // 1. Remove style element
      const styleEl = document.getElementById(STYLE_ELEMENT_ID);
      if (styleEl && styleEl.parentNode) {
        styleEl.parentNode.removeChild(styleEl);
      }

      // 2. Remove root activation attribute
      if (document.documentElement) {
        document.documentElement.removeAttribute(ROOT_ACTIVE_ATTR);
      }

      return true;
    }
  };

  // Expose on globalThis
  global.VisionFreeStyler = VisionFreeStyler;

})(typeof globalThis !== 'undefined' ? globalThis : this);

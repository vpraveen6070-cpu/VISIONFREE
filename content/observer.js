/**
 * VISIONFREE — Dynamic Content & SPA Observer (content/observer.js)
 * Phase 3: Single Page Application & Dynamic DOM Resilience
 *
 * Responsibilities:
 * 1. Monitors the DOM for SPA route transitions (React Router, Next.js, Vue Router, Turbo/HTMX).
 * 2. Ensures the VISIONFREE root attribute and stylesheet remain intact across client-side navigations.
 * 3. Uses debounced mutation batching (150ms) to ensure near-zero CPU footprint on dynamic feeds.
 * 4. Guards against self-mutation cycles.
 * 5. Disconnects cleanly upon deactivation with zero memory leaks.
 */

(function (global) {
  'use strict';

  const DEBOUNCE_DELAY_MS = 150;
  let observerInstance = null;
  let debounceTimer = null;
  let isInternalMutation = false;

  const VisionFreeObserver = {
    /**
     * Checks if the observer is currently actively monitoring the DOM.
     * @returns {boolean}
     */
    isActive() {
      return observerInstance !== null;
    },

    /**
     * Starts observing document mutations.
     */
    start() {
      // Avoid duplicate observers
      if (observerInstance) {
        return;
      }

      if (typeof MutationObserver === 'undefined') {
        console.warn('[VISIONFREE Observer] MutationObserver unsupported in this context.');
        return;
      }

      const targetNode = document.documentElement || document.body;
      if (!targetNode) {
        return;
      }

      observerInstance = new MutationObserver((mutations) => {
        if (isInternalMutation) {
          return;
        }

        // Check if any mutation is relevant (head changes, root attribute changes, or childList additions)
        let hasRelevantMutation = false;
        for (const mut of mutations) {
          if (mut.type === 'childList') {
            // Check if head or major structural container was modified
            if (mut.target.nodeName === 'HEAD' || mut.target.nodeName === 'HTML' || mut.target.nodeName === 'BODY') {
              hasRelevantMutation = true;
              break;
            }
          } else if (mut.type === 'attributes') {
            if (mut.attributeName === 'data-visionfree-active' || mut.attributeName === 'class') {
              hasRelevantMutation = true;
              break;
            }
          }
        }

        if (!hasRelevantMutation) {
          return;
        }

        // Debounce reconciliation to avoid CPU churn during heavy DOM streaming
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }

        debounceTimer = setTimeout(() => {
          debounceTimer = null;
          this._reconcile();
        }, DEBOUNCE_DELAY_MS);
      });

      // Observe root attribute modifications and structural child additions
      observerInstance.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['data-visionfree-active', 'class']
      });

      console.log('[VISIONFREE Observer] Started monitoring dynamic SPA DOM.');
    },

    /**
     * Reconciles VISIONFREE state with the DOM.
     * Re-attaches stylesheet or root attribute if purged by client-side routing.
     * @private
     */
    _reconcile() {
      if (!this.isActive() || typeof VisionFreeStyler === 'undefined') {
        return;
      }

      // Check if VISIONFREE is supposed to be active
      if (!VisionFreeStyler.getCurrentSettings()) {
        return;
      }

      isInternalMutation = true;
      try {
        const reattached = VisionFreeStyler.ensureAttached();
        if (reattached) {
          console.log('[VISIONFREE Observer] Restored styling after dynamic SPA route transition.');
        }
      } catch (err) {
        console.warn('[VISIONFREE Observer] Reconcile error:', err);
      } finally {
        isInternalMutation = false;
      }
    },

    /**
     * Stops and disconnects the observer, cleaning up all timers and references.
     */
    stop() {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
        debounceTimer = null;
      }

      if (observerInstance) {
        observerInstance.disconnect();
        observerInstance = null;
        console.log('[VISIONFREE Observer] Disconnected.');
      }
    }
  };

  // Expose on globalThis
  global.VisionFreeObserver = VisionFreeObserver;

})(typeof globalThis !== 'undefined' ? globalThis : this);


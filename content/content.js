/**
 * VISIONFREE — Content Script Coordinator (content/content.js)
 * Phase 3: Dynamic SPA Content Coordination & Live Updates
 *
 * Runs inside the webpage's isolated JavaScript execution context.
 * Receives lifecycle commands from the background service worker:
 * - ACTIVATE: applies styling and launches dynamic DOM observer.
 * - DEACTIVATE: tears down styling and disconnects observer.
 * - UPDATE_SETTINGS: live-updates visual styles without page reloads.
 * - PING: confirms script responsiveness.
 */

(function () {
  'use strict';

  // Guard against duplicate script injection
  if (window.__VISIONFREE_CONTENT_INITIALIZED__) {
    return;
  }
  window.__VISIONFREE_CONTENT_INITIALIZED__ = true;

  console.log('[VISIONFREE] Content script initialized on:', window.location.hostname);

  /**
   * Message listener for background service worker commands
   */
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || typeof message.action !== 'string') {
      return false;
    }

    switch (message.action) {
      case 'PING':
        sendResponse({
          status: 'PONG',
          active: typeof VisionFreeStyler !== 'undefined' ? VisionFreeStyler.isActive() : false
        });
        break;

      case 'ACTIVATE':
        try {
          if (typeof VisionFreeStyler === 'undefined') {
            throw new Error('VisionFreeStyler module is not loaded.');
          }

          const settings = message.settings || {};
          VisionFreeStyler.apply(settings);

          // Launch dynamic DOM observer for SPA resilience
          if (typeof VisionFreeObserver !== 'undefined') {
            VisionFreeObserver.start();
          }

          console.log('[VISIONFREE] Activated with sanitized display preferences:', settings);
          sendResponse({ success: true, active: true });
        } catch (err) {
          console.error('[VISIONFREE] Activation failed:', err);
          sendResponse({ success: false, error: err.message });
        }
        break;

      case 'DEACTIVATE':
        try {
          // Stop observer first
          if (typeof VisionFreeObserver !== 'undefined') {
            VisionFreeObserver.stop();
          }

          // Cleanly remove all styles and attributes
          if (typeof VisionFreeStyler !== 'undefined') {
            VisionFreeStyler.remove();
          }

          console.log('[VISIONFREE] Deactivated. Restored original webpage appearance.');
          sendResponse({ success: true, active: false });
        } catch (err) {
          console.error('[VISIONFREE] Deactivation failed:', err);
          sendResponse({ success: false, error: err.message });
        }
        break;

      case 'UPDATE_SETTINGS':
        try {
          // Live preference update on active tab
          if (typeof VisionFreeStyler !== 'undefined' && VisionFreeStyler.isActive()) {
            const settings = message.settings || {};
            VisionFreeStyler.apply(settings);
            console.log('[VISIONFREE] Applied live preferences update:', settings);
            sendResponse({ success: true, active: true, updated: true });
          } else {
            sendResponse({ success: false, reason: 'Tab is not active' });
          }
        } catch (err) {
          console.error('[VISIONFREE] Live settings update failed:', err);
          sendResponse({ success: false, error: err.message });
        }
        break;

      case 'GET_STATUS':
        sendResponse({
          active: typeof VisionFreeStyler !== 'undefined' ? VisionFreeStyler.isActive() : false
        });
        break;

      default:
        return false;
    }

    return false;
  });

})();

/**
 * VISIONFREE — Background Service Worker (background/service-worker.js)
 * Phase 3: Live Settings Broadcasting & Secure Content Coordination
 *
 * Responsibilities:
 * 1. Handles toolbar icon clicks via chrome.action.onClicked (no popup).
 * 2. Manages per-tab ON/OFF state using chrome.storage.session.
 * 3. Sanitizes display preferences before dispatching to content scripts.
 * 4. Injects only required rendering modules into the host webpage (preserving prescription privacy).
 * 5. Broadcasts live settings updates to active tabs when the active profile changes.
 * 6. Cleans up tab state on tab close or page reload.
 */

try {
  importScripts('../core/profiles.js', '../core/storage.js');
} catch (e) {
  console.error('[VISIONFREE SW] Could not import dependencies:', e);
}

const BADGE_COLOR_ACTIVE = '#2563EB'; // Vibrant cobalt blue
const BADGE_COLOR_ERROR = '#DC2626';  // Alert red

/**
 * Checks if a URL is eligible for content script injection.
 * Chrome forbids scripts on internal pages and the Chrome Web Store.
 * @param {string} url
 * @returns {boolean}
 */
function isInjectableUrl(url) {
  if (!url || typeof url !== 'string') return false;

  const restrictedPrefixes = [
    'chrome://',
    'chrome-extension://',
    'edge://',
    'about:',
    'devtools://',
    'view-source:',
    'data:'
  ];

  if (restrictedPrefixes.some(prefix => url.startsWith(prefix))) {
    return false;
  }

  try {
    const parsed = new URL(url);
    if (
      parsed.hostname === 'chromewebstore.google.com' ||
      (parsed.hostname === 'chrome.google.com' && parsed.pathname.startsWith('/webstore'))
    ) {
      return false;
    }
  } catch {
    return false;
  }

  return true;
}

/**
 * Displays an error badge on the tab and logs a helpful explanation.
 * @param {number} tabId
 * @param {string} message
 */
async function reportTabError(tabId, message) {
  console.warn(`[VISIONFREE SW] Tab ${tabId}: ${message}`);
  try {
    await chrome.action.setBadgeText({ tabId, text: '!' });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: BADGE_COLOR_ERROR });
    await chrome.action.setTitle({
      tabId,
      title: `VISIONFREE: ${message}`
    });

    // Auto-clear error indicator after 4 seconds
    setTimeout(async () => {
      try {
        await chrome.action.setBadgeText({ tabId, text: '' });
        await chrome.action.setTitle({ tabId, title: 'VISIONFREE: Click to toggle' });
      } catch {
        // Tab might be closed
      }
    }, 4000);
  } catch (err) {
    // Suppress secondary badge errors
  }
}

/**
 * Ensures the content script and its modules are injected into the target tab.
 * Strictly injects only the presentation engine, omitting prescription storage.
 * @param {number} tabId
 * @returns {Promise<boolean>}
 */
async function ensureContentScriptInjected(tabId) {
  try {
    // 1. Ping the tab to check if content script is already listening
    const response = await chrome.tabs.sendMessage(tabId, { action: 'PING' });
    if (response && response.status === 'PONG') {
      return true;
    }
  } catch {
    // Content script is not loaded; proceed to programmatic injection
  }

  try {
    // 2. Dynamically inject the rendering dependencies in order
    await chrome.scripting.executeScript({
      target: { tabId },
      files: [
        'content/styler.js',
        'content/observer.js',
        'content/content.js'
      ]
    });
    return true;
  } catch (err) {
    console.error(`[VISIONFREE SW] Script injection failed for tab ${tabId}:`, err);
    return false;
  }
}

/**
 * Handles toolbar icon click event.
 */
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.id) return;
  const tabId = tab.id;

  // 1. Verify URL is supported
  if (!isInjectableUrl(tab.url)) {
    await reportTabError(tabId, 'Cannot run on system or Web Store pages.');
    return;
  }

  try {
    // 2. Query current activation state for this specific tab
    const isCurrentlyActive = await VisionFreeStorage.getTabState(tabId);
    const targetState = !isCurrentlyActive;

    // 3. Ensure content script is ready
    const ready = await ensureContentScriptInjected(tabId);
    if (!ready) {
      await reportTabError(tabId, 'Could not initialize page scripts.');
      return;
    }

    if (targetState) {
      // --- ACTIVATE ---
      // Retrieves ONLY sanitized display preferences from active profile
      const rawSettings = await VisionFreeStorage.getSettings();
      const settings = VisionFreeStorage.sanitizeDisplayPreferences(rawSettings);

      const response = await chrome.tabs.sendMessage(tabId, {
        action: 'ACTIVATE',
        settings
      });

      if (response && response.success) {
        await VisionFreeStorage.setTabState(tabId, true);
        await chrome.action.setBadgeText({ tabId, text: 'ON' });
        await chrome.action.setBadgeBackgroundColor({ tabId, color: BADGE_COLOR_ACTIVE });
        await chrome.action.setTitle({ tabId, title: 'VISIONFREE: Active (Click to disable)' });
        console.log(`[VISIONFREE SW] Tab ${tabId} activated successfully.`);
      } else {
        await reportTabError(tabId, 'Activation failed in page context.');
      }
    } else {
      // --- DEACTIVATE ---
      await chrome.tabs.sendMessage(tabId, { action: 'DEACTIVATE' });

      await VisionFreeStorage.setTabState(tabId, false);
      await chrome.action.setBadgeText({ tabId, text: '' });
      await chrome.action.setTitle({ tabId, title: 'VISIONFREE: Inactive (Click to activate)' });
      console.log(`[VISIONFREE SW] Tab ${tabId} deactivated.`);
    }

  } catch (err) {
    console.error(`[VISIONFREE SW] Error handling click on tab ${tabId}:`, err);
    await reportTabError(tabId, 'An unexpected error occurred.');
  }
});

/**
 * Broadcasts live preference updates to all active tabs when storage changes.
 */
chrome.storage.onChanged.addListener(async (changes, areaName) => {
  if (areaName !== 'local') return;

  // React if settings, active profile id, or profile list changes
  if (changes.visionfree_settings || changes.visionfree_active_profile_id || changes.visionfree_profiles) {
    try {
      const rawSettings = await VisionFreeStorage.getSettings();
      const settings = VisionFreeStorage.sanitizeDisplayPreferences(rawSettings);
      const activeTabIds = await VisionFreeStorage.getActiveTabIds();

      if (activeTabIds.length === 0) return;

      console.log(`[VISIONFREE SW] Broadcasting live settings update to ${activeTabIds.length} active tab(s)...`);

      for (const tabId of activeTabIds) {
        chrome.tabs.sendMessage(tabId, {
          action: 'UPDATE_SETTINGS',
          settings
        }).catch(() => {
          // Tab might have been navigated, closed, or permission expired
        });
      }
    } catch (err) {
      console.warn('[VISIONFREE SW] Live broadcast error:', err);
    }
  }
});

/**
 * Tab cleanup: When a tab is closed, clean up its session state.
 */
chrome.tabs.onRemoved.addListener(async (tabId) => {
  try {
    await VisionFreeStorage.removeTabState(tabId);
  } catch (err) {
    // Ignore errors during tab cleanup
  }
});

/**
 * Tab navigation: When a tab navigates to a new URL, reset its activation state.
 */
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status === 'loading') {
    try {
      const wasActive = await VisionFreeStorage.getTabState(tabId);
      if (wasActive) {
        await VisionFreeStorage.setTabState(tabId, false);
        await chrome.action.setBadgeText({ tabId, text: '' });
        await chrome.action.setTitle({ tabId, title: 'VISIONFREE: Inactive (Click to activate)' });
      }
    } catch {
      // Ignore navigation update errors
    }
  }
});

/**
 * Extension install / update lifecycle
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('[VISIONFREE SW] Extension installed/updated. Reason:', details.reason);
  await VisionFreeStorage.initialize();
});

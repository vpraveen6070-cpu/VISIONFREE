/**
 * VISIONFREE — Storage Foundation Module (core/storage.js)
 *
 * Responsibilities:
 * 1. Centralizes read/write access to Chrome Storage APIs (local and session).
 * 2. Enforces TRUSTED_CONTEXTS storage isolation for privacy protection.
 * 3. Sanitizes display preferences before passing them to webpage content scripts.
 * 4. Implements the Phase 2 & 3 versioned Vision Profile schema with backward compatibility.
 * 5. Manages per-tab session state isolation for toolbar one-click activation.
 */

(function (global) {
  'use strict';

  // Fallback defaults for display preferences
  const DEFAULT_SETTINGS = {
    version: '0.3.0',
    lineSpacing: '1.6',       // Line-height multiplier ('1.4', '1.6', '1.8', '2.0')
    fontWeightDelta: '0',     // Font-weight adjustment ('0', '100', '200')
    letterSpacing: '0.02em',  // Letter spacing adjustment ('0em', '0.02em', '0.04em')
    highContrastText: false   // Micro-contrast text accentuation
  };

  const STORAGE_KEY = 'visionfree_settings';
  const PROFILES_KEY = 'visionfree_profiles';
  const ACTIVE_PROFILE_KEY = 'visionfree_active_profile_id';
  const ASSESSMENTS_KEY = 'visionfree_assessments';
  const TAB_STATE_PREFIX = 'vf_tab_';

  const VisionFreeStorage = {
    DEFAULT_SETTINGS: Object.freeze({ ...DEFAULT_SETTINGS }),

    /**
     * Sanitizes display preferences, strictly stripping out any prescription data (SPH, CYL, Axis).
     * @param {Object} raw
     * @returns {{ lineSpacing: string, letterSpacing: string, fontWeightDelta: string, highContrastText: boolean }}
     */
    sanitizeDisplayPreferences(raw = {}) {
      const allowedLineSpacing = ['1.4', '1.6', '1.8', '2.0'];
      const allowedLetterSpacing = ['0em', '0.02em', '0.04em'];
      const allowedFontWeight = ['0', '100', '200'];

      const lineSpacing = allowedLineSpacing.includes(String(raw.lineSpacing)) ? String(raw.lineSpacing) : '1.6';
      const letterSpacing = allowedLetterSpacing.includes(String(raw.letterSpacing)) ? String(raw.letterSpacing) : '0.02em';
      const fontWeightDelta = allowedFontWeight.includes(String(raw.fontWeightDelta)) ? String(raw.fontWeightDelta) : '0';
      const highContrastText = Boolean(raw.highContrastText);

      // Explicitly construct return object containing ONLY visual display attributes
      return {
        lineSpacing,
        letterSpacing,
        fontWeightDelta,
        highContrastText
      };
    },

    /**
     * Initializes storage, enforces TRUSTED_CONTEXTS security, and migrates legacy settings.
     * @returns {Promise<{ profiles: Array, activeProfileId: string }>}
     */
    async initialize() {
      try {
        if (!chrome?.storage?.local) {
          console.warn('[VISIONFREE Storage] chrome.storage.local unavailable. Using in-memory fallback.');
          const def = this._createDefaultProfileFallback();
          return { profiles: [def], activeProfileId: def.id };
        }

        // Restrict storage.local to trusted extension contexts (Options, ServiceWorker)
        if (typeof chrome.storage.local.setAccessLevel === 'function') {
          try {
            await chrome.storage.local.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' });
          } catch (e) {
            // setAccessLevel may throw if called repeatedly or unsupported
          }
        }

        const data = await chrome.storage.local.get([PROFILES_KEY, ACTIVE_PROFILE_KEY, STORAGE_KEY]);
        let profiles = Array.isArray(data[PROFILES_KEY]) ? data[PROFILES_KEY] : null;
        let activeId = data[ACTIVE_PROFILE_KEY];

        // Migration or First-Time Initialization
        if (!profiles || profiles.length === 0) {
          console.log('[VISIONFREE Storage] Initializing profile schema v2.0.0...');
          const legacySettings = data[STORAGE_KEY] || {};
          const initialProfile = this._createDefaultProfileFallback('Default Profile', 'default_profile');

          // Adopt any existing preferences
          if (legacySettings.lineSpacing) {
            initialProfile.preferences.lineSpacing = legacySettings.lineSpacing;
          }
          if (legacySettings.letterSpacing) {
            initialProfile.preferences.letterSpacing = legacySettings.letterSpacing;
          }
          if (legacySettings.fontWeightDelta !== undefined) {
            initialProfile.preferences.fontWeightDelta = String(legacySettings.fontWeightDelta);
          }
          if (legacySettings.highContrastText !== undefined) {
            initialProfile.preferences.highContrastText = legacySettings.highContrastText;
          }

          profiles = [initialProfile];
          activeId = initialProfile.id;

          await chrome.storage.local.set({
            [PROFILES_KEY]: profiles,
            [ACTIVE_PROFILE_KEY]: activeId,
            [STORAGE_KEY]: { ...DEFAULT_SETTINGS, ...initialProfile.preferences }
          });
        }

        // Validate activeId points to an existing profile
        if (!profiles.some(p => p.id === activeId)) {
          activeId = profiles[0].id;
          await chrome.storage.local.set({ [ACTIVE_PROFILE_KEY]: activeId });
        }

        return { profiles, activeProfileId: activeId };
      } catch (err) {
        console.error('[VISIONFREE Storage] Initialization error:', err);
        const def = this._createDefaultProfileFallback();
        return { profiles: [def], activeProfileId: def.id };
      }
    },

    /**
     * Helper to create a default profile structure.
     */
    _createDefaultProfileFallback(name = 'Default Profile', id = null) {
      if (global.VisionFreeProfiles?.createDefaultProfile) {
        return global.VisionFreeProfiles.createDefaultProfile(name, id);
      }

      return {
        id: id || 'prof_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 8),
        schemaVersion: '2.0.0',
        name,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        prescription: {
          rightEye: { sph: '', cyl: '', axis: '' },
          leftEye: { sph: '', cyl: '', axis: '' }
        },
        preferences: {
          lineSpacing: '1.6',
          letterSpacing: '0.02em',
          fontWeightDelta: '0',
          highContrastText: false
        }
      };
    },

    /**
     * Retrieves all saved vision profiles.
     * @returns {Promise<Array>}
     */
    async getProfiles() {
      const state = await this.initialize();
      return state.profiles;
    },

    /**
     * Retrieves the currently selected active profile.
     * @returns {Promise<Object>}
     */
    async getActiveProfile() {
      const state = await this.initialize();
      const active = state.profiles.find(p => p.id === state.activeProfileId);
      return active || state.profiles[0] || this._createDefaultProfileFallback();
    },

    /**
     * Retrieves the ID of the active profile.
     * @returns {Promise<string>}
     */
    async getActiveProfileId() {
      const state = await this.initialize();
      return state.activeProfileId;
    },

    /**
     * Sets the active profile ID and synchronizes its display preferences.
     * @param {string} profileId
     * @returns {Promise<boolean>}
     */
    async setActiveProfileId(profileId) {
      try {
        if (!chrome?.storage?.local) return false;
        const profiles = await this.getProfiles();
        const target = profiles.find(p => p.id === profileId);
        if (!target) {
          console.warn(`[VISIONFREE Storage] Profile ID ${profileId} not found.`);
          return false;
        }

        const sanitizedPrefs = this.sanitizeDisplayPreferences(target.preferences);

        await chrome.storage.local.set({
          [ACTIVE_PROFILE_KEY]: profileId,
          [STORAGE_KEY]: {
            ...DEFAULT_SETTINGS,
            ...sanitizedPrefs,
            updatedAt: Date.now()
          }
        });

        return true;
      } catch (err) {
        console.error('[VISIONFREE Storage] Error setting active profile:', err);
        return false;
      }
    },

    /**
     * Saves or updates a vision profile.
     * @param {Object} profile
     * @returns {Promise<{ success: boolean, profile?: Object, error?: string }>}
     */
    async saveProfile(profile) {
      try {
        if (!chrome?.storage?.local) {
          throw new Error('chrome.storage.local unavailable.');
        }

        if (global.VisionFreeProfiles?.validateProfile) {
          const validation = global.VisionFreeProfiles.validateProfile(profile);
          if (!validation.valid) {
            return { success: false, error: 'Validation failed', details: validation.errors };
          }
        }

        const state = await this.initialize();
        const profiles = [...state.profiles];
        const existingIdx = profiles.findIndex(p => p.id === profile.id);

        const updatedProfile = {
          ...profile,
          updatedAt: Date.now()
        };

        if (existingIdx >= 0) {
          profiles[existingIdx] = updatedProfile;
        } else {
          updatedProfile.id = updatedProfile.id || (global.VisionFreeProfiles?.generateId ? global.VisionFreeProfiles.generateId() : 'prof_' + Date.now());
          updatedProfile.createdAt = Date.now();
          profiles.push(updatedProfile);
        }

        await chrome.storage.local.set({ [PROFILES_KEY]: profiles });

        // If the saved profile is active, keep preferences synced
        if (updatedProfile.id === state.activeProfileId) {
          const sanitizedPrefs = this.sanitizeDisplayPreferences(updatedProfile.preferences);
          await chrome.storage.local.set({
            [STORAGE_KEY]: {
              ...DEFAULT_SETTINGS,
              ...sanitizedPrefs,
              updatedAt: Date.now()
            }
          });
        }

        return { success: true, profile: updatedProfile };
      } catch (err) {
        console.error('[VISIONFREE Storage] Error saving profile:', err);
        return { success: false, error: err.message };
      }
    },

    /**
     * Deletes a vision profile by ID.
     * @param {string} profileId
     * @returns {Promise<{ success: boolean, newActiveId?: string, error?: string }>}
     */
    async deleteProfile(profileId) {
      try {
        if (!chrome?.storage?.local) return { success: false, error: 'Storage unavailable.' };

        const state = await this.initialize();
        if (state.profiles.length <= 1) {
          return { success: false, error: 'Cannot delete the only existing profile.' };
        }

        const remaining = state.profiles.filter(p => p.id !== profileId);
        if (remaining.length === state.profiles.length) {
          return { success: false, error: 'Profile not found.' };
        }

        let newActiveId = state.activeProfileId;
        if (state.activeProfileId === profileId) {
          newActiveId = remaining[0].id;
        }

        await chrome.storage.local.set({
          [PROFILES_KEY]: remaining,
          [ACTIVE_PROFILE_KEY]: newActiveId
        });

        // Sync preferences of the new active profile
        const activeProfile = remaining.find(p => p.id === newActiveId);
        if (activeProfile) {
          const sanitizedPrefs = this.sanitizeDisplayPreferences(activeProfile.preferences);
          await chrome.storage.local.set({
            [STORAGE_KEY]: {
              ...DEFAULT_SETTINGS,
              ...sanitizedPrefs,
              updatedAt: Date.now()
            }
          });
        }

        return { success: true, newActiveId };
      } catch (err) {
        console.error('[VISIONFREE Storage] Error deleting profile:', err);
        return { success: false, error: err.message };
      }
    },

    /**
     * Resets the active profile to factory defaults while preserving its ID and name.
     * @returns {Promise<boolean>}
     */
    async resetActiveProfile() {
      try {
        const active = await this.getActiveProfile();
        const resetData = this._createDefaultProfileFallback(active.name, active.id);
        resetData.createdAt = active.createdAt || Date.now();
        resetData.updatedAt = Date.now();

        await this.saveProfile(resetData);
        return true;
      } catch (err) {
        console.error('[VISIONFREE Storage] Error resetting active profile:', err);
        return false;
      }
    },

    /**
     * Returns ONLY sanitized display preferences from the active profile for webpage styling.
     * Strips away all clinical prescription values (SPH, CYL, Axis).
     * @returns {Promise<Object>}
     */
    async getSettings() {
      try {
        const active = await this.getActiveProfile();
        return this.sanitizeDisplayPreferences(active.preferences);
      } catch (err) {
        console.error('[VISIONFREE Storage] getSettings fallback:', err);
        return this.sanitizeDisplayPreferences(DEFAULT_SETTINGS);
      }
    },

    /**
     * Saves presentation preferences to the active profile.
     * @param {Object} newSettings
     * @returns {Promise<boolean>}
     */
    async saveSettings(newSettings) {
      try {
        const active = await this.getActiveProfile();
        active.preferences = {
          ...(active.preferences || {}),
          ...this.sanitizeDisplayPreferences(newSettings)
        };
        const res = await this.saveProfile(active);
        return res.success;
      } catch (err) {
        console.error('[VISIONFREE Storage] saveSettings error:', err);
        return false;
      }
    },

    /**
     * Per-Tab Session State Management
     */
    async getTabState(tabId) {
      if (!tabId || tabId < 0) return false;
      const key = TAB_STATE_PREFIX + tabId;
      try {
        if (chrome?.storage?.session) {
          const res = await chrome.storage.session.get([key]);
          return Boolean(res && res[key]);
        }
      } catch (err) {}
      return false;
    },

    async setTabState(tabId, isActive) {
      if (!tabId || tabId < 0) return;
      const key = TAB_STATE_PREFIX + tabId;
      try {
        if (chrome?.storage?.session) {
          if (isActive) {
            await chrome.storage.session.set({ [key]: true });
          } else {
            await chrome.storage.session.remove([key]);
          }
        }
      } catch (err) {}
    },

    async removeTabState(tabId) {
      if (!tabId || tabId < 0) return;
      const key = TAB_STATE_PREFIX + tabId;
      try {
        if (chrome?.storage?.session) {
          await chrome.storage.session.remove([key]);
        }
      } catch (err) {}
    },

    /**
     * Retrieves a list of tab IDs that are currently active in session storage.
     * Used for broadcasting live settings updates.
     * @returns {Promise<Array<number>>}
     */
    async getActiveTabIds() {
      try {
        if (!chrome?.storage?.session) return [];
        const allSession = await chrome.storage.session.get(null);
        const activeTabIds = [];

        for (const [key, val] of Object.entries(allSession)) {
          if (key.startsWith(TAB_STATE_PREFIX) && val === true) {
            const tabId = parseInt(key.replace(TAB_STATE_PREFIX, ''), 10);
            if (!isNaN(tabId)) {
              activeTabIds.push(tabId);
            }
          }
        }
        return activeTabIds;
      } catch (err) {
        console.warn('[VISIONFREE Storage] Could not query active tab IDs:', err);
        return [];
      }
    },

    /**
     * Retrieves assessment data for a specific profile.
     * @param {string} [profileId]
     * @returns {Promise<Object>}
     */
    async getAssessment(profileId) {
      try {
        if (!chrome?.storage?.local) {
          const pid = profileId || 'default_profile';
          return global.VisionFreeAssessment?.createEmptyAssessment
            ? global.VisionFreeAssessment.createEmptyAssessment(pid)
            : { profileId: pid };
        }

        const targetId = profileId || await this.getActiveProfileId();
        const data = await chrome.storage.local.get([ASSESSMENTS_KEY]);
        const assessments = data[ASSESSMENTS_KEY] || {};

        if (assessments[targetId]) {
          return assessments[targetId];
        }

        // Return new blank assessment structure
        return global.VisionFreeAssessment?.createEmptyAssessment
          ? global.VisionFreeAssessment.createEmptyAssessment(targetId)
          : { profileId: targetId };
      } catch (err) {
        console.error('[VISIONFREE Storage] Error getting assessment:', err);
        const pid = profileId || 'default_profile';
        return global.VisionFreeAssessment?.createEmptyAssessment
          ? global.VisionFreeAssessment.createEmptyAssessment(pid)
          : { profileId: pid };
      }
    },

    /**
     * Saves or merges assessment updates for a profile.
     * Strictly isolates assessment data from the clinical prescription.
     * @param {string} profileId
     * @param {Object} updates
     * @returns {Promise<boolean>}
     */
    async saveAssessment(profileId, updates = {}) {
      try {
        if (!chrome?.storage?.local) return false;
        const targetId = profileId || await this.getActiveProfileId();
        const current = await this.getAssessment(targetId);

        const merged = {
          ...current,
          ...updates,
          profileId: targetId,
          updatedAt: Date.now()
        };

        const data = await chrome.storage.local.get([ASSESSMENTS_KEY]);
        const assessments = data[ASSESSMENTS_KEY] || {};
        assessments[targetId] = merged;

        await chrome.storage.local.set({ [ASSESSMENTS_KEY]: assessments });
        return true;
      } catch (err) {
        console.error('[VISIONFREE Storage] Error saving assessment:', err);
        return false;
      }
    },

    /**
     * Clears assessment records for a profile.
     * @param {string} profileId
     * @returns {Promise<boolean>}
     */
    async clearAssessment(profileId) {
      try {
        if (!chrome?.storage?.local) return false;
        const targetId = profileId || await this.getActiveProfileId();
        const blank = global.VisionFreeAssessment?.createEmptyAssessment
          ? global.VisionFreeAssessment.createEmptyAssessment(targetId)
          : { profileId: targetId };

        const data = await chrome.storage.local.get([ASSESSMENTS_KEY]);
        const assessments = data[ASSESSMENTS_KEY] || {};
        assessments[targetId] = blank;

        await chrome.storage.local.set({ [ASSESSMENTS_KEY]: assessments });
        return true;
      } catch (err) {
        console.error('[VISIONFREE Storage] Error clearing assessment:', err);
        return false;
      }
    }
  };

  global.VisionFreeStorage = VisionFreeStorage;

})(typeof globalThis !== 'undefined' ? globalThis : this);

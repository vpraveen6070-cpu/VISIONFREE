/**
 * VISIONFREE — Personal Vision Profile Module (core/profiles.js)
 *
 * Responsibilities:
 * 1. Defines the profile data schema (v2.0.0).
 * 2. Implements ophthalmic input validation for SPH, CYL, and Axis values.
 * 3. Provides standard visual preference presets (neutral display terms).
 * 4. Supplies default profile generation and profile cloning/sanitization utilities.
 */

(function (global) {
  'use strict';

  // Standard display preference presets (neutral terminology)
  const PREFERENCE_PRESETS = Object.freeze({
    standard: {
      name: 'Standard Reading',
      lineSpacing: '1.6',
      letterSpacing: '0.02em',
      fontWeightDelta: '0',
      highContrastText: false
    },
    spacious: {
      name: 'Spacious Reading',
      lineSpacing: '1.8',
      letterSpacing: '0.04em',
      fontWeightDelta: '0',
      highContrastText: false
    },
    high_contrast: {
      name: 'High Contrast',
      lineSpacing: '1.6',
      letterSpacing: '0.02em',
      fontWeightDelta: '100',
      highContrastText: true
    },
    compact: {
      name: 'Compact Reading',
      lineSpacing: '1.4',
      letterSpacing: '0em',
      fontWeightDelta: '0',
      highContrastText: false
    }
  });

  const VisionFreeProfiles = {
    SCHEMA_VERSION: '2.0.0',
    PRESETS: PREFERENCE_PRESETS,

    /**
     * Generates a unique, non-colliding profile ID.
     * @returns {string}
     */
    generateId() {
      return 'prof_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 8);
    },

    /**
     * Creates a blank or default profile object.
     * @param {string} [name='Default Profile']
     * @param {string|null} [id=null]
     * @returns {Object}
     */
    createDefaultProfile(name = 'Default Profile', id = null) {
      const now = Date.now();
      return {
        id: id || this.generateId(),
        schemaVersion: this.SCHEMA_VERSION,
        name: name.trim() || 'Untitled Profile',
        createdAt: now,
        updatedAt: now,
        prescription: {
          rightEye: {
            sph: '',
            cyl: '',
            axis: ''
          },
          leftEye: {
            sph: '',
            cyl: '',
            axis: ''
          }
        },
        preferences: {
          lineSpacing: '1.6',
          letterSpacing: '0.02em',
          fontWeightDelta: '100',
          highContrastText: false
        }
      };
    },

    /**
     * Validates a Sphere (SPH) value.
     * Allows positive, negative, zero, and decimal values.
     * Accepts empty string if user has not entered a prescription yet.
     * @param {string|number} val
     * @returns {{ valid: boolean, error?: string, parsed?: number|null }}
     */
    validateSphere(val) {
      if (val === '' || val === null || val === undefined) {
        return { valid: true, parsed: null };
      }

      const str = String(val).trim();
      if (!/^[+-]?\d*(\.\d+)?$/.test(str) || str === '+' || str === '-' || str === '.') {
        return { valid: false, error: 'Sphere must be a valid number (e.g. -2.00, +1.50, 0).' };
      }

      const num = parseFloat(str);
      if (isNaN(num)) {
        return { valid: false, error: 'Invalid Sphere value.' };
      }

      return { valid: true, parsed: num };
    },

    /**
     * Validates a Cylinder (CYL) value.
     * Allows positive, negative, zero, and decimal values.
     * @param {string|number} val
     * @returns {{ valid: boolean, error?: string, parsed?: number|null, isZeroOrEmpty: boolean }}
     */
    validateCylinder(val) {
      if (val === '' || val === null || val === undefined) {
        return { valid: true, parsed: null, isZeroOrEmpty: true };
      }

      const str = String(val).trim();
      if (!/^[+-]?\d*(\.\d+)?$/.test(str) || str === '+' || str === '-' || str === '.') {
        return { valid: false, error: 'Cylinder must be a valid number (e.g. -0.75, +0.50, 0).' };
      }

      const num = parseFloat(str);
      if (isNaN(num)) {
        return { valid: false, error: 'Invalid Cylinder value.' };
      }

      const isZero = num === 0;
      return { valid: true, parsed: num, isZeroOrEmpty: isZero };
    },

    /**
     * Validates an Axis value.
     * Required between 1 and 180 degrees if cylinder is non-zero.
     * Inactive/optional if cylinder is zero or empty.
     * @param {string|number} axisVal
     * @param {string|number} cylVal
     * @returns {{ valid: boolean, error?: string, parsed?: number|null }}
     */
    validateAxis(axisVal, cylVal) {
      const cylValidation = this.validateCylinder(cylVal);

      // If cylinder is invalid, axis check is deferred
      if (!cylValidation.valid) {
        return { valid: true, parsed: null };
      }

      const hasCyl = !cylValidation.isZeroOrEmpty;
      const str = axisVal === null || axisVal === undefined ? '' : String(axisVal).trim();

      // When CYL is 0 or empty, Axis is not required
      if (!hasCyl) {
        if (str === '') {
          return { valid: true, parsed: null };
        }
        // If user entered something anyway, verify it's between 1 and 180
      } else {
        // When CYL is non-zero, Axis is mandatory
        if (str === '') {
          return { valid: false, error: 'Axis is required (1° to 180°) when Cylinder is non-zero.' };
        }
      }

      if (!/^\d+(\.\d+)?$/.test(str)) {
        return { valid: false, error: 'Axis must be a positive number between 1 and 180 degrees.' };
      }

      const num = parseFloat(str);
      if (isNaN(num) || num < 1 || num > 180) {
        return { valid: false, error: 'Axis must be between 1° and 180°.' };
      }

      return { valid: true, parsed: num };
    },

    /**
     * Validates a single eye's full prescription.
     * @param {Object} eye
     * @param {string} [eyeName='Eye']
     * @returns {{ valid: boolean, errors: Object }}
     */
    validateEyePrescription(eye = {}, eyeName = 'Eye') {
      const errors = {};

      const sphResult = this.validateSphere(eye.sph);
      if (!sphResult.valid) {
        errors.sph = sphResult.error;
      }

      const cylResult = this.validateCylinder(eye.cyl);
      if (!cylResult.valid) {
        errors.cyl = cylResult.error;
      }

      const axisResult = this.validateAxis(eye.axis, eye.cyl);
      if (!axisResult.valid) {
        errors.axis = axisResult.error;
      }

      return {
        valid: Object.keys(errors).length === 0,
        errors
      };
    },

    /**
     * Validates an entire profile data structure.
     * @param {Object} profile
     * @returns {{ valid: boolean, errors: Object }}
     */
    validateProfile(profile) {
      const errors = {
        name: null,
        rightEye: {},
        leftEye: {}
      };

      if (!profile || typeof profile !== 'object') {
        return { valid: false, errors: { general: 'Profile must be an object.' } };
      }

      // Name validation
      if (!profile.name || typeof profile.name !== 'string' || !profile.name.trim()) {
        errors.name = 'Profile name cannot be empty.';
      } else if (profile.name.trim().length > 60) {
        errors.name = 'Profile name cannot exceed 60 characters.';
      }

      // Prescription validation for each eye
      const rx = profile.prescription || {};
      const odResult = this.validateEyePrescription(rx.rightEye || {}, 'Right Eye (OD)');
      if (!odResult.valid) {
        errors.rightEye = odResult.errors;
      }

      const osResult = this.validateEyePrescription(rx.leftEye || {}, 'Left Eye (OS)');
      if (!osResult.valid) {
        errors.leftEye = osResult.errors;
      }

      const hasRightErrors = Object.keys(errors.rightEye).length > 0;
      const hasLeftErrors = Object.keys(errors.leftEye).length > 0;
      const hasErrors = Boolean(errors.name || hasRightErrors || hasLeftErrors);

      return {
        valid: !hasErrors,
        errors
      };
    }
  };

  // Expose on globalThis
  global.VisionFreeProfiles = VisionFreeProfiles;

})(typeof globalThis !== 'undefined' ? globalThis : this);

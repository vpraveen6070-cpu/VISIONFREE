/**
 * VISIONFREE — Vision Assessment & Calibration Engine (core/assessment.js)
 * Phase 4 Corrections: Measurement Accuracy, Contrast Mathematics & Data Consistency
 *
 * Responsibilities:
 * 1. Physical display calibration math & stale calibration detection (DPR / Zoom / Display resolution).
 * 2. Visual angle trigonometry (Experimental 5×5 Tumbling E optotype with 5:5:1 geometric proportions).
 * 3. Multi-trial visual task progression (5 trials per level, operational >=80% threshold rule).
 * 4. Multi-trial relative contrast task (4 trials per level, operational >=75% threshold rule, sRGB transfer function).
 * 5. Reading performance assessment & 4-question comprehension evaluation (programmatic word count).
 * 6. Scientific disclaimers and empirical screen-based observation labeling.
 */

(function (global) {
  'use strict';

  // Helper to count words programmatically in a text passage
  function countWords(text) {
    if (!text || typeof text !== 'string') return 0;
    return text.trim().split(/\s+/).filter(Boolean).length;
  }

  // Standard Tumbling-E cardinal orientations (Angles in degrees)
  const OPTOTYPE_DIRECTIONS = Object.freeze([
    { id: 'right', label: 'Right (E)', symbol: 'E', angle: 0 },
    { id: 'down',  label: 'Down (Ш)',  symbol: 'Ш', angle: 90 },
    { id: 'left',  label: 'Left (Ǝ)',  symbol: 'Ǝ', angle: 180 },
    { id: 'up',    label: 'Up (M)',    symbol: 'M', angle: 270 }
  ]);

  // Standard progressive visual angle steps (in arcminutes)
  // 5 arcmin = 20/20 Snellen equivalent total optotype height
  const VISUAL_ANGLE_LEVELS_ARCMIN = Object.freeze([
    30.0, // Level 1 (~20/125 equiv)
    20.0, // Level 2 (~20/80 equiv)
    15.0, // Level 3 (~20/60 equiv)
    10.0, // Level 4 (~20/40 equiv)
    7.5,  // Level 5 (~20/30 equiv)
    5.0   // Level 6 (~20/20 reference)
  ]);

  // Number of trials required per size level in Visual Task
  const ACUITY_TRIALS_PER_LEVEL = 5;
  // Threshold criterion: at least 4 out of 5 correct (80%) to pass a level
  const ACUITY_PASS_THRESHOLD_COUNT = 4;

  // Relative contrast levels (Nominal contrast percentage)
  const CONTRAST_LEVELS_PERCENT = Object.freeze([
    100.0, // Level 1: Full contrast
    50.0,  // Level 2
    25.0,  // Level 3
    12.0,  // Level 4
    6.0,   // Level 5
    3.0,   // Level 6
    1.5    // Level 7: Trace threshold
  ]);

  // Number of trials per contrast level
  const CONTRAST_TRIALS_PER_LEVEL = 4;
  // Threshold criterion: at least 3 out of 4 correct (75%)
  const CONTRAST_PASS_THRESHOLD_COUNT = 3;

  // Standardized reading passage with 4 comprehension questions
  const PASSAGE_RAW_TEXT = 'Human visual perception relies on subtle contrast transitions and comfortable spatial frequencies. When reading long articles on digital displays, text layout directly influences cognitive stamina. Optimal paragraph line spacing prevents the reader from losing their place between lines, while subtle letter tracking minimizes visual crowding. These adjustments allow our visual cortex to recognize character wordforms more fluidly. By tuning digital display parameters to individual viewing comfort, readers can engage with technical and literary content with greater ease, reducing the fatigue often associated with prolonged screen sessions.';

  const STANDARD_READING_PASSAGE = Object.freeze({
    title: 'Digital Typography & Human Vision',
    text: PASSAGE_RAW_TEXT,
    wordCount: countWords(PASSAGE_RAW_TEXT), // 86 words calculated programmatically
    questions: [
      {
        id: 'q1',
        prompt: 'What does human visual perception rely on according to the text?',
        options: [
          { id: 'a', text: 'Rapid blinking and high brightness' },
          { id: 'b', text: 'Subtle contrast transitions and comfortable spatial frequencies' },
          { id: 'c', text: 'Small fonts and darkened rooms' },
          { id: 'd', text: 'Constantly shifting color temperatures' }
        ],
        correctId: 'b'
      },
      {
        id: 'q2',
        prompt: 'What is the main benefit of optimal paragraph line spacing?',
        options: [
          { id: 'a', text: 'Prevents the reader from losing their place between lines' },
          { id: 'b', text: 'Doubles reading speed automatically' },
          { id: 'c', text: 'Changes font colors dynamically' },
          { id: 'd', text: 'Hides unwanted display reflections' }
        ],
        correctId: 'a'
      },
      {
        id: 'q3',
        prompt: 'What visual issue does subtle letter tracking minimize?',
        options: [
          { id: 'a', text: 'Display battery power consumption' },
          { id: 'b', text: 'Visual crowding between character glyphs' },
          { id: 'c', text: 'Internet network bandwidth usage' },
          { id: 'd', text: 'Mouse cursor tracking latency' }
        ],
        correctId: 'b'
      },
      {
        id: 'q4',
        prompt: 'What is the overall goal of tuning digital display parameters to individual viewing comfort?',
        options: [
          { id: 'a', text: 'To eliminate the need for computer displays' },
          { id: 'b', text: 'To engage with content with greater ease and reduce fatigue' },
          { id: 'c', text: 'To force all web pages into a single column' },
          { id: 'd', text: 'To maximize screen contrast to 100% at all times' }
        ],
        correctId: 'b'
      }
    ]
  });

  const VisionFreeAssessment = {
    DIRECTIONS: OPTOTYPE_DIRECTIONS,
    ANGLE_LEVELS: VISUAL_ANGLE_LEVELS_ARCMIN,
    ACUITY_TRIALS_PER_LEVEL,
    ACUITY_PASS_THRESHOLD_COUNT,
    CONTRAST_LEVELS: CONTRAST_LEVELS_PERCENT,
    CONTRAST_TRIALS_PER_LEVEL,
    CONTRAST_PASS_THRESHOLD_COUNT,
    STANDARD_READING_PASSAGE,

    /**
     * Calculates pixels per physical millimeter from a manual 100mm ruler calibration.
     * @param {number} displayedCssPixels
     * @param {number} [targetMm=100]
     * @returns {number} pxPerMm
     */
    calculatePxPerMm(displayedCssPixels, targetMm = 100) {
      if (!displayedCssPixels || displayedCssPixels <= 0 || targetMm <= 0) {
        return 3.78; // Standard 96 DPI CSS fallback (~3.779 px/mm)
      }
      return parseFloat((displayedCssPixels / targetMm).toFixed(4));
    },

    /**
     * Calculates the required physical optotype height in millimeters for a target visual angle.
     * Formula: Height = 2 * Distance * tan(Angle_degrees / 2)
     * @param {number} angleArcmin - Total subtended visual angle in arcminutes
     * @param {number} viewingDistanceCm - Distance from screen in centimeters
     * @returns {number} Height in millimeters
     */
    calculateOptotypeHeightMm(angleArcmin, viewingDistanceCm) {
      if (!angleArcmin || angleArcmin <= 0 || !viewingDistanceCm || viewingDistanceCm <= 0) {
        return 5.0;
      }
      const distanceMm = viewingDistanceCm * 10;
      const angleRad = (angleArcmin / 60) * (Math.PI / 180);
      const heightMm = 2 * distanceMm * Math.tan(angleRad / 2);
      return parseFloat(heightMm.toFixed(4));
    },

    /**
     * Calculates rendered CSS pixel size of an optotype.
     * @param {number} angleArcmin
     * @param {number} pxPerMm
     * @param {number} viewingDistanceCm
     * @returns {number} CSS pixels
     */
    getOptotypePixelSize(angleArcmin, pxPerMm, viewingDistanceCm) {
      if (!pxPerMm || pxPerMm <= 0 || !viewingDistanceCm || viewingDistanceCm <= 0) {
        return Math.max(10, Math.round(angleArcmin * 2.2));
      }
      const heightMm = this.calculateOptotypeHeightMm(angleArcmin, viewingDistanceCm);
      const px = heightMm * pxPerMm;
      return Math.max(8, Math.round(px));
    },

    /**
     * Counts words in a string using standard whitespace separation.
     * @param {string} text
     * @returns {number}
     */
    countWords,

    /**
     * Converts linear relative luminance (0 to 1) to an sRGB channel value (0 to 1).
     * Standard IEC 61966-2-1 electro-optical transfer function.
     * @param {number} L - Linear relative luminance
     * @returns {number} Normalized sRGB channel
     */
    linearToSrgb(L) {
      const clamped = Math.max(0, Math.min(1, L));
      if (clamped <= 0.0031308) {
        return 12.92 * clamped;
      }
      return 1.055 * Math.pow(clamped, 1 / 2.4) - 0.055;
    },

    /**
     * Decodes a normalized sRGB channel value (0 to 1) to linear relative luminance.
     * @param {number} S - Normalized sRGB channel
     * @returns {number} Linear relative luminance
     */
    srgbToLinear(S) {
      const clamped = Math.max(0, Math.min(1, S));
      if (clamped <= 0.04045) {
        return clamped / 12.92;
      }
      return Math.pow((clamped + 0.055) / 1.055, 2.4);
    },

    /**
     * Calculates the 8-bit sRGB grayscale channel value for a target nominal relative luminance contrast against a white background (L_bg = 1.0).
     * Procedure:
     * 1. Normalized contrast C = contrastPercent / 100
     * 2. Target foreground relative luminance L = 1 - C
     * 3. Non-linear sRGB channel S = linearToSrgb(L)
     * 4. 8-bit channel = round(255 * S)
     * Note: Represents nominal sRGB-relative-luminance contrast. Does not guarantee physical monitor luminance or calibrate monitor gamma.
     * @param {number} contrastPercent (0 to 100)
     * @returns {number} 8-bit integer channel (0 to 255)
     */
    getContrastRgbChannel(contrastPercent) {
      const clampedC = Math.max(0, Math.min(100, contrastPercent)) / 100;
      const L = 1 - clampedC;
      const S = this.linearToSrgb(L);
      return Math.round(255 * Math.max(0, Math.min(1, S)));
    },

    /**
     * Generates an sRGB contrast color string against a white (#FFFFFF) background.
     * @param {number} contrastPercent (0 to 100)
     * @returns {string} rgb(r, g, b)
     */
    getContrastColor(contrastPercent) {
      const val = this.getContrastRgbChannel(contrastPercent);
      return `rgb(${val}, ${val}, ${val})`;
    },

    /**
     * Decodes an 8-bit sRGB channel value back to nominal linear relative contrast against white.
     * @param {number} channelValue (0 to 255)
     * @returns {number} Decoded contrast percentage (0 to 100)
     */
    decodeSrgbContrast(channelValue) {
      const S = Math.max(0, Math.min(255, channelValue)) / 255;
      const L = this.srgbToLinear(S);
      return parseFloat(((1 - L) * 100).toFixed(2));
    },

    /**
     * Generates an SVG string for an experimental 5x5 Tumbling E optotype with 5:5:1 geometric proportions.
     * Proportions: 5 units total height, 5 units width, 1 unit stroke, 1 unit gap.
     * Screen-based experimental stimulus, not clinically certified or standardized.
     * @param {number} sizePx - Rendered bounding box size in CSS pixels
     * @param {number} angleDeg - Rotation angle in degrees (0=Right, 90=Down, 180=Left, 270=Up)
     * @param {string} [color='#000000'] - Fill color
     * @returns {string} SVG HTML string
     */
    generateTumblingESVG(sizePx, angleDeg, color = '#000000') {
      const size = Math.max(8, Math.round(sizePx));
      // 5x5 grid path on a 50x50 canvas:
      // Spine: 0..10, Top: 0..50 (y:0..10), Mid: 0..40 (y:20..30), Bot: 0..50 (y:40..50)
      const pathD = 'M 0,0 L 50,0 L 50,10 L 10,10 L 10,20 L 40,20 L 40,30 L 10,30 L 10,40 L 50,40 L 50,50 L 0,50 Z';

      return `<svg viewBox="0 0 50 50" width="${size}" height="${size}" style="transform: rotate(${angleDeg}deg); transform-origin: 50% 50%; display: block;" role="img" aria-label="Tumbling E">
        <path d="${pathD}" fill="${color}" />
      </svg>`;
    },

    /**
     * Generates a random Tumbling E direction, avoiding immediate repetition if previous given.
     * @param {string} [previousId]
     * @returns {{ id: string, label: string, symbol: string, angle: number }}
     */
    getRandomDirection(previousId = null) {
      let pool = OPTOTYPE_DIRECTIONS;
      if (previousId) {
        const filtered = pool.filter(d => d.id !== previousId);
        if (filtered.length > 0) pool = filtered;
      }
      const idx = Math.floor(Math.random() * pool.length);
      return pool[idx];
    },

    /**
     * Computes reading speed in Words Per Minute (WPM).
     * @param {number} wordCount
     * @param {number} durationSeconds
     * @returns {number} WPM
     */
    calculateWPM(wordCount, durationSeconds) {
      if (!wordCount || !durationSeconds || durationSeconds <= 0) {
        return 0;
      }
      const minutes = durationSeconds / 60;
      return Math.round(wordCount / minutes);
    },

    /**
     * Checks if current browser DPR or screen resolution has changed relative to saved calibration.
     * Does NOT invalidate solely based on window resizing if physical screen scale is unchanged.
     * Note: Browser APIs cannot detect physical monitor changes if screen resolution and DPR match.
     * @param {Object} cal - Saved calibration object
     * @returns {{ isStale: boolean, reason?: string }}
     */
    checkCalibrationFreshness(cal) {
      if (!cal || !cal.isCalibrated) {
        return { isStale: false };
      }

      if (typeof window === 'undefined') {
        return { isStale: false };
      }

      const currentDpr = window.devicePixelRatio || 1;
      const savedDpr = cal.calibratedDpr || 1;

      // Check DPR / browser zoom change
      if (Math.abs(currentDpr - savedDpr) > 0.05) {
        return {
          isStale: true,
          reason: `Display scaling or browser zoom changed (DPR was ${savedDpr.toFixed(2)}, now ${currentDpr.toFixed(2)}). Display conditions may have changed. Please verify calibration.`
        };
      }

      // Check screen display resolution changes (e.g. monitor topology or display setting changes)
      if (typeof window.screen !== 'undefined') {
        const currentScreenW = window.screen.width;
        const currentScreenH = window.screen.height;
        const savedScreenW = cal.calibratedScreenWidth || currentScreenW;
        const savedScreenH = cal.calibratedScreenHeight || currentScreenH;

        if (currentScreenW !== savedScreenW || currentScreenH !== savedScreenH) {
          return {
            isStale: true,
            reason: 'Screen resolution or display arrangement changed. Display conditions may have changed. Please verify calibration.'
          };
        }
      }

      return { isStale: false };
    },

    /**
     * Creates an empty assessment structure for a profile.
     * @param {string} profileId
     * @returns {Object}
     */
    createEmptyAssessment(profileId) {
      const sw = typeof window !== 'undefined' && window.screen ? window.screen.width : 1920;
      const sh = typeof window !== 'undefined' && window.screen ? window.screen.height : 1080;
      return {
        profileId,
        schemaVersion: '4.1.0',
        updatedAt: Date.now(),
        calibration: {
          isCalibrated: false,
          isStale: false,
          pxPerMm: 3.78,
          sliderPx: 378,
          targetMm: 100,
          viewingDistanceCm: 50,
          calibratedScreenWidth: sw,
          calibratedScreenHeight: sh,
          calibratedDpr: typeof window !== 'undefined' ? (window.devicePixelRatio || 1) : 1,
          calibratedAt: null
        },
        visualAcuity: {
          rightEye: null,
          leftEye: null
        },
        contrast: null,
        reading: null
      };
    }
  };

  global.VisionFreeAssessment = VisionFreeAssessment;

})(typeof globalThis !== 'undefined' ? globalThis : this);

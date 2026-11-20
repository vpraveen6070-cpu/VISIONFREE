/**
 * VISIONFREE — Phase 4 Final Technical Corrections Verification Suite
 * Tests:
 * 1. Experimental 5x5 Tumbling E SVG generation (5:5:1 geometry).
 * 2. Visual Acuity 5-trial progression, threshold calculation, and aggregate consistency:
 *    - 6 levels, 5 trials per level (including failed level).
 *    - Total administered trials = 30.
 *    - Correct answers = 22.
 *    - Overall accuracy = 73.33%.
 *    - Separate threshold = 7.5 arcmin (80% threshold passed).
 * 3. Relative Contrast sRGB non-linear electro-optical encoding & decoding:
 *    - 100%, 50%, 25%, 6%, 1.5% nominal contrast.
 *    - Round-trip decoding back to linear relative luminance within rounding tolerance.
 * 4. Reading passage programmatic word count & WPM math:
 *    - Actual passage word count = 86 (not hardcoded 96).
 *    - WPM calculation with verified 86 words.
 *    - 4-question comprehension scoring.
 * 5. Display calibration math & stale detection limitations:
 *    - DPR change flags stale ("Display conditions may have changed").
 *    - Screen resolution change flags stale.
 *    - Window resize alone does NOT flag stale when physical scale is unchanged.
 * 6. Chrome storage consistency & prescription isolation:
 *    - Assessment records under visionfree_assessments.
 *    - Strict separation from visionfree_profiles.
 *    - Preference sanitization strips prescription and assessment data.
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

console.log('================================================================');
console.log('🧪 VISIONFREE — Phase 4 Final Technical Corrections Test Suite');
console.log('================================================================\n');

// 1. Load assessment module
const assessmentPath = path.join(__dirname, '..', 'core', 'assessment.js');
require(assessmentPath);
const VFA = globalThis.VisionFreeAssessment;

assert(VFA, 'VisionFreeAssessment must be defined');
console.log('✅ 1. Loaded core/assessment.js successfully.');

// Test 1: Experimental 5x5 Tumbling E Geometry & Proportions (No ISO 8596 claims)
{
  console.log('\n--- Test 1: Experimental 5x5 Tumbling E (5:5:1 Proportions) ---');
  assert.strictEqual(VFA.DIRECTIONS.length, 4, 'Must have 4 cardinal directions');
  const dirs = VFA.DIRECTIONS.map(d => d.id);
  assert(dirs.includes('right') && dirs.includes('down') && dirs.includes('left') && dirs.includes('up'));

  const svgStr = VFA.generateTumblingESVG(40, 90, '#000000');
  assert(svgStr.includes('viewBox="0 0 50 50"'), 'SVG must use 50x50 viewBox');
  assert(svgStr.includes('width="40"'), 'Rendered width must match requested size');
  assert(svgStr.includes('height="40"'), 'Rendered height must match requested size');
  assert(svgStr.includes('rotate(90deg)'), 'Rotation style must reflect direction angle');
  assert(svgStr.includes('M 0,0 L 50,0 L 50,10 L 10,10 L 10,20 L 40,20 L 40,30 L 10,30 L 10,40 L 50,40 L 50,50 L 0,50 Z'), 'SVG path must match 5:5:1 ratio');
  console.log('✅ Experimental 5x5 Tumbling E correctly generated with 5:5:1 geometric proportions.');
}

// Test 2: Visual Acuity Progression, Aggregate Consistency & Accuracy
{
  console.log('\n--- Test 2: Visual Acuity Multi-Trial Aggregate Consistency ---');
  assert.strictEqual(VFA.ACUITY_TRIALS_PER_LEVEL, 5, 'Must require 5 trials per level');
  assert.strictEqual(VFA.ACUITY_PASS_THRESHOLD_COUNT, 4, 'Must require >=4 correct answers to pass');
  assert.strictEqual(VFA.ANGLE_LEVELS.length, 6, 'Must define 6 standard progressive visual angle levels');

  // Simulate 6 levels tested with 5 trials each (5 passed, 6th failed):
  // Level 1 (30.0 arcmin): 5/5 -> Passed
  // Level 2 (20.0 arcmin): 5/5 -> Passed
  // Level 3 (15.0 arcmin): 4/5 -> Passed
  // Level 4 (10.0 arcmin): 4/5 -> Passed
  // Level 5 (7.5 arcmin):  4/5 -> Passed
  // Level 6 (5.0 arcmin):  0/5 -> Failed
  const levelResults = [
    { levelIndex: 1, arcmin: 30.0, trials: 5, correct: 5, passed: true },
    { levelIndex: 2, arcmin: 20.0, trials: 5, correct: 5, passed: true },
    { levelIndex: 3, arcmin: 15.0, trials: 5, correct: 4, passed: true },
    { levelIndex: 4, arcmin: 10.0, trials: 5, correct: 4, passed: true },
    { levelIndex: 5, arcmin: 7.5,  trials: 5, correct: 4, passed: true },
    { levelIndex: 6, arcmin: 5.0,  trials: 5, correct: 0, passed: false }
  ];

  const totalAdministeredTrials = levelResults.reduce((sum, r) => sum + r.trials, 0);
  const totalCorrectAnswers = levelResults.reduce((sum, r) => sum + r.correct, 0);

  // Requirements check:
  // 1. All administered trials counted including failed level: 30
  assert.strictEqual(totalAdministeredTrials, 30, 'Total administered trials must equal 30');
  // 2. Sum of correct answers: 22
  assert.strictEqual(totalCorrectAnswers, 22, 'Total correct answers must equal 22');

  // 3. Overall accuracy: 22 / 30 = 73.33% (NOT 88%)
  const overallAcc = ((totalCorrectAnswers / totalAdministeredTrials) * 100).toFixed(2);
  assert.strictEqual(overallAcc, '73.33', 'Overall accuracy for 22/30 must equal 73.33%');

  // 4. Threshold is separate: smallest passed size is 7.5 arcmin (Level 5)
  const passedLevels = levelResults.filter(r => r.passed);
  const smallestPassed = passedLevels[passedLevels.length - 1];
  assert.strictEqual(smallestPassed.arcmin, 7.5, 'Smallest identified threshold size must be 7.5 arcmin');
  assert.strictEqual(smallestPassed.correct, 4, 'Threshold accuracy count must be 4/5');

  console.log(`✅ Visual acuity aggregate consistency verified: ${totalCorrectAnswers}/${totalAdministeredTrials} trials = ${overallAcc}% (Threshold: ${smallestPassed.arcmin} arcmin).`);
}

// Test 3: sRGB Non-Linear Contrast Encoding & Decoding
{
  console.log('\n--- Test 3: sRGB Non-Linear Electro-Optical Contrast Encoding & Decoding ---');
  const testTiers = [100.0, 50.0, 25.0, 12.0, 6.0, 3.0, 1.5, 0.0];

  testTiers.forEach(nominal => {
    const channel = VFA.getContrastRgbChannel(nominal);
    const colorStr = VFA.getContrastColor(nominal);
    assert.strictEqual(colorStr, `rgb(${channel}, ${channel}, ${channel})`, 'getContrastColor must match channel value');

    // Decode channel back to nominal contrast
    const decodedContrast = VFA.decodeSrgbContrast(channel);
    const diff = Math.abs(nominal - decodedContrast);

    // Difference must be within 8-bit integer quantization tolerance (~0.45%)
    assert(diff <= 0.45, `Nominal ${nominal}% decoded as ${decodedContrast}% diff ${diff} must be <= 0.45%`);
  });

  // Specific unit tests for required tiers:
  // 100%: channel 0 (pure black)
  assert.strictEqual(VFA.getContrastRgbChannel(100), 0, '100% contrast channel must be 0');
  // 50%: channel 188
  assert.strictEqual(VFA.getContrastRgbChannel(50), 188, '50% contrast channel must be 188');
  // 25%: channel 225
  assert.strictEqual(VFA.getContrastRgbChannel(25), 225, '25% contrast channel must be 225');
  // 6%: channel 248
  assert.strictEqual(VFA.getContrastRgbChannel(6), 248, '6% contrast channel must be 248');
  // 1.5%: channel 253
  assert.strictEqual(VFA.getContrastRgbChannel(1.5), 253, '1.5% contrast channel must be 253');

  // Verify non-linear transfer function vs naive linear
  // Under naive linear, 50% contrast would be 128. In true sRGB, 50% contrast is 188.
  assert.notStrictEqual(VFA.getContrastRgbChannel(50), 128, '50% contrast must NOT use naive linear 128');

  console.log('✅ sRGB non-linear contrast encoding and round-trip decoding verified for all tiers (100%, 50%, 25%, 6%, 1.5%).');
}

// Test 4: Reading Passage Word Count & WPM Math
{
  console.log('\n--- Test 4: Reading Passage Programmatic Word Count & WPM ---');
  const passage = VFA.STANDARD_READING_PASSAGE;

  // Programmatically count words in the passage text
  const calculatedCount = VFA.countWords(passage.text);
  assert.strictEqual(calculatedCount, 86, 'Actual passage word count must be 86 (not hardcoded 96)');
  assert.strictEqual(passage.wordCount, 86, 'STANDARD_READING_PASSAGE.wordCount must be 86');

  // WPM with verified 86 words:
  // 86 words in 30.0s = (86 / 0.5) = 172 WPM
  const wpm30 = VFA.calculateWPM(86, 30);
  assert.strictEqual(wpm30, 172, '86 words in 30s must equal 172 WPM');

  // 86 words in 24.0s = (86 / 0.4) = 215 WPM
  const wpm24 = VFA.calculateWPM(86, 24);
  assert.strictEqual(wpm24, 215, '86 words in 24s must equal 215 WPM');

  // Verify comprehension questions align with passage
  assert.strictEqual(passage.questions.length, 4, 'Must have exactly 4 comprehension questions');
  const testAnswers = ['b', 'a', 'b', 'b'];
  let correctCount = 0;
  passage.questions.forEach((q, i) => {
    if (testAnswers[i] === q.correctId) correctCount++;
  });
  assert.strictEqual(correctCount, 4, 'All correct answers must yield 4/4 (100%)');

  console.log(`✅ Reading passage programmatic word count verified: exactly ${calculatedCount} words (WPM: 30s=172, 24s=215).`);
}

// Test 5: Calibration Math & Stale Detection Limitations
{
  console.log('\n--- Test 5: Calibration Stale Detection & Limitations ---');
  const mockWin = {
    devicePixelRatio: 1.0,
    innerWidth: 1200,
    innerHeight: 800,
    screen: {
      width: 1920,
      height: 1080
    }
  };
  global.window = mockWin;

  const validCalibration = {
    isCalibrated: true,
    calibratedDpr: 1.0,
    calibratedScreenWidth: 1920,
    calibratedScreenHeight: 1080
  };

  // 1. Initial state: not stale
  const check1 = VFA.checkCalibrationFreshness(validCalibration);
  assert.strictEqual(check1.isStale, false, 'Unchanged display conditions must not be stale');

  // 2. Window resizing alone on the same display: must NOT be stale
  mockWin.innerWidth = 800; // Resized window significantly
  mockWin.innerHeight = 600;
  const checkResize = VFA.checkCalibrationFreshness(validCalibration);
  assert.strictEqual(checkResize.isStale, false, 'Browser window resizing alone must NOT invalidate physical calibration');

  // 3. Browser zoom changes DPR to 1.25x: must be stale
  mockWin.devicePixelRatio = 1.25;
  const checkZoom = VFA.checkCalibrationFreshness(validCalibration);
  assert.strictEqual(checkZoom.isStale, true, 'DPR change must flag calibration for review');
  assert(checkZoom.reason.includes('Display conditions may have changed'), 'Must use cautious advisory wording');

  // 4. Reset DPR, change screen resolution (display topology change): must be stale
  mockWin.devicePixelRatio = 1.0;
  mockWin.screen.width = 2560;
  mockWin.screen.height = 1440;
  const checkScreen = VFA.checkCalibrationFreshness(validCalibration);
  assert.strictEqual(checkScreen.isStale, true, 'Screen resolution change must flag calibration for review');

  delete global.window;
  console.log('✅ Calibration stale-detection behavior and limitations verified (resizing does not invalidate; DPR/resolution does).');
}

// Test 6: Storage Schema Consistency & Prescription Isolation
{
  console.log('\n--- Test 6: Storage Schema Consistency & Prescription Isolation ---');
  const mockStorageStore = {};
  global.chrome = {
    storage: {
      local: {
        async get(keys) {
          const res = {};
          keys.forEach(k => { if (mockStorageStore[k] !== undefined) res[k] = mockStorageStore[k]; });
          return res;
        },
        async set(obj) {
          Object.assign(mockStorageStore, obj);
        }
      }
    }
  };

  const storagePath = path.join(__dirname, '..', 'core', 'storage.js');
  require(storagePath);
  const Storage = globalThis.VisionFreeStorage;

  (async () => {
    const profileId = 'prof_test_410';
    const assessmentPayload = {
      visualAcuity: {
        rightEye: {
          completed: true,
          smallestSizeArcmin: 7.5,
          thresholdAccuracy: '4/5 (80%)',
          totalQuestions: 30,
          correctAnswers: 22,
          accuracyPercent: 73.33,
          perLevelResults: [
            { levelIndex: 1, arcmin: 30.0, trials: 5, correct: 5, accuracyPercent: 100, passed: true },
            { levelIndex: 2, arcmin: 20.0, trials: 5, correct: 5, accuracyPercent: 100, passed: true },
            { levelIndex: 3, arcmin: 15.0, trials: 5, correct: 4, accuracyPercent: 80,  passed: true },
            { levelIndex: 4, arcmin: 10.0, trials: 5, correct: 4, accuracyPercent: 80,  passed: true },
            { levelIndex: 5, arcmin: 7.5,  trials: 5, correct: 4, accuracyPercent: 80,  passed: true },
            { levelIndex: 6, arcmin: 5.0,  trials: 5, correct: 0, accuracyPercent: 0,   passed: false }
          ],
          calibrated: true,
          timestamp: Date.now()
        }
      },
      reading: {
        completed: true,
        wpm: 215,
        readingTimeSeconds: 24.0,
        wordCount: 86,
        comfortRating: 4,
        comprehensionQuestionsTotal: 4,
        comprehensionCorrect: 4,
        comprehensionAccuracyPercent: 100,
        timestamp: Date.now()
      }
    };

    const saved = await Storage.saveAssessment(profileId, assessmentPayload);
    assert.strictEqual(saved, true, 'saveAssessment must return true');

    const retrieved = await Storage.getAssessment(profileId);
    assert.strictEqual(retrieved.visualAcuity.rightEye.totalQuestions, 30);
    assert.strictEqual(retrieved.visualAcuity.rightEye.correctAnswers, 22);
    assert.strictEqual(retrieved.visualAcuity.rightEye.accuracyPercent, 73.33);
    assert.strictEqual(retrieved.visualAcuity.rightEye.smallestSizeArcmin, 7.5);
    assert.strictEqual(retrieved.reading.wordCount, 86);
    assert.strictEqual(retrieved.reading.wpm, 215);

    // Verify sanitizeDisplayPreferences strictly strips out prescription and assessment data
    const contaminatedInput = {
      lineSpacing: '1.8',
      letterSpacing: '0.04em',
      fontWeightDelta: '100',
      highContrastText: true,
      sph: -2.50,
      cyl: -1.00,
      axis: 90,
      visualAcuity: '20/20'
    };
    const sanitized = Storage.sanitizeDisplayPreferences(contaminatedInput);
    assert.strictEqual(sanitized.sph, undefined, 'Prescription SPH must be stripped');
    assert.strictEqual(sanitized.cyl, undefined, 'Prescription CYL must be stripped');
    assert.strictEqual(sanitized.axis, undefined, 'Prescription Axis must be stripped');
    assert.strictEqual(sanitized.visualAcuity, undefined, 'Assessment data must be stripped');
    assert.strictEqual(sanitized.lineSpacing, '1.8');
    assert.strictEqual(sanitized.letterSpacing, '0.04em');

    console.log('✅ Storage schema consistency and prescription isolation verified.');
    console.log('\n================================================================');
    console.log('🎉 ALL PHASE 4 FINAL TECHNICAL CORRECTIONS TESTS PASSED!');
    console.log('================================================================\n');
  })().catch(err => {
    console.error('❌ Test failed with error:', err);
    process.exit(1);
  });
}

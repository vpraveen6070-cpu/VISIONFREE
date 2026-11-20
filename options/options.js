/**
 * VISIONFREE — Options & Assessment Controller (options/options.js)
 * Phase 4 Corrections: Multi-Trial Visual Tasks, Comprehension & Stale Calibration
 */

document.addEventListener('DOMContentLoaded', async () => {
  // =========================================================================
  // DOM REFERENCES: WORKSPACE TABS
  // =========================================================================
  const tabBtnProfiles = document.getElementById('tab-btn-profiles');
  const tabBtnAssessment = document.getElementById('tab-btn-assessment');
  const panelProfiles = document.getElementById('panel-profiles');
  const panelAssessment = document.getElementById('panel-assessment');

  // =========================================================================
  // DOM REFERENCES: PROFILE MANAGEMENT (Phases 1-3)
  // =========================================================================
  const profileSelect = document.getElementById('profile-select');
  const activeBadge = document.getElementById('active-badge');
  const btnCreateProfile = document.getElementById('btn-create-profile');
  const btnSetActive = document.getElementById('btn-set-active');
  const btnRenameProfile = document.getElementById('btn-rename-profile');
  const btnDeleteProfile = document.getElementById('btn-delete-profile');
  const btnResetProfile = document.getElementById('btn-reset-profile');

  const profileNameDialog = document.getElementById('profile-name-dialog');
  const profileDialogLabel = document.getElementById('profile-dialog-label');
  const profileNameInput = document.getElementById('profile-name-input');
  const profileNameError = document.getElementById('profile-name-error');
  const btnSaveProfileName = document.getElementById('btn-save-profile-name');
  const btnCancelProfileName = document.getElementById('btn-cancel-profile-name');

  const prescriptionForm = document.getElementById('prescription-form');
  const odSph = document.getElementById('od-sph');
  const odCyl = document.getElementById('od-cyl');
  const odAxis = document.getElementById('od-axis');
  const osSph = document.getElementById('os-sph');
  const osCyl = document.getElementById('os-cyl');
  const osAxis = document.getElementById('os-axis');
  const prescriptionFeedback = document.getElementById('prescription-feedback');

  const preferencesForm = document.getElementById('preferences-form');
  const presetSelect = document.getElementById('preset-select');
  const lineSpacingSelect = document.getElementById('lineSpacing');
  const letterSpacingSelect = document.getElementById('letterSpacing');
  const fontWeightSelect = document.getElementById('fontWeightDelta');
  const highContrastCheckbox = document.getElementById('highContrastText');
  const previewBox = document.getElementById('sample-preview');
  const preferencesFeedback = document.getElementById('preferences-feedback');

  // =========================================================================
  // DOM REFERENCES: ASSESSMENT & CALIBRATION (Phase 4)
  // =========================================================================
  const specViewport = document.getElementById('spec-viewport');
  const specDpr = document.getElementById('spec-dpr');
  const specScreen = document.getElementById('spec-screen');
  const specPxMm = document.getElementById('spec-px-mm');
  const calStatusBadge = document.getElementById('cal-status-badge');
  const calStaleWarning = document.getElementById('cal-stale-warning');
  const calStaleReason = document.getElementById('cal-stale-reason');

  const rulerBar = document.getElementById('ruler-bar');
  const calSlider = document.getElementById('cal-slider');
  const calSliderDisplay = document.getElementById('cal-slider-display');
  const viewingDistanceInput = document.getElementById('viewing-distance-input');
  const btnSaveCalibration = document.getElementById('btn-save-calibration');
  const btnResetCalibration = document.getElementById('btn-reset-calibration');
  const calFeedback = document.getElementById('cal-feedback');

  // Visual Task Controls
  const btnStartAcuity = document.getElementById('btn-start-acuity');
  const btnPauseAcuity = document.getElementById('btn-pause-acuity');
  const btnResumeAcuity = document.getElementById('btn-resume-acuity');
  const btnRestartAcuity = document.getElementById('btn-restart-acuity');
  const btnCancelAcuity = document.getElementById('btn-cancel-acuity');

  const acuityStage = document.getElementById('acuity-stage');
  const acuityOptotypeWrapper = document.getElementById('acuity-optotype-wrapper');
  const acuityPausedOverlay = document.getElementById('acuity-paused-overlay');
  const acuityLevelIndicator = document.getElementById('acuity-level-indicator');
  const acuityTrialIndicator = document.getElementById('acuity-trial-indicator');
  const acuityScoreIndicator = document.getElementById('acuity-score-indicator');
  const acuityStatusMsg = document.getElementById('acuity-status-msg');

  const acuityResultCard = document.getElementById('acuity-result-card');
  const resAcuityEye = document.getElementById('res-acuity-eye');
  const resAcuityThreshold = document.getElementById('res-acuity-threshold');
  const resAcuityThreshAcc = document.getElementById('res-acuity-thresh-acc');
  const resAcuityOverallAcc = document.getElementById('res-acuity-overall-acc');
  const resAcuityCal = document.getElementById('res-acuity-cal');
  const resAcuityBreakdown = document.getElementById('res-acuity-breakdown');
  const btnDirAll = document.querySelectorAll('.btn-dir:not(.btn-dir-contrast)');

  // Contrast Task Controls
  const btnStartContrast = document.getElementById('btn-start-contrast');
  const btnPauseContrast = document.getElementById('btn-pause-contrast');
  const btnResumeContrast = document.getElementById('btn-resume-contrast');
  const btnRestartContrast = document.getElementById('btn-restart-contrast');
  const btnCancelContrast = document.getElementById('btn-cancel-contrast');

  const contrastStage = document.getElementById('contrast-stage');
  const contrastOptotypeWrapper = document.getElementById('contrast-optotype-wrapper');
  const contrastPausedOverlay = document.getElementById('contrast-paused-overlay');
  const contrastLevelIndicator = document.getElementById('contrast-level-indicator');
  const contrastTrialIndicator = document.getElementById('contrast-trial-indicator');
  const contrastScoreIndicator = document.getElementById('contrast-score-indicator');
  const contrastStatusMsg = document.getElementById('contrast-status-msg');

  const contrastResultCard = document.getElementById('contrast-result-card');
  const resContrastThresh = document.getElementById('res-contrast-thresh');
  const resContrastThreshAcc = document.getElementById('res-contrast-thresh-acc');
  const resContrastLevels = document.getElementById('res-contrast-levels');
  const resContrastBreakdown = document.getElementById('res-contrast-breakdown');
  const btnDirContrastAll = document.querySelectorAll('.btn-dir-contrast');

  // Reading Task Controls
  const btnStartReading = document.getElementById('btn-start-reading');
  const btnFinishReading = document.getElementById('btn-finish-reading');
  const readingTimerDisplay = document.getElementById('reading-timer-display');
  const readingPassageCard = document.getElementById('reading-passage-card');

  const readingComprehensionBox = document.getElementById('reading-comprehension-box');
  const comprehensionForm = document.getElementById('comprehension-form');
  const compErrorMsg = document.getElementById('comp-error-msg');
  const btnRatingAll = document.querySelectorAll('.btn-rating');

  const readingResultCard = document.getElementById('reading-result-card');
  const resReadingWpm = document.getElementById('res-reading-wpm');
  const resReadingTime = document.getElementById('res-reading-time');
  const resReadingComp = document.getElementById('res-reading-comp');
  const resReadingComfort = document.getElementById('res-reading-comfort');

  // History Table
  const assessmentHistoryBody = document.getElementById('assessment-history-body');
  const btnClearAssessments = document.getElementById('btn-clear-assessments');

  // =========================================================================
  // APPLICATION STATE
  // =========================================================================
  let allProfiles = [];
  let activeProfileId = '';
  let selectedProfileId = '';
  let dialogMode = 'create';

  // Calibration State
  let currentCalibration = {
    isCalibrated: false,
    pxPerMm: 3.78,
    sliderPx: 378,
    targetMm: 100,
    viewingDistanceCm: 50,
    calibratedScreenWidth: window.screen ? window.screen.width : 1920,
    calibratedScreenHeight: window.screen ? window.screen.height : 1080,
    calibratedDpr: window.devicePixelRatio || 1
  };

  // Multi-Trial Visual Acuity Task State
  let acuityState = 'idle'; // 'idle' | 'running' | 'paused'
  let acuityEye = 'rightEye';
  let acuityLevelIdx = 0;
  let acuityTrialInLevel = 0;
  let acuityLevelCorrect = 0;
  let acuityTotalTrials = 0;
  let acuityTotalCorrect = 0;
  let acuityPerLevelResults = [];
  let currentAcuityDirection = null;
  let smallestAcuityPassedArcmin = null;
  let thresholdAccuracyStr = '--';

  // Multi-Trial Contrast Task State
  let contrastState = 'idle'; // 'idle' | 'running' | 'paused'
  let contrastLevelIdx = 0;
  let contrastTrialInLevel = 0;
  let contrastLevelCorrect = 0;
  let contrastTotalTrials = 0;
  let contrastTotalCorrect = 0;
  let contrastPerLevelResults = [];
  let currentContrastDirection = null;
  let lowestContrastPassed = null;
  let contrastThresholdAccuracyStr = '--';

  // Reading Task State
  let isReadingRunning = false;
  let readingStartTime = 0;
  let readingTimerInterval = null;
  let readingElapsedSeconds = 0;
  let readingComfortRating = 4;

  // =========================================================================
  // 1. WORKSPACE INITIALIZATION & TABS
  // =========================================================================
  function switchTab(targetPanelId) {
    if (targetPanelId === 'panel-profiles') {
      tabBtnProfiles.classList.add('active');
      tabBtnAssessment.classList.remove('active');
      panelProfiles.classList.add('active');
      panelAssessment.classList.remove('active');
    } else {
      tabBtnProfiles.classList.remove('active');
      tabBtnAssessment.classList.add('active');
      panelProfiles.classList.remove('active');
      panelAssessment.classList.add('active');
      loadCalibrationIntoUI();
      loadAssessmentHistoryTable();
    }
  }

  tabBtnProfiles.addEventListener('click', () => switchTab('panel-profiles'));
  tabBtnAssessment.addEventListener('click', () => switchTab('panel-assessment'));

  async function initializeWorkspace() {
    try {
      const state = await VisionFreeStorage.initialize();
      allProfiles = state.profiles;
      activeProfileId = state.activeProfileId;
      selectedProfileId = activeProfileId;

      renderProfileSelector();
      loadProfileIntoUI(selectedProfileId);
      loadHardwareDisplaySpecs();
      await loadCalibrationIntoUI();
      await loadAssessmentHistoryTable();
    } catch (err) {
      console.error('[VISIONFREE Options] Initialization error:', err);
    }
  }

  // =========================================================================
  // 2. PROFILE MANAGEMENT (Phases 1-3)
  // =========================================================================
  function renderProfileSelector() {
    profileSelect.innerHTML = '';
    allProfiles.forEach(prof => {
      const opt = document.createElement('option');
      opt.value = prof.id;
      opt.textContent = prof.name + (prof.id === activeProfileId ? ' (Active)' : '');
      profileSelect.appendChild(opt);
    });

    profileSelect.value = selectedProfileId;
    updateActiveIndicator();
  }

  function updateActiveIndicator() {
    const isCurrentActive = (selectedProfileId === activeProfileId);
    activeBadge.style.display = isCurrentActive ? 'inline-block' : 'none';
    btnSetActive.disabled = isCurrentActive;
    btnSetActive.style.opacity = isCurrentActive ? '0.6' : '1';

    const canDelete = allProfiles.length > 1;
    btnDeleteProfile.disabled = !canDelete;
    btnDeleteProfile.style.opacity = canDelete ? '1' : '0.5';
  }

  function loadProfileIntoUI(profileId) {
    const profile = allProfiles.find(p => p.id === profileId);
    if (!profile) return;

    clearAllErrors();

    const rx = profile.prescription || {};
    const od = rx.rightEye || {};
    const os = rx.leftEye || {};

    odSph.value = od.sph !== undefined ? od.sph : '';
    odCyl.value = od.cyl !== undefined ? od.cyl : '';
    odAxis.value = od.axis !== undefined ? od.axis : '';

    osSph.value = os.sph !== undefined ? os.sph : '';
    osCyl.value = os.cyl !== undefined ? os.cyl : '';
    osAxis.value = os.axis !== undefined ? os.axis : '';

    const prefs = profile.preferences || VisionFreeStorage.DEFAULT_SETTINGS;
    lineSpacingSelect.value = prefs.lineSpacing || '1.6';
    letterSpacingSelect.value = prefs.letterSpacing || '0.02em';
    fontWeightSelect.value = prefs.fontWeightDelta !== undefined ? String(prefs.fontWeightDelta) : '0';
    highContrastCheckbox.checked = Boolean(prefs.highContrastText);

    detectMatchingPreset(prefs);
    updateLivePreview();
  }

  function clearAllErrors() {
    [odSph, odCyl, odAxis, osSph, osCyl, osAxis].forEach(inp => inp.classList.remove('is-invalid'));
    ['od-sph-error', 'od-cyl-error', 'od-axis-error', 'os-sph-error', 'os-cyl-error', 'os-axis-error', 'profile-name-error'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
  }

  function updateLivePreview() {
    previewBox.style.lineHeight = lineSpacingSelect.value;
    previewBox.style.letterSpacing = letterSpacingSelect.value;

    const delta = fontWeightSelect.value;
    if (delta === '100') {
      previewBox.style.fontWeight = '500';
    } else if (delta === '200') {
      previewBox.style.fontWeight = '600';
    } else {
      previewBox.style.fontWeight = 'normal';
    }

    previewBox.style.textShadow = highContrastCheckbox.checked ? '0 0 0.5px rgba(0, 0, 0, 0.4)' : 'none';
  }

  function detectMatchingPreset(prefs) {
    if (!VisionFreeProfiles?.PRESETS) return;
    const presets = VisionFreeProfiles.PRESETS;
    let matchedKey = 'custom';
    for (const [key, p] of Object.entries(presets)) {
      if (
        p.lineSpacing === prefs.lineSpacing &&
        p.letterSpacing === prefs.letterSpacing &&
        String(p.fontWeightDelta) === String(prefs.fontWeightDelta) &&
        Boolean(p.highContrastText) === Boolean(prefs.highContrastText)
      ) {
        matchedKey = key;
        break;
      }
    }
    presetSelect.value = matchedKey;
  }

  function showStatus(element, message, isError = false) {
    element.textContent = message;
    element.style.color = isError ? '#dc2626' : '#16a34a';
    setTimeout(() => { element.textContent = ''; }, 4000);
  }

  function validateField(inputEl, errorElId, validationFn, ...extraArgs) {
    const res = validationFn.call(VisionFreeProfiles, inputEl.value, ...extraArgs);
    const errorEl = document.getElementById(errorElId);
    if (!res.valid) {
      inputEl.classList.add('is-invalid');
      if (errorEl) errorEl.textContent = res.error || 'Invalid value.';
      return false;
    } else {
      inputEl.classList.remove('is-invalid');
      if (errorEl) errorEl.textContent = '';
      return true;
    }
  }

  odSph.addEventListener('blur', () => validateField(odSph, 'od-sph-error', VisionFreeProfiles.validateSphere));
  osSph.addEventListener('blur', () => validateField(osSph, 'os-sph-error', VisionFreeProfiles.validateSphere));
  odCyl.addEventListener('blur', () => {
    validateField(odCyl, 'od-cyl-error', VisionFreeProfiles.validateCylinder);
    validateField(odAxis, 'od-axis-error', VisionFreeProfiles.validateAxis, odCyl.value);
  });
  osCyl.addEventListener('blur', () => {
    validateField(osCyl, 'os-cyl-error', VisionFreeProfiles.validateCylinder);
    validateField(osAxis, 'os-axis-error', VisionFreeProfiles.validateAxis, osCyl.value);
  });
  odAxis.addEventListener('blur', () => validateField(odAxis, 'od-axis-error', VisionFreeProfiles.validateAxis, odCyl.value));
  osAxis.addEventListener('blur', () => validateField(osAxis, 'os-axis-error', VisionFreeProfiles.validateAxis, osCyl.value));

  profileSelect.addEventListener('change', async () => {
    selectedProfileId = profileSelect.value;
    loadProfileIntoUI(selectedProfileId);
    updateActiveIndicator();
    await loadCalibrationIntoUI();
    await loadAssessmentHistoryTable();
  });

  btnSetActive.addEventListener('click', async () => {
    const success = await VisionFreeStorage.setActiveProfileId(selectedProfileId);
    if (success) {
      activeProfileId = selectedProfileId;
      renderProfileSelector();
      showStatus(prescriptionFeedback, 'Profile set as active.');
    }
  });

  btnCreateProfile.addEventListener('click', () => {
    dialogMode = 'create';
    profileDialogLabel.textContent = 'Create New Vision Profile:';
    profileNameInput.value = '';
    profileNameError.textContent = '';
    profileNameDialog.style.display = 'block';
    profileNameInput.focus();
  });

  btnRenameProfile.addEventListener('click', () => {
    dialogMode = 'rename';
    const prof = allProfiles.find(p => p.id === selectedProfileId);
    profileDialogLabel.textContent = 'Rename Profile:';
    profileNameInput.value = prof ? prof.name : '';
    profileNameError.textContent = '';
    profileNameDialog.style.display = 'block';
    profileNameInput.focus();
  });

  btnCancelProfileName.addEventListener('click', () => {
    profileNameDialog.style.display = 'none';
  });

  btnSaveProfileName.addEventListener('click', async () => {
    const name = profileNameInput.value.trim();
    if (!name) {
      profileNameError.textContent = 'Name cannot be empty.';
      return;
    }
    if (name.length > 60) {
      profileNameError.textContent = 'Name cannot exceed 60 characters.';
      return;
    }

    if (dialogMode === 'create') {
      const newProf = VisionFreeProfiles.createDefaultProfile(name);
      const res = await VisionFreeStorage.saveProfile(newProf);
      if (res.success) {
        allProfiles = await VisionFreeStorage.getProfiles();
        selectedProfileId = newProf.id;
        renderProfileSelector();
        loadProfileIntoUI(selectedProfileId);
        profileNameDialog.style.display = 'none';
        showStatus(prescriptionFeedback, `Created profile "${name}".`);
      }
    } else {
      const prof = allProfiles.find(p => p.id === selectedProfileId);
      if (prof) {
        prof.name = name;
        const res = await VisionFreeStorage.saveProfile(prof);
        if (res.success) {
          allProfiles = await VisionFreeStorage.getProfiles();
          renderProfileSelector();
          profileNameDialog.style.display = 'none';
          showStatus(prescriptionFeedback, 'Profile renamed.');
        }
      }
    }
  });

  btnDeleteProfile.addEventListener('click', async () => {
    if (allProfiles.length <= 1) {
      alert('Cannot delete the only remaining profile.');
      return;
    }
    const prof = allProfiles.find(p => p.id === selectedProfileId);
    if (!confirm(`Delete profile "${prof?.name}"?`)) return;

    const res = await VisionFreeStorage.deleteProfile(selectedProfileId);
    if (res.success) {
      allProfiles = await VisionFreeStorage.getProfiles();
      activeProfileId = await VisionFreeStorage.getActiveProfileId();
      selectedProfileId = activeProfileId;
      renderProfileSelector();
      loadProfileIntoUI(selectedProfileId);
      await loadAssessmentHistoryTable();
    }
  });

  btnResetProfile.addEventListener('click', async () => {
    const prof = allProfiles.find(p => p.id === selectedProfileId);
    if (!confirm(`Reset "${prof?.name}" to defaults?`)) return;

    if (prof) {
      prof.prescription = { rightEye: { sph: '', cyl: '', axis: '' }, leftEye: { sph: '', cyl: '', axis: '' } };
      prof.preferences = { lineSpacing: '1.6', letterSpacing: '0.02em', fontWeightDelta: '0', highContrastText: false };
      await VisionFreeStorage.saveProfile(prof);
      loadProfileIntoUI(selectedProfileId);
      showStatus(prescriptionFeedback, 'Reset to defaults.');
    }
  });

  prescriptionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ok = validateField(odSph, 'od-sph-error', VisionFreeProfiles.validateSphere) &&
               validateField(odCyl, 'od-cyl-error', VisionFreeProfiles.validateCylinder) &&
               validateField(odAxis, 'od-axis-error', VisionFreeProfiles.validateAxis, odCyl.value) &&
               validateField(osSph, 'os-sph-error', VisionFreeProfiles.validateSphere) &&
               validateField(osCyl, 'os-cyl-error', VisionFreeProfiles.validateCylinder) &&
               validateField(osAxis, 'os-axis-error', VisionFreeProfiles.validateAxis, osCyl.value);

    if (!ok) {
      showStatus(prescriptionFeedback, 'Please fix errors before saving.', true);
      return;
    }

    const current = allProfiles.find(p => p.id === selectedProfileId);
    if (!current) return;

    current.prescription = {
      rightEye: { sph: odSph.value.trim(), cyl: odCyl.value.trim(), axis: odAxis.value.trim() },
      leftEye: { sph: osSph.value.trim(), cyl: osCyl.value.trim(), axis: osAxis.value.trim() }
    };

    const res = await VisionFreeStorage.saveProfile(current);
    if (res.success) {
      showStatus(prescriptionFeedback, 'Prescription saved.');
    }
  });

  presetSelect.addEventListener('change', () => {
    const key = presetSelect.value;
    if (key === 'custom') return;
    const p = VisionFreeProfiles.PRESETS[key];
    if (p) {
      lineSpacingSelect.value = p.lineSpacing;
      letterSpacingSelect.value = p.letterSpacing;
      fontWeightSelect.value = String(p.fontWeightDelta);
      highContrastCheckbox.checked = p.highContrastText;
      updateLivePreview();
    }
  });

  [lineSpacingSelect, letterSpacingSelect, fontWeightSelect].forEach(sel => {
    sel.addEventListener('change', () => {
      detectMatchingPreset({
        lineSpacing: lineSpacingSelect.value,
        letterSpacing: letterSpacingSelect.value,
        fontWeightDelta: fontWeightSelect.value,
        highContrastText: highContrastCheckbox.checked
      });
      updateLivePreview();
    });
  });

  highContrastCheckbox.addEventListener('change', () => {
    detectMatchingPreset({
      lineSpacing: lineSpacingSelect.value,
      letterSpacing: letterSpacingSelect.value,
      fontWeightDelta: fontWeightSelect.value,
      highContrastText: highContrastCheckbox.checked
    });
    updateLivePreview();
  });

  preferencesForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const current = allProfiles.find(p => p.id === selectedProfileId);
    if (!current) return;

    current.preferences = {
      lineSpacing: lineSpacingSelect.value,
      letterSpacing: letterSpacingSelect.value,
      fontWeightDelta: fontWeightSelect.value,
      highContrastText: highContrastCheckbox.checked
    };

    const res = await VisionFreeStorage.saveProfile(current);
    if (res.success) {
      showStatus(preferencesFeedback, 'Preferences saved.');
    }
  });

  // =========================================================================
  // 3. DISPLAY CALIBRATION & STALE MONITORING (Phase 4A & 4B)
  // =========================================================================
  function loadHardwareDisplaySpecs() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const dpr = window.devicePixelRatio || 1;
    const sw = window.screen.width;
    const sh = window.screen.height;

    specViewport.textContent = `${w} × ${h} px`;
    specDpr.textContent = `${dpr.toFixed(2)}x`;
    specScreen.textContent = `${sw} × ${sh} px`;
  }

  window.addEventListener('resize', () => {
    loadHardwareDisplaySpecs();
    checkCalibrationStatusFreshness();
  });

  function updateRulerBarDisplay(px) {
    rulerBar.style.width = `${px}px`;
    const pxPerMm = VisionFreeAssessment.calculatePxPerMm(px, 100);
    calSliderDisplay.textContent = `${px} px (${pxPerMm} px/mm)`;
    specPxMm.textContent = `${pxPerMm} px/mm`;
  }

  calSlider.addEventListener('input', () => {
    const px = parseInt(calSlider.value, 10);
    updateRulerBarDisplay(px);
  });

  function checkCalibrationStatusFreshness() {
    if (!currentCalibration.isCalibrated) {
      calStatusBadge.className = 'badge badge-uncalibrated';
      calStatusBadge.textContent = 'Uncalibrated Mode';
      calStaleWarning.style.display = 'none';
      return;
    }

    const freshness = VisionFreeAssessment.checkCalibrationFreshness(currentCalibration);
    if (freshness.isStale) {
      calStatusBadge.className = 'badge badge-uncalibrated';
      calStatusBadge.textContent = 'Calibration Stale (Zoom Changed)';
      calStaleReason.textContent = freshness.reason || 'Display scaling or browser zoom has changed.';
      calStaleWarning.style.display = 'block';
    } else {
      calStatusBadge.className = 'badge badge-calibrated';
      calStatusBadge.textContent = `Calibrated (${currentCalibration.pxPerMm} px/mm)`;
      calStaleWarning.style.display = 'none';
    }
  }

  async function loadCalibrationIntoUI() {
    try {
      const assessmentData = await VisionFreeStorage.getAssessment(selectedProfileId);
      const cal = assessmentData.calibration || {};

      currentCalibration = {
        isCalibrated: Boolean(cal.isCalibrated),
        pxPerMm: cal.pxPerMm || 3.78,
        sliderPx: cal.sliderPx || 378,
        targetMm: 100,
        viewingDistanceCm: cal.viewingDistanceCm || 50,
        calibratedScreenWidth: cal.calibratedScreenWidth || (window.screen ? window.screen.width : 1920),
        calibratedScreenHeight: cal.calibratedScreenHeight || (window.screen ? window.screen.height : 1080),
        calibratedDpr: cal.calibratedDpr || (window.devicePixelRatio || 1)
      };

      calSlider.value = currentCalibration.sliderPx;
      viewingDistanceInput.value = currentCalibration.viewingDistanceCm;
      updateRulerBarDisplay(currentCalibration.sliderPx);

      checkCalibrationStatusFreshness();
    } catch (err) {
      console.warn('[VISIONFREE Calibration] Error loading calibration:', err);
    }
  }

  btnSaveCalibration.addEventListener('click', async () => {
    const sliderPx = parseInt(calSlider.value, 10);
    const viewingDist = parseFloat(viewingDistanceInput.value) || 50;
    const pxPerMm = VisionFreeAssessment.calculatePxPerMm(sliderPx, 100);

    const calibrationPayload = {
      isCalibrated: true,
      pxPerMm,
      sliderPx,
      targetMm: 100,
      viewingDistanceCm: viewingDist,
      calibratedScreenWidth: window.screen ? window.screen.width : 1920,
      calibratedScreenHeight: window.screen ? window.screen.height : 1080,
      calibratedDpr: window.devicePixelRatio || 1,
      calibratedAt: Date.now()
    };

    currentCalibration = { ...calibrationPayload };
    await VisionFreeStorage.saveAssessment(selectedProfileId, { calibration: calibrationPayload });

    checkCalibrationStatusFreshness();
    showStatus(calFeedback, 'Calibration saved successfully.');
    await loadAssessmentHistoryTable();
  });

  btnResetCalibration.addEventListener('click', async () => {
    calSlider.value = 378;
    viewingDistanceInput.value = 50;
    updateRulerBarDisplay(378);

    const calibrationPayload = {
      isCalibrated: false,
      pxPerMm: 3.78,
      sliderPx: 378,
      targetMm: 100,
      viewingDistanceCm: 50,
      calibratedScreenWidth: window.screen ? window.screen.width : 1920,
      calibratedScreenHeight: window.screen ? window.screen.height : 1080,
      calibratedDpr: window.devicePixelRatio || 1,
      calibratedAt: null
    };

    currentCalibration = { ...calibrationPayload };
    await VisionFreeStorage.saveAssessment(selectedProfileId, { calibration: calibrationPayload });

    checkCalibrationStatusFreshness();
    showStatus(calFeedback, 'Calibration reset to defaults.');
    await loadAssessmentHistoryTable();
  });

  // =========================================================================
  // 4. MULTI-TRIAL VISUAL ACUITY TASK (Experimental 5x5 Tumbling E - 5:5:1 Proportions)
  // =========================================================================
  function renderAcuityTrial() {
    if (acuityState !== 'running') return;

    const angleLevels = VisionFreeAssessment.ANGLE_LEVELS;
    const currentAngle = angleLevels[acuityLevelIdx] || 5.0;

    let pxSize = 32;
    if (currentCalibration.isCalibrated) {
      pxSize = VisionFreeAssessment.getOptotypePixelSize(
        currentAngle,
        currentCalibration.pxPerMm,
        currentCalibration.viewingDistanceCm
      );
    } else {
      pxSize = Math.max(12, Math.round(currentAngle * 2.2));
    }

    // Randomize orientation avoiding immediate repetition
    currentAcuityDirection = VisionFreeAssessment.getRandomDirection(currentAcuityDirection?.id);

    // Experimental 5x5 Tumbling E SVG rendering with 5:5:1 proportions
    acuityOptotypeWrapper.innerHTML = VisionFreeAssessment.generateTumblingESVG(pxSize, currentAcuityDirection.angle, '#000000');
    acuityPausedOverlay.style.display = 'none';

    // Update Progress UI
    acuityLevelIndicator.textContent = `Level ${acuityLevelIdx + 1} of ${angleLevels.length} (~${currentAngle} arcmin)`;
    acuityTrialIndicator.textContent = `Trial ${acuityTrialInLevel + 1} of ${VisionFreeAssessment.ACUITY_TRIALS_PER_LEVEL} (Level Correct: ${acuityLevelCorrect})`;
    acuityScoreIndicator.textContent = `Total: ${acuityTotalTrials} | Total Correct: ${acuityTotalCorrect}`;
    acuityStatusMsg.textContent = 'Indicate direction: Keyboard arrows or buttons below';
  }

  function handleAcuityAnswer(chosenDirId) {
    if (acuityState !== 'running' || !currentAcuityDirection) return;

    acuityTotalTrials++;
    acuityTrialInLevel++;

    const isCorrect = (chosenDirId === currentAcuityDirection.id);
    if (isCorrect) {
      acuityLevelCorrect++;
      acuityTotalCorrect++;
    }

    // Check if current 5-trial batch is completed
    if (acuityTrialInLevel >= VisionFreeAssessment.ACUITY_TRIALS_PER_LEVEL) {
      const currentAngle = VisionFreeAssessment.ANGLE_LEVELS[acuityLevelIdx];
      const levelAcc = (acuityLevelCorrect / VisionFreeAssessment.ACUITY_TRIALS_PER_LEVEL) * 100;
      const passed = (acuityLevelCorrect >= VisionFreeAssessment.ACUITY_PASS_THRESHOLD_COUNT);

      acuityPerLevelResults.push({
        levelIndex: acuityLevelIdx + 1,
        arcmin: currentAngle,
        trials: VisionFreeAssessment.ACUITY_TRIALS_PER_LEVEL,
        correct: acuityLevelCorrect,
        accuracyPercent: levelAcc,
        passed
      });

      if (passed) {
        smallestAcuityPassedArcmin = currentAngle;
        thresholdAccuracyStr = `${acuityLevelCorrect}/${VisionFreeAssessment.ACUITY_TRIALS_PER_LEVEL} (${levelAcc.toFixed(0)}%)`;

        // Advance to next size level if available
        if (acuityLevelIdx < VisionFreeAssessment.ANGLE_LEVELS.length - 1) {
          acuityLevelIdx++;
          acuityTrialInLevel = 0;
          acuityLevelCorrect = 0;
          briefStageBlank(acuityOptotypeWrapper, () => renderAcuityTrial());
          return;
        } else {
          // Completed all levels!
          finishAcuityTask();
          return;
        }
      } else {
        // Failed threshold criterion (< 4 of 5 correct)
        finishAcuityTask();
        return;
      }
    }

    // Next trial in same level
    briefStageBlank(acuityOptotypeWrapper, () => renderAcuityTrial());
  }

  function briefStageBlank(wrapperEl, nextFn) {
    wrapperEl.style.opacity = '0';
    setTimeout(() => {
      wrapperEl.style.opacity = '1';
      nextFn();
    }, 120);
  }

  async function finishAcuityTask() {
    acuityState = 'idle';
    setAcuityControlsState('finished');
    acuityStatusMsg.textContent = 'Visual task complete! Result saved.';

    const totalAdministeredTrials = acuityPerLevelResults.reduce((sum, r) => sum + r.trials, 0);
    const totalCorrectAnswers = acuityPerLevelResults.reduce((sum, r) => sum + r.correct, 0);
    const overallAcc = totalAdministeredTrials > 0
      ? ((totalCorrectAnswers / totalAdministeredTrials) * 100).toFixed(2)
      : '0.00';
    const thresholdDisplay = smallestAcuityPassedArcmin !== null ? `${smallestAcuityPassedArcmin} arcmin` : 'Threshold > 30 arcmin (Inconclusive)';

    resAcuityEye.textContent = acuityEye === 'rightEye' ? 'Right Eye (OD)' : 'Left Eye (OS)';
    resAcuityThreshold.textContent = thresholdDisplay;
    resAcuityThreshAcc.textContent = thresholdAccuracyStr;
    resAcuityOverallAcc.textContent = `${overallAcc}% (${totalCorrectAnswers}/${totalAdministeredTrials})`;
    resAcuityCal.textContent = currentCalibration.isCalibrated ? 'Calibrated Display' : 'Uncalibrated Display';

    // Populate Breakdown list
    resAcuityBreakdown.innerHTML = '';
    acuityPerLevelResults.forEach(r => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span>Level ${r.levelIndex} (${r.arcmin} arcmin): ${r.correct}/${r.trials} correct (${r.accuracyPercent.toFixed(0)}%)</span>
        <strong style="color: ${r.passed ? '#16a34a' : '#dc2626'};">${r.passed ? 'PASSED' : 'FAILED'}</strong>
      `;
      resAcuityBreakdown.appendChild(li);
    });

    acuityResultCard.style.display = 'block';

    // Save record into storage
    const record = {
      completed: true,
      smallestSizeArcmin: smallestAcuityPassedArcmin,
      thresholdAccuracy: thresholdAccuracyStr,
      totalQuestions: totalAdministeredTrials,
      correctAnswers: totalCorrectAnswers,
      accuracyPercent: parseFloat(overallAcc),
      perLevelResults: acuityPerLevelResults,
      calibrated: currentCalibration.isCalibrated,
      timestamp: Date.now()
    };

    const currentAss = await VisionFreeStorage.getAssessment(selectedProfileId);
    const visualAcuity = currentAss.visualAcuity || {};
    visualAcuity[acuityEye] = record;

    await VisionFreeStorage.saveAssessment(selectedProfileId, { visualAcuity });
    await loadAssessmentHistoryTable();
  }

  function setAcuityControlsState(state) {
    if (state === 'running') {
      btnStartAcuity.style.display = 'none';
      btnPauseAcuity.style.display = 'inline-block';
      btnResumeAcuity.style.display = 'none';
      btnRestartAcuity.style.display = 'inline-block';
      btnCancelAcuity.style.display = 'inline-block';
    } else if (state === 'paused') {
      btnStartAcuity.style.display = 'none';
      btnPauseAcuity.style.display = 'none';
      btnResumeAcuity.style.display = 'inline-block';
      btnRestartAcuity.style.display = 'inline-block';
      btnCancelAcuity.style.display = 'inline-block';
    } else { // 'idle' or 'finished'
      btnStartAcuity.style.display = 'inline-block';
      btnPauseAcuity.style.display = 'none';
      btnResumeAcuity.style.display = 'none';
      btnRestartAcuity.style.display = 'none';
      btnCancelAcuity.style.display = 'none';
    }
  }

  btnStartAcuity.addEventListener('click', () => {
    const selectedEyeRadio = document.querySelector('input[name="acuity-eye"]:checked');
    acuityEye = selectedEyeRadio ? selectedEyeRadio.value : 'rightEye';

    acuityState = 'running';
    acuityLevelIdx = 0;
    acuityTrialInLevel = 0;
    acuityLevelCorrect = 0;
    acuityTotalTrials = 0;
    acuityTotalCorrect = 0;
    acuityPerLevelResults = [];
    smallestAcuityPassedArcmin = null;
    thresholdAccuracyStr = '--';

    acuityResultCard.style.display = 'none';
    setAcuityControlsState('running');
    renderAcuityTrial();
  });

  btnPauseAcuity.addEventListener('click', () => {
    if (acuityState !== 'running') return;
    acuityState = 'paused';
    setAcuityControlsState('paused');
    acuityPausedOverlay.style.display = 'flex';
    acuityStatusMsg.textContent = 'Visual task paused.';
  });

  btnResumeAcuity.addEventListener('click', () => {
    if (acuityState !== 'paused') return;
    acuityState = 'running';
    setAcuityControlsState('running');
    acuityPausedOverlay.style.display = 'none';
    renderAcuityTrial();
  });

  btnRestartAcuity.addEventListener('click', () => {
    if (!confirm('Restart visual task from Level 1?')) return;
    btnStartAcuity.click();
  });

  btnCancelAcuity.addEventListener('click', () => {
    acuityState = 'idle';
    setAcuityControlsState('idle');
    acuityPausedOverlay.style.display = 'none';
    acuityStatusMsg.textContent = 'Visual task cancelled.';
  });

  btnDirAll.forEach(btn => {
    btn.addEventListener('click', () => {
      handleAcuityAnswer(btn.dataset.dir);
    });
  });

  window.addEventListener('keydown', (e) => {
    if (acuityState !== 'running') return;
    const keyMap = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right' };
    if (keyMap[e.key]) {
      e.preventDefault();
      handleAcuityAnswer(keyMap[e.key]);
    }
  });

  // =========================================================================
  // 5. MULTI-TRIAL RELATIVE CONTRAST ASSESSMENT
  // =========================================================================
  function renderContrastTrial() {
    if (contrastState !== 'running') return;

    const contrastLevels = VisionFreeAssessment.CONTRAST_LEVELS;
    const currentContrast = contrastLevels[contrastLevelIdx] || 100;

    currentContrastDirection = VisionFreeAssessment.getRandomDirection(currentContrastDirection?.id);

    contrastOptotypeWrapper.innerHTML = VisionFreeAssessment.generateTumblingESVG(
      54,
      currentContrastDirection.angle,
      VisionFreeAssessment.getContrastColor(currentContrast)
    );
    contrastPausedOverlay.style.display = 'none';

    contrastLevelIndicator.textContent = `Contrast Tier ${contrastLevelIdx + 1} of ${contrastLevels.length} (${currentContrast}%)`;
    contrastTrialIndicator.textContent = `Trial ${contrastTrialInLevel + 1} of ${VisionFreeAssessment.CONTRAST_TRIALS_PER_LEVEL} (Correct: ${contrastLevelCorrect})`;
    contrastScoreIndicator.textContent = `Total: ${contrastTotalTrials} | Correct: ${contrastTotalCorrect}`;
    contrastStatusMsg.textContent = 'Indicate orientation of the symbol';
  }

  function handleContrastAnswer(dirId) {
    if (contrastState !== 'running' || !currentContrastDirection) return;

    contrastTotalTrials++;
    contrastTrialInLevel++;

    const isCorrect = (dirId === currentContrastDirection.id);
    if (isCorrect) {
      contrastLevelCorrect++;
      contrastTotalCorrect++;
    }

    // Check if batch of 4 trials is completed
    if (contrastTrialInLevel >= VisionFreeAssessment.CONTRAST_TRIALS_PER_LEVEL) {
      const currentContrast = VisionFreeAssessment.CONTRAST_LEVELS[contrastLevelIdx];
      const tierAcc = (contrastLevelCorrect / VisionFreeAssessment.CONTRAST_TRIALS_PER_LEVEL) * 100;
      const passed = (contrastLevelCorrect >= VisionFreeAssessment.CONTRAST_PASS_THRESHOLD_COUNT);

      contrastPerLevelResults.push({
        levelIndex: contrastLevelIdx + 1,
        contrastPercent: currentContrast,
        trials: VisionFreeAssessment.CONTRAST_TRIALS_PER_LEVEL,
        correct: contrastLevelCorrect,
        accuracyPercent: tierAcc,
        passed
      });

      if (passed) {
        lowestContrastPassed = currentContrast;
        contrastThresholdAccuracyStr = `${contrastLevelCorrect}/${VisionFreeAssessment.CONTRAST_TRIALS_PER_LEVEL} (${tierAcc.toFixed(0)}%)`;

        if (contrastLevelIdx < VisionFreeAssessment.CONTRAST_LEVELS.length - 1) {
          contrastLevelIdx++;
          contrastTrialInLevel = 0;
          contrastLevelCorrect = 0;
          briefStageBlank(contrastOptotypeWrapper, () => renderContrastTrial());
          return;
        } else {
          finishContrastTask();
          return;
        }
      } else {
        finishContrastTask();
        return;
      }
    }

    briefStageBlank(contrastOptotypeWrapper, () => renderContrastTrial());
  }

  async function finishContrastTask() {
    contrastState = 'idle';
    setContrastControlsState('finished');
    contrastStatusMsg.textContent = 'Contrast task complete!';

    const totalAdministeredTrials = contrastPerLevelResults.reduce((sum, r) => sum + r.trials, 0);
    const totalCorrectAnswers = contrastPerLevelResults.reduce((sum, r) => sum + r.correct, 0);
    const overallAcc = totalAdministeredTrials > 0
      ? ((totalCorrectAnswers / totalAdministeredTrials) * 100).toFixed(2)
      : '0.00';

    const threshDisplay = lowestContrastPassed !== null ? `${lowestContrastPassed}% Contrast` : 'Threshold > 100%';
    resContrastThresh.textContent = threshDisplay;
    resContrastThreshAcc.textContent = contrastThresholdAccuracyStr;
    resContrastLevels.textContent = `${contrastPerLevelResults.length} Tiers Evaluated`;

    resContrastBreakdown.innerHTML = '';
    contrastPerLevelResults.forEach(r => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span>Tier ${r.levelIndex} (${r.contrastPercent}% contrast): ${r.correct}/${r.trials} correct (${r.accuracyPercent.toFixed(0)}%)</span>
        <strong style="color: ${r.passed ? '#16a34a' : '#dc2626'};">${r.passed ? 'PASSED' : 'FAILED'}</strong>
      `;
      resContrastBreakdown.appendChild(li);
    });

    contrastResultCard.style.display = 'block';

    const record = {
      completed: true,
      thresholdPercent: lowestContrastPassed,
      thresholdAccuracy: contrastThresholdAccuracyStr,
      totalLevelsTested: contrastPerLevelResults.length,
      totalQuestions: totalAdministeredTrials,
      correctAnswers: totalCorrectAnswers,
      accuracyPercent: parseFloat(overallAcc),
      perLevelResults: contrastPerLevelResults,
      calibrated: currentCalibration.isCalibrated,
      timestamp: Date.now()
    };

    await VisionFreeStorage.saveAssessment(selectedProfileId, { contrast: record });
    await loadAssessmentHistoryTable();
  }

  function setContrastControlsState(state) {
    if (state === 'running') {
      btnStartContrast.style.display = 'none';
      btnPauseContrast.style.display = 'inline-block';
      btnResumeContrast.style.display = 'none';
      btnRestartContrast.style.display = 'inline-block';
      btnCancelContrast.style.display = 'inline-block';
    } else if (state === 'paused') {
      btnStartContrast.style.display = 'none';
      btnPauseContrast.style.display = 'none';
      btnResumeContrast.style.display = 'inline-block';
      btnRestartContrast.style.display = 'inline-block';
      btnCancelContrast.style.display = 'inline-block';
    } else {
      btnStartContrast.style.display = 'inline-block';
      btnPauseContrast.style.display = 'none';
      btnResumeContrast.style.display = 'none';
      btnRestartContrast.style.display = 'none';
      btnCancelContrast.style.display = 'none';
    }
  }

  btnStartContrast.addEventListener('click', () => {
    contrastState = 'running';
    contrastLevelIdx = 0;
    contrastTrialInLevel = 0;
    contrastLevelCorrect = 0;
    contrastTotalTrials = 0;
    contrastTotalCorrect = 0;
    contrastPerLevelResults = [];
    lowestContrastPassed = null;
    contrastThresholdAccuracyStr = '--';

    contrastResultCard.style.display = 'none';
    setContrastControlsState('running');
    renderContrastTrial();
  });

  btnPauseContrast.addEventListener('click', () => {
    if (contrastState !== 'running') return;
    contrastState = 'paused';
    setContrastControlsState('paused');
    contrastPausedOverlay.style.display = 'flex';
    contrastStatusMsg.textContent = 'Contrast task paused.';
  });

  btnResumeContrast.addEventListener('click', () => {
    if (contrastState !== 'paused') return;
    contrastState = 'running';
    setContrastControlsState('running');
    contrastPausedOverlay.style.display = 'none';
    renderContrastTrial();
  });

  btnRestartContrast.addEventListener('click', () => {
    if (!confirm('Restart contrast task from Tier 1?')) return;
    btnStartContrast.click();
  });

  btnCancelContrast.addEventListener('click', () => {
    contrastState = 'idle';
    setContrastControlsState('idle');
    contrastPausedOverlay.style.display = 'none';
    contrastStatusMsg.textContent = 'Contrast task cancelled.';
  });

  btnDirContrastAll.forEach(btn => {
    btn.addEventListener('click', () => {
      handleContrastAnswer(btn.dataset.dir);
    });
  });

  // =========================================================================
  // 6. READING PERFORMANCE & 4-QUESTION COMPREHENSION
  // =========================================================================
  btnStartReading.addEventListener('click', () => {
    isReadingRunning = true;
    readingStartTime = performance.now();
    readingElapsedSeconds = 0;

    readingPassageCard.classList.remove('blurred');
    btnStartReading.disabled = true;
    btnFinishReading.disabled = false;
    readingComprehensionBox.style.display = 'none';
    readingResultCard.style.display = 'none';

    readingTimerInterval = setInterval(() => {
      const now = performance.now();
      readingElapsedSeconds = (now - readingStartTime) / 1000;
      readingTimerDisplay.textContent = `${readingElapsedSeconds.toFixed(1)} s`;
    }, 100);
  });

  btnFinishReading.addEventListener('click', () => {
    if (!isReadingRunning) return;
    isReadingRunning = false;
    clearInterval(readingTimerInterval);

    readingPassageCard.classList.add('blurred');
    btnStartReading.disabled = false;
    btnFinishReading.disabled = true;

    // Show Comprehension Questions
    readingComprehensionBox.style.display = 'block';
    compErrorMsg.textContent = '';
  });

  btnRatingAll.forEach(btn => {
    btn.addEventListener('click', () => {
      btnRatingAll.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      readingComfortRating = parseInt(btn.dataset.rating, 10);
    });
  });

  comprehensionForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const questions = VisionFreeAssessment.STANDARD_READING_PASSAGE.questions;
    let answeredAll = true;
    let correctCount = 0;
    const answersRecord = [];

    for (const q of questions) {
      const selected = document.querySelector(`input[name="comp-${q.id}"]:checked`);
      if (!selected) {
        answeredAll = false;
        break;
      }
      const isRight = (selected.value === q.correctId);
      if (isRight) correctCount++;
      answersRecord.push({
        questionId: q.id,
        selectedAnswer: selected.value,
        correctAnswer: q.correctId,
        isCorrect: isRight
      });
    }

    if (!answeredAll) {
      compErrorMsg.textContent = 'Please answer all 4 comprehension questions.';
      return;
    }

    compErrorMsg.textContent = '';
    const wordCount = VisionFreeAssessment.STANDARD_READING_PASSAGE.wordCount;
    const wpm = VisionFreeAssessment.calculateWPM(wordCount, readingElapsedSeconds);
    const compAcc = ((correctCount / questions.length) * 100).toFixed(0);

    resReadingWpm.textContent = `${wpm} WPM`;
    resReadingTime.textContent = `${readingElapsedSeconds.toFixed(1)} s`;
    resReadingComp.textContent = `${correctCount}/${questions.length} Correct (${compAcc}%)`;
    resReadingComfort.textContent = `${readingComfortRating} / 5`;

    readingComprehensionBox.style.display = 'none';
    readingResultCard.style.display = 'block';

    const record = {
      completed: true,
      wpm,
      readingTimeSeconds: parseFloat(readingElapsedSeconds.toFixed(1)),
      wordCount,
      comfortRating: readingComfortRating,
      comprehensionQuestionsTotal: questions.length,
      comprehensionCorrect: correctCount,
      comprehensionAccuracyPercent: parseFloat(compAcc),
      comprehensionAnswers: answersRecord,
      timestamp: Date.now()
    };

    await VisionFreeStorage.saveAssessment(selectedProfileId, { reading: record });
    await loadAssessmentHistoryTable();
  });

  // =========================================================================
  // 7. ASSESSMENT HISTORY TABLE & CLEAR
  // =========================================================================
  async function loadAssessmentHistoryTable() {
    try {
      const assessmentData = await VisionFreeStorage.getAssessment(selectedProfileId);
      const tbody = assessmentHistoryBody;
      tbody.innerHTML = '';

      const rows = [];

      // Calibration record
      const cal = assessmentData.calibration;
      if (cal && cal.isCalibrated) {
        const fresh = VisionFreeAssessment.checkCalibrationFreshness(cal);
        rows.push({
          type: 'Display Calibration',
          metric: `${cal.pxPerMm} px/mm (Dist: ${cal.viewingDistanceCm} cm)`,
          condition: fresh.isStale ? 'Stale (Zoom Changed)' : 'Calibrated Display',
          conditionBadge: fresh.isStale ? 'badge-uncalibrated' : 'badge-calibrated',
          date: new Date(cal.calibratedAt || Date.now()).toLocaleDateString()
        });
      }

      // Visual Tasks
      const va = assessmentData.visualAcuity || {};
      if (va.rightEye) {
        const thresh = va.rightEye.smallestSizeArcmin ? `${va.rightEye.smallestSizeArcmin} arcmin` : 'Inconclusive';
        rows.push({
          type: 'Right Eye Visual Task (OD)',
          metric: `Threshold: ${thresh} (${va.rightEye.thresholdAccuracy || 'Pass'}, Overall: ${va.rightEye.accuracyPercent}% acc)`,
          condition: va.rightEye.calibrated ? 'Calibrated' : 'Uncalibrated',
          conditionBadge: va.rightEye.calibrated ? 'badge-calibrated' : 'badge-neutral',
          date: new Date(va.rightEye.timestamp).toLocaleDateString()
        });
      }
      if (va.leftEye) {
        const thresh = va.leftEye.smallestSizeArcmin ? `${va.leftEye.smallestSizeArcmin} arcmin` : 'Inconclusive';
        rows.push({
          type: 'Left Eye Visual Task (OS)',
          metric: `Threshold: ${thresh} (${va.leftEye.thresholdAccuracy || 'Pass'}, Overall: ${va.leftEye.accuracyPercent}% acc)`,
          condition: va.leftEye.calibrated ? 'Calibrated' : 'Uncalibrated',
          conditionBadge: va.leftEye.calibrated ? 'badge-calibrated' : 'badge-neutral',
          date: new Date(va.leftEye.timestamp).toLocaleDateString()
        });
      }

      // Contrast Task
      if (assessmentData.contrast) {
        const cThresh = assessmentData.contrast.thresholdPercent !== null ? `${assessmentData.contrast.thresholdPercent}%` : 'Inconclusive';
        rows.push({
          type: 'Relative Contrast Task',
          metric: `Threshold: ${cThresh} (${assessmentData.contrast.thresholdAccuracy || 'Pass'}, ${assessmentData.contrast.totalLevelsTested} tiers tested)`,
          condition: assessmentData.contrast.calibrated ? 'Calibrated' : 'Uncalibrated',
          conditionBadge: assessmentData.contrast.calibrated ? 'badge-calibrated' : 'badge-neutral',
          date: new Date(assessmentData.contrast.timestamp).toLocaleDateString()
        });
      }

      // Reading Performance
      if (assessmentData.reading) {
        const compStr = assessmentData.reading.comprehensionAccuracyPercent !== undefined
          ? `Comp: ${assessmentData.reading.comprehensionCorrect}/${assessmentData.reading.comprehensionQuestionsTotal} (${assessmentData.reading.comprehensionAccuracyPercent}%)`
          : 'Comp: N/A';
        rows.push({
          type: 'Reading Performance',
          metric: `${assessmentData.reading.wpm} WPM (${assessmentData.reading.readingTimeSeconds}s | ${compStr} | Comfort: ${assessmentData.reading.comfortRating}/5)`,
          condition: 'Standard Typography',
          conditionBadge: 'badge-neutral',
          date: new Date(assessmentData.reading.timestamp).toLocaleDateString()
        });
      }

      if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-table-msg">No assessment records saved yet for this profile.</td></tr>';
        return;
      }

      rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${r.type}</strong></td>
          <td>${r.metric}</td>
          <td><span class="badge ${r.conditionBadge}">${r.condition}</span></td>
          <td>${r.date}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.warn('[VISIONFREE Options] Error loading assessment table:', err);
    }
  }

  btnClearAssessments.addEventListener('click', async () => {
    const prof = allProfiles.find(p => p.id === selectedProfileId);
    if (!confirm(`Clear all assessment records for "${prof?.name}"?`)) return;

    await VisionFreeStorage.clearAssessment(selectedProfileId);
    await loadCalibrationIntoUI();
    await loadAssessmentHistoryTable();
    acuityResultCard.style.display = 'none';
    contrastResultCard.style.display = 'none';
    readingResultCard.style.display = 'none';
  });

  // Launch workspace
  await initializeWorkspace();
});

# VISIONFREE

**Computational Digital Content Adaptation Prototype for Personalized Reading Comfort**

> **Phase 4 Release (v0.4.0)** — Vision Assessment & Display Calibration System

---

## 1. Project Introduction

VISIONFREE is an exploratory Chrome extension designed to investigate how digital webpage content can be computationally preprocessed to match an individual's visual reading comfort.

### Core Operating Philosophy:
- **Direct in-page modification:** Operates directly on the host webpage's DOM and styles.
- **Zero screen capture:** Uses no screenshots, screen recording, external windows, or canvas mirrors.
- **Full interactivity:** Original links, buttons, form inputs, scrolling, and text selection remain completely functional and responsive.
- **Non-destructive:** Activating VISIONFREE applies subtle, reversible typographic adaptation; disabling it restores the host webpage to its pristine, original state with zero residual changes.
- **Strict Privacy Isolation:** Clinical spectacles prescription values (SPH, CYL, Axis) remain within trusted extension storage contexts and are **never** injected into the webpage DOM or altered by assessment tasks.
- **Display Calibration & Visual Tasks (Phase 4):** Provides physical display scaling calibration, visual-angle-based Tumbling E acuity tasks, relative contrast assessment, and standardized reading performance evaluation.
- **Important Scientific Disclaimer:** VISIONFREE is a digital content-adaptation prototype. Assessment features are screen-based experimental observations designed to support future display research. They do **not** diagnose eyesight, measure clinical visual acuity, or replace prescribed spectacles.

---

## 2. Phase 4 Objectives & Features Implemented

Phase 4 introduces a dedicated **Vision Assessment & Display Calibration System** inside the full-page Options interface:

1. **Interactive Display Calibration:**
   - **Physical Ruler Calibration:** Displays a horizontal reference bar with an interactive slider. The user measures the bar against a physical metric ruler and adjusts the slider until it measures **exactly 100 millimeters (10 cm)**.
   - **Empirical Scale Derivation:** Calculates the relationship between browser CSS pixels and physical display millimeters:
     $$\text{Pixels per mm (px/mm)} = \frac{\text{Slider CSS Pixels}}{100 \text{ mm}}$$
   - **Viewing Distance Input:** Records the user's manual eye-to-screen distance (in centimeters, e.g. 50 cm).
   - **Hardware Metrology:** Gathers `window.devicePixelRatio`, viewport dimensions, and screen resolution.
2. **Experimental Visual Acuity Task (Tumbling E):**
   - **Standard Optotypes:** Displays the Tumbling E symbol in four randomized cardinal orientations: Up ($\uparrow$), Down ($\downarrow$), Left ($\leftarrow$), Right ($\rightarrow$).
   - **Visual Angle Geometry:** Calculates optotype physical height using standard ophthalmic visual angle formulas:
     $$\text{Physical Height (mm)} = 2 \times \text{Viewing Distance (mm)} \times \tan\left(\frac{\theta \text{ (arcmin)}}{2 \times 60} \times \frac{\pi}{180}\right)$$
   - **Adaptive Difficulty:** Progresses through 6 visual angle levels (from $30.0$ arcmin down to $5.0$ arcmin reference level).
   - **Monocular Protocol:** Dedicated separate testing and records for **Right Eye (OD)** and **Left Eye (OS)**.
   - **Keyboard & Button Input:** Responds to on-screen directional buttons or keyboard arrow keys (`ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`).
   - **Calibration Fallback:** Supports calibrated screen testing with an uncalibrated exploratory mode when calibration is absent.
3. **Relative Contrast Perception Assessment:**
   - Evaluates contrast perception by presenting optotypes against a neutral background across seven progressive contrast tiers ($100\%$, $50\%$, $25\%$, $12\%$, $6\%$, $3\%$, $1.5\%$).
   - Estimates the relative threshold where contrast can no longer be resolved.
   - Explicitly notes display limitations (ambient lighting, gamma, and OS display processing).
4. **Standardized Reading-Performance Assessment:**
   - Presents a standardized 96-word passage on digital typography and visual fatigue.
   - Real-time stopwatch timer measures reading duration.
   - Computes reading pace in Words Per Minute (WPM):
     $$\text{WPM} = \frac{\text{Word Count}}{\text{Time in Minutes}}$$
   - Records subjective reading comfort on a 1–5 scale.
5. **Assessment History & Results Reporting:**
   - Displays a structured table of recorded results (Display Calibration, OD/OS Acuity, Contrast, and Reading WPM) associated with the currently selected vision profile.
   - One-click clear functionality to delete assessment records.
6. **Strict Clinical Isolation:**
   - Assessment records are stored under `visionfree_assessments` in `chrome.storage.local`.
   - Prescription parameters (SPH, CYL, Axis) are strictly protected and never modified by assessment routines.

---

## 3. Project Folder Structure

```
VISIONFREE/
├── manifest.json              # Extension metadata, MV3 declarations, and permissions (v0.4.0)
├── background/
│   └── service-worker.js      # Toolbar click handler, badge controller, & live settings broadcaster
├── options/
│   ├── options.html           # Full-page workspace: Tab 1 (Profiles) & Tab 2 (Assessment Suite)
│   ├── options.css            # Styles for calibration ruler, test arenas, and reading passage
│   └── options.js             # Controller for profile management, calibration math, and task runners
├── content/
│   ├── content.js             # Webpage content script coordinator and message router
│   ├── styler.js              # Scoped CSS styling engine with element exemptions
│   └── observer.js            # MutationObserver for SPA client-side route transitions
├── core/
│   ├── assessment.js          # Calibration geometry, visual angle formulas, & reading metrics
│   ├── profiles.js            # Profile schema definition, prescription validation, and presets
│   └── storage.js             # Storage abstraction module (assessment isolation & session state)
├── assets/
│   └── icons/                 # Valid RGBA PNG icons (16, 32, 48, 128 px)
└── README.md                  # Comprehensive documentation and developer guide
```

---

## 4. Assessment Data Storage Schema (v4.0.0)

Assessment results are stored in `chrome.storage.local` under the key `visionfree_assessments`, indexed by `profileId`:

```json
{
  "visionfree_assessments": {
    "prof_l9x1z2_k89a1": {
      "profileId": "prof_l9x1z2_k89a1",
      "schemaVersion": "4.0.0",
      "updatedAt": 1700000050000,
      "calibration": {
        "isCalibrated": true,
        "pxPerMm": 3.78,
        "sliderPx": 378,
        "targetMm": 100,
        "viewingDistanceCm": 50,
        "viewportWidth": 1920,
        "viewportHeight": 1080,
        "devicePixelRatio": 2,
        "calibratedAt": 1700000000000
      },
      "visualAcuity": {
        "rightEye": {
          "completed": true,
          "smallestSizeArcmin": 7.5,
          "thresholdAccuracy": "4/5 (80%)",
          "totalQuestions": 30,
          "correctAnswers": 22,
          "accuracyPercent": 73.33,
          "perLevelResults": [
            { "levelIndex": 1, "arcmin": 30.0, "trials": 5, "correct": 5, "accuracyPercent": 100, "passed": true },
            { "levelIndex": 2, "arcmin": 20.0, "trials": 5, "correct": 5, "accuracyPercent": 100, "passed": true },
            { "levelIndex": 3, "arcmin": 15.0, "trials": 5, "correct": 4, "accuracyPercent": 80,  passed: true },
            { "levelIndex": 4, "arcmin": 10.0, "trials": 5, "correct": 4, "accuracyPercent": 80,  passed: true },
            { "levelIndex": 5, "arcmin": 7.5,  trials: 5, correct: 4, "accuracyPercent": 80,  passed: true },
            { "levelIndex": 6, "arcmin": 5.0,  trials: 5, correct: 0, "accuracyPercent": 0,   passed: false }
          ],
          "calibrated": true,
          "timestamp": 1700000020000
        },
        "leftEye": null
      },
      "contrast": {
        "completed": true,
        "thresholdPercent": 6.0,
        "thresholdAccuracy": "3/4 (75%)",
        "totalLevelsTested": 5,
        "totalQuestions": 20,
        "correctAnswers": 18,
        "accuracyPercent": 90.0,
        "calibrated": true,
        "timestamp": 1700000030000
      },
      "reading": {
        "completed": true,
        "wpm": 215,
        "readingTimeSeconds": 24.0,
        "wordCount": 86,
        "comfortRating": 4,
        "comprehensionQuestionsTotal": 4,
        "comprehensionCorrect": 4,
        "comprehensionAccuracyPercent": 100,
        "timestamp": 1700000040000
      }
    }
  }
}
```

---

## 5. Phase 4 Technical Corrections & Scientific Methodology

In accordance with rigorous psychophysical and browser-based assessment methodology, the following corrections have been implemented:

1. **Experimental 5×5 Tumbling E Optotype (5:5:1 Geometric Proportions):**
   - The visual task presents an **experimental 5×5 Tumbling E optotype with 5:5:1 geometric proportions** (5 units total height, 5 units total width, 1 unit stroke thickness, 1 unit gap height).
   - This task is an experimental screen-based visual observation. It does **not** claim clinical ISO 8596 certification, standardised clinical measurement, or professional visual-acuity diagnosis.

2. **Visual Acuity Aggregate Statistics & Scoring Rules:**
   - Evaluates **5 randomized trials per size level** (avoiding immediate orientation repeats).
   - **Operational Threshold Rule:** Requires at least **4 out of 5 correct (80%)** at a given level before advancing to smaller optotypes. Under independent, uniformly random guessing (4 choices), the theoretical per-level probability of guessing $\ge 4/5$ is $P(X \ge 4) = 1.56\%$. However, this is an operational experimental threshold rule and does not prove clinical accuracy or establish high overall statistical confidence across repeated testing blocks.
   - **Aggregate Consistency:** All administered trials across all tested levels (including the final failed level) are strictly counted in `totalQuestions` and `correctAnswers`. For example, a user completing 5 passed levels and failing the 6th level with 22 correct answers out of 30 total administered trials has an aggregate accuracy of exactly **73.33%** ($22 / 30$), while their separate identified threshold size is recorded as **7.5 arcmin**.
   - Incomplete or cancelled tasks do not generate completed-result records.

3. **sRGB Non-Linear Electro-Optical Contrast Encoding:**
   - Stimulus foreground text colors are computed using the standard non-linear sRGB electro-optical transfer function (IEC 61966-2-1), correcting previous naive linear approximations:
     - Normalized contrast: $C = \text{contrastPercentage} / 100$
     - Target foreground relative luminance: $L = 1 - C$
     - Non-linear sRGB channel:
       $$S = \begin{cases} 12.92 \times L & \text{if } L \le 0.0031308 \\ 1.055 \times L^{1/2.4} - 0.055 & \text{otherwise} \end{cases}$$
     - 8-bit channel: $\text{RGB} = \text{round}(255 \times S)$
   - Distinguishes nominal sRGB-relative-luminance contrast from physical calibrated monitor luminance. Does not claim to correct hardware monitor gamma or guarantee absolute physical candela/$\text{m}^2$ luminance.
   - **Operational Threshold Rule:** Requires at least **3 out of 4 correct (75%)** (theoretical random-guessing probability $P(X \ge 3) = 5.08\%$) to advance to lower contrast tiers.

4. **Programmatic Reading Passage Word Count:**
   - The standardized reading passage word count is computed programmatically at runtime (`countWords` $\rightarrow$ exactly **86 words**) rather than relying on an unverified hardcoded count.
   - WPM calculations directly utilize the verified 86-word count ($\text{WPM} = \text{round}(86 / (\text{seconds} / 60))$).
   - Speed (WPM), reading time, 4-question comprehension score, and subjective comfort (1–5) are stored and reported as distinct metrics.

5. **Display Calibration Reliability & Stale Detection Limitations:**
   - Physical ruler calibration establishes $\text{px}/\text{mm}$ scaling and snapshots `devicePixelRatio` (DPR) and `screen.width`/`screen.height`.
   - Browser window resizing alone on the same display does **not** invalidate calibration since physical pixel pitch remains unchanged.
   - Meaningful changes in DPR (browser zoom) or screen resolution trigger a review banner: *"Display conditions may have changed. Please verify calibration."*
   - **Limitation Notice:** Web browsers cannot detect physical monitor changes if screen resolution and DPR match. Users are advised to recalibrate manually when swapping physical monitors.

---

## 6. How to Load and Test Locally on Your Mac

### Step 1: Reload Extension
1. Open Google Chrome and navigate to `chrome://extensions`.
2. Locate the **VISIONFREE** card (version `0.4.1`).
3. Click the circular **Reload** icon on the card.

### Step 2: Open Assessment Workspace
1. Right-click the **VISIONFREE** toolbar icon $\rightarrow$ select **Options**.
2. Click the second navigation tab at the top: **Vision Assessment & Calibration**.

### Step 3: Run Display Calibration & Test Stale Detection
1. Hold a metric ruler up against your monitor.
2. Adjust the slider until the blue reference bar measures **exactly 100 mm (10 cm)**.
3. Enter your measured viewing distance (e.g., `50` cm).
4. Click **Save Display Calibration**. Notice the badge changes to green: `Calibrated (X.XX px/mm)`.
5. *Test Zoom Invalidation:* Press `Cmd + +` to zoom. Notice the advisory banner appears: *"Display conditions may have changed. Please verify calibration."* Reset zoom with `Cmd + 0`.
6. *Verify Window Resizing Behavior:* Resize the browser window width and height. Notice that calibration remains valid and does not trigger false stale warnings.

### Step 4: Run Multi-Trial Visual Acuity Task
1. Select **Right Eye (OD)** and gently cover your left eye.
2. Click **Start Visual Task**.
3. Use the arrow keys (`↑`, `↓`, `←`, `→`) or click on-screen buttons.
4. Each level tests **5 randomized trials**. Note how it requires at least 4/5 correct to advance.
5. Try clicking **Pause** and **Resume** to verify task lifecycle controls.
6. Upon completing or failing a level, review the per-level breakdown: notice that all administered trials (e.g. 30) are counted towards the aggregate accuracy (e.g. 73.33%), while the threshold is reported separately.

### Step 5: Run Multi-Trial Relative Contrast Task
1. Click **Start Contrast Task**.
2. Each tier tests **4 randomized trials** with sRGB non-linear contrast reduction.
3. Requires $\ge 3/4$ (75%) correct to advance. Review your threshold result.

### Step 6: Run Reading Performance Task & Comprehension Evaluation
1. Click **Start Reading**. The paragraph text will unblur and the live stopwatch starts.
2. Read the 86-word passage at your normal pace.
3. Click **Finished Reading**.
4. The 4-question comprehension evaluation appears. Select answers for all 4 questions.
5. Select a comfort rating (1–5) and click **Submit Comprehension & Save**.
6. Review your separate metrics: Reading Speed (WPM, calculated with 86 words), Reading Time, Comprehension Score, and Comfort Score.

### Step 7: Inspect History & Persistence
1. Scroll down to Section 4F: verify your new assessment entries appear in the records table with exact threshold accuracies.
2. Refresh the browser tab (`Cmd + R`) to confirm that records persist cleanly from `chrome.storage.local`.

---

## 7. Automated Test Suite Results

The automated test suite (`node tests/test_phase4.js`) verifies all 6 assessment domains:

```text
================================================================
🧪 VISIONFREE — Phase 4 Final Technical Corrections Test Suite
================================================================

✅ 1. Loaded core/assessment.js successfully.

--- Test 1: Experimental 5x5 Tumbling E (5:5:1 Proportions) ---
✅ Experimental 5x5 Tumbling E correctly generated with 5:5:1 geometric proportions.

--- Test 2: Visual Acuity Multi-Trial Aggregate Consistency ---
✅ Visual acuity aggregate consistency verified: 22/30 trials = 73.33% (Threshold: 7.5 arcmin).

--- Test 3: sRGB Non-Linear Electro-Optical Contrast Encoding & Decoding ---
✅ sRGB non-linear contrast encoding and round-trip decoding verified for all tiers (100%, 50%, 25%, 6%, 1.5%).

--- Test 4: Reading Passage Programmatic Word Count & WPM ---
✅ Reading passage programmatic word count verified: exactly 86 words (WPM: 30s=172, 24s=215).

--- Test 5: Calibration Stale Detection & Limitations ---
✅ Calibration stale-detection behavior and limitations verified (resizing does not invalidate; DPR/resolution does).

--- Test 6: Storage Schema Consistency & Prescription Isolation ---
✅ Storage schema consistency and prescription isolation verified.

================================================================
🎉 ALL PHASE 4 FINAL TECHNICAL CORRECTIONS TESTS PASSED!
================================================================
```

---

## 8. Features Reserved for Phase 5 and Later

The following capabilities belong strictly to future research stages:
- **Phase 5:** Experimental optical blur modeling, Point Spread Function (PSF) inverse filtering, directional SVG convolution matrices, and WebGL shader prototyping.
- **Phase 6:** Cross-platform multi-DPI parity audits, font-smoothing adaptations, and Chrome Web Store release preparation.


# Technical Design Document: NeuralAudit E-commerce Integrity System

**Role:** Technical Architect (SDE-3)
**Target:** Implementation Team (Intern & Mentor)
**Status:** Implementation Ready

---

## 1. System Overview
The **NeuralAudit** system is designed to verify the visual-to-metadata consistency of multi-variant product listings. The core challenge is "State-Syncing": ensuring that when a user (or bot) selects a specific variant, the image displayed matches the expected color category.

## 2. Architecture Diagram (Mental Model)
The system follows a linear pipeline:
1. **Scraper (Ingestion)** -> 2. **Preprocessing (Cleaning)** -> 3. **Inference (Analysis)** -> 4. **Logic Layer (Decision)** -> 5. **Database (Record)**

---

## 3. Module Breakdown & Implementation Details

### Module A: State-Aware Scraper (Selenium)
**Objective:** Capture pairs of `(Image, Color_Text)` by interacting with the UI.
* **The Logic:** You cannot just download images from the source code. You must mimic a user.
* **Implementation Steps:**
    1. Load the product URL.
    2. Identify the "Swatch Container" (the area with color dots).
    3. Loop through each `dot`:
        - `element.click()`
        - `time.sleep(1.5)` (Wait for the JS to swap the main image).
        - Get the `src` attribute of the primary image.
        - Get the `innerText` of the active color label.
* **Technical Tip:** Use `WebDriverWait` with `expected_conditions` instead of hard `time.sleep` to make it robust.

### Module B: OpenCV Preprocessing (The Focus Module)
**Objective:** Remove background noise to help the CNN focus on the product.
* **Implementation Steps:**
    1. **Resize:** Convert all images to `224x224` pixels.
    2. **Center-Crop:** E-commerce products are usually in the center. Crop the middle 60% of the image.
    3. **HSV Transformation:** Convert from BGR to HSV. This allows the system to calculate the "Dominant Hue" (0-179) as a first-pass check.
* **Formula:** `Image_Processed = CenterCrop(Resize(Original_Image))`

### Module C: CNN Auditor (PyTorch/ResNet)
**Objective:** Categorize the visual "truth" of the image.
* **Model:** Use `torchvision.models.resnet18(pretrained=True)`.
* **Modification:** Change the `fc` (fully connected) layer to output 10 classes (Red, Blue, Green, etc.).
* **The Concept:** Transfer Learning. We use a model that already knows what "shapes" are and teach it specifically about "colors."

### Module D: The Family Mapping Logic (The Decision)
**Objective:** Bridge the gap between "Midnight Navy" and "Blue".
* **Mapping Table:** Create a Python dictionary:
    ```python
    mapping = {
        "Navy": "Blue",
        "Cyan": "Blue",
        "Crimson": "Red",
        "Rose": "Red"
    }
    ```
* **Validation Rule:**
    ```python
    if CNN_Prediction == mapping.get(Metadata_Label):
        status = "Verified"
    else:
        status = "Flagged"
    ```

---

## 4. Implementation Guide for Interns

### Step 1: Environment Setup
You will need a Virtual Environment (`venv`). Install these libraries:
`pip install selenium opencv-python torch torchvision supabase fastapi`

### Step 2: Database Schema
Create a table in Supabase called `audit_results`:
- `id` (Primary Key)
- `product_url` (Text)
- `scraped_color` (Text)
- `cnn_prediction` (Text)
- `is_mismatch` (Boolean)
- `confidence_score` (Float)

### Step 3: Error Handling
E-commerce sites often change their HTML classes. Wrap your Selenium selectors in `try-except` blocks. If the "Color Dot" isn't found, log the error but don't crash the script.

---

## 5. Summary of Tasks for the Mentor
1. **Code Review:** Ensure the intern is not "hardcoding" URLs. Use a CSV of URLs as input.
2. **Model Validation:** Check the Confusion Matrix. Are we confusing "Pink" with "Red"? If so, increase the weight of the "Hue" check from OpenCV.
3. **Storage Efficiency:** Don't store the actual images in the DB; store the **URLs** to save space.

---

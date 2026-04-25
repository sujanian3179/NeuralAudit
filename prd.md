
# PRD: NeuralAudit – E-commerce Variant Integrity System (Phase 1)

**Product Manager:** [Your Name]
**Date:** 2023 (Internship Project)
**Target:** Technical Architect / Engineering Team

---

## 1. 📋 Executive Summary
**NeuralAudit** is an AI-driven quality assurance tool designed to eliminate "Content Mismatch" errors in multi-variant e-commerce listings. The system audits product pages where multiple color/style options exist to ensure that the image displayed to the customer aligns perfectly with the metadata/color name selected.

## 2. 🎯 Problem Statement
- **High Return Rates:** Mismatched variant images (e.g., clicking 'Blue' but seeing 'Pink') are the leading cause of "Item Not As Described" returns.
- **Dynamic Content:** Traditional scrapers cannot handle Javascript-heavy color swatches that change images dynamically upon clicking.
- **Naming Inconsistency:** Marketing names (e.g., "Mayan Blue") do not match standard pixel-level classification (e.g., "Light Blue").

## 3. 🚀 Functional Requirements (FR)

### FR1: State-Aware Data Retrieval
- **Mechanism:** Must use a headless browser (Selenium/Playwright) to detect and click every "Color Swatch" (dot/thumbnail) on a product page.
- **Condition:** Wait for the DOM to update the primary image before capturing the pair.
- **Output:** A synchronized dataset: `(Variant_Image_URL, Metadata_Color_Label)`.

### FR2: Image Normalization & Focus
- **OpenCV Integration:** Automated center-cropping (40% of image area) to isolate the product and discard background noise.
- **Color Space:** Convert images from RGB to **HSV** for hue-based heuristic verification.

### FR3: Deep Learning Audit (The CNN)
- **Model:** ResNet-18 (chosen for speed and efficiency in production).
- **Classification:** Categorize visual product data into 10 **Primary Color Families**.
- **Accuracy Target:** 95% on distinct color family detection.

### FR4: Family-Mapping Logic
- **Cross-Modal Logic:** The system must check if the `Metadata_Color_Label` belongs to the `CNN_Predicted_Family`.
- **Ex:** "Mayan Blue" belongs to "Blue Family". If CNN predicts "Blue", Status = `VERIFIED`. If CNN predicts "Pink", Status = `FLAGGED`.

## 4. 🏗️ Technical Architecture
- **Infrastructure:**
    - **Scraper:** Python + Selenium.
    - **Database:** Supabase (PostgreSQL) for audit trails.
    - **Inference:** FastAPI + PyTorch/TensorFlow.
- **Hosting:** Hugging Face Spaces (CPU/GPU) for no-cost deployment.

## 5. 📉 Success Metrics (KPIs)
- **Detection Rate:** Identify at least 90% of manual "Sync Errors" inserted during testing.
- **Processing Time:** Full audit of a 10-variant SKU in < 45 seconds.
- **Scalability:** System must handle multiple concurrent scrapes without IP blocking.

## 6. 🛠️ Future Improvements (Phase 2)
- Transition from CNN to **Vision Transformers (ViT)** for better texture and material detection.
- Implement **Natural Language Processing (NLP)** to audit more complex description fields.

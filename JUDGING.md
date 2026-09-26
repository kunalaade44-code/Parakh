# ⚖️ Judging Engine & Normalization Specification

## 1. The Challenge of Fair Judging
In hackathons, different judges possess inherent subjective biases:
- **Harsh Judges**: Award scores concentrated between 1.0 and 3.0.
- **Lenient Judges**: Award scores between 4.0 and 5.0.

Simply calculating a raw arithmetic mean penalizes teams reviewed by stricter judges.

---

## 2. Mathematical Normalization Model

To ensure statistical fairness, the engine applies **Z-Score Standardization** combined with **Min-Max Boundary Preservation**.

### Step 1: Weighted Criterion Evaluation
For a given review $k$ by judge $j$ on project $i$:

$$R_{j,i} = \sum_{c \in C} w_c \cdot s_{c, j, i}$$

Where $w_c$ represents normalized criterion weights ($\sum w_c = 1.0$) and $s_{c, j, i} \in [1.0, 5.0]$.

### Step 2: Per-Judge Variance Calculation
For all evaluations submitted by judge $j$:

$$\mu_j = \frac{1}{N_j} \sum_{i=1}^{N_j} R_{j, i}, \quad \sigma_j = \sqrt{\frac{1}{N_j} \sum_{i=1}^{N_j} (R_{j, i} - \mu_j)^2}$$

### Step 3: Z-Score Standardized Mapping
The normalized rating $Z_{j, i}$ is transformed back to standard 5-point scale:

$$Z_{j, i} = \text{clip}\left(3.0 + 0.8 \cdot \left(\frac{R_{j, i} - \mu_j}{\sigma_j + \epsilon}\right), 1.0, 5.0\right)$$

### Step 4: Blended Final Composite
The final score combines 70% Z-score normalized value and 30% baseline raw score:

$$\text{FinalScore}(i) = 0.70 \cdot \bar{Z}_i + 0.30 \cdot \bar{R}_i$$

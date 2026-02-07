# Equipment Reliability Analysis & Methodology Report

## 1. Problem Statement (The Issue)
In high-demand industrial environments, equipment failure (breakdowns) leads to significant production losses and high repair costs. The challenge identified was:
*   **Unstructured Data:** Failure data was scattered across multiple Excel sheets.
*   **Metric Complexity:** Manually calculating industry-standard reliability metrics (MTTF, MTTR, Failure Rates) is prone to human error.
*   **Cost Visibility:** Difficulty in identifying the true financial impact, specifically differentiating between general production repairs and standard maintenance costs.
*   **Efficiency Gaps:** Lack of a centralized way to see "Grand Totals" of costs and reliability performance across different departments or time periods (sheets).

---

## 2. Analysis Methodology
The dashboard employs a systematic 3-step approach to analyze the data:
1.  **Data Intake & Normalization:** The system reads Excel files, cleans column headers (removing extra spaces/handling case sensitivity), and converts raw text data into numeric values for calculation.
2.  **Fuzzy Scanning:** It iterates through every sheet in the workbook to find matching data even if the column names vary slightly (e.g., "Repairing cost" vs. "Repairing  cost").
3.  **Conditional Filtering:** To derive accurate production efficiency, the system specifically filters out the `MAINTENANCE` department data from repair cost calculations, focusing on the core equipment issues.

---

## 3. Mathematical Formulas Used

The system utilizes standard Industrial Engineering and Reliability Engineering formulas:

### A. Reliability Calculations
*   **Operating Time:**
    $$\text{Operating Time} = \text{Observation Period} - \text{Downtime}$$
    *(Note: Default Observation Period is 1440 minutes/24 hours per record).*

*   **Mean Time To Failure (MTTF):**
    $$\text{MTTF} = \frac{\sum \text{Total Operating Time}}{\text{Total Number of Failures}}$$
    *Measures the average time the equipment is working between failures.*

*   **Failure Rate ($\lambda$):**
    $$\lambda = \frac{1}{\text{MTTF}}$$

### B. Repair Performance Calculations
*   **Mean Time To Repair (MTTR):**
    $$\text{MTTR} = \frac{\sum \text{Total Repair Duration}}{\text{Total Number of Repairs}}$$
    *Measures the average time taken to fix the equipment and resume production.*

*   **Repair Rate ($\mu$):**
    $$\mu = \frac{1}{\text{MTTR}}$$

### C. Financial Impact (Cost)
*   **Total Repair Cost (All):**
    $$\sum \text{Repairing Cost (per sheet)}$$

*   **Exclude MAINTENANCE Cost:**
    $$\sum \text{Repairing Cost} \text{ where } \text{Department} \neq \text{'MAINTENANCE'}$$

---

## 4. Operational Insights Produced
By applying these formulas, the dashboard generates the following insights:
1.  **Availability Breakdown:** A visual timeline showing the ratio of equipment uptime (Green) vs. downtime (Red).
2.  **Pareto Analysis (Reasons):** Identification of the top 10 reasons causing most failures to prioritize maintenance efforts.
3.  **Cross-Sheet Grand Totals:** A consolidated view of all expenses and reliability gaps across the entire facility (multiple sheets).
4.  **Unit Consistency:** The ability to toggle results between **Minutes** and **Hours** for both operational and management-level reporting.

---

**Conclusion:** This methodology ensures that the factory gets a mathematically sound, data-driven report that isolates actual breakdown costs and provides a clear roadmap for improving equipment uptime.

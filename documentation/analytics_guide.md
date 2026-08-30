# CineScope SQL — Analytics Logic & Technical Guide

## 1. Executive Business Logic Overview

The **CineScope SQL Movie Analytics System** converts raw film industry data into strategic financial and operational insights. It is specifically designed for executive decision-makers at streaming services (e.g., Netflix, Amazon Prime Video), major studios (e.g., Warner Bros., Universal), and theatrical distribution companies.

### Core Business Objectives
1. **Capital Allocation & Risk Mitigation**: Evaluate historical Return on Investment (ROI %) per genre and runtime category to optimize production greenlight decisions.
2. **Talent Contract Optimization**: Quantify actor and director commercial consistency and hit-rate percentages to negotiate performance-contingent contracts.
3. **Distribution Strategy**: Measure international vs. domestic revenue contribution ratios and analyze decade-over-decade box-office growth.

---

## 2. SQL Scripts & Business Metrics Reference

### Script 01: `sql/01_basic_movie_analysis.sql`
- **Scope**: Foundation queries, sorting, filtering, range checks, and descriptive statistics.
- **Key Functions**: `COUNT()`, `AVG()`, `MAX()`, `MIN()`, `SUM()`, `GROUP BY`, `HAVING`.

### Script 02: `sql/02_financial_roi_analysis.sql`
- **Scope**: Financial profitability, ROI %, genre risk ranking, and tier segmentation.
- **Core Formula**:
  $$\text{ROI \%} = \frac{(\text{Domestic Revenue} + \text{International Revenue}) - \text{Budget}}{\text{Budget}} \times 100$$
- **Windowing & CTEs**:
  - `genre_financial_summary` CTE calculates total and average financial performance per genre.
  - `DENSE_RANK() OVER (ORDER BY total_genre_revenue DESC)` ranks genres by revenue without skipping ranks for ties.
  - `CASE` statements segment films into four commercial tiers:
    - **Blockbuster**: $\ge 400\%$ ROI ($4\times+$ multiplier)
    - **Profitable**: $100\% - 399\%$ ROI ($1\times - 4\times$ multiplier)
    - **Broke Even**: $0\% - 99\%$ ROI ($0\times - 1\times$ multiplier)
    - **Box Office Flop**: $< 0\%$ ROI ($<0\times$ multiplier)

### Script 03: `sql/03_talent_and_director_performance.sql`
- **Scope**: Director/Actor track record analysis, hit rates, and consistency scores.
- **Key Logic**:
  - `AVG(revenue) OVER (PARTITION BY director_id)` calculates lifetime career average box-office yield.
  - **Talent Hit Rate %**:
    $$\text{Hit Rate \%} = \frac{\text{Count of Movies with ROI } \ge 100\%}{\text{Total Projects Starred}} \times 100$$
  - **Consistency Score**: Measures rating dispersion using sample standard deviation `STDDEV_SAMP(imdb_rating)`.

### Script 04: `sql/04_audience_sentiment_and_runtime.sql`
- **Scope**: Duration correlation, IMDb rating brackets, and multi-genre tagging.
- **Runtime Bucketing**:
  - Short ($<90$ min)
  - Standard ($90-120$ min)
  - Feature ($121-150$ min)
  - Epic ($150+$ min)
- **Multi-genre Unnesting**: Joins `movie_genres` to evaluate individual genre tags in cross-genre releases.

### Script 05: `sql/05_time_series_trends.sql`
- **Scope**: Year-over-Year (YoY) and Month-over-Month (MoM) growth, running totals.
- **Key Functions**:
  - `LAG(total_annual_revenue, 1) OVER (ORDER BY release_year)` retrieves prior-period box office revenue.
  - `SUM(annual_revenue) OVER (ORDER BY release_year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` computes cumulative running gross totals.

---

## 3. Executive Insights & Strategic Recommendations

| Insight Category | Observed Trend | Executive Recommendation |
| :--- | :--- | :--- |
| **Runtime Sweet Spot** | Films in the **121–150m** and **150m+** buckets generate the highest average global revenue ($1.1B+ average). | Allocate premium production budgets ($150M+) primarily to feature/epic runtimes that support immersive world-building. |
| **Genre Profitability** | Action & Science Fiction deliver high gross revenue but carry higher budget risk. Crime & Drama yield lower total revenue but higher profit margins. | Balance portfolio risk by pairing 1-2 high-budget Sci-Fi tentpoles with 3-4 mid-budget Crime/Thriller projects. |
| **Talent Consistency** | Directors like Christopher Nolan and James Cameron exhibit a $100\%$ commercial hit rate across multiple decades. | Utilize performance-contingent backend pool contracts for top-tier directors to align incentives with box-office milestones. |

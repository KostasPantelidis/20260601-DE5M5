# 20260601-DE5M5

### Scenario
A library wants to automate their manual data quality process using Python and Azure DevOps. This project ingests, cleans and transforms borrowing records, ready for presentation in Power BI.

### User Stories or Backlog




### Datasets
Two CSV files are used:
- customer.csv   : library member records (ID, Name)
- borrowings.csv : book checkout and return

### Solutions Diagram




### Known Data Issues 
- Missing or empty values
- Duplicate records
- Invalid or inconsistent dates
- Customer IDs that don't match between the two files

### Planned Approach
1. Plan: set up Azure DevOps, Kanban board and document architecture
2. Ingest: load CSVs using Python
3. Clean: detect and flag data issues
4. Test: unit tests to validate cleaning logic
5. Automate: CI/CD pipeline to run the process end-to-end
6. Report: outputs, analysis of cleaned data in Power BI

### Repo Structure
library-data-quality/
├── data/               # Source CSV files 
├── src/                # Python scripts (ingest, clean, transform) 
├── tests/              # Unit tests 
├── output/             # Cleaned data ready for Power BI 
└── pipeline/           # Azure DevOps pipeline


### How to Run
pip install -r requirements.txt 
python src/clean.py 
pytest tests/

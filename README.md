# Library Data Quality Automation (Project 20260601-DE5M5)

## 📖 Scenario
A library wants to automate its manual data quality process using Python and Azure DevOps. This project ingests, cleans, and transforms library borrowing records, making them ready for seamless presentation and analysis in Power BI.

---

## 👥 User Stories
* **As a Data Analyst,** I want automated data cleaning so that I don't have to spend hours manually fixing CSV files every week.
* **As a Library Manager,** I want a Power BI dashboard showing key operational metrics so that I can make data-driven decisions about our book inventory.
* **As a DevOps Engineer,** I want this entire pipeline automated with CI/CD so that every data update is validated and processed without manual intervention.

---

## 📊 Datasets
The project processes two core source CSV files located in the `data/` directory:
* `customer.csv`: Library member records containing unique IDs and Names.
* `borrowings.csv`: Book checkout and return transactions.

### Known Data Issues Handled:
* Missing or empty values
* Duplicate records
* Invalid or inconsistent date formats
* Referential integrity issues (Customer IDs that don't match between files)

---

## 🛠️ Solutions Diagram & Process Flow

[ data/ ]                [ src/ ]                [ output/ ]             [ Power BI ]
+--------------+       +-----------------+       +--------------+       +------------------+
| customer.csv | ----> |                 |       |              |       |  • Total Records |
|              |       |  cleanerapp.py  | ----> |  result.csv  | ----> |  • Records Dropped|
| borrowings.csv| ----> |                 |       |              |       |  • Exec Time     |
+--------------+       +-----------------+       +--------------+       +------------------+
▲
| (Validated by)
+--------------+
|    pytest    |
+--------------+


### Planned Approach:
1. **Plan:** Set up Azure DevOps Kanban board and document core architecture.
2. **Ingest & Clean:** Run `cleanerapp.py` to ingest the raw CSVs, apply cleaning logic, and flag data issues.
3. **Test:** Execute unit tests via `pytest` to validate cleaning logic.
4. **Automate:** Trigger Azure DevOps CI/CD pipeline to run the process end-to-end.
5. **Report:** Load the final `result.csv` into Power BI to visualize data health and metrics.

---

## 📁 Repository Structure

```text
library-data-quality/
├── data/                  # Source CSV files (customer.csv, borrowings.csv)
├── src/                   # Core Python application logic
│   └── cleanerapp.py      # Main execution script for ingestion & cleaning
├── tests/                 # Unit tests to validate cleaning logic
├── output/                # Target directory for processed data
│   └── result.csv         # Cleaned output file used by Power BI
├── pipeline/              # Azure DevOps pipeline YAML configurations
├── archive/               # Docker demos, Jupyter Notebooks, training & exercises
└── requirements.txt       # Python dependencies

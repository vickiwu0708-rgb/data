# 处理论文数据 (Academic Paper Data Processing)

A Python toolkit for loading, cleaning, and analyzing academic paper datasets.

## Files

| File | Description |
|---|---|
| `papers.csv` | Sample paper dataset (CSV format) |
| `process_papers.py` | Main data processing script |
| `test_process_papers.py` | Unit tests |
| `requirements.txt` | Python dependencies |

## Usage

Install dependencies:
```
pip install -r requirements.txt
```

Run the processing pipeline:
```
python process_papers.py
```

This will:
1. Load papers from `papers.csv`
2. Clean and normalize each record (strip whitespace, parse authors/keywords into lists, convert year and citations to integers)
3. Remove duplicate entries (based on DOI)
4. Print summary statistics and top keywords
5. Save the processed output to `papers_processed.json`

## Input Format (`papers.csv`)

| Column | Description |
|---|---|
| `title` | Paper title |
| `authors` | Semicolon-separated list of authors |
| `year` | Publication year |
| `journal` | Journal or conference name |
| `keywords` | Semicolon-separated keywords |
| `abstract` | Abstract text |
| `doi` | Digital Object Identifier |
| `citations` | Citation count |

## Functions

- `load_papers(filepath)` — Load CSV into a list of dicts
- `clean_paper(paper)` / `clean_papers(papers)` — Normalize records
- `remove_duplicates(papers)` — Deduplicate by DOI
- `filter_by_year(papers, start, end)` — Filter by year range
- `sort_by_citations(papers)` — Sort by citation count
- `get_top_keywords(papers, top_n)` — Most common keywords
- `get_publication_stats(papers)` — Summary statistics
- `papers_by_year(papers)` — Group by year
- `save_papers_json(papers, filepath)` — Export to JSON
- `process(input_csv, output_json)` — Full pipeline
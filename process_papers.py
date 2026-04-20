"""
处理论文数据 - Academic Paper Data Processing
"""

import csv
import json
from collections import Counter


def load_papers(filepath):
    """Load papers from a CSV file."""
    papers = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers.append(dict(row))
    return papers


def clean_paper(paper):
    """Clean and normalize a single paper record."""
    cleaned = {}

    # Strip whitespace from all string fields
    for key, value in paper.items():
        cleaned[key] = value.strip() if isinstance(value, str) else value

    # Normalize year to integer
    try:
        cleaned['year'] = int(cleaned.get('year', 0))
    except (ValueError, TypeError):
        cleaned['year'] = None

    # Normalize citations to integer
    try:
        cleaned['citations'] = int(cleaned.get('citations', 0))
    except (ValueError, TypeError):
        cleaned['citations'] = 0

    # Parse authors into a list
    authors_raw = cleaned.get('authors', '')
    cleaned['authors'] = [a.strip() for a in authors_raw.split(';') if a.strip()]

    # Parse keywords into a list
    keywords_raw = cleaned.get('keywords', '')
    cleaned['keywords'] = [k.strip() for k in keywords_raw.split(';') if k.strip()]

    return cleaned


def clean_papers(papers):
    """Clean a list of paper records."""
    return [clean_paper(p) for p in papers]


def remove_duplicates(papers):
    """Remove duplicate papers based on DOI."""
    seen_dois = set()
    unique = []
    for paper in papers:
        doi = paper.get('doi', '').strip()
        if doi and doi in seen_dois:
            continue
        if doi:
            seen_dois.add(doi)
        unique.append(paper)
    return unique


def filter_by_year(papers, start_year, end_year):
    """Filter papers published within a year range (inclusive)."""
    return [
        p for p in papers
        if p.get('year') is not None and start_year <= p['year'] <= end_year
    ]


def sort_by_citations(papers, descending=True):
    """Sort papers by citation count."""
    return sorted(papers, key=lambda p: p.get('citations', 0), reverse=descending)


def get_top_keywords(papers, top_n=10):
    """Return the most common keywords across all papers."""
    all_keywords = []
    for paper in papers:
        all_keywords.extend(paper.get('keywords', []))
    counter = Counter(all_keywords)
    return counter.most_common(top_n)


def get_publication_stats(papers):
    """Compute basic statistics for the paper dataset."""
    years = [p['year'] for p in papers if p.get('year') is not None]
    citations = [p['citations'] for p in papers]

    stats = {
        'total_papers': len(papers),
        'year_range': (min(years), max(years)) if years else (None, None),
        'total_citations': sum(citations),
        'avg_citations': round(sum(citations) / len(citations), 2) if citations else 0,
        'max_citations': max(citations) if citations else 0,
        'top_paper': None,
    }

    if papers:
        top = max(papers, key=lambda p: p.get('citations', 0))
        stats['top_paper'] = {
            'title': top.get('title', ''),
            'citations': top.get('citations', 0),
        }

    return stats


def papers_by_year(papers):
    """Group papers by publication year."""
    groups = {}
    for paper in papers:
        year = paper.get('year')
        if year not in groups:
            groups[year] = []
        groups[year].append(paper)
    return groups


def save_papers_json(papers, filepath):
    """Save processed papers to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def process(input_csv, output_json):
    """Full pipeline: load, clean, deduplicate, and save paper data."""
    print(f"Loading papers from {input_csv}...")
    papers = load_papers(input_csv)

    print(f"Loaded {len(papers)} papers. Cleaning...")
    papers = clean_papers(papers)

    print("Removing duplicates...")
    papers = remove_duplicates(papers)
    print(f"{len(papers)} papers after deduplication.")

    stats = get_publication_stats(papers)
    print("\n=== 统计信息 (Statistics) ===")
    print(f"论文总数 (Total papers): {stats['total_papers']}")
    print(f"年份范围 (Year range): {stats['year_range'][0]} - {stats['year_range'][1]}")
    print(f"总引用次数 (Total citations): {stats['total_citations']}")
    print(f"平均引用次数 (Avg citations): {stats['avg_citations']}")
    print(f"最高引用次数 (Max citations): {stats['max_citations']}")
    if stats['top_paper']:
        print(f"引用最多的论文 (Most cited paper): {stats['top_paper']['title']} ({stats['top_paper']['citations']} citations)")

    top_keywords = get_top_keywords(papers, top_n=10)
    print("\n=== 高频关键词 (Top Keywords) ===")
    for keyword, count in top_keywords:
        print(f"  {keyword}: {count}")

    papers_sorted = sort_by_citations(papers)

    print(f"\nSaving processed data to {output_json}...")
    save_papers_json(papers_sorted, output_json)
    print("Done.")

    return papers_sorted


if __name__ == '__main__':
    process('papers.csv', 'papers_processed.json')

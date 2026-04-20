"""
Tests for process_papers.py
"""

import json
import os
import tempfile
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from process_papers import (
    clean_paper,
    clean_papers,
    remove_duplicates,
    filter_by_year,
    sort_by_citations,
    get_top_keywords,
    get_publication_stats,
    papers_by_year,
    save_papers_json,
    load_papers,
    process,
)

SAMPLE_PAPERS_RAW = [
    {
        'title': ' Paper A ',
        'authors': 'Smith, J.; Doe, A.',
        'year': '2020',
        'journal': 'Journal A',
        'keywords': 'machine learning; deep learning',
        'abstract': 'Abstract A',
        'doi': '10.1000/aaa',
        'citations': '100',
    },
    {
        'title': 'Paper B',
        'authors': 'Lee, K.',
        'year': '2018',
        'journal': 'Journal B',
        'keywords': 'deep learning; NLP',
        'abstract': 'Abstract B',
        'doi': '10.1000/bbb',
        'citations': '50',
    },
    {
        'title': 'Paper C',
        'authors': 'Wang, L.',
        'year': '2020',
        'journal': 'Journal C',
        'keywords': 'machine learning',
        'abstract': 'Abstract C',
        'doi': '10.1000/ccc',
        'citations': '200',
    },
]


def test_clean_paper_strips_whitespace():
    raw = SAMPLE_PAPERS_RAW[0]
    cleaned = clean_paper(raw)
    assert cleaned['title'] == 'Paper A'


def test_clean_paper_year_as_int():
    cleaned = clean_paper(SAMPLE_PAPERS_RAW[0])
    assert cleaned['year'] == 2020
    assert isinstance(cleaned['year'], int)


def test_clean_paper_citations_as_int():
    cleaned = clean_paper(SAMPLE_PAPERS_RAW[0])
    assert cleaned['citations'] == 100
    assert isinstance(cleaned['citations'], int)


def test_clean_paper_authors_as_list():
    cleaned = clean_paper(SAMPLE_PAPERS_RAW[0])
    assert isinstance(cleaned['authors'], list)
    assert len(cleaned['authors']) == 2
    assert 'Smith, J.' in cleaned['authors']


def test_clean_paper_keywords_as_list():
    cleaned = clean_paper(SAMPLE_PAPERS_RAW[0])
    assert isinstance(cleaned['keywords'], list)
    assert 'machine learning' in cleaned['keywords']
    assert 'deep learning' in cleaned['keywords']


def test_clean_papers():
    cleaned = clean_papers(SAMPLE_PAPERS_RAW)
    assert len(cleaned) == 3
    for p in cleaned:
        assert isinstance(p['year'], int)
        assert isinstance(p['authors'], list)


def test_remove_duplicates_keeps_unique():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    unique = remove_duplicates(papers)
    assert len(unique) == 3


def test_remove_duplicates_removes_duplicate_doi():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    papers.append(dict(papers[0]))  # duplicate DOI
    unique = remove_duplicates(papers)
    assert len(unique) == 3


def test_filter_by_year():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    filtered = filter_by_year(papers, 2019, 2020)
    assert all(2019 <= p['year'] <= 2020 for p in filtered)
    assert len(filtered) == 2


def test_sort_by_citations_descending():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    sorted_papers = sort_by_citations(papers)
    assert sorted_papers[0]['citations'] >= sorted_papers[-1]['citations']


def test_sort_by_citations_ascending():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    sorted_papers = sort_by_citations(papers, descending=False)
    assert sorted_papers[0]['citations'] <= sorted_papers[-1]['citations']


def test_get_top_keywords():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    top = get_top_keywords(papers, top_n=3)
    assert len(top) <= 3
    keywords = [kw for kw, _ in top]
    assert 'machine learning' in keywords
    assert 'deep learning' in keywords


def test_get_publication_stats():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    stats = get_publication_stats(papers)
    assert stats['total_papers'] == 3
    assert stats['year_range'] == (2018, 2020)
    assert stats['total_citations'] == 350
    assert stats['avg_citations'] == round(350 / 3, 2)
    assert stats['max_citations'] == 200
    assert stats['top_paper']['title'] == 'Paper C'


def test_papers_by_year():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    grouped = papers_by_year(papers)
    assert 2020 in grouped
    assert len(grouped[2020]) == 2
    assert len(grouped[2018]) == 1


def test_save_and_load_json():
    papers = clean_papers(SAMPLE_PAPERS_RAW)
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        tmp_path = f.name
    try:
        save_papers_json(papers, tmp_path)
        with open(tmp_path, encoding='utf-8') as f:
            loaded = json.load(f)
        assert len(loaded) == len(papers)
        assert loaded[0]['title'] == papers[0]['title']
    finally:
        os.unlink(tmp_path)


def test_load_papers_from_csv():
    rows = [
        {'title': 'Test Paper', 'authors': 'A, B', 'year': '2021',
         'journal': 'J', 'keywords': 'kw', 'abstract': 'abs',
         'doi': '10.0/test', 'citations': '5'},
    ]
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w',
                                     newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        tmp_path = f.name
    try:
        papers = load_papers(tmp_path)
        assert len(papers) == 1
        assert papers[0]['title'] == 'Test Paper'
    finally:
        os.unlink(tmp_path)


def test_full_process_pipeline():
    rows = SAMPLE_PAPERS_RAW
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w',
                                     newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        csv_path = f.name

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        json_path = f.name

    try:
        result = process(csv_path, json_path)
        assert len(result) == 3
        # Sorted by citations descending
        assert result[0]['citations'] >= result[-1]['citations']
        # JSON file was written
        with open(json_path, encoding='utf-8') as jf:
            loaded = json.load(jf)
        assert len(loaded) == 3
    finally:
        os.unlink(csv_path)
        os.unlink(json_path)


if __name__ == '__main__':
    tests = [
        test_clean_paper_strips_whitespace,
        test_clean_paper_year_as_int,
        test_clean_paper_citations_as_int,
        test_clean_paper_authors_as_list,
        test_clean_paper_keywords_as_list,
        test_clean_papers,
        test_remove_duplicates_keeps_unique,
        test_remove_duplicates_removes_duplicate_doi,
        test_filter_by_year,
        test_sort_by_citations_descending,
        test_sort_by_citations_ascending,
        test_get_top_keywords,
        test_get_publication_stats,
        test_papers_by_year,
        test_save_and_load_json,
        test_load_papers_from_csv,
        test_full_process_pipeline,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")

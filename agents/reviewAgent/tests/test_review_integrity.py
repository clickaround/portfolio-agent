import json

import pytest

from portfolio_agent.engine import review


def make_review(tmp_path):
    att = tmp_path / 'attempts' / '01'
    (att / 'preview').mkdir(parents=True)
    (att / 'scenes').mkdir()
    (att / 'preview' / 'page-01.png').write_bytes(b'frame')
    (att / 'scenes' / 'page-01.json').write_text('{}')
    (att / 'book.pdf').write_bytes(b'pdf')
    (att / 'qa.json').write_text('{"gate_pass": true}')
    ctx = review.review_context(tmp_path)
    data = {'review_context_sha256': ctx['review_context_sha256'], 'frame_hashes': ctx['frames'],
            'reviewed_frames': list(ctx['frames']), 'reviewer_mode': 'human',
            'dimension_scores': {name: .9 for name in review.DIMENSIONS}, 'blockers': []}
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(data))
    return att, path


@pytest.mark.parametrize('relative', ['preview/page-01.png', 'scenes/page-01.json', 'book.pdf', 'qa.json'])
def test_mutation_after_context_rejected_at_record(tmp_path, relative):
    att, path = make_review(tmp_path)
    (att / relative).write_bytes(b'changed')
    with pytest.raises(review.ReviewError):
        review.record_review(tmp_path, path)


@pytest.mark.parametrize('relative', ['preview/page-01.png', 'scenes/page-01.json', 'book.pdf', 'qa.json'])
def test_mutation_after_record_rejected_at_finalize(tmp_path, relative):
    att, path = make_review(tmp_path)
    review.record_review(tmp_path, path)
    (att / relative).write_bytes(b'changed')
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path)


def test_finalize_removes_previous_missing_format(tmp_path):
    _, path = make_review(tmp_path)
    review.record_review(tmp_path, path)
    final = tmp_path / 'final'
    final.mkdir()
    (final / 'book.pptx').write_bytes(b'old')
    review.finalize(tmp_path)
    assert (final / 'book.pdf').read_bytes() == b'pdf'
    assert not (final / 'book.pptx').exists()


def test_rebinding_context_invalidates_previous_review(tmp_path):
    _, path = make_review(tmp_path)
    review.record_review(tmp_path, path)
    context = tmp_path / 'attempts' / '01' / 'review-context.json'
    data = json.loads(context.read_text())
    data['created'] = 'new binding'
    context.write_text(json.dumps(data))
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path)


def test_adding_export_after_review_is_rejected(tmp_path):
    att, path = make_review(tmp_path)
    review.record_review(tmp_path, path)
    (att / 'book.pptx').write_bytes(b'new export')
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path)

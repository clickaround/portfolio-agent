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


def test_native_approval_cannot_override_unrelated_blocker(tmp_path):
    att, path = make_review(tmp_path)
    (att / 'qa.json').write_text(json.dumps({'gate_pass': False, 'blocking_issues': [
        {'code': 'NATIVE_EDIT_UNVERIFIED'}, {'code': 'BROKEN_PDF'}]}))
    ctx = review.review_context(tmp_path)
    data = json.loads(path.read_text())
    data.update(review_context_sha256=ctx['review_context_sha256'], frame_hashes=ctx['frames'],
                native_edit_confirmation={'reviewed_exported_pages': True, 'content_and_source_fidelity_confirmed': True,
                                          'page_geometry_and_clipping_confirmed': True})
    path.write_text(json.dumps(data))
    review.record_review(tmp_path, path)
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path)


def native_review(tmp_path):
    import fitz

    out = tmp_path / 'out'
    parent = out / 'attempts' / '00'
    parent.mkdir(parents=True)
    (parent / 'book.designcraft').write_bytes(b'synthetic original')
    (tmp_path / 'images').mkdir()
    source = tmp_path / 'images' / 'source.png'
    source.write_bytes(b'synthetic source')
    manifest = {'assets': [{'relative_path': 'images/source.png', 'sha256': review.sha256(source)}]}
    (parent / 'manifest.json').write_text(json.dumps(manifest))
    att = out / 'attempts' / '01'
    (att / 'preview').mkdir(parents=True)
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((40, 40), 'Synthetic')
    doc.save(att / 'book.pdf')
    doc.close()
    doc = fitz.open(att / 'book.pdf')
    doc[0].get_pixmap(dpi=96, colorspace=fitz.csRGB, alpha=False).save(att / 'preview' / 'page-01.png')
    doc.close()
    (att / 'book.designcraft').write_bytes(b'synthetic native')
    (att / 'source-manifest.json').write_bytes((parent / 'manifest.json').read_bytes())
    meta = {'parent_attempt': '00', 'parent_native_sha256': review.sha256(parent / 'book.designcraft'),
            'native_sha256': review.sha256(att / 'book.designcraft'),
            'pdf_sha256': review.sha256(att / 'book.pdf'), 'preview_source': 'edited_pdf', 'preview_dpi': 96,
            'preview_colorspace': 'RGB', 'preview_alpha': False, 'structural_validation_passed': True, 'pages': 1,
            'preview_sha256': {'page-01.png': review.sha256(att / 'preview' / 'page-01.png')},
            'source_evidence': {'status': 'verified', 'manifest_sha256': review.sha256(att / 'source-manifest.json'),
                                'assets': [{'path': 'images/source.png', 'sha256': review.sha256(source)}], 'issues': []}}
    (att / 'import.json').write_text(json.dumps(meta))
    (att / 'qa.json').write_text(json.dumps({'gate_pass': False, 'blocking_issues': [{'code': 'NATIVE_EDIT_UNVERIFIED'}],
                                             'native_edit': meta}))
    ctx = review.review_context(out)
    data = {'review_context_sha256': ctx['review_context_sha256'], 'frame_hashes': ctx['frames'],
            'reviewed_frames': list(ctx['frames']), 'reviewer_mode': 'human',
            'dimension_scores': {name: .9 for name in review.DIMENSIONS}, 'blockers': [],
            'native_edit_confirmation': {'reviewed_exported_pages': True, 'content_and_source_fidelity_confirmed': True,
                                         'page_geometry_and_clipping_confirmed': True}}
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(data))
    return att, path


def test_human_attested_native_output_can_finalize(tmp_path):
    _, path = native_review(tmp_path)
    review.record_review(tmp_path / 'out', path)
    rec = review.finalize(tmp_path / 'out')
    assert rec['native_edit_human_attested'] is True
    assert (tmp_path / 'out' / 'final' / 'book.designcraft').read_bytes() == b'synthetic native'


@pytest.mark.parametrize('field', ['reviewed_exported_pages', 'content_and_source_fidelity_confirmed', 'page_geometry_and_clipping_confirmed'])
def test_native_requires_every_confirmation(tmp_path, field):
    _, path = native_review(tmp_path)
    data = json.loads(path.read_text())
    data['native_edit_confirmation'][field] = False
    path.write_text(json.dumps(data))
    with pytest.raises(review.ReviewError):
        review.record_review(tmp_path / 'out', path)


def test_native_cannot_be_approved_by_agent(tmp_path):
    _, path = native_review(tmp_path)
    data = json.loads(path.read_text())
    data['reviewer_mode'] = 'fresh_subagent'
    path.write_text(json.dumps(data))
    with pytest.raises(review.ReviewError):
        review.record_review(tmp_path / 'out', path)


def test_native_preview_must_match_rendered_pdf(tmp_path):
    att, path = native_review(tmp_path)
    import fitz

    fake = fitz.Pixmap(fitz.csRGB, (0, 0, 400, 267), False)
    fake.clear_with(0)
    fake.save(att / 'preview' / 'page-01.png')
    meta = json.loads((att / 'import.json').read_text())
    meta['preview_sha256']['page-01.png'] = review.sha256(att / 'preview' / 'page-01.png')
    (att / 'import.json').write_text(json.dumps(meta))
    qa = json.loads((att / 'qa.json').read_text())
    qa['native_edit'] = meta
    (att / 'qa.json').write_text(json.dumps(qa))
    with pytest.raises(review.ReviewError):
        review.review_context(tmp_path / 'out')


def test_native_human_confirmation_does_not_override_other_blocker(tmp_path):
    att, path = native_review(tmp_path)
    qa = json.loads((att / 'qa.json').read_text())
    qa['blocking_issues'].append({'code': 'BROKEN_PDF'})
    (att / 'qa.json').write_text(json.dumps(qa))
    ctx = review.review_context(tmp_path / 'out')
    data = json.loads(path.read_text())
    data['review_context_sha256'] = ctx['review_context_sha256']
    path.write_text(json.dumps(data))
    review.record_review(tmp_path / 'out', path)
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path / 'out')


def test_native_metadata_changes_after_review_invalidate_approval(tmp_path):
    att, path = native_review(tmp_path)
    review.record_review(tmp_path / 'out', path)
    (att / 'import.json').write_text('{}')
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path / 'out')


def test_native_parent_change_invalidates_approval(tmp_path):
    _, path = native_review(tmp_path)
    review.record_review(tmp_path / 'out', path)
    (tmp_path / 'out' / 'attempts' / '00' / 'book.designcraft').write_bytes(b'changed original')
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path / 'out')


@pytest.mark.parametrize('stage', ['record', 'finalize'])
def test_native_source_change_is_rejected(tmp_path, stage):
    _, path = native_review(tmp_path)
    if stage == 'finalize':
        review.record_review(tmp_path / 'out', path)
    (tmp_path / 'images' / 'source.png').write_bytes(b'changed')
    with pytest.raises(review.ReviewError):
        if stage == 'record':
            review.record_review(tmp_path / 'out', path)
        else:
            review.finalize(tmp_path / 'out')


def test_native_manifest_missing_is_rejected(tmp_path):
    att, path = native_review(tmp_path)
    (att / 'source-manifest.json').unlink()
    with pytest.raises(review.ReviewError):
        review.record_review(tmp_path / 'out', path)


def test_manifest_parent_modified_after_review_is_rejected(tmp_path):
    _, path = native_review(tmp_path)
    review.record_review(tmp_path / 'out', path)
    (tmp_path / 'out' / 'attempts' / '00' / 'manifest.json').write_text('{}')
    with pytest.raises(review.ReviewError):
        review.finalize(tmp_path / 'out')


def test_manifest_path_traversal_is_rejected(tmp_path):
    att, _ = native_review(tmp_path)
    original = att.parent / '00' / 'manifest.json'
    manifest = json.loads(original.read_text())
    manifest['assets'][0]['relative_path'] = 'images/../../secret.png'
    original.write_text(json.dumps(manifest))
    (att / 'source-manifest.json').write_bytes(original.read_bytes())
    meta = json.loads((att / 'import.json').read_text())
    meta['source_evidence']['manifest_sha256'] = review.sha256(original)
    meta['source_evidence']['assets'][0]['path'] = 'images/../../secret.png'
    (att / 'import.json').write_text(json.dumps(meta))
    qa = json.loads((att / 'qa.json').read_text())
    qa['native_edit'] = meta
    (att / 'qa.json').write_text(json.dumps(qa))
    with pytest.raises(review.ReviewError):
        review.review_context(tmp_path / 'out')


@pytest.mark.parametrize('stage', ['context', 'record', 'finalize'])
def test_pending_ledger_blocks_review_and_finalization(tmp_path, stage):
    att, path = make_review(tmp_path)
    if stage == 'finalize':
        review.record_review(tmp_path, path)
    (att / 'ledger-pending.json').write_text('{}')
    with pytest.raises(review.ReviewError, match='ledger'):
        if stage == 'context':
            review.review_context(tmp_path)
        elif stage == 'record':
            review.record_review(tmp_path, path)
        else:
            review.finalize(tmp_path)
    assert not (tmp_path / 'final' / 'FINAL.json').exists()

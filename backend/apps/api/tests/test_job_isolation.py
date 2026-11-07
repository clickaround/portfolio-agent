from threading import Event

from pascal_api.storage.jobs import JobStore


def test_jobs_for_same_project_do_not_run_together(tmp_path):
    store = JobStore(tmp_path, workers=3)
    first_started, release, second_started, other_started = Event(), Event(), Event(), Event()

    def first(log):
        first_started.set()
        assert release.wait(5)
        return {}

    try:
        store.submit("compose", "same", first)
        assert first_started.wait(2)
        store.submit("plan", "same", lambda log: second_started.set() or {})
        store.submit("compose", "other", lambda log: other_started.set() or {})
        assert other_started.wait(2)
        assert not second_started.wait(0.3)
    finally:
        release.set()
        store.pool.shutdown(wait=True)
    assert second_started.is_set()

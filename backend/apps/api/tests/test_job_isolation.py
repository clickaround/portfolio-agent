from threading import Event, Thread

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


def test_terminal_status_is_not_visible_before_history_is_saved(tmp_path):
    store = JobStore(tmp_path, workers=1)
    saving, release, read_done = Event(), Event(), Event()
    original_save = store._save

    def slow_save(job):
        if job["status"] in ("succeeded", "failed"):
            saving.set()
            assert release.wait(5)
        original_save(job)

    store._save = slow_save
    job = store.submit("test", "demo", lambda log: {})
    try:
        assert saving.wait(2)
        reader = Thread(target=lambda: (store.get(job["id"]), read_done.set()))
        reader.start()
        assert not read_done.wait(0.2)
    finally:
        release.set()
        store.pool.shutdown(wait=True)
    reader.join(timeout=2)
    assert read_done.is_set()
    assert JobStore(tmp_path).get(job["id"])["status"] == "succeeded"

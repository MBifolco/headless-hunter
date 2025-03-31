import pytest
from modules.base import JobSite  # Adjust the import based on your project structure


@pytest.fixture
def app_config():
    return {
        "location_terms": ["New York", "San Francisco"],
        "remote": True,
        "positive_terms": ["engineer", "developer"],
        "negative_terms": ["sales", "intern"]
    }

@pytest.fixture
def jobsite(app_config):
    return JobSite(id="test", name="TestSite", url="https://example.com", app_config=app_config)

def test_location_check_match(jobsite):
    job = {"location_city": "New York"}
    assert jobsite.location_check(job) is True

def test_location_check_no_match(jobsite):
    job = {"location_city": "Chicago"}
    assert jobsite.location_check(job) is False

def test_remote_check_true(jobsite):
    job = {"remote": True}
    assert jobsite.remote_check(job) is True

def test_remote_check_false(jobsite):
    job = {"remote": False}
    assert jobsite.remote_check(job) is False

def test_position_check_positive(jobsite):
    job = {"title": "Senior Software Engineer"}
    assert jobsite.position_check(job) is True

def test_position_check_negative(jobsite):
    job = {"title": "Sales Executive"}
    assert jobsite.position_check(job) is False

def test_position_check_neutral(jobsite):
    job = {"title": "Operations Manager"}
    assert jobsite.position_check(job) is False

def test_should_save_job_all_checks_pass(jobsite):
    job = {
        "location_city": "San Francisco",
        "remote": True,
        "title": "Software Engineer"
    }
    assert jobsite.should_save_job(job) is True

def test_should_save_job_fails_location(jobsite):
    job = {
        "location_city": "Chicago",
        "remote": True,
        "title": "Software Engineer"
    }
    assert jobsite.should_save_job(job) is False

def test_should_save_job_fails_position(jobsite):
    job = {
        "location_city": "New York",
        "remote": True,
        "title": "Marketing Specialist"
    }
    assert jobsite.should_save_job(job) is False

def test_should_save_job_fails_remote_and_location(jobsite):
    job = {
        "location_city": "Boston",
        "remote": False,
        "title": "Software Engineer"
    }
    assert jobsite.should_save_job(job) is False

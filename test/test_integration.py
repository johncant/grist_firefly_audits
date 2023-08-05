import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pyquery import PyQuery as pq

GRIST_BASE_URL="http://localhost:8484"
GRIST_API_KEY="b977ce54ae6978fdf31620baf74648d30e8b15b2"
FIREFLYIII_BASE_URL="http://localhost:8080"


@pytest.fixture
def fireflyiii_token():
    
    # Call private API, which is preferable to scraping, and probably easier
    # than execcing stuff in the container.
    s = requests.Session()

    # Get cookies
    page_response = s.get(FIREFLYIII_BASE_URL)

    if page_response.status_code != 200:
        raise ValueError("Firefly-iii returned %d" % page_response.status_code)

    # This is how ff3 gets a xsrf token in v5.7.14
    d = pq(page_response.content)
    xsrf_token = d('meta[name="csrf-token"]').attr("content").strip()

    # Get token
    resp = s.post(
        f"{FIREFLYIII_BASE_URL}/oauth/personal-access-tokens",
        headers={
            "X-CSRF-TOKEN": xsrf_token,
        },
        json={
            "name": "foo",
            "errors": [],
            "scopes": [],
        }
    )

    if resp.status_code != 200:
        raise ValueError(resp.content)

    return resp.json()["accessToken"]


def test_integration(fireflyiii_token):
    import pdb; pdb.set_trace()

# Tests
# 1. Test that X correctly fetches acounts from firefly-iii
# 1. Test that X correctly aggregates transactions from firefly-iii
# 2. Test that X installs the n8n workflow
# 3. Test that X installs the firefly-iii webhooks
# 4. Test that creating a transaction triggers the n8n workflow and causes X to update
# 5. Test that updating a transaction triggers the n8n workflow and causes X to update
# 6. Test that deleting a transaction triggers the n8n workflow and causes X to update
# 7. Test that X uninstalls the firefly-iii webhooks
# 8. Test that X uninstalls the n8n workflow

@pytest.fixture
def grist_document():
    pass

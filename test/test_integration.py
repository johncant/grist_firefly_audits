import time
from dataclasses import dataclass

import pytest
import requests
from grist_api import GristDocAPI
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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


@dataclass
class FireflyIIIApiClient:
    url: str
    access_token: str

    def request(self, *, path, method, json):
        resp = requests.request(
            method=method,
            url=f"{self.url}{path}",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            },
            json=json,
            allow_redirects=False,
        )

        if resp.status_code != 200:
            raise ValueError(resp.content)

        return resp.json()

    def post(self, **kwargs):
        return self.request(method="POST", **kwargs)

    def get(self, **kwargs):
        return self.request(method="GET", **kwargs)


@pytest.fixture
def fireflyiii_api_client(fireflyiii_token):
    return FireflyIIIApiClient(
        url=FIREFLYIII_BASE_URL,
        access_token=fireflyiii_token,
    )


@pytest.fixture
def fireflyiii_account(fireflyiii_api_client):
    account_data = {
        "name": "MyBank Current Account",
        "account_role": "defaultAsset",
        "type": "asset",
        "opening_balance": "0.00",
        "opening_balance_date": "2000-01-01 00:00:00",
        "currency_code": "GBP",
        "active": True,
        "order": 1,
    }

    return fireflyiii_api_client.post(
        path="/api/v1/accounts",
        json=account_data,
    )["data"]


@pytest.fixture
def fireflyiii_transaction(fireflyiii_api_client, fireflyiii_account):
    transaction_data = {
        "error_if_duplicate_hash": False,
        "apply_rules": False,
        "fire_webhooks": True,
        "group_title": "Test transaction",
        "transactions": [
            {
                "type": "withdrawal",
                "date": "2023-01-01T00:05:00+00:00",
                "amount": "123.45",
                "currency_code": "GBP",
                "source_id": fireflyiii_account["id"],
                "destination_name": "Pizza"
            }
        ]
    }

    return fireflyiii_api_client.post(
        path="/api/v1/transactions",
        json=transaction_data,
    )["data"]




def test_grist_doc_finds_account(fireflyiii_token, fireflyiii_account):
    grist_api = GristDocAPI("2Gs4vAitoJH6", server=GRIST_BASE_URL, api_key=GRIST_API_KEY)

    grist_api.add_records("Firefly_iii_connections", [
        {
            "url": "http://fireflyiii:8080",
            "access_token": fireflyiii_token,
            "name": "Test ff3",
        }
    ])

    grist_api.add_records("Accounts", [
        {
            "account_name": "MyBank Current Account",
            "Firefly_iii_connection": 1,
            "account_type": "asset",
        }
    ])

    time.sleep(1) # Is there a method in grist_api that waits for REQUEST to finish?
    accounts = grist_api.fetch_table("Accounts")
    account = accounts[0]

    # Correct account id from firefly-iii was looked up
    assert account.account_id == "1"

# Tests
# 1. Done - Test that X correctly fetches acounts from firefly-iii
# 2. Test that X correctly aggregates transactions from firefly-iii
# 3. Test that X installs the n8n workflow
# 4. Test that X installs the firefly-iii webhooks
# 5. Test that creating a transaction triggers the n8n workflow and causes X to update
# 6. Test that updating a transaction triggers the n8n workflow and causes X to update
# 7. Test that deleting a transaction triggers the n8n workflow and causes X to update
# 8. Test that X uninstalls the firefly-iii webhooks
# 9. Test that X uninstalls the n8n workflow

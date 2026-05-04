import json
import sys
import types
import unittest
from unittest.mock import patch


requests_stub = types.ModuleType("requests")
requests_stub.Request = object
requests_stub.Session = object
requests_stub.get = lambda *args, **kwargs: None
requests_stub.post = lambda *args, **kwargs: None
sys.modules.setdefault("requests", requests_stub)

from sixe_idp.api import (
    Client,
    ExtractionTaskClient,
    IDPException,
    Task,
    compute_hmac_sha256,
    verify_app_header_for_mode2,
)


class FakeOauthClient(object):
    token_header = {"Authorization": "Bearer test"}

    def refresh_oauth(self, refresh_interval):
        pass


class FakeResponse(object):
    def __init__(self, ok=True, payload=None, content=b"content", text=""):
        self.ok = ok
        self._payload = payload if payload is not None else {"data": "APP123"}
        self.content = content
        self.text = text

    def json(self):
        return self._payload


class ApiRegressionTests(unittest.TestCase):
    def make_client(self):
        return Client("https://idp-sea.6estates.com/", FakeOauthClient())

    def test_client_uses_normalized_base_url(self):
        client = self.make_client()

        self.assertEqual("https://idp-sea.6estates.com", client.http_host)
        self.assertEqual(
            "https://idp-sea.6estates.com/customer/extraction/fields/async",
            client.extraction_async_create_url,
        )

    def test_callback_mode2_verifies_binary_payloads(self):
        signature = compute_hmac_sha256("secret", b"result-file")

        self.assertTrue(verify_app_header_for_mode2(b"result-", b"file", signature, "secret"))

    def test_extraction_create_accepts_multiple_files(self):
        client = self.make_client()
        response = FakeResponse()

        with patch("sixe_idp.api.requests.post", return_value=response) as post:
            task = client.extraction_async_create(
                file=[("bank-1.pdf", b"one"), ("bank-2.pdf", b"two")],
                file_type="CBKS",
            )

        self.assertEqual("APP123", task.application_id)
        self.assertEqual(
            [("file", ("bank-1.pdf", b"one")), ("file", ("bank-2.pdf", b"two"))],
            post.call_args.kwargs["files"],
        )

    def test_legacy_extraction_create_accepts_multiple_files(self):
        client = ExtractionTaskClient(token="token", region="sea", isOauth=True)

        with patch("sixe_idp.api.requests.post", return_value=FakeResponse()) as post:
            client.create(
                file=[("bank-1.pdf", b"one"), ("bank-2.pdf", b"two")],
                file_type="CBKS",
            )

        self.assertEqual(
            [("file", ("bank-1.pdf", b"one")), ("file", ("bank-2.pdf", b"two"))],
            post.call_args.kwargs["files"],
        )

    def test_faas_create_uses_country_and_region_id_keys(self):
        client = self.make_client()

        with patch("sixe_idp.api.requests.post", return_value=FakeResponse()) as post:
            client.extraction_faas_create(
                files={"files": ("bank.pdf", b"data")},
                customerType=1,
                countryId="100065",
                regionId="ID-JK",
                informationType=0,
            )

        data = post.call_args.kwargs["data"]
        self.assertEqual("100065", data["countryId"])
        self.assertEqual("ID-JK", data["regionId"])
        self.assertNotIn("countryld", data)
        self.assertNotIn("regionld", data)

    def test_document_agent_serializes_file_doc_type_list(self):
        client = self.make_client()
        mappings = [{"fileName": "invoice.pdf", "fileType": "CINV", "fileTypeFrom": 1}]

        with patch("sixe_idp.api.requests.post", return_value=FakeResponse()) as post:
            client.extraction_doc_agent_create(
                flowCode="DAG1",
                file=("invoice.pdf", b"data"),
                fileDocTypeList=mappings,
            )

        self.assertEqual(json.dumps(mappings), post.call_args.kwargs["data"]["fileDocTypeList"])

    def test_split_create_sends_detect_mode(self):
        client = self.make_client()

        with patch("sixe_idp.api.requests.post", return_value=FakeResponse()) as post:
            client.split_and_extraction_async_create(
                file=("split.pdf", b"data"),
                group_id=1029,
                detect_mode=5,
                extract_mode=0,
                hitl=False,
            )

        data = post.call_args.kwargs["data"]
        self.assertEqual(1029, data["groupId"])
        self.assertEqual(5, data["detectMode"])
        self.assertEqual(0, data["extractMode"])

    def test_fs_agent_create_accepts_multiple_named_files(self):
        client = self.make_client()

        with patch("sixe_idp.api.requests.post", return_value=FakeResponse()) as post:
            client.fs_agent_create(
                file_content=[b"one", b"two"],
                filename=["fs-1.pdf", "fs-2.pdf"],
            )

        self.assertEqual(
            [("files", ("fs-1.pdf", b"one")), ("files", ("fs-2.pdf", b"two"))],
            post.call_args.kwargs["files"],
        )

    def test_task_exposes_application_id_with_task_id_alias(self):
        task = Task({"data": "APP123"})

        self.assertEqual("APP123", task.application_id)
        self.assertEqual("APP123", task.task_id)

    def test_faas_result_raises_idp_exception_on_error_response(self):
        client = self.make_client()
        response = FakeResponse(ok=False, payload={"message": "bad request"}, text="bad request")

        with patch("sixe_idp.api.requests.post", return_value=response):
            with self.assertRaises(IDPException):
                client.extraction_faas_result("FAAS123")

    def test_faas_export_returns_success_content_even_if_body_mentions_error_code(self):
        client = self.make_client()
        response = FakeResponse(ok=True, content=b"xlsx", text='{"errorCode":0}')

        with patch("sixe_idp.api.requests.post", return_value=response):
            self.assertEqual(b"xlsx", client.extraction_faas_export("FAAS123"))

    def test_faas_export_raises_idp_exception_on_error_response(self):
        client = self.make_client()
        response = FakeResponse(ok=False, payload={"message": "export failed"}, text="export failed")

        with patch("sixe_idp.api.requests.post", return_value=response):
            with self.assertRaises(IDPException):
                client.extraction_faas_export("FAAS123")


if __name__ == "__main__":
    unittest.main()

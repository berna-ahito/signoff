import io

import pytest


def _create_request(client, headers):
    resp = client.post(
        "/requests/",
        json={
            "title": "Attachment Test",
            "description": "Testing file attachments for procurement workflow",
            "category": "IT",
            "urgency": "low",
            "quantity": 1,
            "estimated_cost": 100.0,
            "justification": "Required for testing attachment functionality",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _upload_file(client, req_id, headers, name="test.txt", content=b"hello world", content_type="text/plain"):
    return client.post(
        f"/requests/{req_id}/attachments",
        files={"file": (name, io.BytesIO(content), content_type)},
        headers=headers,
    )


def test_upload_attachment_returns_201(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    resp = _upload_file(client, req_id, auth_headers["alice"])

    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert "id" in data
    assert "created_at" in data
    assert "file_data" not in data


def test_get_attachments_returns_metadata_list(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    _upload_file(client, req_id, auth_headers["alice"], name="file1.txt", content=b"data1")
    _upload_file(client, req_id, auth_headers["alice"], name="file2.txt", content=b"data2")

    resp = client.get(f"/requests/{req_id}/attachments", headers=auth_headers["alice"])
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    filenames = {item["filename"] for item in items}
    assert filenames == {"file1.txt", "file2.txt"}
    for item in items:
        assert "id" in item
        assert "filename" in item
        assert "content_type" in item
        assert "uploaded_by" in item
        assert "created_at" in item
        assert "file_data" not in item


def test_download_attachment_returns_bytes(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    original_content = b"procurement file content"
    upload_resp = _upload_file(client, req_id, auth_headers["alice"], content=original_content)
    attachment_id = upload_resp.json()["id"]

    dl_resp = client.get(
        f"/requests/{req_id}/attachments/{attachment_id}/download",
        headers=auth_headers["alice"],
    )
    assert dl_resp.status_code == 200
    assert dl_resp.content == original_content
    assert "text/plain" in dl_resp.headers["content-type"]
    assert "test.txt" in dl_resp.headers["content-disposition"]


def test_upload_exceeds_5mb_returns_400(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    big_content = b"x" * (6 * 1024 * 1024)  # 6 MB
    resp = _upload_file(client, req_id, auth_headers["alice"], content=big_content)
    assert resp.status_code == 400
    assert "5MB" in resp.json()["detail"]


def test_upload_exceeds_5_file_limit_returns_400(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    for i in range(5):
        r = _upload_file(client, req_id, auth_headers["alice"], name=f"file{i}.txt", content=b"data")
        assert r.status_code == 201

    sixth = _upload_file(client, req_id, auth_headers["alice"], name="file6.txt", content=b"data")
    assert sixth.status_code == 400
    assert "5" in sixth.json()["detail"]


def test_idor_different_request_download_returns_404(client, auth_headers, seed_users):
    req1_id = _create_request(client, auth_headers["alice"])
    req2_id = _create_request(client, auth_headers["alice"])

    upload_resp = _upload_file(client, req1_id, auth_headers["alice"])
    attachment_id = upload_resp.json()["id"]

    # Try to download req1's attachment via req2's URL
    dl_resp = client.get(
        f"/requests/{req2_id}/attachments/{attachment_id}/download",
        headers=auth_headers["alice"],
    )
    assert dl_resp.status_code == 404


def test_unauthenticated_upload_returns_401(client, auth_headers, seed_users):
    req_id = _create_request(client, auth_headers["alice"])
    resp = _upload_file(client, req_id, headers={})  # no auth
    assert resp.status_code == 401


def test_idor_list_attachments_different_user_returns_403(client, auth_headers, seed_users):
    # Alice creates a request and uploads an attachment
    req_id = _create_request(client, auth_headers["alice"])
    _upload_file(client, req_id, auth_headers["alice"])

    # Bob (manager) tries to list Alice's attachments — request has no assigned_role,
    # so _get_request_or_403 denies him with 403
    resp = client.get(f"/requests/{req_id}/attachments", headers=auth_headers["bob"])
    assert resp.status_code == 403

from datetime import date, timedelta


def create_problem(client, leetcode_id=128, rating="RED", tag_ids=None):
    return client.post("/api/v1/problems", json={
        "leetcode_id": leetcode_id,
        "title": "最长连续序列",
        "title_en": "Longest Consecutive Sequence",
        "leetcode_url": "https://leetcode.cn/problems/longest-consecutive-sequence/",
        "difficulty": "MEDIUM",
        "initial_rating": rating,
        "tag_ids": tag_ids or [],
        "mistake_reason": "没有想到 set",
        "correct_solution": "从序列起点开始枚举",
    })


def test_problem_crud_and_duplicate(client):
    created = create_problem(client)
    assert created.status_code == 201
    body = created.json()
    assert body["review_stage"] == "RED_D1"
    assert body["review_count"] == 1
    duplicate = create_problem(client)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PROBLEM_ALREADY_EXISTS"
    problem_id = body["id"]
    fetched = client.get(f"/api/v1/problems/{problem_id}")
    assert fetched.json()["title"] == "最长连续序列"
    updated = client.patch(f"/api/v1/problems/{problem_id}", json={"title": "最长连续序列（更新）", "difficulty": "HARD"})
    assert updated.json()["difficulty"] == "HARD"
    assert client.delete(f"/api/v1/problems/{problem_id}").status_code == 204
    assert client.get(f"/api/v1/problems/{problem_id}").status_code == 404


def test_validation_error_format(client):
    response = create_problem(client, leetcode_id=0)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_tag_crud_and_filter(client):
    tag = client.post("/api/v1/tags", json={"name": "哈希表"})
    assert tag.status_code == 201
    tag_id = tag.json()["id"]
    create_problem(client, tag_ids=[tag_id])
    assert client.get("/api/v1/problems", params={"tag": "哈希表"}).json()["total"] == 1
    assert len(client.get("/api/v1/tags").json()) == 1
    assert client.delete(f"/api/v1/tags/{tag_id}").status_code == 204
    assert client.get("/api/v1/problems").json()["total"] == 1


def test_search_filter_sort_pagination(client):
    create_problem(client, 128, "RED")
    second = client.post("/api/v1/problems", json={"leetcode_id": 1, "title": "两数之和", "title_en": "Two Sum", "difficulty": "EASY", "initial_rating": "YELLOW"})
    assert second.status_code == 201
    assert client.get("/api/v1/problems", params={"search": "consecutive"}).json()["total"] == 1
    assert client.get("/api/v1/problems", params={"search": "1"}).json()["items"][0]["leetcode_id"] == 1
    assert client.get("/api/v1/problems", params={"rating": "YELLOW"}).json()["total"] == 1
    page = client.get("/api/v1/problems", params={"sort": "leetcode_id", "order": "asc", "page_size": 1}).json()
    assert page["items"][0]["leetcode_id"] == 1 and page["total"] == 2


def test_review_submission_due_history_and_schedule(client):
    problem = create_problem(client).json()
    problem_id = problem["id"]
    history = client.get(f"/api/v1/problems/{problem_id}/reviews").json()
    assert len(history) == 1 and history[0]["stage_before"] is None
    manual_date = date.today() - timedelta(days=1)
    scheduled = client.post(f"/api/v1/problems/{problem_id}/schedule", json={"next_review_at": manual_date.isoformat()})
    assert scheduled.status_code == 200
    assert len(client.get("/api/v1/reviews/due").json()) == 1
    reviewed = client.post(f"/api/v1/problems/{problem_id}/reviews", json={"rating": "YELLOW", "duration_minutes": 24, "used_hint": True, "note": "边界仍不熟"})
    assert reviewed.status_code == 201
    assert reviewed.json()["stage_after"] == "YELLOW_D3"
    current = client.get(f"/api/v1/problems/{problem_id}").json()
    assert current["review_count"] == 2 and current["rating"] == "YELLOW"
    assert len(client.get(f"/api/v1/problems/{problem_id}/reviews").json()) == 2


def test_statistics(client):
    create_problem(client, 128, "RED")
    create_problem(client, 1, "GREEN")
    stats = client.get("/api/v1/statistics/overview")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] == 2 and body["red"] == 1 and body["green"] == 1
    assert body["reviews_7d"] == 2


def test_web_pages_smoke(client):
    create_problem(client)
    for path in ["/", "/problems", "/problems/new", "/review", "/history", "/statistics", "/settings", "/docs"]:
        response = client.get(path)
        assert response.status_code == 200, path


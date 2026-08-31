from datetime import date, timedelta


def create_problem(client, leetcode_id=128, rating="RED", tag_ids=None, solved_on=None):
    payload = {
        "leetcode_id": leetcode_id,
        "title": "最长连续序列",
        "title_en": "Longest Consecutive Sequence",
        "leetcode_url": "https://leetcode.cn/problems/longest-consecutive-sequence/",
        "difficulty": "MEDIUM",
        "initial_rating": rating,
        "tag_ids": tag_ids or [],
        "mistake_reason": "没有想到 set",
        "correct_solution": "从序列起点开始枚举",
    }
    if solved_on is not None:
        payload["solved_on"] = solved_on
    return client.post("/api/v1/problems", json=payload)


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


def test_create_problem_with_past_solved_date(client):
    solved_on = date.today() - timedelta(days=10)
    response = create_problem(client, solved_on=solved_on.isoformat())
    assert response.status_code == 201
    problem = response.json()
    assert problem["next_review_at"] == (solved_on + timedelta(days=1)).isoformat()
    assert len(client.get("/api/v1/reviews/due").json()) == 1
    history = client.get(f"/api/v1/problems/{problem['id']}/reviews").json()
    assert history[0]["reviewed_at"].startswith(solved_on.isoformat())
    assert history[0]["next_review_at"] == (solved_on + timedelta(days=1)).isoformat()


def test_create_problem_rejects_future_solved_date(client):
    response = create_problem(client, solved_on=(date.today() + timedelta(days=1)).isoformat())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_submit_historical_reviews_in_date_order(client):
    solved_on = date.today() - timedelta(days=30)
    problem = create_problem(client, rating="RED", solved_on=solved_on.isoformat()).json()
    first_review_date = solved_on + timedelta(days=1)
    reviewed = client.post(
        f"/api/v1/problems/{problem['id']}/reviews",
        json={"rating": "YELLOW", "reviewed_on": first_review_date.isoformat()},
    )
    assert reviewed.status_code == 201
    assert reviewed.json()["reviewed_at"].startswith(first_review_date.isoformat())
    assert reviewed.json()["next_review_at"] == (first_review_date + timedelta(days=3)).isoformat()

    second_review_date = first_review_date + timedelta(days=3)
    reviewed_again = client.post(
        f"/api/v1/problems/{problem['id']}/reviews",
        json={"rating": "YELLOW", "reviewed_on": second_review_date.isoformat()},
    )
    assert reviewed_again.status_code == 201
    assert reviewed_again.json()["stage_after"] == "YELLOW_D7"
    assert reviewed_again.json()["next_review_at"] == (second_review_date + timedelta(days=7)).isoformat()

    out_of_order = client.post(
        f"/api/v1/problems/{problem['id']}/reviews",
        json={"rating": "RED", "reviewed_on": first_review_date.isoformat()},
    )
    assert out_of_order.status_code == 422
    assert out_of_order.json()["error"]["code"] == "REVIEW_DATE_OUT_OF_ORDER"


def test_submit_review_rejects_future_date(client):
    problem = create_problem(client).json()
    response = client.post(
        f"/api/v1/problems/{problem['id']}/reviews",
        json={"rating": "GREEN", "reviewed_on": (date.today() + timedelta(days=1)).isoformat()},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


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


def test_web_form_creates_historical_problem(client):
    solved_on = date.today() - timedelta(days=20)
    form = client.get("/problems/new")
    assert f'value="{date.today().isoformat()}"' in form.text
    response = client.post(
        "/problems/new",
        data={
            "leetcode_id": "200",
            "title": "岛屿数量",
            "difficulty": "MEDIUM",
            "initial_rating": "GREEN",
            "solved_on": solved_on.isoformat(),
            "tags": "图, DFS",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    problem = client.get("/api/v1/problems", params={"search": "200"}).json()["items"][0]
    assert problem["next_review_at"] == (solved_on + timedelta(days=7)).isoformat()


def test_web_review_form_accepts_historical_date(client):
    solved_on = date.today() - timedelta(days=10)
    problem = create_problem(client, solved_on=solved_on.isoformat()).json()
    page = client.get(f"/review?problem_id={problem['id']}")
    assert 'name="reviewed_on"' in page.text
    assert f'min="{solved_on.isoformat()}"' in page.text
    assert 'type="button" data-rating="RED"' in page.text
    assert 'id="submit-review" disabled' in page.text
    assert "提交复习" in page.text
    response = client.post(
        f"/review/{problem['id']}",
        data={
            "rating": "GREEN",
            "reviewed_on": (solved_on + timedelta(days=1)).isoformat(),
            "duration_minutes": "18",
            "note": "历史复习记录",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    current = client.get(f"/api/v1/problems/{problem['id']}").json()
    assert current["next_review_at"] == (solved_on + timedelta(days=8)).isoformat()

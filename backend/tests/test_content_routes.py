import httpx
import respx

from tests.conftest import SUPABASE_REST
from tests.factories import auth_headers, lesson_row, phrase_row, scenario_row


def mock_get(table: str, rows: list) -> respx.Route:
    return respx.mock.get(f"{SUPABASE_REST}/{table}").mock(
        return_value=httpx.Response(200, json=rows)
    )


@respx.mock
def test_list_lessons_with_phrase_counts(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_phrases", [phrase_row(1), phrase_row(2), phrase_row(3)])

    response = client.get("/api/lessons", headers=auth_headers())

    assert response.status_code == 200
    [lesson] = response.json()
    assert lesson["slug"] == "cafe-essentials"
    assert lesson["phrase_count"] == 3


@respx.mock
def test_lesson_detail_includes_phrases(client):
    mock_get("lessons", [lesson_row()])
    mock_get("lesson_phrases", [phrase_row()])

    response = client.get("/api/lessons/cafe-essentials", headers=auth_headers())

    body = response.json()
    assert body["phrases"][0]["hangul"] == "아이스 아메리카노 주세요"


@respx.mock
def test_unknown_lesson_404(client):
    mock_get("lessons", [])
    response = client.get("/api/lessons/nope", headers=auth_headers())
    assert response.status_code == 404


@respx.mock
def test_list_scenarios(client):
    mock_get("scenarios", [scenario_row()])
    response = client.get("/api/scenarios", headers=auth_headers())
    [scenario] = response.json()
    assert scenario["slug"] == "cafe-iced-americano"
    assert "greeted" in scenario["completion_goals"]


def test_content_requires_auth(client):
    assert client.get("/api/lessons").status_code == 401

from app.services.goals import detect_goals, merge_goals

ALL_GOALS = ["greeted", "ordered_drink", "stated_size_or_temp", "paid", "said_thanks"]


def test_greeting_detected():
    assert detect_goals("안녕하세요", ALL_GOALS) == {"greeted"}


def test_iced_americano_order_hits_two_goals():
    assert detect_goals("아이스 아메리카노 주세요", ALL_GOALS) == {
        "ordered_drink",
        "stated_size_or_temp",
    }


def test_paying_by_card():
    assert detect_goals("카드로 할게요", ALL_GOALS) == {"paid"}


def test_thanks():
    assert detect_goals("감사합니다", ALL_GOALS) == {"said_thanks"}


def test_english_smalltalk_hits_nothing():
    assert detect_goals("What do you recommend?", ALL_GOALS) == set()


def test_only_candidate_goals_are_considered():
    assert detect_goals("안녕하세요 감사합니다", ["said_thanks"]) == {"said_thanks"}


def test_unknown_goal_name_never_matches():
    assert detect_goals("아무거나", ["nonexistent_goal"]) == set()


def test_merge_preserves_order_and_dedupes():
    assert merge_goals(["greeted"], {"paid", "greeted"}) == ["greeted", "paid"]

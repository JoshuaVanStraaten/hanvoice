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


# --- Goals for the four scenarios added 2026-07-12 ----------------------------

RESTAURANT = ["greeted", "ordered_food", "asked_for_water", "paid", "said_thanks"]
TAXI = ["greeted", "stated_destination", "asked_duration_or_distance", "paid", "said_thanks"]
MARKET = ["greeted", "asked_price", "asked_discount", "paid", "said_thanks"]
MEETING = ["greeted", "introduced_self", "asked_name", "said_nice_to_meet", "shared_background"]


def test_restaurant_order_and_water():
    assert detect_goals("김치찌개 주세요", RESTAURANT) == {"ordered_food"}
    assert detect_goals("물 좀 주세요", RESTAURANT) == {"asked_for_water"}
    assert detect_goals("계산할게요", RESTAURANT) == {"paid"}


def test_taxi_destination_and_duration():
    assert detect_goals("명동까지 가 주세요", TAXI) == {"stated_destination"}
    assert detect_goals("여기서 멀어요?", TAXI) == {"asked_duration_or_distance"}
    assert detect_goals("얼마나 걸려요?", TAXI) == {"asked_duration_or_distance"}


def test_market_price_and_discount():
    assert detect_goals("이거 얼마예요?", MARKET) == {"asked_price"}
    assert detect_goals("너무 비싸요. 깎아 주세요", MARKET) == {"asked_discount"}
    assert detect_goals("현금으로 할게요", MARKET) == {"paid"}


def test_first_meeting_intro_vs_asking_name():
    # Introducing yourself must not also count as asking their name.
    assert detect_goals("저는 알렉스예요", MEETING) == {"introduced_self"}
    assert detect_goals("제 이름은 알렉스예요", MEETING) == {"introduced_self"}
    assert detect_goals("이름이 뭐예요?", MEETING) == {"asked_name"}
    assert detect_goals("만나서 반가워요", MEETING) == {"said_nice_to_meet"}
    assert detect_goals("한국어 조금 해요", MEETING) == {"shared_background"}

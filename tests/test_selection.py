import importlib


def test_pick_champion_prefers_lower_metric():
    train = importlib.import_module("mlops_forecasting.train")
    results = [
        {"model_name": "a", "primary_value": 11.0},
        {"model_name": "b", "primary_value": 7.0},
    ]
    champion, challenger = train._pick_champion(results)
    assert champion["model_name"] == "b"
    assert challenger["model_name"] == "a"

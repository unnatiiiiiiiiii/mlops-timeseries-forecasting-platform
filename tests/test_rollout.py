from mlops_forecasting.pipelines.rollout import build_rollout_commands


def test_rollout_promote_commands_include_stable_and_canary_scale():
    cmds = build_rollout_commands("promote")
    joined = [" ".join(c) for c in cmds]

    assert any("deployment/forecasting-api-stable" in c for c in joined)
    assert any("deployment/forecasting-api-canary" in c for c in joined)


def test_rollout_hold_has_no_commands():
    assert build_rollout_commands("hold") == []

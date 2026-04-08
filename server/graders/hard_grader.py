def grade(initial_state: dict, final_state: dict, action_history: list) -> float:
    score = 1.0
    unhealthy_count = sum(1 for m in final_state["metrics"] if not m["healthy"])
    score -= unhealthy_count * 0.15
    for entry in action_history:
        if entry.get("result") == "harmful":
            score -= 0.25
        if entry.get("acted_on_false_positive"):
            score -= 0.15
    if unhealthy_count == 0:
        score += 0.15
    if unhealthy_count == 0 and len(action_history) <= 20:
        score += 0.1
    return max(0.0, min(1.0, score))

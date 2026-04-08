def grade(initial_state: dict, final_state: dict, action_history: list) -> float:
    score = 1.0
    unhealthy = [m for m in final_state["metrics"] if not m["healthy"]]
    if unhealthy:
        score -= 0.5
    for entry in action_history:
        result = entry.get("result", "")
        if result == "no_effect":
            score -= 0.1
        if result == "invalid":
            score -= 0.15
    if not unhealthy and len(action_history) <= 5:
        score += 0.1  # speed bonus
    return max(0.0, min(1.0, score))

## RESTART_SERVICE(service)
After: latency_ms=260, error_rate=0.02, cpu_pct=40, healthy=recompute
Result: "success"

## ROLLBACK_DEPLOY(service)
If error_rate > 0.30: same as RESTART_SERVICE, result="success"
If error_rate <= 0.30: result="no_effect"

## SCALE_UP(service, replicas)
After: cpu_pct = max(10, cpu_pct - 30), latency_ms = max(80, latency_ms - 50)
Result: "success"

## SCALE_DOWN(service, replicas)
After: cpu_pct = min(100, cpu_pct + 20)
If service was healthy before: result="harmful"
Else: result="success"

## DRAIN_QUEUE(queue)
queue: latency_ms=150, error_rate=0.01, cpu_pct=30
worker: latency_ms=200, error_rate=0.01, cpu_pct=35
Both: healthy=recompute, result="success"

## SHIFT_TRAFFIC(from_service, to_service, pct)
from_service.cpu_pct = max(10, cpu_pct - pct*0.3)
to_service.cpu_pct = cpu_pct + pct*0.2
If to_service.cpu_pct > 80 after: result="harmful"
Else: result="success"

## TOGGLE_FEATURE_FLAG(flag, value=False)
api.error_rate=0.01, api.healthy=recompute, result="success"
If value=True: result="no_effect"

## CLEAR_CACHE(service)
cache: latency_ms=120, error_rate=0.01, cpu_pct=25, healthy=True
Result: "success"

## OBSERVE(service)
No state change. Result: "no_effect"

## INVALID action_type
Result: "invalid"

## Health recompute rule
healthy = True if latency_ms < 300 AND error_rate < 0.05 AND cpu_pct < 80

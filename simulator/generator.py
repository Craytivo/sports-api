from __future__ import annotations
import copy
from typing import Any, Iterable

def perturb(scenario: dict[str,Any], **changes: Any) -> dict[str,Any]:
    """Return a deterministic variant without mutating the canonical fixture."""
    out=copy.deepcopy(scenario)
    for path,value in changes.items():
        target=out; parts=path.split('.')
        for key in parts[:-1]: target=target[key]
        target[parts[-1]]=value
    out['id']=f"{scenario['id']}__variant"; out['generated_from']=scenario['id']
    return out

def event_variant(scenario: dict[str,Any], event: dict[str,Any]) -> dict[str,Any]:
    out=copy.deepcopy(scenario); out.setdefault('events',[]).append(copy.deepcopy(event)); out['id']=f"{scenario['id']}__event_{event.get('type','unknown')}"; out['generated_from']=scenario['id']; return out

def generate_clock_variants(scenario: dict[str,Any], seconds: Iterable[int]) -> list[dict[str,Any]]:
    return [perturb(scenario, **{'game_state.seconds_remaining':s}) for s in seconds]

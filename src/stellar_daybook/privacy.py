from __future__ import annotations


def should_skip_sample(
    exe_name: str | None,
    window_title: str | None,
    cfg: dict,
) -> bool:
    pr = cfg.get("privacy") or {}
    names = {str(x).lower() for x in (pr.get("exclude_process_names") or [])}
    subs = [str(x).lower() for x in (pr.get("exclude_window_title_substrings") or [])]
    en = (exe_name or "").lower()
    wt = (window_title or "").lower()
    if en and en in names:
        return True
    for s in subs:
        if s and s in wt:
            return True
    return False

"""把 parser.ParsedPage 输出成前端用的 JSON 结构。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .parser import (
    SLOT_KEYS,
    SLOT_LABELS,
    SLOT_PERIODS,
    SLOTS_PER_DAY,
    WEEKDAY_NAMES,
    Course,
    ParsedPage,
    Room,
)


CST = timezone(timedelta(hours=8))


def _course_to_dict(c: Course | None) -> dict | None:
    if c is None:
        return None
    # 字段名简写:c=课程, l=班级(class 是关键字), t=教师 —— 减小 JSON 体积
    return {"c": c.name, "l": c.klass, "t": c.teacher}


def _room_to_dict(r: Room) -> dict:
    return {
        "id": r.id,
        "type": r.type,
        # 7 行(周一..周日) × 7 列(时段),null=空闲
        "schedule": [
            [_course_to_dict(slot) for slot in day]
            for day in r.schedule
        ],
    }


def merge_pages(pages: Iterable[ParsedPage]) -> ParsedPage:
    """把多个页面(t=1 普通 + t=2 多媒体)合并,按 id 去重。"""
    semester = ""
    seen: dict[str, Room] = {}
    for page in pages:
        if page.semester and not semester:
            semester = page.semester
        for room in page.rooms:
            seen.setdefault(room.id, room)
    rooms = sorted(seen.values(), key=lambda r: r.id)
    return ParsedPage(semester=semester, rooms=rooms)


def build(page: ParsedPage, source_urls: list[str] | None = None) -> dict:
    """生成最终的前端 JSON 结构。"""
    return {
        "meta": {
            "semester": page.semester,
            "synced_at": datetime.now(CST).isoformat(timespec="seconds"),
            "source": source_urls or [],
            "weekdays": list(WEEKDAY_NAMES),
            "slots": [
                {"key": SLOT_KEYS[i], "label": SLOT_LABELS[i], "period": SLOT_PERIODS[i]}
                for i in range(SLOTS_PER_DAY)
            ],
            "caveat": "本学期常规课表汇总,临时调课/补课/会议占用不在此列",
            "room_count": len(page.rooms),
        },
        "rooms": [_room_to_dict(r) for r in page.rooms],
    }


def write_json(data: dict, path: Path, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")

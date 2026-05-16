"""离线测试 parser:在已下载的 .research/public_classroom_t2.html 上验证。"""

import sys
from pathlib import Path

if sys.platform == "win32":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

from jxnu_classroom.parser import (
    SLOT_KEYS,
    SLOTS_PER_DAY,
    WEEK_DAYS,
    WEEKDAY_NAMES,
    parse,
)


def main() -> int:
    fixture = Path(__file__).resolve().parents[2] / ".research" / "public_classroom_t2.html"
    if not fixture.exists():
        print(f"FAIL: 找不到 fixture {fixture}", file=sys.stderr)
        return 1

    html_text = fixture.read_bytes().decode("utf-8", errors="replace")
    page = parse(html_text)

    print("== Parser smoke test ==")
    print(f"  学期      : {page.semester!r}")
    print(f"  教室总数  : {len(page.rooms)}")
    print(f"  时段配置  : {SLOTS_PER_DAY} 时段/天 × {WEEK_DAYS} 天 = {SLOTS_PER_DAY * WEEK_DAYS}")

    assert "学期" in page.semester, f"学期解析异常: {page.semester!r}"
    assert len(page.rooms) > 100, f"教室数过少: {len(page.rooms)}"

    occupied = 0
    courses_set = set()
    teachers_set = set()
    for room in page.rooms:
        assert len(room.schedule) == WEEK_DAYS
        for day in room.schedule:
            assert len(day) == SLOTS_PER_DAY
            for slot in day:
                if slot is not None:
                    occupied += 1
                    courses_set.add(slot.name)
                    teachers_set.add(slot.teacher)

    print(f"  占用格子  : {occupied}")
    print(f"  不重复课程: {len(courses_set)}")
    print(f"  不重复教师: {len(teachers_set)}")

    first = page.rooms[0]
    print(f"\n  第 1 个教室: id={first.id!r}  type={first.type!r}")
    print("  本周课表:")
    for wd, day in enumerate(first.schedule):
        for sl, course in enumerate(day):
            if course:
                print(f"    {WEEKDAY_NAMES[wd]} {SLOT_KEYS[sl]:>3s}  "
                      f"{course.name} | {course.klass} | {course.teacher}")

    # 数字对照:文件里有 4437 个 #DDEEFF td(grep -c 数据),即占用格
    # 但部分可能是 colspan 跨越的空格子,也可能我们解析时有遗漏
    print(f"\n  占用格子数 = {occupied}  (HTML 中 #DDEEFF 出现 4437 次,差异可能源于跨行 colspan)")

    print("\n[OK] parser 解析通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

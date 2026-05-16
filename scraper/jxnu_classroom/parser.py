"""把 Public_ClassRoom.aspx 的 HTML 解析为结构化数据。

页面布局:
  <table>
    <tr>  天表头(星期一..星期日)            </tr>
    <tr>  时段大表头(上午/下午/晚上)        </tr>
    <tr>  时段细表头(教室|12|3|4|5|67|89|晚) </tr>
    <tr>  W1101 (多媒体) | 49 个时段格      </tr>  ← 每个教室一行
    ...
  </table>

单元格规则:
  空闲: <td bgcolor=""><div>&nbsp;</div></td>
  占用: <td bgcolor="#DDEEFF">
          <div>&nbsp;<a Title='课程名称:xxx\n班级名称:yyy\n任课教师:zzz'>C</a></div>
        </td>
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from lxml import html as lxml_html


WEEK_DAYS = 7
SLOTS_PER_DAY = 7   # 12 / 3 / 4 / 5 / 67 / 89 / 晚上
SLOT_KEYS: tuple[str, ...] = ("12", "3", "4", "5", "67", "89", "ev")
SLOT_LABELS: tuple[str, ...] = ("1-2节", "第3节", "第4节", "第5节", "6-7节", "8-9节", "晚上")
SLOT_PERIODS: tuple[str, ...] = ("上午", "上午", "上午", "上午", "下午", "下午", "晚上")
WEEKDAY_NAMES: tuple[str, ...] = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


@dataclass
class Course:
    name: str            # 课程名称
    klass: str           # 班级名称
    teacher: str         # 任课教师


@dataclass
class Room:
    id: str              # 例如 "W1101"
    type: str            # "多媒体" / "普通"
    # 7 行(周一..周日) × 7 列(时段),None=空闲
    schedule: List[List[Optional[Course]]] = field(default_factory=list)


@dataclass
class ParsedPage:
    semester: str        # 例如 "25-26第2学期"
    rooms: List[Room]


def _extract_semester(tree) -> str:
    """从 #lblTitle 抽学期段。"""
    nodes = tree.xpath('//*[@id="lblTitle"]/text()')
    if not nodes:
        return ""
    full = nodes[0].strip()
    parts = [p.strip() for p in full.replace("　", " ").split() if p.strip()]
    for p in parts:
        if "学期" in p:
            return p
    return full


def _parse_course_title(title_attr: str) -> Optional[Course]:
    """Title 属性形如 '课程名称:xxx\\n班级名称:yyy\\n任课教师:zzz'(全角冒号)。"""
    if not title_attr:
        return None
    # 全角冒号统一成半角,便于 split
    normalized = title_attr.replace("：", ":")
    fields: dict[str, str] = {}
    for line in normalized.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fields[k.strip()] = v.strip()
    name = fields.get("课程名称", "")
    klass = fields.get("班级名称", "")
    teacher = fields.get("任课教师", "")
    if not (name or klass or teacher):
        return None
    return Course(name=name, klass=klass, teacher=teacher)


def _parse_room_row(tr_el) -> Optional[Room]:
    tds = tr_el.xpath('./td')
    if not tds:
        return None
    first = tds[0]
    # 教室行的首 td 是 width="1%"
    if first.get("width") != "1%":
        return None

    text = "".join(first.itertext()).replace("\xa0", " ").strip()
    if not text:
        return None
    parts = text.split()
    if not parts:
        return None
    room_id = parts[0]

    # 教室类型在括号里:(多媒体) 或 (普通)
    room_type = "未知"
    for p in parts[1:]:
        cleaned = p.strip("()()　 ").strip()
        if cleaned:
            room_type = cleaned
            break

    cells = tds[1:]
    expected = WEEK_DAYS * SLOTS_PER_DAY
    if len(cells) < expected:
        return None

    schedule: List[List[Optional[Course]]] = []
    idx = 0
    for _ in range(WEEK_DAYS):
        day_slots: List[Optional[Course]] = []
        for _ in range(SLOTS_PER_DAY):
            cell = cells[idx]
            idx += 1
            bg = (cell.get("bgcolor") or "").strip()
            if not bg:
                day_slots.append(None)
                continue
            a_els = cell.xpath('.//a')
            if not a_els:
                day_slots.append(None)
                continue
            title_attr = a_els[0].get("Title") or a_els[0].get("title") or ""
            day_slots.append(_parse_course_title(title_attr))
        schedule.append(day_slots)

    return Room(id=room_id, type=room_type, schedule=schedule)


def parse(html_text: str) -> ParsedPage:
    tree = lxml_html.fromstring(html_text)
    semester = _extract_semester(tree)
    rooms: List[Room] = []
    for tr in tree.xpath('//table//tr'):
        room = _parse_room_row(tr)
        if room is not None:
            rooms.append(room)
    return ParsedPage(semester=semester, rooms=rooms)

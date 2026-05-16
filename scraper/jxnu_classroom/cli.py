"""命令行入口。

子命令:
  login   测试 CAS 登录,可选保存登录后页面 HTML(目前主路径用不到,留作高级查询备用)
  sync    抓取教室教学安排页,产出前端可用的 JSON
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .builder import build, merge_pages, write_json
from .cas import CasLoginError, login
from .config import JxnuConfig
from .jwc import PUBLIC_CLASSROOM_URL, fetch_public_classroom, make_session
from .parser import parse


def _fix_windows_console_encoding() -> None:
    """Windows 控制台默认 GBK 导致中文乱码,改成 UTF-8。"""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_login(args: argparse.Namespace) -> int:
    _setup_logging(args.verbose)
    try:
        config = JxnuConfig.from_env(args.env)
    except RuntimeError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        return 2

    try:
        result = login(config, target_path=args.target)
    except CasLoginError as e:
        print(f"\n登录失败:\n  {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n意外错误: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print()
    print("=== 登录成功 ===")
    print(f"最终 URL : {result.portal_url}")
    print(f"Cookies  : {sorted(result.session_cookies.keys())}")
    print(f"页面大小 : {len(result.portal_html):,} bytes")

    if args.dump:
        dump_path = Path(args.dump).resolve()
        dump_path.write_text(result.portal_html, encoding="utf-8")
        print(f"页面已保存: {dump_path}")

    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    _setup_logging(args.verbose)
    session = make_session()
    pages = []
    sources: list[str] = []
    for t in (1, 2):
        try:
            html_text = fetch_public_classroom(t, session=session)
        except Exception as e:
            print(f"抓取 t={t} 失败: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
        pages.append(parse(html_text))
        sources.append(f"{PUBLIC_CLASSROOM_URL}?t={t}")

    merged = merge_pages(pages)
    if not merged.rooms:
        print("解析后没有任何教室,可能页面结构发生变化", file=sys.stderr)
        return 1

    data = build(merged, source_urls=sources)
    out_path = Path(args.output).resolve()
    write_json(data, out_path, pretty=args.pretty)

    print(f"✓ 已写入 {out_path}")
    print(f"  学期      : {merged.semester}")
    print(f"  教室总数  : {len(merged.rooms)}")
    occupied = sum(
        1
        for r in merged.rooms
        for day in r.schedule
        for slot in day
        if slot is not None
    )
    total_slots = len(merged.rooms) * 7 * 7
    print(f"  占用格子  : {occupied} / {total_slots} ({occupied / max(total_slots, 1):.1%})")
    print(f"  文件大小  : {out_path.stat().st_size:,} bytes")
    return 0


def main(argv: list[str] | None = None) -> int:
    _fix_windows_console_encoding()
    parser = argparse.ArgumentParser(
        prog="jxnu-classroom",
        description="江西师大空闲教室查询 - 爬虫命令行",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="测试 CAS 登录(备用,主路径不需要)")
    p_login.add_argument("--verbose", "-v", action="store_true",
                         help="打印详细日志")
    p_login.add_argument("--env", type=Path, default=None,
                         help="指定 .env 路径(默认从当前目录/scraper/ 找)")
    p_login.add_argument("--target", default="/Portal/Director.aspx?Goto=Office&Type=Student",
                         help="登录后跳转的目标(默认: 学生工作台)")
    p_login.add_argument("--dump", default=None,
                         help="把登录后页面 HTML 保存到指定文件")
    p_login.set_defaults(func=cmd_login)

    p_sync = sub.add_parser("sync", help="抓取教室教学安排页,产出 JSON")
    p_sync.add_argument("--verbose", "-v", action="store_true",
                        help="打印详细日志")
    p_sync.add_argument("--output", "-o",
                        default="../data/classrooms.json",
                        help="JSON 输出路径(默认: ../data/classrooms.json)")
    p_sync.add_argument("--pretty", action="store_true",
                        help="美化 JSON(体积大,只调试用)")
    p_sync.set_defaults(func=cmd_sync)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

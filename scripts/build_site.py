#!/usr/bin/env python3
"""构建用于 GitHub Pages 部署的站点目录，并为静态资源附加内容哈希版本号。

解决的问题
----------
GitHub Pages 对所有响应统一发送 ``Cache-Control: max-age=600``。浏览器在
10 分钟窗口内可以继续使用缓存的旧 CSS/JS；同时 HTML 与 CSS 的缓存过期时机
不同步，部署后用户可能看到「新 HTML + 旧 CSS」的混合状态。

本脚本在**部署构建阶段**（不修改仓库内的原始文件）为每个本地 CSS/JS 计算
SHA-256 内容哈希，并把 HTML 中的引用改写为带 ``?v=<hash>`` 的形式：

- 文件内容变化 -> 哈希变化 -> URL 变化 -> 浏览器必然重新下载；
- 文件内容不变 -> 哈希不变 -> URL 不变 -> 浏览器缓存继续有效。

用法
----
    python scripts/build_site.py                # 仓库根 -> .site-build/
    python scripts/build_site.py --source . --output .site-build

实现要点
--------
- 仅改写构建产物，仓库源文件零改动；改写只增删 ``?v=/&v=`` 参数，
  剥离后必须与源文件逐字节一致（内置验证）。
- 全站 HTML 为 UTF-8 + CRLF，读写均用 ``newline=''`` 精确保留原始字节。
- 两处动态加载不在 HTML 属性中，单独锚点改写：
  ``doc/_static/zh-search.js`` 内嵌 zh-search-data.js 的版本号（先改写脚本
  再统一计算哈希，保证脚本版本号对应其最终内容）；``doc/search.html`` 的
  ``Search.loadIndex("searchindex.js")``。
- 外部 CDN/第三方 URL 不改写。

GitHub Pages 的限制（见「静态资源缓存失效说明.md」）：HTML 自身仍会被缓存
最多 10 分钟（max-age=600），这一层无法通过构建脚本控制；版本号保证的是
「拿到新 HTML 后一定加载新 CSS/JS」。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

# 部署目录中需要排除的内容：版本控制、CI、测试与本地开发文件，网站运行不需要。
# 注意：仓库根目录的 *.md 被 about.html / terms.html 引用，必须保留。
EXCLUDED_DIR_NAMES = {
    ".git",
    ".github",
    ".workbuddy",
    "__pycache__",
    "node_modules",
    "scripts",          # 仅存在于仓库根目录
    "tests",            # 仅存在于仓库根目录
    "translation_review",
}
EXCLUDED_FILE_NAMES = {
    ".git",             # worktree 中 .git 是文件而非目录
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    "package.json",
    "package-lock.json",
}
EXCLUDED_FILE_SUFFIXES = {".pyc"}

# HTML 中 (href|src)="...css/js" 引用。扩展名仅匹配小写（全站已核实无大写、
# 无 %编码、无单引号、无绝对路径引用；含 scheme 的 URL 因路径段不允许 ':' 而
# 天然不匹配）。
# 分组：1=前缀(href=")  2=路径  3=.css/.js  4=现有查询串(含?)  5=右引号
REF_RE = re.compile(r'((?:href|src)\s*=\s*")([^"*?#:]*?)(\.(?:css|js))(\?[^"]*)?(")')

# 构建时需要改写的动态资源加载（按精确锚点匹配；锚点消失时构建失败，避免静默失效）。
ZH_SEARCH_DATA_ANCHOR = re.compile(r"new URL\('zh-search-data\.js',\s*ownURL\)")
SEARCHINDEX_ANCHOR = re.compile(r'Search\.loadIndex\("searchindex\.js"\)')

# 用于验证的「版本号剥离」模式：把 (?|&)v=<hash> 去掉后必须还原出原始内容。
VERSION_PARAM_RE = re.compile(r"[?&]v=[0-9a-f]{8,16}")


class BuildError(RuntimeError):
    """构建失败：输入不符合预期，必须阻止部署。"""


def read_exact(path: Path) -> str:
    """按 UTF-8 读取且不做换行符转换（全站为 CRLF，必须逐字节保留）。"""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_exact(path: Path, text: str) -> None:
    """按 UTF-8 写入且不做换行符转换。"""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _strip_version(text: str) -> str:
    """移除本脚本追加的 v= 参数（仅用于验证可还原性）。"""
    return VERSION_PARAM_RE.sub("", text)


def collect_site_files(source: Path, output: Path) -> list[Path]:
    """收集网站需要的源文件（先物化列表再创建输出目录，避免自我复制）。"""
    files: list[Path] = []
    for path in source.rglob("*"):
        if path.resolve() == output or output in path.resolve().parents:
            continue  # 输出目录本身（可能存在旧产物）
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if any(part in EXCLUDED_DIR_NAMES for part in rel.parts[:-1]):
            continue
        name = rel.parts[-1]
        if name in EXCLUDED_FILE_NAMES or path.suffix in EXCLUDED_FILE_SUFFIXES:
            continue
        files.append(path)
    return files


def copy_site(source: Path, output: Path) -> int:
    """把网站所需文件复制到输出目录（先清空旧产物），返回复制文件数。"""
    files = collect_site_files(source, output)
    if output.exists():
        try:
            shutil.rmtree(output)
        except OSError as exc:  # 权限/占用/受保护目录
            raise BuildError(
                f"无法清空旧输出目录 {output}（{exc}）。请手动删除后重试。"
            ) from exc
    output.mkdir(parents=True)
    for path in sorted(files):
        rel = path.relative_to(source)
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return len(files)


def compute_hashes(output: Path, hash_length: int) -> dict[str, str]:
    """为输出目录中所有 CSS/JS 计算内容哈希，键为相对 POSIX 路径。"""
    hashes: dict[str, str] = {}
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.suffix not in (".css", ".js"):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.relative_to(output).as_posix()] = digest[:hash_length]
    return hashes


def rewrite_dynamic_loads(output: Path, hashes: dict[str, str]) -> dict[str, int]:
    """改写两处不在 HTML 属性中的动态资源加载。

    1. ``doc/_static/zh-search.js`` 通过 ``new URL('zh-search-data.js', ownURL)``
       动态加载 15MB 中文索引。必须先改写该脚本，再计算脚本自身哈希，
       否则索引更新时脚本内容已变、HTML 中的版本号却不变，浏览器会继续用
       缓存的旧脚本并请求旧索引。
    2. ``doc/search.html`` 通过 ``Search.loadIndex("searchindex.js")`` 用
       jQuery ajax(cache:true) 加载英文搜索索引，同样需要版本号。
    """
    stats = {"zh-search-data.js": 0, "searchindex.js": 0}

    data_key = "doc/_static/zh-search-data.js"
    loader = output / "doc" / "_static" / "zh-search.js"
    if data_key in hashes and loader.exists():
        text = read_exact(loader)
        matches = ZH_SEARCH_DATA_ANCHOR.findall(text)
        if not matches:
            raise BuildError(
                "doc/_static/zh-search.js 中找不到 zh-search-data.js 加载锚点，"
                "请同步更新 scripts/build_site.py 的 ZH_SEARCH_DATA_ANCHOR。"
            )
        text = ZH_SEARCH_DATA_ANCHOR.sub(
            "new URL('zh-search-data.js?v=%s', ownURL)" % hashes[data_key], text
        )
        write_exact(loader, text)
        stats["zh-search-data.js"] = len(matches)

    index_key = "doc/searchindex.js"
    search_page = output / "doc" / "search.html"
    if index_key in hashes and search_page.exists():
        text = read_exact(search_page)
        matches = SEARCHINDEX_ANCHOR.findall(text)
        if not matches:
            raise BuildError(
                'doc/search.html 中找不到 Search.loadIndex("searchindex.js") 锚点，'
                "请同步更新 scripts/build_site.py 的 SEARCHINDEX_ANCHOR。"
            )
        text = SEARCHINDEX_ANCHOR.sub(
            'Search.loadIndex("searchindex.js?v=%s")' % hashes[index_key], text
        )
        write_exact(search_page, text)
        stats["searchindex.js"] = len(matches)
    return stats


def _versioned_url(query: str, version: str) -> str:
    """在现有查询串上追加/替换 v= 参数，返回新的查询串（含 '?'）。"""
    if not query:
        return "?v=" + version
    params = query[1:].split("&")
    for i, param in enumerate(params):
        if param.split("=", 1)[0] == "v":
            params[i] = "v=" + version
            return "?" + "&".join(params)
    return "?" + "&".join(params) + "&v=" + version


def rewrite_html_references(output: Path, hashes: dict[str, str]) -> dict[str, int]:
    """改写输出目录中全部 HTML 的本地 CSS/JS 引用，返回统计。"""
    stats = {"html_files": 0, "rewritten": 0, "skipped_external": 0, "skipped_missing": 0}

    for html_path in sorted(output.rglob("*.html")):
        rel = html_path.relative_to(output)
        html_dir = output / rel.parent

        def replace(match: re.Match[str]) -> str:
            prefix, path, ext, query, quote = match.groups()
            url = path + ext
            if url.startswith(("http:", "https:", "//", "data:")) or "://" in url:
                stats["skipped_external"] += 1
                return match.group(0)
            norm = re.sub(r"^\./+", "", url)
            candidate = (html_dir / norm).resolve()
            try:
                resolved = candidate.relative_to(output.resolve())
            except ValueError:
                stats["skipped_missing"] += 1
                return match.group(0)
            version = hashes.get(resolved.as_posix())
            if version is None:
                stats["skipped_missing"] += 1
                return match.group(0)
            new_query = _versioned_url(query or "", version)
            stats["rewritten"] += 1
            return prefix + url + new_query + quote

        text = read_exact(html_path)
        new_text = REF_RE.sub(replace, text)
        if new_text != text:
            write_exact(html_path, new_text)
        stats["html_files"] += 1
    return stats


def verify_build(source: Path, output: Path) -> dict[str, int]:
    """验证构建产物：

    1. 每个 HTML 剥离版本号后与源文件逐字节一致（正文零改动）；
    2. 版本化引用都指向输出目录内实际存在的文件；
    3. zh-search.js 剥离版本号后与源文件一致。
    """
    stats = {"html_checked": 0, "html_mismatch": 0, "refs_resolved": 0, "refs_missing": 0}
    output_resolved = output.resolve()

    for html_path in sorted(output.rglob("*.html")):
        rel = html_path.relative_to(output).as_posix()
        built = read_exact(html_path)
        original = read_exact(source / rel)
        # search.html 的 Search.loadIndex 属于脚本内改写，剥离后同样应还原。
        if _strip_version(built) != original:
            stats["html_mismatch"] += 1
            if stats["html_mismatch"] <= 5:
                print(f"  内容不一致: {rel}", file=sys.stderr)
        stats["html_checked"] += 1

        for match in REF_RE.finditer(built):
            url = match.group(2) + match.group(3)
            if url.startswith(("http:", "https:", "//", "data:")) or "://" in url:
                continue
            query = match.group(4) or ""
            if not re.search(r"[?&]v=[0-9a-f]{8,16}", query):
                continue  # 未版本化（外部/缺失目标，改写阶段已如实跳过）
            norm = re.sub(r"^\./+", "", url)
            candidate = (output / Path(rel).parent / norm).resolve()
            try:
                resolved = candidate.relative_to(output_resolved).as_posix()
            except ValueError:
                stats["refs_missing"] += 1
                continue
            if (output / resolved).exists():
                stats["refs_resolved"] += 1
            else:
                stats["refs_missing"] += 1

    loader_rel = "doc/_static/zh-search.js"
    loader_out = output / loader_rel
    loader_src = source / loader_rel
    if loader_out.exists() and loader_src.exists():
        if _strip_version(read_exact(loader_out)) != read_exact(loader_src):
            raise BuildError("doc/_static/zh-search.js 剥离版本号后与源文件不一致。")

    if stats["html_mismatch"]:
        raise BuildError(f"{stats['html_mismatch']} 个 HTML 剥离版本号后与源文件不一致。")
    if stats["refs_missing"]:
        raise BuildError(f"{stats['refs_missing']} 个版本化引用指向不存在的文件。")
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", default=".", help="仓库根目录（默认当前目录）")
    parser.add_argument("--output", default=".site-build", help="部署产物目录")
    parser.add_argument("--hash-length", type=int, default=10,
                        help="哈希版本号长度（默认 10 个十六进制字符）")
    parser.add_argument("--manifest",
                        help="可选：把版本清单写入该 JSON 文件（不要放在输出目录内）")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    # 输出目录位于源目录内是正常用法（如仓库根的 .site-build/），收集文件时会排除它；
    # 但输出目录等于源目录、或输出目录包含源目录，会清空源码或造成自我复制。
    if output == source or output in source.parents:
        print("错误：输出目录不能等于源目录，也不能包含源目录。", file=sys.stderr)
        return 2
    if output.exists() and (output / ".git").exists():
        print(f"错误：输出目录 {output} 看起来是一个 Git 仓库，拒绝清空。", file=sys.stderr)
        return 2

    print(f"[1/5] 复制站点文件 {source} -> {output}")
    copied = copy_site(source, output)
    print(f"      复制 {copied} 个文件")

    print("[2/5] 预改写动态资源加载（zh-search.js 内嵌索引版本号）")
    # 先改写 zh-search.js（其内容将包含 zh-search-data.js 的哈希），
    # 再统一计算哈希，保证 HTML 引用的版本号对应脚本最终内容。
    pre_hashes = compute_hashes(output, args.hash_length)
    dynamic_stats = rewrite_dynamic_loads(output, pre_hashes)

    print("[3/5] 计算 CSS/JS 内容哈希")
    hashes = compute_hashes(output, args.hash_length)
    print(f"      {len(hashes)} 个 CSS/JS 文件")

    print("[4/5] 改写 HTML 资源引用")
    stats = rewrite_html_references(output, hashes)
    print(
        f"      HTML {stats['html_files']} 个；改写引用 {stats['rewritten']} 处；"
        f"跳过外部链接 {stats['skipped_external']} 处；跳过缺失目标 {stats['skipped_missing']} 处"
    )
    print(
        f"      动态加载改写：zh-search-data.js x{dynamic_stats['zh-search-data.js']}，"
        f"searchindex.js x{dynamic_stats['searchindex.js']}"
    )

    print("[5/5] 验证构建产物")
    verify_stats = verify_build(source, output)
    print(
        f"      HTML 校验 {verify_stats['html_checked']} 个全部可还原；"
        f"版本化引用 {verify_stats['refs_resolved']} 处全部有效"
    )

    if args.manifest:
        manifest = {
            "hash_length": args.hash_length,
            "versioned_files": len(hashes),
            "rewritten_references": stats["rewritten"],
            "hashes": hashes,
        }
        Path(args.manifest).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"      版本清单已写入 {args.manifest}")

    print("构建完成。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print(f"构建失败：{exc}", file=sys.stderr)
        sys.exit(1)

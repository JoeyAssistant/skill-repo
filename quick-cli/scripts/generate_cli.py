#!/usr/bin/env python3
"""
CLI 生成器 - 根据 dataclass 定义生成 CRUD CLI 脚本

用法:
    python generate_cli.py --schema <schema_file> --output <output_dir>
"""
import argparse
import ast
import re
import sys
import shutil
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any, Optional


@dataclass
class FieldInfo:
    name: str
    type_name: str
    default: Any = None
    has_default: bool = False
    is_required: bool = True
    is_enum: bool = False
    enum_values: list = dataclass_field(default_factory=list)


@dataclass
class DataClassInfo:
    name: str
    fields: list = dataclass_field(default_factory=list)
    enums: dict = dataclass_field(default_factory=dict)


def parse_dataclass_file(file_path: str) -> DataClassInfo:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    # 提取枚举
    enums = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Enum":
                    values = []
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    values.append(target.id)
                    if values:
                        enums[node.name] = values

    info = DataClassInfo(name="")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            has_dataclass = any(
                (isinstance(d, ast.Name) and d.id == "dataclass") or
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
                for d in node.decorator_list
            )
            if has_dataclass:
                info.name = node.name
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        f_name = item.target.id
                        f_type = ast.unparse(item.annotation) if item.annotation else "Any"
                        has_default = item.value is not None
                        f_default = ast.unparse(item.value) if has_default else None

                        is_enum = any(en in f_type for en in enums)
                        enum_values = []
                        for en, vals in enums.items():
                            if en in f_type:
                                enum_values = vals
                                break

                        info.fields.append(FieldInfo(
                            name=f_name, type_name=f_type, default=f_default,
                            has_default=has_default, is_required=not has_default,
                            is_enum=is_enum, enum_values=enum_values
                        ))
                break
    info.enums = enums
    return info


def generate_cli_script(info: DataClassInfo) -> str:
    name = info.name
    cli_name = name.lower()
    data_file = f"{cli_name}_data.json"

    # 枚举定义
    enum_defs = ""
    for en, vals in info.enums.items():
        enum_defs += f"\nclass {en}(str, Enum):\n"
        for v in vals:
            enum_defs += f'    {v} = "{v.lower()}"\n'

    # 参数生成
    add_params, list_params, update_params = [], [], []
    record_fields, filter_conds, update_fields = [], [], []

    for f in info.fields:
        fn = f.name.replace("_", "-")
        cli_type = f.type_name if f.is_enum else {"str": "str", "int": "int", "float": "float", "bool": "bool"}.get(f.type_name, "str")

        # add
        default_val = f.default if f.default else '""'
        if f.is_required:
            add_params.append(f'    {f.name}: {cli_type} = Option(..., help="{f.name}"),')
        else:
            add_params.append(f'    {f.name}: {cli_type} = Option({default_val}, help="{f.name}"),')

        # list
        list_params.append(f'    {f.name}: Optional[{cli_type}] = Option(None, help="按 {f.name} 过滤"),')

        # update
        update_params.append(f'    {f.name}: Optional[{cli_type}] = Option(None, help="{f.name}"),')

        # record
        if f.is_enum:
            record_fields.append(f'        "{f.name}": {f.name}.value if isinstance({f.name}, {cli_type}) else {f.name},')
        else:
            record_fields.append(f'        "{f.name}": {f.name},')

        # filter
        if f.is_enum:
            filter_conds.append(f'        ("{f.name}", {f.name}.value if {f.name} else None),')
        else:
            filter_conds.append(f'        ("{f.name}", {f.name}),')

        # update dict
        if f.is_enum:
            update_fields.append(f'        "{f.name}": {f.name}.value if {f.name} else None,')
        else:
            update_fields.append(f'        "{f.name}": {f.name},')

    return f'''#!/usr/bin/env python3
"""{name} CLI - CRUD 命令行工具"""
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum

try:
    import typer
    from typer import Option, Argument
except ImportError:
    print("Error: typer not installed. Run: pip install typer")
    sys.exit(1)
{enum_defs}
DATA_FILE = Path(__file__).parent / "{data_file}"

def load_data() -> list[dict]:
    if not DATA_FILE.exists(): return []
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_data(data: list[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_by_id(data: list[dict], id: str) -> Optional[dict]:
    for item in data:
        if item.get("id") == id: return item
    return None

def filter_data(data: list[dict], filters: list[tuple]) -> list[dict]:
    result = data
    for key, value in filters:
        if value is not None:
            result = [item for item in result if str(item.get(key)) == str(value)]
    return result

def output_json(data: Any):
    print(json.dumps(data, ensure_ascii=False, default=str))

app = typer.Typer(help="{name} 管理工具")

@app.command()
def add(
{chr(10).join(add_params)}
    data_file: Optional[str] = Option(None, "--data-file", help="数据文件路径"),
):
    global DATA_FILE
    if data_file: DATA_FILE = Path(data_file)
    data = load_data()
    new_record = {{
        "id": str(uuid.uuid4()),
{chr(10).join(record_fields)}
        "created_at": datetime.now().isoformat(),
    }}
    data.append(new_record)
    save_data(data)
    output_json(new_record)

@app.command()
def list(
{chr(10).join(list_params)}
    data_file: Optional[str] = Option(None, "--data-file", help="数据文件路径"),
):
    global DATA_FILE
    if data_file: DATA_FILE = Path(data_file)
    if not DATA_FILE.exists():
        output_json([])
        return
    data = load_data()
    filters = [
{chr(10).join(filter_conds)}
    ]
    output_json(filter_data(data, filters))

@app.command()
def get(
    id: str = Argument(..., help="{name} ID"),
    data_file: Optional[str] = Option(None, "--data-file", help="数据文件路径"),
):
    global DATA_FILE
    if data_file: DATA_FILE = Path(data_file)
    if not DATA_FILE.exists():
        print("Error: Data file not found", file=sys.stderr)
        raise typer.Exit(1)
    record = find_by_id(load_data(), id)
    if record is None:
        print(f"Error: {name} with id '{{id}}' not found", file=sys.stderr)
        raise typer.Exit(1)
    output_json(record)

@app.command()
def update(
    id: str = Argument(..., help="{name} ID"),
{chr(10).join(update_params)}
    data_file: Optional[str] = Option(None, "--data-file", help="数据文件路径"),
):
    global DATA_FILE
    if data_file: DATA_FILE = Path(data_file)
    if not DATA_FILE.exists():
        print("Error: Data file not found", file=sys.stderr)
        raise typer.Exit(1)
    data = load_data()
    record = find_by_id(data, id)
    if record is None:
        print(f"Error: {name} with id '{{id}}' not found", file=sys.stderr)
        raise typer.Exit(1)
    updates = {{
{chr(10).join(update_fields)}
    }}
    for key, value in updates.items():
        if value is not None: record[key] = value
    record["updated_at"] = datetime.now().isoformat()
    save_data(data)
    output_json(record)

@app.command()
def delete(
    id: str = Argument(..., help="{name} ID"),
    data_file: Optional[str] = Option(None, "--data-file", help="数据文件路径"),
):
    global DATA_FILE
    if data_file: DATA_FILE = Path(data_file)
    if not DATA_FILE.exists():
        print("Error: Data file not found", file=sys.stderr)
        raise typer.Exit(1)
    data = load_data()
    record = find_by_id(data, id)
    if record is None:
        print(f"Error: {name} with id '{{id}}' not found", file=sys.stderr)
        raise typer.Exit(1)
    data.remove(record)
    save_data(data)
    output_json(record)

if __name__ == "__main__":
    app()
'''


def main():
    parser = argparse.ArgumentParser(description="根据 dataclass 生成 CRUD CLI")
    parser.add_argument("--schema", required=True, help="dataclass 文件路径")
    parser.add_argument("--output", default=".", help="输出目录")
    parser.add_argument("--name", help="自定义 CLI 名称")
    args = parser.parse_args()

    info = parse_dataclass_file(args.schema)
    if not info.name:
        print("Error: 未找到 @dataclass 定义", file=sys.stderr)
        sys.exit(1)

    print(f"解析到 dataclass: {info.name}")
    print(f"字段: {[f.name for f in info.fields]}")

    cli_script = generate_cli_script(info)
    cli_name = args.name or info.name.lower()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    cli_file = output_dir / f"{cli_name}.py"
    with open(cli_file, "w", encoding="utf-8") as f:
        f.write(cli_script)
    print(f"生成 CLI: {cli_file}")

    shutil.copy(args.schema, output_dir / "schema.py")
    print(f"复制 schema: {output_dir / 'schema.py'}")

    print(f"\n使用: cd {output_dir} && python {cli_name}.py --help")


if __name__ == "__main__":
    main()

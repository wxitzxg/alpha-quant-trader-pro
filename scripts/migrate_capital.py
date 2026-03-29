#!/usr/bin/env python3
"""
资金账户数据迁移脚本

迁移内容：
1. 为 cash_balance 表添加 initial_capital 字段
2. 创建 capital_adjustments 表

使用方式：
    # 迁移（默认 initial_capital = 0）
    python scripts/migrate_capital.py

    # 迁移并设置初始资金
    python scripts/migrate_capital.py --initial-capital 100000

    # 回滚
    python scripts/migrate_capital.py --rollback
"""

import os
import sys
import argparse
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from common.config import get_config


def get_db_url() -> str:
    """获取数据库连接 URL"""
    config = get_config()
    return config.database.url


def get_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    return create_engine(db_url)


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    sql = text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND column_name = '{column_name}'
    """)
    with engine.connect() as conn:
        result = conn.execute(sql)
        return result.fetchone() is not None


def check_table_exists(engine, table_name: str) -> bool:
    """检查表是否存在"""
    sql = text(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = '{table_name}'
    """)
    with engine.connect() as conn:
        result = conn.execute(sql)
        return result.fetchone() is not None


def migrate(initial_capital: float = 0):
    """
    执行迁移

    Args:
        initial_capital: 初始资金（默认 0）
    """
    engine = get_engine()

    print("=" * 60)
    print("资金账户数据迁移")
    print("=" * 60)

    # 1. 检查并添加 initial_capital 字段
    print("\n[Step 1] 检查 cash_balance 表...")

    if check_column_exists(engine, 'cash_balance', 'initial_capital'):
        print("  ✓ initial_capital 字段已存在，跳过")
    else:
        print("  + 添加 initial_capital 字段...")
        sql = text("""
            ALTER TABLE cash_balance
            ADD COLUMN initial_capital DECIMAL(15, 4) NOT NULL DEFAULT 0
        """)
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        print("  ✓ initial_capital 字段添加成功")

    # 2. 创建 capital_adjustments 表
    print("\n[Step 2] 检查 capital_adjustments 表...")

    if check_table_exists(engine, 'capital_adjustments'):
        print("  ✓ capital_adjustments 表已存在，跳过")
    else:
        print("  + 创建 capital_adjustments 表...")
        sql = text("""
            CREATE TABLE capital_adjustments (
                id SERIAL PRIMARY KEY,
                amount DECIMAL(15, 4) NOT NULL,
                adjustment_type VARCHAR(20) NOT NULL,
                reason VARCHAR(200),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        print("  ✓ capital_adjustments 表创建成功")

        # 创建索引
        sql = text("""
            CREATE INDEX idx_capital_adjustments_created_at
            ON capital_adjustments (created_at DESC)
        """)
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        print("  ✓ 索引创建成功")

    # 3. 设置初始资金（如果指定且当前为 0）
    print("\n[Step 3] 检查初始资金...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT initial_capital FROM cash_balance WHERE id = 1"))
        row = result.fetchone()

        if row is None:
            # 没有记录，创建一条
            print("  + 创建 cash_balance 记录...")
            sql = text("""
                INSERT INTO cash_balance (id, amount, initial_capital, version)
                VALUES (1, 0, :initial_capital, 0)
                ON CONFLICT (id) DO NOTHING
            """)
            conn.execute(sql, {"initial_capital": initial_capital})
            conn.commit()
            print(f"  ✓ 初始资金设置为: ¥{initial_capital:,.2f}")
        elif row[0] == 0 and initial_capital > 0:
            # 当前为 0，更新
            print(f"  + 更新初始资金为: ¥{initial_capital:,.2f}")
            conn.execute(text("UPDATE cash_balance SET initial_capital = :val WHERE id = 1"), {"val": initial_capital})
            conn.commit()
        else:
            print(f"  ✓ 当前初始资金: ¥{row[0]:,.2f}")

    # 4. 验证
    print("\n[Step 4] 验证迁移结果...")

    with engine.connect() as conn:
        # 验证字段
        result = conn.execute(text("SELECT amount, initial_capital FROM cash_balance WHERE id = 1"))
        row = result.fetchone()
        if row:
            print(f"  ✓ cash_balance: amount={row[0]}, initial_capital={row[1]}")
        else:
            print("  ✓ cash_balance: 无记录（新账户）")

        # 验证表
        result = conn.execute(text("SELECT COUNT(*) FROM capital_adjustments"))
        count = result.fetchone()[0]
        print(f"  ✓ capital_adjustments: {count} 条记录")

    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


def rollback():
    """回滚迁移"""
    engine = get_engine()

    print("=" * 60)
    print("资金账户数据回滚")
    print("=" * 60)

    # 1. 删除 capital_adjustments 表
    print("\n[Step 1] 删除 capital_adjustments 表...")

    if check_table_exists(engine, 'capital_adjustments'):
        sql = text("DROP TABLE IF EXISTS capital_adjustments")
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        print("  ✓ capital_adjustments 表已删除")
    else:
        print("  ✓ capital_adjustments 表不存在，跳过")

    # 2. 删除 initial_capital 字段
    print("\n[Step 2] 删除 initial_capital 字段...")

    if check_column_exists(engine, 'cash_balance', 'initial_capital'):
        sql = text("ALTER TABLE cash_balance DROP COLUMN IF EXISTS initial_capital")
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        print("  ✓ initial_capital 字段已删除")
    else:
        print("  ✓ initial_capital 字段不存在，跳过")

    print("\n" + "=" * 60)
    print("回滚完成！")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="资金账户数据迁移脚本")
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=0,
        help="初始资金（默认 0）"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移"
    )

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate(args.initial_capital)


if __name__ == "__main__":
    main()

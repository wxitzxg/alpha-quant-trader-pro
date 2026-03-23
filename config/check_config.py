#!/usr/bin/env python3
"""
配置检查脚本
验证环境变量配置是否正确
"""

import os
import sys

def check_files():
    """检查必要文件是否存在"""
    print("=== 1. 检查文件存在性 ===")
    files = {
        '.env.example': '环境变量模板',
        '.env': '开发环境配置',
        '.env.test': '测试环境配置',
        'config/database.yaml': '数据库配置',
        'config/config.yaml': '统一配置'
    }
    
    all_exist = True
    for file, desc in files.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"  {status} {file} ({desc})")
        if not exists:
            all_exist = False
    
    return all_exist

def check_gitignore():
    """检查 Git 忽略规则"""
    print("\n=== 2. 检查 Git 忽略规则 ===")
    sensitive_files = ['.env', '.env.test', '.env.production']
    
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
    
    all_ignored = True
    for file in sensitive_files:
        if file in gitignore:
            print(f"  ✅ {file} 已被忽略")
        else:
            print(f"  ❌ {file} 未被忽略")
            all_ignored = False
    
    return all_ignored

def check_config_content():
    """检查配置内容"""
    print("\n=== 3. 检查配置内容 ===")
    
    # 检查 database.yaml 中 URL 是否为空
    with open('config/database.yaml', 'r') as f:
        content = f.read()
        if 'url: ""' in content or "url: ''" in content:
            print("  ✅ database.yaml 中数据库 URL 为空（安全）")
        else:
            print("  ⚠️  database.yaml 中可能包含硬编码的数据库 URL")
    
    # 检查 .env 和 .env.test 是否使用不同数据库
    with open('.env', 'r') as f:
        dev_content = f.read()
    with open('.env.test', 'r') as f:
        test_content = f.read()
    
    if 'alpha_quant' in dev_content:
        print("  ✅ .env 使用开发数据库 (alpha_quant)")
    else:
        print("  ❌ .env 未使用开发数据库")
    
    if 'test_stock_market' in test_content:
        print("  ✅ .env.test 使用测试数据库 (test_stock_market)")
    else:
        print("  ❌ .env.test 未使用测试数据库")

def check_env_loading():
    """检查环境变量加载"""
    print("\n=== 4. 检查环境变量加载 ===")
    
    # 检查 .env 文件是否包含 DATABASE_URL
    with open('.env', 'r') as f:
        content = f.read()
        if 'DATABASE_URL' in content:
            print("  ✅ .env 包含 DATABASE_URL")
        else:
            print("  ❌ .env 不包含 DATABASE_URL")
    
    # 测试加载
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print(f"  ✅ 环境变量已加载: {db_url[:50]}...")
    else:
        print("  ❌ 环境变量未加载")

if __name__ == "__main__":
    print("🚀 配置检查开始...\n")
    
    all_ok = True
    all_ok &= check_files()
    all_ok &= check_gitignore()
    check_config_content()
    check_env_loading()
    
    print("\n" + "="*50)
    if all_ok:
        print("✅ 所有检查通过！")
    else:
        print("⚠️  部分检查未通过，请查看上面的警告")
    print("="*50)

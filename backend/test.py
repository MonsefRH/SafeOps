# test.py

import os
import subprocess

# 🔴 Hardcoded secret
API_KEY = "sk_test_1234567890abcdef"

# 🔴 Dangerous call - command injection risk
def run_command(cmd):
    os.system(cmd)

# 🔴 Using subprocess without sanitization
def unsafe_subprocess(user_input):
    subprocess.call(f"ls {user_input}", shell=True)

# ✅ Safe example
def greet(name):
    print(f"Hello, {name}!")

# 🔴 SQL injection risk
def login(cursor, username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)

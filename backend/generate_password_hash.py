"""
Run this once to turn your chosen password into a bcrypt hash, then
paste the result into backend/.env as AUTH_PASSWORD_HASH.

Usage:
    python generate_password_hash.py
"""

import getpass
import bcrypt

if __name__ == "__main__":
    password = getpass.getpass("Choose a password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords didn't match, try again.")
    else:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        print("\nAdd this line to backend/.env:\n")
        print(f"AUTH_PASSWORD_HASH={hashed}")
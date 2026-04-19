#!/usr/bin/env python3
"""
Password Encryption Utility
Demonstrates the same password hashing used in the Bibliotheca authentication system.
Uses Werkzeug security functions for secure password hashing and verification.
"""

from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Hash a password using Werkzeug's generate_password_hash.
    This creates a secure hash with salt that can be stored in the database.

    Args:
        password (str): The plain text password to hash

    Returns:
        str: The hashed password string
    """
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """
    Verify a password against its hash using Werkzeug's check_password_hash.

    Args:
        hashed_password (str): The hashed password from the database
        password (str): The plain text password to verify

    Returns:
        bool: True if password matches, False otherwise
    """
    return check_password_hash(hashed_password, password)

def demonstrate_password_hashing():
    """
    Demonstration of password hashing and verification.
    """
    print("=== Password Encryption Demonstration ===\n")

    # Example passwords
    test_passwords = [
        "password123",
        "mySecurePass!2024",
        "librarian123",  # Same as used in seed.py
        "adminPassword"
    ]

    print("Hashing passwords:")
    print("-" * 50)

    hashed_passwords = {}
    for password in test_passwords:
        hashed = hash_password(password)
        hashed_passwords[password] = hashed
        print(f"Password: '{password}'")
        print(f"Hash: {hashed}")
        print()

    print("Verifying passwords:")
    print("-" * 50)

    # Test correct passwords
    for password, hashed in hashed_passwords.items():
        is_valid = verify_password(hashed, password)
        print(f"Password: '{password}' -> Valid: {is_valid}")

    print()

    # Test incorrect passwords
    print("Testing incorrect passwords:")
    print("-" * 30)

    test_cases = [
        ("password123", "wrongpassword"),
        ("librarian123", "librarian124"),
        ("mySecurePass!2024", "mysecurepass!2024")  # Case sensitive
    ]

    for correct_password, wrong_password in test_cases:
        hashed = hashed_passwords[correct_password]
        is_valid = verify_password(hashed, wrong_password)
        print(f"Correct: '{correct_password}', Attempted: '{wrong_password}' -> Valid: {is_valid}")

if __name__ == "__main__":
    print(hash_password("password001") ) # Example of hashing the librarian password for use in seed.py
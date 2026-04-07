"""This module provides functions for hashing and verifying sensitive data, such as user passwords, in the PayU Authentication Service. It utilizes the Passlib library with the Argon2 hashing algorithm to securely hash plaintext data and verify it against stored hashed values. The `hash_data` function takes a plaintext string and returns a securely hashed version of it, while the `verify_data` function compares a plaintext string with a hashed version to check for a match. By using these functions, we can enhance the security of user data by ensuring that sensitive information is not stored in plaintext and can be safely verified during authentication processes."""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_data(data: str) -> str:
    """Hash the provided data using the password context. This function takes a plaintext string (e.g., a user's password) and returns a securely hashed version of that string using the Argon2 hashing algorithm. By hashing sensitive data before storing it in the database, we can enhance security and protect against potential data breaches, as the original plaintext data cannot be easily retrieved from the hashed version.    Args:    data: The plaintext string to be hashed.    Returns:   A securely hashed version of the input data."""
    return pwd_context.hash(data)


def verify_data(plain_data: str, hashed_data: str) -> bool:
    """Verify that the provided plain data matches the hashed data. This function uses the password context to compare the plain data with the hashed version, returning True if they match and False otherwise. This is commonly used for verifying passwords during authentication processes, ensuring that the provided password matches the stored hashed password without exposing the actual password in plaintext.    Args:    plain_data: The plaintext data to be verified (e.g., a user's input password).    hashed_data: The hashed version of the data to compare against (e.g., the stored hashed password).    Returns:   A boolean value indicating whether the plain data matches the hashed data."""
    return pwd_context.verify(plain_data, hashed_data)

from app.security import hash_password,verify_password
def test_password_hashing():
    hashed=hash_password("a-long-test-password")
    assert hashed!="a-long-test-password" and verify_password("a-long-test-password",hashed) and not verify_password("wrong",hashed)

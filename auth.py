from supabase_client import supabase

def signup(email, password):
    res = supabase.auth.sign_up({"email": email, "password": password})
    if res.user:
        print("✅ Signup successful. Check your email to confirm.")
    else:
        print("❌ Signup failed:", res.get("error") or res)

def login(email, password):
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if res.session:
        print("✅ Login successful.")
        return res.user.id
    else:
        print("❌ Login failed.")
        return None

def logout():
    supabase.auth.sign_out()
    print("✅ Logged out.")

def reset_password(email):
    supabase.auth.reset_password_email(email)
    print("🔁 Password reset email sent.")

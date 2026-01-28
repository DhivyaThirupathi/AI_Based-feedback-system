from auth import create_user

success, msg = create_user(
    username="superadmin",
    password="admin123",
    email="superadmin@example.com",
    role="super_admin",
    assigned_districts=["ALL"],
    role_category="All"
)

print(msg)

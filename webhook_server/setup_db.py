"""
Database setup script

Bu scriptni serverni birinchi marta ishga tushirishdan oldin ishga tushiring:
    python -m webhook_server.setup_db
"""

from database import init_db

if __name__ == "__main__":
    print("🔧 Setting up database...")
    init_db()
    print("✅ Database setup completed!")
    print("\n📝 Database file: payments.db")
    print("📋 Tables created:")
    print("   - orders (Order table)")
    print("   - click_transactions (PayTechUZ)")
    print("   - payme_transactions (PayTechUZ)")

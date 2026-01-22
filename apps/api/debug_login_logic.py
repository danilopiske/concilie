from app.core.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository
from app.core import security

try:
    db = SessionLocal()
    repo = UsuarioRepository(db)
    user = repo.obter_por_usuario("admin")
    
    if user:
        print(f"User found: {user.usuario}")
        print(f"Stored Password (First 5 chars): {user.senha[:5] if user.senha else 'None'}...")
        print(f"Is bcrypt? {user.senha.startswith('$') if user.senha else False}")
        
        try:
            is_valid = security.verify_password("1234", user.senha)
            print(f"Verify '1234': {is_valid}")
        except Exception as e:
            print(f"Verify Error: {e}")
            
            # Check if plain text match works
            if user.senha == "1234":
                print("Plain text match confirmed. Legacy password.")

    else:
        print("User admin not found")

except Exception as e:
    print(f"Global Error: {e}")
finally:
    db.close()

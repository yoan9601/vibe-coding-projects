from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TelegramSetup, TwoFactorVerify, Token
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user
from app.services.telegram import telegram_service
from app.services.cache import cache_service
from app.services.audit import audit_service
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration
    audit_service.log_action(
        db=db,
        user=new_user,
        action="register",
        entity_type="user",
        entity_id=new_user.id
    )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with username and password"""
    
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if 2FA is enabled
    if user.is_2fa_enabled and user.telegram_id:
        # Generate and send 2FA code
        code = telegram_service.generate_code()
        
        # Store code in cache (expires in 5 minutes)
        cache_key = f"2fa:{user.id}"
        cache_service.set(cache_key, code, expire=300)
        
        # Send code via Telegram
        success = await telegram_service.send_code(user.telegram_id, code)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send 2FA code"
            )
        
        # Return token that indicates 2FA is required
        temp_token = create_access_token(
            data={"sub": user.username, "2fa_pending": True},
            expires_delta=timedelta(minutes=5)
        )
        
        return Token(access_token=temp_token, requires_2fa=True)
    
    # No 2FA, create regular access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Log login
    audit_service.log_action(
        db=db,
        user=user,
        action="login",
        entity_type="user",
        entity_id=user.id
    )
    
    return Token(access_token=access_token)


@router.post("/verify-2fa", response_model=Token)
async def verify_2fa(
    verification: TwoFactorVerify,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA code and get final access token"""
    
    # Get code from cache
    cache_key = f"2fa:{user.id}"
    stored_code = cache_service.get(cache_key)
    
    if not stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA code expired or not found"
        )
    
    # Verify code
    if verification.code != stored_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )
    
    # Delete used code
    cache_service.delete(cache_key)
    
    # Create final access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Log successful 2FA
    audit_service.log_action(
        db=db,
        user=user,
        action="2fa_verified",
        entity_type="user",
        entity_id=user.id
    )
    
    return Token(access_token=access_token)


@router.post("/enable-2fa", response_model=UserResponse)
async def setup_telegram(
    telegram_data: TelegramSetup,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup Telegram 2FA for current user"""
    
    # Verify chat ID
    is_valid = await telegram_service.verify_chat_id(telegram_data.telegram_chat_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram chat ID"
        )
    
    # Update user
    user.telegram_id = telegram_data.telegram_chat_id
    user.is_2fa_enabled = True
    
    db.commit()
    db.refresh(user)
    
    # Log setup
    audit_service.log_action(
        db=db,
        user=user,
        action="setup_2fa",
        entity_type="user",
        entity_id=user.id,
        details={"method": "telegram"}
    )
    
    return user


@router.post("/disable-2fa", response_model=UserResponse)
async def disable_2fa(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for current user"""
    
    user.is_2fa_enabled = False
    
    db.commit()
    db.refresh(user)
    
    # Log disable
    audit_service.log_action(
        db=db,
        user=user,
        action="disable_2fa",
        entity_type="user",
        entity_id=user.id
    )
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return user

@router.post("/change-password")
async def change_password(
    password_data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required"
        )
    
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.hashed_password = hash_password(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}
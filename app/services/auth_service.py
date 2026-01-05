"""
認證服務
LINE Login 整合 + JWT Token 管理
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging
import secrets

from app.config import settings
from app.models.user import User
from app.models.user_settings import UserIndicatorSettings, UserAlertSettings, UserIndicatorParams

logger = logging.getLogger(__name__)

# JWT 設定
JWT_ALGORITHM = "HS256"


class AuthService:
    """認證服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== LINE Login ====================
    
    def get_line_auth_url(self, state: str = None) -> str:
        """
        取得 LINE 授權 URL
        
        Args:
            state: 防 CSRF 的隨機字串
            
        Returns:
            LINE 授權頁面 URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
            "redirect_uri": settings.LINE_LOGIN_CALLBACK_URL,
            "state": state,
            "scope": "profile openid email",
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://access.line.me/oauth2/v2.1/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        用 authorization code 換取 access token
        
        Args:
            code: LINE 回傳的 authorization code
            
        Returns:
            包含 access_token, id_token 等的字典
        """
        url = "https://api.line.me/oauth2/v2.1/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINE_LOGIN_CALLBACK_URL,
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
            "client_secret": settings.LINE_LOGIN_CHANNEL_SECRET,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"LINE token 交換失敗: {e}")
            return None
    
    async def get_line_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        用 access token 取得 LINE 用戶資料
        
        Args:
            access_token: LINE access token
            
        Returns:
            用戶資料字典 (userId, displayName, pictureUrl, statusMessage)
        """
        url = "https://api.line.me/v2/profile"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"取得 LINE 用戶資料失敗: {e}")
            return None
    
    async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        驗證 LINE ID Token
        
        Args:
            id_token: LINE ID Token
            
        Returns:
            解碼後的 token payload
        """
        url = "https://api.line.me/oauth2/v2.1/verify"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "id_token": id_token,
                        "client_id": settings.LINE_LOGIN_CHANNEL_ID,
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"LINE ID Token 驗證失敗: {e}")
            return None
    
    # ==================== 用戶管理 ====================
    
    def get_user_by_line_id(self, line_user_id: str) -> Optional[User]:
        """根據 LINE User ID 取得用戶"""
        stmt = select(User).where(User.line_user_id == line_user_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 取得用戶"""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def create_user(
        self,
        line_user_id: str,
        display_name: str = None,
        picture_url: str = None,
        email: str = None,
    ) -> User:
        """
        建立新用戶
        
        會自動建立預設設定
        """
        user = User(
            line_user_id=line_user_id,
            display_name=display_name,
            picture_url=picture_url,
            email=email,
        )
        self.db.add(user)
        self.db.flush()  # 取得 user.id
        
        # 建立預設設定
        indicator_settings = UserIndicatorSettings.create_default(user.id)
        alert_settings = UserAlertSettings.create_default(user.id)
        params = UserIndicatorParams.create_default(user.id)
        
        self.db.add(indicator_settings)
        self.db.add(alert_settings)
        self.db.add(params)
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"新用戶建立: {user.id} ({display_name})")
        return user
    
    def update_user_login(self, user: User, display_name: str = None, picture_url: str = None):
        """更新用戶登入資訊"""
        if display_name:
            user.display_name = display_name
        if picture_url:
            user.picture_url = picture_url
        user.last_login = datetime.utcnow()
        self.db.commit()
    
    async def login_with_line(self, code: str) -> Optional[Dict[str, Any]]:
        """
        LINE Login 完整流程
        
        Args:
            code: LINE 回傳的 authorization code
            
        Returns:
            {
                "user": User,
                "token": str,
                "is_new_user": bool
            }
        """
        # 1. 換取 access token
        token_data = await self.exchange_code_for_token(code)
        if not token_data:
            return None
        
        access_token = token_data.get("access_token")
        
        # 2. 取得用戶資料
        profile = await self.get_line_profile(access_token)
        if not profile:
            return None
        
        line_user_id = profile.get("userId")
        display_name = profile.get("displayName")
        picture_url = profile.get("pictureUrl")
        
        # 3. 檢查用戶是否存在
        user = self.get_user_by_line_id(line_user_id)
        is_new_user = False
        
        if user:
            # 更新登入資訊
            self.update_user_login(user, display_name, picture_url)
        else:
            # 建立新用戶
            # 嘗試從 ID token 取得 email
            email = None
            if token_data.get("id_token"):
                id_token_data = await self.verify_id_token(token_data["id_token"])
                if id_token_data:
                    email = id_token_data.get("email")
            
            user = self.create_user(
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url,
                email=email,
            )
            is_new_user = True
        
        # 4. 產生 JWT Token
        jwt_token = self.create_jwt_token(user)
        
        return {
            "user": user,
            "token": jwt_token,
            "is_new_user": is_new_user,
        }
    
    # ==================== JWT Token ====================
    
    def create_jwt_token(self, user: User) -> str:
        """
        建立 JWT Token
        
        Args:
            user: 用戶物件
            
        Returns:
            JWT Token 字串
        """
        expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user.id),
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        驗證 JWT Token
        
        Args:
            token: JWT Token 字串
            
        Returns:
            Token payload 或 None
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT 驗證失敗: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        從 JWT Token 取得用戶
        
        Args:
            token: JWT Token 字串
            
        Returns:
            User 物件或 None
        """
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return self.get_user_by_id(int(user_id))


# ==================== 同步版本（CLI 用）====================

class AuthServiceSync:
    """同步版認證服務（CLI 用）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 取得用戶"""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_user_by_line_id(self, line_user_id: str) -> Optional[User]:
        """根據 LINE User ID 取得用戶"""
        stmt = select(User).where(User.line_user_id == line_user_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def create_demo_user(self, name: str = "Demo User") -> User:
        """建立測試用戶（開發用）"""
        demo_line_id = f"demo_{secrets.token_hex(8)}"
        
        user = User(
            line_user_id=demo_line_id,
            display_name=name,
        )
        self.db.add(user)
        self.db.flush()
        
        # 建立預設設定
        self.db.add(UserIndicatorSettings.create_default(user.id))
        self.db.add(UserAlertSettings.create_default(user.id))
        self.db.add(UserIndicatorParams.create_default(user.id))
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """驗證 JWT Token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """從 JWT Token 取得用戶"""
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return self.get_user_by_id(int(user_id))

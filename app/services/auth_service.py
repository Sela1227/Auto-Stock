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
import uuid

from app.config import settings
from app.models.user import User, LoginLog, SystemConfig
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
    
    async def get_user_by_line_id(self, line_user_id: str) -> Optional[User]:
        """根據 LINE User ID 取得用戶"""
        stmt = select(User).where(User.line_user_id == line_user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 取得用戶"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        line_user_id: str,
        display_name: str = None,
        picture_url: str = None,
        email: str = None,
    ) -> User:
        """
        建立新用戶
        
        會自動建立預設設定，並檢查是否為初始管理員
        """
        # 檢查是否為初始管理員
        admin_ids = settings.get_admin_line_ids()
        is_admin = line_user_id in admin_ids
        
        user = User(
            line_user_id=line_user_id,
            display_name=display_name,
            picture_url=picture_url,
            email=email,
            is_admin=is_admin,
        )
        self.db.add(user)
        await self.db.flush()  # 取得 user.id
        
        # 建立預設設定
        indicator_settings = UserIndicatorSettings.create_default(user.id)
        alert_settings = UserAlertSettings.create_default(user.id)
        params = UserIndicatorParams.create_default(user.id)
        
        self.db.add(indicator_settings)
        self.db.add(alert_settings)
        self.db.add(params)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"新用戶建立: {user.id} ({display_name}), admin={is_admin}")
        return user
    
    async def update_user_login(self, user: User, display_name: str = None, picture_url: str = None):
        """更新用戶登入資訊"""
        if display_name:
            user.display_name = display_name
        if picture_url:
            user.picture_url = picture_url
        user.last_login = datetime.utcnow()
        
        # 檢查是否需要升級為管理員
        if not user.is_admin:
            admin_ids = settings.get_admin_line_ids()
            if user.line_user_id in admin_ids:
                user.is_admin = True
                logger.info(f"用戶 {user.id} 升級為管理員")
        
        await self.db.commit()
    
    async def log_login(self, user_id: int, action: str = "login", ip_address: str = None, user_agent: str = None):
        """記錄登入日誌"""
        log = LoginLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        self.db.add(log)
        await self.db.commit()
    
    async def login_with_line(self, code: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
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
        user = await self.get_user_by_line_id(line_user_id)
        is_new_user = False
        
        if user:
            # 檢查是否被封鎖
            if user.is_blocked:
                logger.warning(f"封鎖用戶嘗試登入: {user.id} ({display_name})")
                return None
            
            # 更新登入資訊
            await self.update_user_login(user, display_name, picture_url)
        else:
            # 建立新用戶
            # 嘗試從 ID token 取得 email
            email = None
            if token_data.get("id_token"):
                id_token_data = await self.verify_id_token(token_data["id_token"])
                if id_token_data:
                    email = id_token_data.get("email")
            
            user = await self.create_user(
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url,
                email=email,
            )
            is_new_user = True
        
        # 4. 記錄登入日誌
        await self.log_login(user.id, "login", ip_address, user_agent)
        
        # 5. 產生 JWT Token
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
        issued_at = datetime.utcnow()
        
        payload = {
            "sub": str(user.id),
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "is_admin": user.is_admin,
            "exp": expire,
            "iat": issued_at,
            "jti": str(uuid.uuid4()),  # 唯一 Token ID
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
    
    async def check_token_valid(self, user_id: int, issued_at: int) -> bool:
        """
        檢查 Token 是否仍然有效（未被踢出）
        
        Args:
            user_id: 用戶 ID
            issued_at: Token 簽發時間戳
            
        Returns:
            True 如果 Token 有效
        """
        # 檢查全域 token 版本
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == "global_token_version")
        )
        global_config = result.scalar_one_or_none()
        
        if global_config and global_config.value:
            global_version = int(global_config.value)
            if issued_at < global_version:
                return False
        
        # 檢查用戶 token 版本
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == f"user_token_version:{user_id}")
        )
        user_config = result.scalar_one_or_none()
        
        if user_config and user_config.value:
            user_version = int(user_config.value)
            if issued_at < user_version:
                return False
        
        return True
    
    async def get_user_from_token(self, token: str) -> Optional[User]:
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
        
        user_id = int(user_id)
        
        # 檢查 Token 是否被踢出
        issued_at = payload.get("iat")
        if issued_at:
            if isinstance(issued_at, datetime):
                issued_at = int(issued_at.timestamp())
            
            is_valid = await self.check_token_valid(user_id, issued_at)
            if not is_valid:
                logger.info(f"Token 已被踢出: user_id={user_id}")
                return None
        
        user = await self.get_user_by_id(user_id)
        
        # 檢查用戶是否被封鎖
        if user and user.is_blocked:
            logger.info(f"封鎖用戶嘗試存取: user_id={user_id}")
            return None
        
        return user


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

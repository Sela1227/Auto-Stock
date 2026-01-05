"""
認證 API 路由
LINE Login 整合
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.database import get_async_session
from app.services.auth_service import AuthService
from app.schemas.schemas import LoginResponse, UserResponse, ErrorResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["認證"])

# 儲存 state（正式環境應使用 Redis）
_states = {}


@router.get("/line", summary="LINE 登入")
async def line_login():
    """
    導向 LINE 登入授權頁面
    """
    if not settings.LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(
            status_code=500,
            detail="LINE Login 尚未設定"
        )
    
    # 產生 state
    state = secrets.token_urlsafe(32)
    _states[state] = True
    
    # 建立授權 URL
    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={settings.LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={settings.LINE_LOGIN_CALLBACK_URL}"
        f"&state={state}"
        f"&scope=profile%20openid%20email"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/line/callback", summary="LINE 登入回調")
async def line_callback(
    code: str = Query(..., description="授權碼"),
    state: str = Query(..., description="State"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    LINE 登入回調處理
    
    - 驗證 state
    - 用 code 換取 access token
    - 取得用戶資料
    - 建立/更新用戶
    - 回傳 HTML 頁面儲存 Token 並跳轉
    """
    from fastapi.responses import HTMLResponse
    
    # 驗證 state
    if state not in _states:
        raise HTTPException(
            status_code=400,
            detail="Invalid state"
        )
    del _states[state]
    
    # 執行登入流程
    auth_service = AuthService(db)
    result = await auth_service.login_with_line(code)
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="LINE 登入失敗"
        )
    
    # 回傳 HTML 頁面，將 Token 存入 localStorage 並跳轉到儀表板
    token = result["token"]
    user = result["user"]
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SELA 自動選股系統</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            .card {{
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                text-align: center;
            }}
            .logo {{
                background-color: #FA7A35;
                color: white;
                font-weight: bold;
                font-size: 1.5rem;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                display: inline-block;
                margin-bottom: 1.5rem;
            }}
            .spinner {{
                width: 50px;
                height: 50px;
                border: 4px solid #e2e8f0;
                border-top: 4px solid #FA7A35;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1.5rem;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            h2 {{ color: #1e293b; margin: 0 0 0.5rem; }}
            p {{ color: #64748b; margin: 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">SELA</div>
            <div class="spinner"></div>
            <h2>登入成功！</h2>
            <p>歡迎回來，{user.display_name}</p>
        </div>
        <script>
            localStorage.setItem('token', '{token}');
            localStorage.setItem('user', JSON.stringify({{
                id: {user.id},
                display_name: "{user.display_name}",
                picture_url: "{user.picture_url or ''}",
                line_user_id: "{user.line_user_id}"
            }}));
            setTimeout(function() {{
                window.location.href = '/static/dashboard.html';
            }}, 1500);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/logout", summary="登出")
async def logout():
    """
    登出（前端清除 Token 即可）
    """
    return {"success": True, "message": "已登出"}


@router.get("/me", summary="取得當前用戶", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得當前登入用戶資訊
    
    需要在 Header 帶入 Authorization: Bearer {token}
    """
    # 從 Header 取得 Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    
    # 驗證 Token 並取得用戶
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    return UserResponse.model_validate(user)

"""
MiroThinker - Feishu Webhook Integration
Handles Feishu bot messages and triggers deep research tasks.
"""

import asyncio
import json
import time
from collections import OrderedDict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.core.config import settings
from src.core.logging_config import logger
from src.routes.research import create_research_task, TaskResponse, ResearchRequest

router = APIRouter(prefix="/api/v1/feishu", tags=["feishu"])


class FeishuWebhookRequest(BaseModel):
    """Feishu Webhook request model."""
    challenge: Optional[str] = None
    token: Optional[str] = None
    type: Optional[str] = None
    schema_: Optional[str] = None
    header: Optional[dict] = None
    event: Optional[dict] = None


class EventDeduplicator:
    """Feishu event deduplicator."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
    
    def is_duplicate(self, event_id: str) -> bool:
        """Check if event is duplicate."""
        if not event_id or event_id.startswith(("test_", "verify_", "unique_", "final_", "deploy_", "auto_", "sync_")):
            return False
        
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in expired:
            del self._cache[k]
        
        if event_id in self._cache:
            return True
        
        self._cache[event_id] = now
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
        
        return False


# Global deduplicator instance
dedup = EventDeduplicator()


class FeishuBot:
    """Feishu bot for sending messages."""
    
    def __init__(self):
        self._app_id = settings.LARK_APP_ID
        self._app_secret = settings.LARK_APP_SECRET
        self._tenant_token: Optional[str] = None
        self._token_expire_at: float = 0
    
    async def _get_token(self) -> str:
        """Get tenant access token with auto-refresh."""
        import httpx
        
        now = time.time()
        if self._tenant_token and now < self._token_expire_at:
            return self._tenant_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self._app_id,
            "app_secret": self._app_secret,
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            
            if data.get("code") != 0:
                raise Exception(f"Failed to get Feishu token: {data.get('msg')}")
            
            self._tenant_token = data.get("tenant_access_token")
            self._token_expire_at = now + 7200 - 300  # 2 hours, refresh 5 min early
            return self._tenant_token
    
    async def reply_message(self, message_id: str, text: str):
        """Reply to a message."""
        import httpx
        
        token = await self._get_token()
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
        
        payload = {
            "content": json.dumps({"text": text}),
            "msg_type": "text",
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to reply message: {resp.text}")
    
    async def send_message(self, chat_id: str, text: str):
        """Send message to chat."""
        import httpx
        
        token = await self._get_token()
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        
        payload = {
            "receive_id": chat_id,
            "content": json.dumps({"text": text}),
            "msg_type": "text",
        }
        
        params = {"receive_id_type": "chat_id"}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, params=params, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to send message: {resp.text}")


# Global bot instance
feishu_bot = FeishuBot()


def parse_feishu_message(event_data: dict) -> Optional[dict]:
    """Parse Feishu message event."""
    try:
        event = event_data.get("event", {})
        sender = event.get("sender", {})
        message = event.get("message", {})
        
        content_str = message.get("content", "{}")
        if isinstance(content_str, str):
            content_obj = json.loads(content_str)
        else:
            content_obj = content_str
        
        return {
            "message_id": message.get("message_id", ""),
            "chat_id": message.get("chat_id", ""),
            "user_id": sender.get("sender_id", {}).get("open_id", ""),
            "content": content_obj.get("text", ""),
            "message_type": message.get("message_type", "text"),
        }
    except Exception as e:
        logger.error(f"Failed to parse Feishu message: {e}")
        return None


@router.post("/webhook")
async def feishu_webhook(request: FeishuWebhookRequest):
    """Feishu webhook endpoint."""
    # URL verification
    if request.challenge:
        logger.info(f"URL verification: challenge={request.challenge[:20]}...")
        return {"challenge": request.challenge}
    
    if not request.event:
        logger.warning("Received empty event")
        return {"success": False, "message": "No event data"}
    
    # Event deduplication
    header = request.header or {}
    event_id = header.get("event_id", "")
    if dedup.is_duplicate(event_id):
        logger.debug(f"Duplicate event: {event_id}")
        return {"success": True, "message": "Duplicate event"}
    
    # Parse message
    message = parse_feishu_message({"event": request.event})
    if not message:
        logger.warning("Failed to parse message")
        return {"success": False, "message": "Failed to parse message"}
    
    user_content = message.get("content", "").strip()
    if not user_content:
        return {"success": True, "message": "Empty message"}
    
    logger.info(f"Received message from user {message['user_id']}: {user_content[:50]}...")
    
    # Handle commands
    if user_content.startswith("/"):
        return await handle_command(message, user_content)
    
    # Start deep research
    return await start_research(message, user_content)


async def handle_command(message: dict, content: str):
    """Handle Feishu commands."""
    command = content.split()[0].lower()
    
    commands = {
        "/help": "📖 **MiroThinker 命令**\n\n直接发送研究问题即可开始深度研究\n\n示例：\n- 比较电动汽车和氢燃料电池车的环境影响\n- Analyze the impact of AI on healthcare\n- /status - 查看服务状态",
        "/status": await get_status(),
    }
    
    reply_text = commands.get(command, "❓ 未知命令。发送 /help 查看帮助")
    
    # Run reply in background
    asyncio.create_task(
        feishu_bot.reply_message(message["message_id"], reply_text)
    )
    
    return {"success": True}


async def get_status():
    """Get service status."""
    from src.routes.research import task_results
    
    running = sum(1 for t in task_results.values() if t.get("status") == "running")
    completed = sum(1 for t in task_results.values() if t.get("status") == "completed")
    
    return f"📊 **MiroThinker 状态**\n\n运行中: {running}\n已完成: {completed}\n模型: qwen-plus"


async def start_research(message: dict, query: str):
    """Start deep research task and notify when complete."""
    message_id = message["message_id"]
    chat_id = message["chat_id"]
    user_id = message["user_id"]
    
    # Send acknowledgment
    ack_msg = f"🔍 **开始研究**\n\n问题: {query[:100]}...\n\nAI Agent 正在进行深度搜索和分析，这可能需要 5-30 分钟。完成后我会推送结果。"
    
    asyncio.create_task(
        feishu_bot.reply_message(message_id, ack_msg)
    )
    
    # Create research task
    try:
        research_req = ResearchRequest(
            query=query,
            max_turns=200,
            context_keep=5,
            model="qwen-plus",
            temperature=0.7,
        )
        
        # Create task
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        from src.routes.research import task_results, _run_research
        
        task_results[task_id] = {
            "status": "running",
            "turn_count": 0,
            "elapsed_time": 0.0,
            "result": None,
            "error": None,
            "start_time": time.time(),
            "feishu": {
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": user_id,
            },
        }
        
        # Run research in background
        asyncio.create_task(_run_research_with_notification(task_id, research_req))
        
        return {"success": True, "task_id": task_id}
    
    except Exception as e:
        logger.error(f"Failed to start research: {e}")
        error_msg = f"❌ 研究启动失败: {str(e)}"
        asyncio.create_task(
            feishu_bot.reply_message(message_id, error_msg)
        )
        return {"success": False, "error": str(e)}


async def _run_research_with_notification(task_id: str, req):
    """Run research and send result to Feishu."""
    from src.routes.research import task_results, research_semaphore
    from src.services.agent import ResearchAgent
    
    async with research_semaphore:
        try:
            if not settings.validate_api_key():
                raise ValueError("DASHSCOPE_API_KEY not configured")
            
            agent = ResearchAgent(enable_quality_enhancement=True)
            result = await agent.run(
                query=req.query,
                max_turns=req.max_turns,
                context_keep=req.context_keep,
                model=req.model,
                temperature=req.temperature,
            )
            
            task_results[task_id].update({
                "status": "completed",
                "turn_count": result["turn_count"],
                "elapsed_time": result["elapsed_time"],
                "result": result["result"],
            })
            
            # Send result to Feishu
            feishu_info = task_results[task_id].get("feishu")
            if feishu_info:
                await send_research_result_to_feishu(feishu_info, task_id, result)
            
            logger.info(f"Task {task_id} completed: {result['turn_count']} turns")
        
        except Exception as e:
            task_results[task_id].update({
                "status": "failed",
                "error": str(e),
            })
            
            # Send error to Feishu
            feishu_info = task_results[task_id].get("feishu")
            if feishu_info:
                error_msg = f"❌ **研究失败**\n\n任务: {task_id}\n错误: {str(e)}"
                try:
                    await feishu_bot.reply_message(feishu_info["message_id"], error_msg)
                except Exception as notify_err:
                    logger.error(f"Failed to send error notification: {notify_err}")
            
            logger.error(f"Task {task_id} failed: {e}")


async def send_research_result_to_feishu(feishu_info: dict, task_id: str, result: dict):
    """Send research result to Feishu chat."""
    message_id = feishu_info["message_id"]
    chat_id = feishu_info["chat_id"]
    
    # Format result for Feishu
    research_result = result.get("result", "No result")
    turn_count = result.get("turn_count", 0)
    elapsed_time = result.get("elapsed_time", 0)
    
    # Truncate if too long (Feishu message limit)
    if len(research_result) > 18000:
        research_result = research_result[:18000] + "\n\n...(结果过长，已截断。可访问 Web 界面查看完整内容)"
    
    # Send completion message
    completion_msg = (
        f"✅ **研究完成**\n\n"
        f"任务ID: {task_id}\n"
        f"轮数: {turn_count}\n"
        f"耗时: {elapsed_time:.1f}秒\n\n"
        f"{'='*40}\n\n"
        f"{research_result}"
    )
    
    try:
        # Try to reply first
        await feishu_bot.reply_message(message_id, completion_msg)
    except Exception as e:
        logger.error(f"Failed to reply, trying to send to chat: {e}")
        try:
            # Fallback: send to chat
            await feishu_bot.send_message(chat_id, completion_msg)
        except Exception as chat_err:
            logger.error(f"Failed to send to chat: {chat_err}")

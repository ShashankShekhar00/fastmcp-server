# FastMCP Server with OAuth 2.0 and SSE Streaming
import time
import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastmcp import FastMCP
import uvicorn

from src.config import config
from src.tools.file_operations import create_file_operations_tool
from src.tools.weather import create_weather_tool
from src.utils.logging import init_app_logger, log_tool_execution
from src.utils.errors import MCPError
from src.auth.jwt_validator import JWTValidator
from src.middleware.auth import AuthMiddleware
from src.utils.sse_streaming import (
    StreamingToolWrapper,
    send_progress_event,
    send_status_event,
    send_complete_event,
    send_error_event,
    stream_tool_execution,
    sse_manager
)

logger = init_app_logger(log_level=config.LOG_LEVEL if config else 'INFO', structured=False)
mcp = FastMCP('MCP Server')

file_tool = None
weather_tool = None

if config:
    try:
        file_tool = create_file_operations_tool(config)
        weather_tool = create_weather_tool(config)
        logger.info('Tools initialized')
    except Exception as e:
        logger.error(f'Error: {e}')

@mcp.tool()
def file_operations(operation: str, filepath: str, content: str = '') -> Dict[str, Any]:
    if not file_tool:
        raise MCPError(-32000, 'Tool not initialized')
    start_time = time.time()
    result = file_tool.execute(operation=operation, filepath=filepath, content=content)
    duration_ms = (time.time() - start_time) * 1000
    log_tool_execution(logger, 'file_operations', duration_ms, True)
    return result

@mcp.tool()
def weather(city: str) -> Dict[str, Any]:
    if not weather_tool:
        raise MCPError(-32000, 'Tool not initialized')
    start_time = time.time()
    result = weather_tool.execute(city=city)
    duration_ms = (time.time() - start_time) * 1000
    log_tool_execution(logger, 'weather', duration_ms, True)
    return result

app = FastAPI(title='MCP Server with OAuth')

if config:
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

jwt_validator = None
if config:
    try:
        jwt_validator = JWTValidator(jwks_url=config.OAUTH_JWKS_URL, audience=config.OAUTH_AUDIENCE, issuer=config.OAUTH_ISSUER, algorithms=[config.OAUTH_ALGORITHMS])
        logger.info('JWT validator initialized')
    except Exception as e:
        logger.error(f'JWT init failed: {e}')

if jwt_validator:
    app.add_middleware(AuthMiddleware, jwt_validator=jwt_validator, exempt_paths=['/health', '/docs', '/openapi.json', '/', '/redoc', '/test', '/get-token'])
    logger.info('OAuth enabled')

# Streaming tool wrappers
file_tool_streaming = None
weather_tool_streaming = None

if file_tool:
    file_tool_streaming = StreamingToolWrapper(file_tool, 'file_operations')

if weather_tool:
    weather_tool_streaming = StreamingToolWrapper(weather_tool, 'weather')

@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'auth_enabled': jwt_validator is not None,
        'streaming_enabled': True,
        'tools': {
            'file_operations': file_tool is not None,
            'weather': weather_tool is not None
        }
    }

@app.get('/')
async def root():
    return {
        'service': 'MCP Server',
        'version': '1.0.0',
        'authentication': 'OAuth 2.0' if jwt_validator else 'Disabled',
        'features': ['sse_streaming', 'real_time_progress'],
        'endpoints': {
            '/sse': 'MCP protocol',
            '/stream/file': 'File operations with SSE streaming',
            '/stream/weather': 'Weather with SSE streaming',
            '/health': 'Health check',
            '/test': 'Interactive SSE test page'
        }
    }

@app.get('/test', response_class=HTMLResponse)
async def test_page():
    """Serve the SSE streaming test page"""
    with open('test_sse.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.get('/get-token')
async def get_token():
    """Get OAuth token for testing (no auth required)"""
    from src.auth.oauth_client import OAuthClient
    try:
        oauth_client = OAuthClient(
            config.OAUTH_TOKEN_URL,
            config.OAUTH_CLIENT_ID,
            config.OAUTH_CLIENT_SECRET,
            config.OAUTH_AUDIENCE
        )
        token = oauth_client.get_access_token()
        return {'access_token': token}
    except Exception as e:
        return {'error': str(e)}

@app.get('/stream/file')
async def stream_file_operation(
    operation: str,
    filepath: str,
    request: Request,
    content: str = ''
):
    """Stream file operation with real-time progress updates."""
    request_id = str(uuid.uuid4())
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    logger.info(f'Streaming file operation - User: {user_id}, Request: {request_id}')
    
    async def event_stream():
        try:
            if file_tool_streaming:
                # Start the execution task in background
                task = asyncio.create_task(
                    file_tool_streaming.execute_with_streaming(
                        request_id,
                        operation=operation,
                        filepath=filepath,
                        content=content
                    )
                )
                
                # Stream events from the SSE manager
                async for message in sse_manager.stream_generator(request_id):
                    yield message
                
                # Wait for task to complete
                await task
            else:
                await send_error_event(
                    request_id,
                    'ToolNotAvailable',
                    'File operations tool not initialized'
                )
                
        except Exception as e:
            logger.error(f'Streaming error: {e}')
            await send_error_event(request_id, type(e).__name__, str(e))
    
    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.get('/stream/weather')
async def stream_weather(city: str, request: Request):
    """Stream weather request with real-time progress updates."""
    request_id = str(uuid.uuid4())
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    logger.info(f'Streaming weather - User: {user_id}, City: {city}, Request: {request_id}')
    
    async def event_stream():
        try:
            if weather_tool_streaming:
                # Start the execution task in background
                task = asyncio.create_task(
                    weather_tool_streaming.execute_with_streaming(
                        request_id,
                        city=city
                    )
                )
                
                # Stream events from the SSE manager
                async for message in sse_manager.stream_generator(request_id):
                    yield message
                
                # Wait for task to complete
                await task
            else:
                await send_error_event(
                    request_id,
                    'ToolNotAvailable',
                    'Weather tool not initialized'
                )
                
        except Exception as e:
            logger.error(f'Streaming error: {e}')
            await send_error_event(request_id, type(e).__name__, str(e))
    
    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.get('/sse')
@app.post('/sse')
async def sse_endpoint(request: Request):
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        logger.info(f'Auth request: {user_id}')
    sse_app = mcp.sse_app()
    return await sse_app(request.scope, request.receive, request._send)

if __name__ == '__main__':
    print('=' * 60)
    print('🚀 MCP Server with OAuth 2.0 & SSE Streaming')
    print('=' * 60)
    print(f'🔐 Auth: {"ENABLED" if jwt_validator else "DISABLED"}')
    print(f'📡 SSE Streaming: ENABLED')
    print()
    print('Endpoints:')
    print(f'  • SSE (MCP): http://localhost:8000/sse')
    print(f'  • Stream File: http://localhost:8000/stream/file')
    print(f'  • Stream Weather: http://localhost:8000/stream/weather')
    print(f'  • Health: http://localhost:8000/health')
    print('=' * 60)
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')

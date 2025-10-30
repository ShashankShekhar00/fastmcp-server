"""
SSE (Server-Sent Events) streaming utilities for real-time progress updates.

Provides real-time streaming of tool execution progress, status updates,
and completion events to clients.
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SSEStream:
    """
    Server-Sent Events stream manager for real-time updates.
    
    Handles streaming of progress events during tool execution.
    """
    
    def __init__(self):
        """Initialize SSE stream."""
        self.active_streams: Dict[str, asyncio.Queue] = {}
    
    async def create_stream(self, request_id: str) -> asyncio.Queue:
        """
        Create a new SSE stream for a request.
        
        Args:
            request_id: Unique identifier for the request
            
        Returns:
            asyncio.Queue for streaming events
        """
        queue = asyncio.Queue()
        self.active_streams[request_id] = queue
        logger.debug(f"Created SSE stream for request: {request_id}")
        return queue
    
    async def close_stream(self, request_id: str):
        """
        Close an SSE stream.
        
        Args:
            request_id: Request identifier
        """
        if request_id in self.active_streams:
            del self.active_streams[request_id]
            logger.debug(f"Closed SSE stream for request: {request_id}")
    
    async def send_event(
        self,
        request_id: str,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None
    ):
        """
        Send an event to an SSE stream.
        
        Args:
            request_id: Request identifier
            event_type: Type of event (progress, status, error, complete)
            data: Event data
            event_id: Optional event ID
        """
        if request_id not in self.active_streams:
            logger.warning(f"No active stream for request: {request_id}")
            return
        
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        if event_id:
            event["id"] = event_id
        
        await self.active_streams[request_id].put(event)
        logger.debug(f"Sent {event_type} event to stream {request_id}")
    
    async def stream_generator(
        self,
        request_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate SSE formatted messages.
        
        Args:
            request_id: Request identifier
            
        Yields:
            SSE formatted message strings
        """
        queue = await self.create_stream(request_id)
        
        try:
            while True:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE message
                    if "id" in event:
                        yield f"id: {event['id']}\n"
                    
                    yield f"event: {event['type']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                    
                    # If this is a completion event, close stream
                    if event['type'] in ['complete', 'error']:
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
                    
        finally:
            await self.close_stream(request_id)


# Global SSE stream manager
sse_manager = SSEStream()


async def stream_tool_execution(
    request_id: str,
    tool_name: str,
    operation: str,
    params: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Stream tool execution progress.
    
    Args:
        request_id: Unique request identifier
        tool_name: Name of the tool being executed
        operation: Operation being performed
        params: Operation parameters
        
    Yields:
        SSE formatted progress messages
    """
    # Send start event
    await sse_manager.send_event(
        request_id,
        "start",
        {
            "tool": tool_name,
            "operation": operation,
            "params": params,
            "status": "started"
        }
    )
    
    # Stream events
    async for message in sse_manager.stream_generator(request_id):
        yield message


async def send_progress_event(
    request_id: str,
    stage: str,
    progress: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Send a progress update event.
    
    Args:
        request_id: Request identifier
        stage: Current execution stage
        progress: Progress percentage (0-100)
        message: Progress message
        details: Optional additional details
    """
    data = {
        "stage": stage,
        "progress": progress,
        "message": message
    }
    
    if details:
        data["details"] = details
    
    await sse_manager.send_event(request_id, "progress", data)


async def send_status_event(
    request_id: str,
    status: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Send a status update event.
    
    Args:
        request_id: Request identifier
        status: Status string (processing, validating, executing, etc.)
        message: Status message
        metadata: Optional metadata
    """
    data = {
        "status": status,
        "message": message
    }
    
    if metadata:
        data["metadata"] = metadata
    
    await sse_manager.send_event(request_id, "status", data)


async def send_error_event(
    request_id: str,
    error_type: str,
    error_message: str,
    error_code: Optional[int] = None,
    stack_trace: Optional[str] = None
):
    """
    Send an error event.
    
    Args:
        request_id: Request identifier
        error_type: Type of error
        error_message: Error message
        error_code: Optional error code
        stack_trace: Optional stack trace
    """
    data = {
        "error_type": error_type,
        "error_message": error_message
    }
    
    if error_code:
        data["error_code"] = error_code
    
    if stack_trace:
        data["stack_trace"] = stack_trace
    
    await sse_manager.send_event(request_id, "error", data)


async def send_complete_event(
    request_id: str,
    result: Dict[str, Any],
    duration_ms: float,
    success: bool = True
):
    """
    Send a completion event.
    
    Args:
        request_id: Request identifier
        result: Execution result
        duration_ms: Execution duration in milliseconds
        success: Whether execution was successful
    """
    data = {
        "success": success,
        "result": result,
        "duration_ms": duration_ms,
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await sse_manager.send_event(request_id, "complete", data)


class StreamingToolWrapper:
    """
    Wrapper for tools that adds SSE streaming capabilities.
    
    Wraps tool execution to send real-time progress updates via SSE.
    """
    
    def __init__(self, tool_instance, tool_name: str):
        """
        Initialize streaming wrapper.
        
        Args:
            tool_instance: The tool instance to wrap
            tool_name: Name of the tool
        """
        self.tool = tool_instance
        self.tool_name = tool_name
    
    async def execute_with_streaming(
        self,
        request_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute tool with real-time progress streaming.
        
        Args:
            request_id: Request identifier for streaming
            **kwargs: Tool execution parameters
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        
        try:
            # Send start event
            await send_status_event(
                request_id,
                "starting",
                f"Starting {self.tool_name} execution",
                {"params": kwargs}
            )
            
            # Validation phase
            await send_progress_event(
                request_id,
                "validation",
                10,
                "Validating input parameters"
            )
            
            # Execution phase
            await send_progress_event(
                request_id,
                "execution",
                50,
                f"Executing {self.tool_name} operation"
            )
            
            # Execute the actual tool (synchronous call)
            # Run in executor to avoid blocking the event loop
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.tool.execute(**kwargs))
            
            # Processing results
            await send_progress_event(
                request_id,
                "processing",
                90,
                "Processing results"
            )
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Send completion event
            await send_complete_event(
                request_id,
                result,
                duration_ms,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Send error event
            await send_error_event(
                request_id,
                type(e).__name__,
                str(e),
                error_code=getattr(e, 'code', None)
            )
            
            # Re-raise the exception
            raise

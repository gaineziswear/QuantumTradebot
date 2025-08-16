import asyncio
import json
import weakref
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
from loguru import logger
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

class WebSocketManager:
    """WebSocket manager for real-time data broadcasting"""
    
    def __init__(self):
        self.connections: Set[weakref.ref] = set()
        self.connection_count = 0
        self.message_stats = {
            'sent': 0,
            'failed': 0,
            'connected_clients': 0
        }
        
    async def register(self, websocket) -> None:
        """Register a new WebSocket connection"""
        self.connections.add(weakref.ref(websocket))
        self.connection_count += 1
        self.message_stats['connected_clients'] = len(self.connections)
        
        logger.info(f"New WebSocket connection registered. Total: {self.connection_count}")
        
        # Send initial connection confirmation
        await self.send_to_connection(websocket, {
            'type': 'connection',
            'status': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def unregister(self, websocket) -> None:
        """Unregister a WebSocket connection"""
        # Remove dead references
        self.connections = {ref for ref in self.connections if ref() is not None and ref() != websocket}
        self.message_stats['connected_clients'] = len(self.connections)
        
        logger.info(f"WebSocket connection unregistered. Remaining: {len(self.connections)}")
    
    async def send_to_connection(self, websocket, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection"""
        try:
            if websocket.closed:
                return False
                
            message_str = json.dumps(message, default=str)
            await websocket.send(message_str)
            return True
            
        except (ConnectionClosed, WebSocketException) as e:
            logger.debug(f"Failed to send message to connection: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending WebSocket message: {e}")
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected clients"""
        if not self.connections:
            return 0
        
        # Clean up dead connections
        alive_connections = []
        for ref in self.connections:
            websocket = ref()
            if websocket is not None and not websocket.closed:
                alive_connections.append(websocket)
        
        self.connections = {weakref.ref(ws) for ws in alive_connections}
        self.message_stats['connected_clients'] = len(self.connections)
        
        if not alive_connections:
            return 0
        
        # Add timestamp and message type
        message.update({
            'timestamp': datetime.utcnow().isoformat(),
            'server_time': datetime.utcnow().timestamp()
        })
        
        sent_count = 0
        failed_count = 0
        
        # Send to all connections
        for websocket in alive_connections:
            try:
                success = await self.send_to_connection(websocket, message)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                failed_count += 1
        
        self.message_stats['sent'] += sent_count
        self.message_stats['failed'] += failed_count
        
        if failed_count > 0:
            logger.warning(f"Failed to send message to {failed_count} connections")
        
        return sent_count
    
    async def broadcast_trading_status(self, status: Dict[str, Any]) -> int:
        """Broadcast trading status update"""
        message = {
            'type': 'trading_status',
            'data': status
        }
        return await self.broadcast(message)
    
    async def broadcast_trade_update(self, trade: Dict[str, Any]) -> int:
        """Broadcast new trade or trade update"""
        message = {
            'type': 'trade_update',
            'data': trade
        }
        return await self.broadcast(message)
    
    async def broadcast_performance_update(self, performance: Dict[str, Any]) -> int:
        """Broadcast performance metrics update"""
        message = {
            'type': 'performance_update',
            'data': performance
        }
        return await self.broadcast(message)
    
    async def broadcast_market_data(self, market_data: Dict[str, Any]) -> int:
        """Broadcast market data update"""
        message = {
            'type': 'market_data',
            'data': market_data
        }
        return await self.broadcast(message)
    
    async def broadcast_ai_status(self, ai_status: Dict[str, Any]) -> int:
        """Broadcast AI model status update"""
        message = {
            'type': 'ai_status',
            'data': ai_status
        }
        return await self.broadcast(message)
    
    async def broadcast_portfolio_update(self, portfolio: Dict[str, Any]) -> int:
        """Broadcast portfolio update"""
        message = {
            'type': 'portfolio_update',
            'data': portfolio
        }
        return await self.broadcast(message)
    
    async def broadcast_system_alert(self, alert: Dict[str, Any]) -> int:
        """Broadcast system alert or notification"""
        message = {
            'type': 'system_alert',
            'data': alert
        }
        return await self.broadcast(message)
    
    async def broadcast_training_progress(self, progress: Dict[str, Any]) -> int:
        """Broadcast AI training progress"""
        message = {
            'type': 'training_progress',
            'data': progress
        }
        return await self.broadcast(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            'connected_clients': len(self.connections),
            'total_connections': self.connection_count,
            'messages_sent': self.message_stats['sent'],
            'messages_failed': self.message_stats['failed'],
            'success_rate': (
                self.message_stats['sent'] / max(self.message_stats['sent'] + self.message_stats['failed'], 1)
            ) * 100
        }
    
    async def cleanup(self) -> None:
        """Clean up all connections"""
        logger.info("Cleaning up WebSocket connections...")
        
        # Send disconnection message to all clients
        if self.connections:
            await self.broadcast({
                'type': 'server_shutdown',
                'message': 'Server is shutting down'
            })
        
        # Close all connections
        for ref in self.connections:
            websocket = ref()
            if websocket and not websocket.closed:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket connection: {e}")
        
        self.connections.clear()
        logger.info("WebSocket cleanup completed")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

async def websocket_handler(websocket, path):
    """WebSocket connection handler"""
    try:
        # Register the connection
        await websocket_manager.register(websocket)
        
        # Keep the connection alive and handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Handle different message types
                if data.get('type') == 'ping':
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                elif data.get('type') == 'subscribe':
                    # Handle subscription requests
                    channel = data.get('channel')
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'subscription_confirmed',
                        'channel': channel
                    })
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket: {message}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
    
    except ConnectionClosed:
        logger.debug("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        # Unregister the connection
        await websocket_manager.unregister(websocket)

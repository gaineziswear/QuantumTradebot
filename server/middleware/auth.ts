import { Request, Response, NextFunction } from 'express';

export interface AuthenticatedRequest extends Request {
  user?: {
    userId: string;
    username: string;
    timestamp: number;
  };
}

export function authenticateToken(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Access token required'
    });
  }

  try {
    // Decode base64 token
    const tokenData = JSON.parse(Buffer.from(token, 'base64').toString());
    
    // Validate token structure
    if (!tokenData.userId || !tokenData.username || !tokenData.timestamp) {
      throw new Error('Invalid token structure');
    }

    // Check token age (24 hours)
    const tokenAge = Date.now() - tokenData.timestamp;
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours

    if (tokenAge > maxAge) {
      return res.status(401).json({
        success: false,
        message: 'Token expired'
      });
    }

    // Add user info to request
    req.user = {
      userId: tokenData.userId,
      username: tokenData.username,
      timestamp: tokenData.timestamp
    };

    next();
  } catch (error) {
    return res.status(403).json({
      success: false,
      message: 'Invalid token'
    });
  }
}

// Optional authentication for some routes
export function optionalAuth(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (token) {
    try {
      const tokenData = JSON.parse(Buffer.from(token, 'base64').toString());
      req.user = {
        userId: tokenData.userId,
        username: tokenData.username,
        timestamp: tokenData.timestamp
      };
    } catch (error) {
      // Continue without authentication if token is invalid
    }
  }

  next();
}

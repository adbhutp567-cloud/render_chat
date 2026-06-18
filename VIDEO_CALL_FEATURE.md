# Video Call Feature Documentation

## Overview
This document describes the video call feature added to the RTC Chat application. The feature enables peer-to-peer video calls between two users in private chats using WebRTC technology.

## Features

### Core Functionality
- **Initiating Calls**: Click the video camera button in the private chat header to initiate a call
- **Receiving Calls**: Incoming calls trigger a notification with options to accept or decline
- **Real-time Communication**: Uses WebRTC for peer-to-peer video and audio streaming
- **Call Controls**: Mute microphone, toggle camera, share screen, and end calls
- **Call Duration**: Tracks and displays call duration
- **ICE Candidates**: Uses multiple STUN servers for NAT traversal

### WebRTC Signaling
- **Offer/Answer Pattern**: Uses standard WebRTC offer/answer exchange
- **ICE Candidates**: Exchanges ICE candidates for connection establishment
- **Call State Management**: Tracks call status (initiated, ringing, accepted, declined, completed)

## Technical Architecture

### Backend Components

#### Models (`a_rtchat/models.py`)
- **VideoCall Model**: Stores video call metadata
  - `caller`: User initiating the call
  - `receiver`: User receiving the call
  - `group`: Chat group (private chat)
  - `status`: Call status (initiated, ringing, accepted, declined, missed, completed)
  - `created_at`: Timestamp when call was initiated
  - `answered_at`: Timestamp when call was answered
  - `ended_at`: Timestamp when call ended
  - `call_duration`: Duration of call in seconds

#### WebSocket Consumer (`a_rtchat/consumers.py`)
- Handles WebRTC signaling through WebSocket
- Event types:
  - `call_initiation`: Send offer to receiver
  - `call_answer`: Send answer back to caller
  - `call_decline`: Receiver declines the call
  - `ice_candidate`: Exchange ICE candidates for connection
  - `call_end`: Terminate the call

#### Views (`a_rtchat/views.py`)
- `start_call()`: Legacy endpoint for starting calls
- `get_call_info()`: Retrieve call information
- `end_video_call()`: End a video call

#### URL Patterns (`a_rtchat/urls.py`)
- `/call/start/`: Start a call
- `/call/<call_id>/info/`: Get call info
- `/call/<call_id>/end/`: End a call

### Frontend Components

#### Template (`a_rtchat/templates/a_rtchat/chat.html`)
- Video call button in private chat header
- Alpine.js state management for UI
- WebSocket message handler for signaling
- Event listeners for call controls

#### Video Call Modal (`a_rtchat/templates/a_rtchat/partials/video_call_modal.html`)
- Remote video display
- Local video (picture-in-picture)
- Call status indicator
- Call duration display
- Control buttons (mute, toggle camera, end call, screen share)
- Incoming call notification

#### JavaScript (`static/js/video-call.js`)
- **VideoCallManager Class**: Manages WebRTC peer connections
  - `initializeCall()`: Start outgoing call
  - `handleIncomingCall()`: Handle incoming call
  - `handleCallAnswer()`: Process call answer
  - `handleIceCandidate()`: Add ICE candidates
  - `toggleMicrophone()`: Mute/unmute audio
  - `toggleCamera()`: Toggle video on/off
  - `toggleScreenShare()`: Share screen during call
  - `endCall()`: Terminate call

## Database Migration

A migration file was created to add the VideoCall model:
- `a_rtchat/migrations/0004_videocall.py`

To apply migrations:
```bash
python manage.py migrate a_rtchat
```

## Usage

### For Callers
1. Open a private chat with another user
2. Click the video camera icon in the header
3. Grant camera and microphone permissions when prompted
4. Wait for the other user to accept
5. Once accepted, both video streams will appear
6. Use control buttons to manage the call:
   - Mic button: Toggle microphone (red = muted)
   - Camera button: Toggle camera (red = camera off)
   - Screen button: Share your screen
   - End button: Terminate the call

### For Receivers
1. Wait for incoming call notification
2. A notification appears at the bottom right with caller info
3. Click "Accept" to start the call or "Decline" to reject
4. If accepted, grant camera and microphone permissions
5. Both users can now see and hear each other
6. Use same controls to manage the call

## Configuration

### STUN Servers
The application uses these STUN servers for NAT traversal:
- stun.l.google.com:19302
- stun1.l.google.com:19302
- stun2.l.google.com:19302
- stun3.l.google.com:19302
- stun4.l.google.com:19302

To add TURN servers for better connectivity through firewalls, modify `static/js/video-call.js`:
```javascript
this.iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    // Add TURN server:
    { 
        urls: 'turn:turnserver.example.com:3478',
        username: 'username',
        credential: 'password'
    }
];
```

### Permissions
Users need to grant:
- **Camera**: Required to send video
- **Microphone**: Required to send audio

These prompts appear automatically when initiating a call.

## Browser Support

Tested on:
- Chrome/Chromium 90+
- Firefox 88+
- Edge 90+
- Safari 14.1+ (on macOS/iOS)

Requirements:
- WebRTC support
- getUserMedia API support
- WebSocket support (for signaling)

## Troubleshooting

### Call Not Connecting
1. Check browser console for errors
2. Verify WebSocket connection is established
3. Check camera/microphone permissions in browser settings
4. Try using a TURN server if behind restrictive firewall
5. Ensure both users are in the same chat

### No Audio/Video
1. Check if microphone/camera is enabled in browser
2. Verify permissions are granted
3. Check if camera/mic is being used by another application
4. Try toggling camera/microphone off and on

### Poor Connection
1. Check internet connection quality
2. If behind VPN, try disabling it
3. Add TURN server for better NAT traversal
4. Close other bandwidth-heavy applications

### Call Not Appearing
1. Verify WebSocket is connected (check browser console)
2. Ensure both users are in a private chat
3. Try refreshing the page
4. Check if browser notifications are blocked

## API Reference

### WebSocket Messages

#### Call Initiation (Caller → Server)
```json
{
    "type": "call_initiation",
    "receiver_username": "string",
    "offer": {
        "type": "offer",
        "sdp": "string"
    }
}
```

#### Call Answer (Receiver → Server)
```json
{
    "type": "call_answer",
    "call_id": "integer",
    "answer": {
        "type": "answer",
        "sdp": "string"
    }
}
```

#### ICE Candidate (Both → Server)
```json
{
    "type": "ice_candidate",
    "call_id": "integer",
    "candidate": {
        "candidate": "string",
        "sdpMLineIndex": "integer",
        "sdpMid": "string"
    }
}
```

#### Call Decline (Receiver → Server)
```json
{
    "type": "call_decline",
    "call_id": "integer"
}
```

#### Call End (Either → Server)
```json
{
    "type": "call_end",
    "call_id": "integer"
}
```

## Future Enhancements

Potential improvements:
1. Group video calls (multiple participants)
2. Call recording
3. Call history and statistics
4. Automatic retry on connection failure
5. Custom STUN/TURN server configuration
6. Call forwarding
7. Voicemail when call missed
8. Call quality indicators
9. Better handling of network disconnections
10. Call scheduling

## Security Considerations

### Current Implementation
- WebRTC connections are peer-to-peer (not routed through server)
- Signaling happens over WebSocket (same security as chat messages)
- No end-to-end encryption for video/audio (WebRTC default)

### Recommended Enhancements
1. Add end-to-end encryption for signaling
2. Implement SFU (Selective Forwarding Unit) for group calls
3. Add rate limiting for call initiation
4. Log call attempts for security audit
5. Validate caller/receiver relationship before initiating

## Support

For issues or questions, please:
1. Check browser console for error messages
2. Review application logs
3. Test with different browsers/networks
4. Contact technical support with detailed error information

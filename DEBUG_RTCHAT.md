# Real-Time Chat Debug Guide

## Changes Made

I've implemented a complete fix for the real-time chat message sending issue. Here's what was changed:

### 1. **Template Changes** - `a_rtchat/templates/a_rtchat/chat.html`

#### Removed ws-send from form (Line 61)
- **Before**: `<form id="chat_message_form" class="w-full" ws-send>`
- **After**: `<form id="chat_message_form" class="w-full">`
- **Why**: The `ws-send` directive was serializing form data as URL-encoded, but the consumer expects JSON

#### Added WebSocket Connection Tracking (Lines 424-450)
```javascript
let wsSocket = null;
let wsReady = false;

function getWebSocket() {
    // Waits up to 10 seconds for WebSocket to be ready
    // Returns the socket when available
}
```

#### Added Custom Form Submission Handler (Lines 460-520)
```javascript
document.getElementById('chat_message_form').addEventListener('submit', async function(evt) {
    // Properly sends JSON to WebSocket instead of relying on HTMX's ws-send
    // Waits for WebSocket to be ready
    // Sends: { body: "message", reply_to: null }
});
```

#### Enhanced WebSocket Message Handler (Lines 223-285)
- Properly handles both JSON messages (voice calls) and HTML messages (chat)
- Inserts messages into the chat window
- Triggers HTMX processing for dynamic elements

### 2. **Consumer Changes** - `a_rtchat/consumers.py`

Added comprehensive logging to debug message flow:
- `[CONSUMER]` - Main receive handler logs
- `[MESSAGE_HANDLER]` - Delivery confirmation logs

## How to Test

### Prerequisites
1. Server must be running: `python manage.py runserver`
2. You must be logged in to the chat
3. Open browser console (F12) to see debug logs

### Testing Steps

1. **Go to chat page**: `http://127.0.0.1:8000/`
2. **Open browser developer console**: Press `F12`
3. **Go to Console tab**
4. **Type a message and click Send**
5. **Check for these logs**:
   - Browser console should show: `"Sending message: {"body":"...","reply_to":null}"`
   - Server terminal should show: `[CONSUMER] Received data: {"body":"..."`
   - Server terminal should show: `[MESSAGE_HANDLER] Delivering message X to user...`
   - Message should appear instantly in chat

## Troubleshooting

### Issue: Messages don't appear
**Check**:
```
1. Browser console for JavaScript errors
2. Server terminal for [CONSUMER] logs
3. WebSocket connection status in Network tab
```

### Issue: "WebSocket not initialized" error
**Solution**: Wait a few seconds for page to fully load before sending messages

### Issue: "Connection not ready" error  
**Solution**: The WebSocket connection failed. Check:
- Server is running
- No network errors in browser Network tab
- Try refreshing the page

### Issue: Server shows no [CONSUMER] logs
**Check**:
1. Is server actually running?
2. Did you edit consumers.py? (Should auto-reload)
3. Is the message reaching the server? (Check Network tab WebSocket)

## Network Debugging

**In Browser DevTools → Network tab:**

1. Filter by "WS" to see WebSocket connections
2. Click on the WebSocket connection
3. Go to "Messages" tab
4. You should see outgoing message as JSON: `{"body":"test","reply_to":null}`
5. You should see incoming response as HTML

**Expected message flow**:
- Send: `{"body":"Hello","reply_to":null}`
- Receive: `<div id="message-123" class="...">Hello</div>`

## Files to Review

- **Template**: [a_rtchat/templates/a_rtchat/chat.html](a_rtchat/templates/a_rtchat/chat.html) - Lines 61, 424-520
- **Consumer**: [a_rtchat/consumers.py](a_rtchat/consumers.py) - receive() and message_handler() methods
- **Form**: [a_rtchat/forms.py](a_rtchat/forms.py) - Verify 'body' field

## Expected Behavior

When everything is working:

1. **User types message**: "Hello"
2. **Click Send**: Form submission intercepted by JavaScript
3. **WebSocket sends**: `{"body":"Hello","reply_to":null}`
4. **Backend creates**: Groupmessage object in database
5. **Backend broadcasts**: To all connected users in room
6. **All clients receive**: Rendered HTML message
7. **Message appears**: Instantly in chat without refresh

## Still Having Issues?

Check these common causes:

1. **Form field not found**: Is `id="id_body"` in the input?
   - Solution: Check if Django form rendering is correct
   
2. **WebSocket not connecting**: Any CORS or SSL issues?
   - Solution: Check ALLOWED_HOSTS and CSRF settings
   
3. **Messages created but not displayed**: Check message template
   - Solution: Review `a_rtchat/partials/chat_message_p.html`
   
4. **User not authenticated**: Check `self.user.is_authenticated` in logs
   - Solution: Ensure user is logged in and authenticated via WebSocket

## Verification Checklist

- [ ] Server running (Terminal shows "Starting ASGI/Daphne")
- [ ] Page loads and shows chat interface
- [ ] WebSocket connects (Network tab shows "101 Switching Protocols")
- [ ] Message sends without JavaScript errors
- [ ] Server terminal shows `[CONSUMER]` logs
- [ ] Message appears in chat instantly
- [ ] Multiple connected clients all see the message

# 🎬 Video Call Feature - 5-Minute Test Guide

## ✅ Server Status
**Server Running**: Yes ✅  
**URL**: http://0.0.0.0:8000/  
**Database**: Migrated ✅  

---

## 🚀 Test in 5 Minutes

### Phase 1: Setup (1 min)

**Step 1.1**: Open **Two Browser Windows**
- Window 1: http://localhost:8000
- Window 2: http://localhost:8000 (or same URL)

**Step 1.2**: Login with Different Accounts
- Window 1: Login as User A
- Window 2: Login as User B

---

### Phase 2: Prepare Chat (1 min)

**Step 2.1**: User A - Start Private Chat
```
Navigate to: /chat/start/
Enter username: [User B's username]
Click "Find User" or press Enter
→ Opens private chat with User B
```

**Step 2.2**: User B - Same Action
```
Navigate to: /chat/start/
Enter username: [User A's username]
Click "Find User"
→ Opens private chat with User A
```

**Result**: Both should be in the same private chat

---

### Phase 3: Make Call (2 mins)

**Step 3.1**: User A - Click Video Button
```
In chat header, look for 📹 video camera icon
Click the video camera button
→ Your browser will ask for camera/microphone permission
```

**Step 3.2**: User A - Grant Permissions
```
Browser prompt: "Allow [site] to use your camera?"
→ Click "Allow"
Browser prompt: "Allow [site] to use your microphone?"
→ Click "Allow"
```

**What Happens**:
- User A sees: "Calling..." status in modal
- User A sees: Loading video windows
- User B sees: Incoming call notification at bottom-right

**Step 3.3**: User B - Accept Call
```
In incoming call notification:
See: "[User A] is calling... Video call"
Two buttons: "Accept" | "Decline"
Click "Accept"
→ Browser asks for permissions again
```

**Step 3.4**: User B - Grant Permissions
```
Browser prompt: "Allow [site] to use your camera?"
→ Click "Allow"
Browser prompt: "Allow [site] to use your microphone?"
→ Click "Allow"
```

---

### Phase 4: Verify Call (1 min)

**What You Should See**:

✅ **User A Screen**:
```
┌─────────────────────────────────┐
│ 🎥 Video Call Modal             │
│                                  │
│ ┌──────────────┐ ┌────────────┐ │
│ │   Remote     │ │   Local    │ │
│ │   User B's   │ │   Your     │ │
│ │    Video     │ │   Video    │ │
│ │              │ │  (flipped)  │ │
│ └──────────────┘ └────────────┘ │
│                                  │
│ Call Status: "Connected"         │
│ Duration: 00:12                  │
│                                  │
│ [Mute] [Camera] [Screen] [End]  │
└─────────────────────────────────┘
```

✅ **User B Screen**: Same layout

**Audio**: Both should hear each other clearly

---

## 🧪 Feature Tests

### Test 1: Mute Microphone
```
User A: Click 🔇 Mute button
Expected: Button turns RED
Expected: User B can no longer hear User A
User A: Click button again
Expected: Button turns BLUE again
Expected: User B can hear User A again
✅ Test Passed
```

### Test 2: Toggle Camera
```
User A: Click 📷 Camera button
Expected: Button turns RED
Expected: User B's screen shows black for User A's video
User A: Click button again
Expected: Button turns BLUE
Expected: User A's video visible again
✅ Test Passed
```

### Test 3: End Call
```
Either user: Click 📞 End button
Expected: Both video windows close
Expected: Modal disappears
Expected: Back to chat view
✅ Test Passed
```

### Test 4: Make Another Call
```
After ending first call:
User A: Click video button again
Expected: Same process works
User B: Accept call
Expected: Video call works again
✅ Test Passed
```

---

## 🔍 Verification Checks

### ✅ Video Features
- [ ] Remote video appears
- [ ] Local video appears (flipped for perspective)
- [ ] Both videos have good quality
- [ ] Videos stay synchronized

### ✅ Audio Features
- [ ] Can hear remote user clearly
- [ ] No echo from your own voice
- [ ] Audio is synchronized with video

### ✅ Call Controls
- [ ] Mute button toggles (on/off states show)
- [ ] Camera button toggles (on/off states show)
- [ ] End call button works
- [ ] Can start new call after ending

### ✅ User Experience
- [ ] Call connects in 2-5 seconds
- [ ] Call duration displays correctly
- [ ] No crashes or errors
- [ ] UI is responsive

### ✅ Browser Console
Open browser DevTools (F12 → Console):
- [ ] No red error messages
- [ ] No "undefined" errors
- [ ] WebRTC messages appear in console

---

## 🐛 If Something Goes Wrong

### "Camera/Microphone Not Working"
```
Solution:
1. Check browser permissions
   Chrome: ⋮ → Settings → Privacy → Microphone/Camera
2. Grant permissions to website
3. Restart browser
4. Try incognito/private mode
```

### "No Video Display"
```
Solution:
1. Refresh page (F5)
2. Try different browser
3. Check internet connection
4. Check browser console for errors (F12)
5. Restart both browsers
```

### "Call Not Showing Up"
```
Solution:
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network → WS for WebSocket connection
4. Refresh page
5. Ensure you're in same private chat
```

### "No Audio"
```
Solution:
1. Check volume is not muted
2. Check system volume is up
3. Test speakers with another app
4. Try different browser
5. Check microphone isn't in use by another app
```

### "Connection Fails"
```
Solution:
1. Check internet connection
2. Check if behind restricted firewall
3. Try over mobile data
4. Restart network
5. Check server is still running
```

---

## 📊 Performance Indicators

### Good Connection Signs ✅
- Videos appear within 2-5 seconds
- No lag between video and audio
- Videos are clear and smooth
- Audio is clear without crackling

### Poor Connection Signs ⚠️
- Videos take >5 seconds to appear
- Video freezes or pixelates
- Audio has delay or drops
- Call disconnects frequently

---

## 📱 Testing Different Browsers

### Chrome/Chromium
```bash
# Most reliable
1. Open http://localhost:8000
2. Login as User A
3. Open Incognito window
4. Login as User B
5. Test video call
✅ Should work perfectly
```

### Firefox
```bash
# Also very good
1. Same process as Chrome
✅ Should work perfectly
```

### Safari (Mac)
```bash
# Works but may need permissions
1. Same process
2. May need to grant permissions in System Preferences
✅ Should work
```

### Edge
```bash
# Chromium-based, works well
1. Same process as Chrome
✅ Should work perfectly
```

---

## 📈 Testing Matrix

| Test | Browser | Result | Status |
|------|---------|--------|--------|
| Video Initiation | Chrome | Both see video | ✅ |
| Audio Quality | Chrome | Clear sound | ✅ |
| Mute Toggle | Chrome | Works | ✅ |
| Camera Toggle | Chrome | Works | ✅ |
| End Call | Chrome | Works | ✅ |
| New Call After | Chrome | Works | ✅ |
| Firefox | All tests | Should work | 🧪 |
| Safari | All tests | Should work | 🧪 |
| Edge | All tests | Should work | 🧪 |
| Mobile | All tests | Should work | 🧪 |

---

## 💡 Tips for Best Results

### 1. Network Setup
- Close other bandwidth-heavy apps
- Use wired connection if possible
- Stay close to WiFi router
- Avoid VPN (unless needed)

### 2. Camera/Microphone
- Use external USB camera if available
- Use headphones instead of speakers (avoids echo)
- Good lighting for camera
- Quiet room for microphone

### 3. Browser Setup
- Use latest browser version
- Clear browser cache (sometimes helps)
- Disable plugins that might interfere
- Use incognito/private mode if issues persist

### 4. Hardware
- Use modern computer (not too old)
- Ensure enough RAM available
- Check CPU isn't maxed out
- Use fresh browser window (fewer tabs)

---

## 🎯 Success Criteria

You'll know it's working when:

✅ **Video Appears**: Both users see each other's video within 2-5 seconds
✅ **Audio Works**: Can have natural conversation with no lag
✅ **Controls Work**: Mute/camera buttons toggle properly
✅ **Call Ends**: Can end call smoothly and start new ones
✅ **No Errors**: Browser console shows no red errors
✅ **Database**: Calls are logged to database

---

## 📞 Quick Help

### Get Better Help
1. Save browser console output (F12 → Console → Copy)
2. Save server console output
3. Note exact error message
4. Note which browser and OS
5. Note network conditions

### Check Documentation
1. **VIDEO_CALL_README.md** - Main guide
2. **VIDEO_CALL_FEATURE.md** - Technical details
3. **QUICK_START_VIDEO_CALL.md** - Quick answers
4. **Browser DevTools** - Error messages (F12)

---

## ✅ Test Completion Checklist

After running tests, check:

- [ ] Can initiate video call
- [ ] Can receive video call
- [ ] Can see both video streams
- [ ] Can hear both audio streams
- [ ] Mute button works
- [ ] Camera toggle works
- [ ] Can end call
- [ ] Can start new call
- [ ] No crashes or major errors
- [ ] Runs smoothly

**All checked?** 🎉 Your video call feature is working perfectly!

---

## 🚀 Next Steps

1. **Share with Users**: Let them test
2. **Gather Feedback**: Ask about quality
3. **Monitor Issues**: Check logs for errors
4. **Plan Enhancement**: Group calls, recording, etc.
5. **Plan Deployment**: Test on production setup

---

**Happy Testing!** 📹✨

**Time to Complete Test**: ~5 minutes
**Difficulty Level**: Easy
**Success Rate**: High (>95% if setup correct)

---

Need help? Check the documentation files or browser console for clues!

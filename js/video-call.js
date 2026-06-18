// WebRTC Video Call Manager
class VideoCallManager {
    constructor() {
        this.peerConnection = null;
        this.localStream = null;
        this.remoteStream = null;
        this.currentCallId = null;
        this.currentCallerId = null;
        this.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
            { urls: 'stun:stun3.l.google.com:19302' },
            { urls: 'stun:stun4.l.google.com:19302' }
        ];
        this.micEnabled = true;
        this.cameraEnabled = true;
        this.screenStream = null;
        this.cameraStream = null;
        this.isScreenSharing = false;
        this.callDurationInterval = null;
        this.callStartTime = null;
        this.alpineState = null;
    }

    isSecureContext() {
        return window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    }

    setAlpineState(state) {
        this.alpineState = state;
    }

    async initializeCall(recipientUsername, chatroomName) {
        try {
            if (!this.isSecureContext()) {
                const port = location.port || '8000';
                const secureUrl = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
                    ? `http://localhost:${port}`
                    : `https://${location.hostname}:${port}`;
                this.handleCallError(`Camera/microphone access requires HTTPS or localhost. Open the app on ${secureUrl} or use HTTPS.`);
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.handleCallError('Your browser does not support camera/microphone access. Use a modern browser like Chrome, Firefox, Edge, or Safari.');
                return;
            }

            // Get local media stream
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true },
                video: { width: { ideal: 1280 }, height: { ideal: 720 } }
            });
            this.cameraStream = this.localStream;

            // Setup local video
            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
                document.getElementById('local-loading').classList.add('hidden');
            }

            // Create peer connection
            this.createPeerConnection();

            // Add tracks to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });

            // Create and send offer
            const offer = await this.peerConnection.createOffer({
                offerToReceiveAudio: true,
                offerToReceiveVideo: true
            });

            await this.peerConnection.setLocalDescription(offer);

            // Send offer through WebSocket
            window.ws.send(JSON.stringify({
                type: 'call_initiation',
                receiver_username: recipientUsername,
                offer: this.descriptionToJson(offer)
            }));

            console.log('📞 Call initiated with offer sent');
            this.updateCallStatus('Calling...');

        } catch (err) {
            console.error('❌ Error initializing call:', err);
            this.handleCallError('Failed to access camera/microphone. Please check permissions. ' + (err && err.name ? err.name + ': ' : '') + (err && err.message ? err.message : '')); 
        }
    }

    createPeerConnection() {
        this.peerConnection = new RTCPeerConnection({
            iceServers: this.iceServers
        });

        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                window.ws.send(JSON.stringify({
                    type: 'ice_candidate',
                    call_id: this.currentCallId,
                    candidate: this.candidateToJson(event.candidate)
                }));
            }
        };

        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            console.log('📹 Received remote track');
            if (!this.remoteStream) {
                this.remoteStream = new MediaStream();
            }
            this.remoteStream.addTrack(event.track);

            const remoteVideo = document.getElementById('remote-video');
            if (remoteVideo) {
                remoteVideo.srcObject = this.remoteStream;
                document.getElementById('remote-loading').classList.add('hidden');
                remoteVideo.play().catch(() => {});
            }
        };

        // Handle connection state changes
        this.peerConnection.onconnectionstatechange = () => {
            console.log('🔌 Connection state:', this.peerConnection.connectionState);
            if (this.peerConnection.connectionState === 'failed') {
                this.handleCallError('Connection failed. Please try again.');
            }
        };

        // Handle ICE connection state
        this.peerConnection.oniceconnectionstatechange = () => {
            console.log('🧊 ICE connection state:', this.peerConnection.iceConnectionState);
        };
    }

    async handleIncomingCall(data) {
        try {
            this.currentCallId = data.call_id;
            const offer = this.jsonToDescription(data.offer);

            if (!this.isSecureContext()) {
                const port = location.port || '8000';
                const secureUrl = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
                    ? `http://localhost:${port}`
                    : `https://${location.hostname}:${port}`;
                this.handleCallError(`Camera/microphone access requires HTTPS or localhost. Open the app on ${secureUrl} or use HTTPS.`);
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.handleCallError('Your browser does not support camera/microphone access. Use a modern browser like Chrome, Firefox, Edge, or Safari.');
                return;
            }

            // Get local media stream
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true },
                video: { width: { ideal: 1280 }, height: { ideal: 720 } }
            });
            this.cameraStream = this.localStream;

            // Setup local video
            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
                document.getElementById('local-loading').classList.add('hidden');
            }

            // Create peer connection
            this.createPeerConnection();

            // Add tracks to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });

            // Set remote description
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));

            // Create and send answer
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);

            window.ws.send(JSON.stringify({
                type: 'call_answer',
                call_id: this.currentCallId,
                answer: this.descriptionToJson(answer)
            }));

            console.log('✅ Call answered');
            this.updateCallStatus('Connected');
            this.startCallDuration();

        } catch (err) {
            console.error('❌ Error handling incoming call:', err);
            this.handleCallError('Failed to access camera/microphone for incoming call. ' + (err && err.name ? err.name + ': ' : '') + (err && err.message ? err.message : ''));
        }
    }

    async handleCallAnswer(data) {
        try {
            this.currentCallId = data.call_id;
            const answer = this.jsonToDescription(data.answer);
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            console.log('✅ Received answer');
            this.updateCallStatus('Connected');
            this.startCallDuration();
        } catch (err) {
            console.error('❌ Error handling answer:', err);
        }
    }

    async handleIceCandidate(data) {
        try {
            if (data.from_user !== this.getCurrentUsername()) {
                const candidate = this.jsonToCandidate(data.candidate);
                await this.peerConnection.addIceCandidate(candidate);
            }
        } catch (err) {
            console.error('❌ Error adding ICE candidate:', err);
        }
    }

    toggleMicrophone() {
        if (this.localStream) {
            this.localStream.getAudioTracks().forEach(track => {
                track.enabled = !track.enabled;
                this.micEnabled = track.enabled;
            });
            const btn = document.getElementById('toggle-mic');
            btn.classList.toggle('bg-red-500/80', !this.micEnabled);
            btn.classList.toggle('bg-slate-800/60', this.micEnabled);
        }
    }

    toggleCamera() {
        if (this.localStream) {
            this.localStream.getVideoTracks().forEach(track => {
                track.enabled = !track.enabled;
                this.cameraEnabled = track.enabled;
            });
            const btn = document.getElementById('toggle-camera');
            btn.classList.toggle('bg-red-500/80', !this.cameraEnabled);
            btn.classList.toggle('bg-slate-800/60', this.cameraEnabled);
        }
    }

    async toggleScreenShare() {
        try {
            if (!this.peerConnection) {
                console.warn('⚠️ Cannot toggle screen share, no active peer connection');
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
                console.warn('⚠️ Screen sharing is not supported by this browser');
                return;
            }

            if (this.isScreenSharing) {
                await this.stopScreenShare();
                return;
            }

            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: { cursor: 'always' },
                audio: false
            });

            const screenTrack = screenStream.getVideoTracks()[0];
            const sender = this.peerConnection
                .getSenders()
                .find(s => s.track && s.track.kind === 'video');

            if (!sender) {
                console.warn('⚠️ No video sender available for screen share');
                return;
            }

            await sender.replaceTrack(screenTrack);
            this.screenStream = screenStream;
            this.isScreenSharing = true;

            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = screenStream;
            }

            screenTrack.onended = async () => {
                await this.stopScreenShare();
            };

            console.log('🖥️ Screen share started');
        } catch (err) {
            console.error('❌ Error toggling screen share:', err);
        }
    }

    async stopScreenShare() {
        try {
            if (this.screenStream) {
                this.screenStream.getTracks().forEach(track => track.stop());
                this.screenStream = null;
            }
            const sender = this.peerConnection
                .getSenders()
                .find(s => s.track && s.track.kind === 'video');

            if (!sender) {
                return;
            }

            if (!this.cameraStream) {
                this.cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                    audio: { echoCancellation: true, noiseSuppression: true }
                });
            }

            const cameraTrack = this.cameraStream.getVideoTracks()[0];
            await sender.replaceTrack(cameraTrack);
            this.localStream = this.cameraStream;
            this.isScreenSharing = false;

            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
            }

            console.log('🛑 Screen share stopped, camera restored');
        } catch (err) {
            console.error('❌ Error stopping screen share:', err);
        }
    }

    declineCall() {
        if (this.currentCallId) {
            window.ws.send(JSON.stringify({
                type: 'call_decline',
                call_id: this.currentCallId
            }));
        }
        this.closeCall();
    }

    endCall() {
        if (this.currentCallId) {
            window.ws.send(JSON.stringify({
                type: 'call_end',
                call_id: this.currentCallId
            }));
        }
        this.closeCall();
    }

    closeCall() {
        // Stop screen share stream if active
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }
        // Stop all tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        if (this.remoteStream) {
            this.remoteStream.getTracks().forEach(track => track.stop());
            this.remoteStream = null;
        }

        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(track => track.stop());
            this.cameraStream = null;
        }

        this.isScreenSharing = false;

        // Close peer connection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        // Clear call duration
        if (this.callDurationInterval) {
            clearInterval(this.callDurationInterval);
            this.callDurationInterval = null;
        }

        // Reset UI
        this.currentCallId = null;
        this.currentCallerId = null;

        // Hide modals - find Alpine element and update its state
        const alpineElement = document.querySelector('[x-data]');
        if (alpineElement && alpineElement.__x) {
            const alpineData = alpineElement.__x.$data;
            alpineData.videoCallActive = false;
            alpineData.incomingCall = false;
        }
    }

    startCallDuration() {
        this.callStartTime = Date.now();
        this.callDurationInterval = setInterval(() => {
            if (this.callStartTime) {
                const duration = Math.floor((Date.now() - this.callStartTime) / 1000);
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                const durationText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                const durationEl = document.getElementById('call-duration');
                if (durationEl) {
                    durationEl.textContent = durationText;
                }
            }
        }, 1000);
    }

    updateCallStatus(status) {
        const statusEl = document.getElementById('call-status-text');
        if (statusEl) {
            statusEl.textContent = status;
        }
    }

    handleCallError(message) {
        console.error('Call error:', message);
        alert(message);
        this.closeCall();
    }

    getCurrentUsername() {
        // Get from the page or DOM
        return document.querySelector('[data-current-user]')?.getAttribute('data-current-user') || '';
    }

    // Serialization helpers
    descriptionToJson(description) {
        return {
            type: description.type,
            sdp: description.sdp
        };
    }

    jsonToDescription(json) {
        return {
            type: json.type,
            sdp: json.sdp
        };
    }

    candidateToJson(candidate) {
        return {
            candidate: candidate.candidate,
            sdpMLineIndex: candidate.sdpMLineIndex,
            sdpMid: candidate.sdpMid
        };
    }

    jsonToCandidate(json) {
        return new RTCIceCandidate({
            candidate: json.candidate,
            sdpMLineIndex: json.sdpMLineIndex,
            sdpMid: json.sdpMid
        });
    }
}

// Initialize manager
const videoCallManager = new VideoCallManager();

// Make it globally accessible
window.videoCallManager = videoCallManager;

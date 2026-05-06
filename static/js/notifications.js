// static/js/notifications.js
/**
 * Handles Firebase Cloud Messaging (FCM) token registration for both Web and Capacitor App.
 */
async function initializeNotifications() {
    // 1. Detect environment
    const isCapacitor = window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.PushNotifications;

    if (isCapacitor) {
        const { PushNotifications } = window.Capacitor.Plugins;
        
        // Request permissions
        let permStatus = await PushNotifications.checkPermissions();
        
        if (permStatus.receive === 'prompt') {
            permStatus = await PushNotifications.requestPermissions();
        }

        if (permStatus.receive === 'granted') {
            // Register with Apple / Google to get a token
            await PushNotifications.register();
            
            // Create the custom sound channel for Android
            if (window.Capacitor.getPlatform() === 'android') {
                await PushNotifications.createChannel({
                    id: 'ihr_custom_sound',
                    name: 'I-HR Notifications',
                    description: 'Notifications for I-HR App',
                    sound: 'notification_sound', // matches the filename in res/raw
                    importance: 5, // Max importance
                    visibility: 1,
                    vibration: true
                });
                console.log('FCM Custom Sound Channel created');
            }
            
            // Listen for the token
            PushNotifications.addListener('registration', async (token) => {
                console.log('Push registration success');
                await registerTokenOnServer(token.value, 'mobile');
            });
            
            // Listen for incoming notifications while app is open
            PushNotifications.addListener('pushNotificationReceived', (notification) => {
                console.log('Push received: ', notification);
                // Show an in-app alert or notification
                const title = notification.title || 'New Notification';
                const body = notification.body || '';
                
                // Show a simple but effective alert if app is open
                if (window.showToast) {
                    window.showToast(`${title}: ${body}`, 'info');
                } else {
                    alert(`${title}\n\n${body}`);
                }
            });

            // Listen for user clicking on a notification
            PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
                console.log('Push action performed', notification);
                // You can redirect the user here if needed
            });
        }
    } else {
        // For Web: 
        if ('serviceWorker' in navigator) {
            try {
                // Register the service worker I just created
                const registration = await navigator.serviceWorker.register('/static/firebase-messaging-sw.js');
                console.log('Web Service Worker registered');

                // Check for Firebase (loaded via CDN in HTML)
                if (window.firebase) {
                    const messaging = firebase.messaging();
                    
                    // Request permission
                    const permission = await Notification.requestPermission();
                    if (permission === 'granted') {
                        // Get token using your VAPID KEY
                        const token = await messaging.getToken({ 
                            vapidKey: 'BOb0KDOU1SA09wiEuBTMwdBeEY92tvyxYE1CcoyNZyWHhZOlf4kzWYPsDE6eOlRaiaAK6pILpJaSU5FOUYleb2U',
                            serviceWorkerRegistration: registration 
                        });

                        if (token) {
                            await registerTokenOnServer(token, 'web');
                        }
                    }
                }
            } catch (err) {
                console.warn('Web FCM initialization failed:', err);
            }
        }
    }
}

async function registerTokenOnServer(token, deviceType) {
    try {
        const response = await fetch('/api/notifications/register-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token, device_type: deviceType })
        });
        const data = await response.json();
        if (data.success) {
            console.log('FCM Token registered on server');
        }
    } catch (e) {
        console.error('Error registering FCM token:', e);
    }
}

// Initialize when the dashboard loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the user is logged in (sidebar is a good indicator)
    if (document.querySelector('.enhanced-sidebar') || document.querySelector('.nav-menu')) {
        initializeNotifications();
    }
});

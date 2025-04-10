// Firebase Authentication Utility
const firebaseAuth = (function() {
  // Get auth instance
  const auth = firebase.auth();
  
  // Cache for the ID token
  let cachedIdToken = '';
  
  // Send token to backend to create or validate session
  const sendTokenToBackend = async (idToken) => {
    try {
      const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ idToken })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error sending token to backend:', error);
      throw error;
    }
  };
  
  // Function to sign out
  const signOut = async () => {
    try {
      // Sign out from Firebase
      await auth.signOut();
      
      // Notify backend about logout
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch (e) {
        console.error('Backend logout notification failed:', e);
      }
      
      // Redirect to login page
      window.location.href = '/login';
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };
  
  // Get current ID token
  const getIdToken = async (forceRefresh = false) => {
    if (cachedIdToken && !forceRefresh) {
      return cachedIdToken;
    }
    
    const currentUser = auth.currentUser;
    if (currentUser) {
      try {
        const idToken = await currentUser.getIdToken(forceRefresh);
        cachedIdToken = idToken;
        return idToken;
      } catch (error) {
        console.error('Error getting ID token:', error);
        return null;
      }
    }
    
    return null;
  };
  
  // Get current user
  const getCurrentUser = () => {
    return auth.currentUser;
  };
  
  // Check if user is authenticated
  const isAuthenticated = () => {
    return !!auth.currentUser;
  };
  
  // Update user profile
  const updateProfile = async (displayName, photoURL) => {
    const currentUser = auth.currentUser;
    if (currentUser) {
      const updateData = {};
      if (displayName) updateData.displayName = displayName;
      if (photoURL) updateData.photoURL = photoURL;
      
      try {
        await currentUser.updateProfile(updateData);
        return true;
      } catch (error) {
        console.error('Error updating profile:', error);
        throw error;
      }
    }
    return false;
  };
  
  // Listen for auth state changes
  auth.onAuthStateChanged(async (user) => {
    if (user) {
      // User is signed in
      try {
        // Get fresh token
        const idToken = await user.getIdToken(true);
        cachedIdToken = idToken;
        
        // Send token to backend
        await sendTokenToBackend(idToken);
      } catch (error) {
        console.error('Error in auth state change handler:', error);
      }
    } else {
      // User is signed out
      cachedIdToken = '';
    }
  });
  
  // Return public API
  return {
    signOut,
    getIdToken,
    getCurrentUser,
    isAuthenticated,
    updateProfile,
    sendTokenToBackend
  };
})();

// Initialize UI elements when document is ready
document.addEventListener('DOMContentLoaded', function() {
  // Check for Auth State and redirect if needed
  firebase.auth().onAuthStateChanged(function(user) {
    // If on login page but already logged in, redirect to dashboard
    const isLoginPage = window.location.pathname === '/login';
    const isRegisterPage = window.location.pathname === '/register';
    
    if (user && (isLoginPage || isRegisterPage)) {
      window.location.href = '/dashboard';
    }
  });
  
  // Handle logout button clicks
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async function(e) {
      e.preventDefault();
      
      try {
        await firebaseAuth.signOut();
      } catch (error) {
        console.error('Error signing out:', error);
      }
    });
  }
  
  // Add auth token to all API requests
  const originalFetch = window.fetch;
  window.fetch = async function(url, options = {}) {
    // Only add token to API requests to our backend
    if (url.toString().startsWith('/api/')) {
      const token = await firebaseAuth.getIdToken();
      if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return originalFetch.call(this, url, options);
  };
});

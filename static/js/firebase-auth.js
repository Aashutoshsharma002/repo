import {
    getAuth,
    onAuthStateChanged,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    updateProfile,
    signOut as firebaseSignOut,
    sendPasswordResetEmail,
    getIdToken
} from 'https://www.gstatic.com/firebasejs/11.0.2/firebase-auth.js';

// Use already-initialized auth instance from the HTML
const auth = window.auth;
if (!auth) {
    console.error("Firebase not initialized. Did you call initializeApp() in your HTML first?");
}

// Track user session
onAuthStateChanged(auth, user => {
    if (user) {
        const userData = {
            uid: user.uid,
            email: user.email,
            displayName: user.displayName || user.email.split('@')[0],
            photoURL: user.photoURL,
            lastLogin: new Date().toISOString()
        };
        localStorage.setItem('currentUser', JSON.stringify(userData));

        const nav = document.getElementById('main-nav');
        if (nav) nav.style.display = 'block';

        if (['/login', '/register'].includes(window.location.pathname)) {
            window.location.href = '/';
        } else if (typeof onAuthSuccess === 'function') {
            onAuthSuccess(user);
        }

        setupApiRequestInterceptor();
    } else {
        localStorage.removeItem('currentUser');
        const nav = document.getElementById('main-nav');
        if (nav) nav.style.display = 'none';

        if (!['/login', '/register'].includes(window.location.pathname)) {
            window.location.href = '/login';
        }
    }
});

// Attach token to API requests
function setupApiRequestInterceptor() {
    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {}) {
        if (url.startsWith('/api/')) {
            try {
                const user = auth.currentUser;
                if (user) {
                    const token = await getIdToken(user);
                    options.headers = options.headers || {};
                    options.headers['Authorization'] = `Bearer ${token}`;
                }
            } catch (err) {
                console.error("Error adding token to fetch:", err);
            }
        }
        return originalFetch(url, options);
    };
}

// Auth functions
function signInWithEmail(email, password) {
    return signInWithEmailAndPassword(auth, email, password)
        .catch(err => {
            console.error("Login error:", err);
            showError(err.message);
        });
}

function signUpWithEmail(email, password, name) {
    return createUserWithEmailAndPassword(auth, email, password)
        .then(cred => updateProfile(cred.user, { displayName: name }))
        .catch(err => {
            console.error("Signup error:", err);
            showError(err.message);
        });
}

function signOut() {
    firebaseSignOut(auth)
        .then(() => {
            localStorage.removeItem('currentUser');
            window.location.href = '/login';
        })
        .catch(err => {
            console.error("Sign out error:", err);
        });
}

function resetPassword(email) {
    sendPasswordResetEmail(auth, email)
        .then(() => showSuccess("Password reset email sent."))
        .catch(err => {
            console.error("Reset password error:", err);
            showError(err.message);
        });
}

// UI helpers
function showError(message) {
    const el = document.getElementById('error-message');
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    } else {
        alert(`Error: ${message}`);
    }
}

function showSuccess(message) {
    const el = document.getElementById('success-message');
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    } else {
        alert(`Success: ${message}`);
    }
}

function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }

    const id = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Make available globally
window.signInWithEmail = signInWithEmail;
window.signUpWithEmail = signUpWithEmail;
window.signOut = signOut;
window.resetPassword = resetPassword;
window.showError = showError;
window.showSuccess = showSuccess;
window.showToast = showToast;

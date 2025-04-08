// Global variables
let currentUser = null;
let currentBoard = null;

// Date formatting utility
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
window.formatDate = formatDate;

// Initialize Select2 for user selection
function initializeSelect2(selector) {
    $(selector).select2({
        placeholder: 'Search for users...',
        minimumInputLength: 3,
        ajax: {
            url: '/api/users/search',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    query: params.term
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(user => ({
                        id: user.id,
                        text: user.display_name || user.email
                    }))
                };
            },
            cache: true
        }
    });
}
window.initializeSelect2 = initializeSelect2;

// Create a new board
async function createBoard(name, description = '') {
    try {
        const response = await fetch('/api/boards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create board');
        }
        
        const board = await response.json();
        return board;
    } catch (error) {
        console.error('Error creating board:', error);
        showError(error.message);
        return null;
    }
}
window.createBoard = createBoard;

// Get all boards for the current user
async function getBoards() {
    try {
        const response = await fetch('/api/boards');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get boards');
        }
        
        const boards = await response.json();
        return boards;
    } catch (error) {
        console.error('Error getting boards:', error);
        showError(error.message);
        return [];
    }
}
window.getBoards = getBoards;

// Get a specific board by ID
async function getBoard(boardId) {
    try {
        const response = await fetch(`/api/boards/${boardId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get board');
        }
        
        const board = await response.json();
        return board;
    } catch (error) {
        console.error('Error getting board:', error);
        showError(error.message);
        return null;
    }
}
window.getBoard = getBoard;

// Add a user to a board
async function addUserToBoard(boardId, email) {
    try {
        const response = await fetch(`/api/boards/${boardId}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to add user to board');
        }
        
        const user = await response.json();
        return user;
    } catch (error) {
        console.error('Error adding user to board:', error);
        showError(error.message);
        return null;
    }
}
window.addUserToBoard = addUserToBoard;

// Remove a user from a board
async function removeUserFromBoard(boardId, userId) {
    try {
        const response = await fetch(`/api/boards/${boardId}/users/${userId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to remove user from board');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error removing user from board:', error);
        showError(error.message);
        return null;
    }
}
window.removeUserFromBoard = removeUserFromBoard;

// Create a new task
async function createTask(boardId, taskData) {
    try {
        const response = await fetch(`/api/tasks?board_id=${boardId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create task');
        }
        
        const task = await response.json();
        return task;
    } catch (error) {
        console.error('Error creating task:', error);
        showError(error.message);
        return null;
    }
}
window.createTask = createTask;

// Update a task
async function updateTask(taskId, taskData) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update task');
        }
        
        const task = await response.json();
        return task;
    } catch (error) {
        console.error('Error updating task:', error);
        showError(error.message);
        return null;
    }
}
window.updateTask = updateTask;

// Delete a task
async function deleteTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete task');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error deleting task:', error);
        showError(error.message);
        return null;
    }
}
window.deleteTask = deleteTask;

// Toggle task completion
async function toggleTaskCompletion(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/complete`, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update task completion');
        }
        
        const task = await response.json();
        return task;
    } catch (error) {
        console.error('Error updating task completion:', error);
        showError(error.message);
        return null;
    }
}
window.toggleTaskCompletion = toggleTaskCompletion;

// Update a board
async function updateBoard(boardId, boardData) {
    try {
        const response = await fetch(`/api/boards/${boardId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(boardData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update board');
        }
        
        const board = await response.json();
        return board;
    } catch (error) {
        console.error('Error updating board:', error);
        showError(error.message);
        return null;
    }
}
window.updateBoard = updateBoard;

// Delete a board
async function deleteBoard(boardId) {
    try {
        const response = await fetch(`/api/boards/${boardId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete board');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error deleting board:', error);
        showError(error.message);
        return null;
    }
}
window.deleteBoard = deleteBoard;

// Get current user data
async function getCurrentUser() {
    try {
        const response = await fetch('/api/auth/user');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get user data');
        }
        
        const user = await response.json();
        currentUser = user;
        return user;
    } catch (error) {
        console.error('Error getting user data:', error);
        showError(error.message);
        return null;
    }
}
window.getCurrentUser = getCurrentUser;

// Show toast notification
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
window.showToast = showToast;

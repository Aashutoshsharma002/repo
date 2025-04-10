// Boards functionality

document.addEventListener('DOMContentLoaded', function() {
  // Handle create board form
  const createBoardForm = document.getElementById('create-board-form');
  if (createBoardForm) {
    createBoardForm.addEventListener('submit', function(e) {
      const boardNameInput = document.getElementById('board-name');
      if (!boardNameInput.value.trim()) {
        e.preventDefault();
        // Show error message
        const errorElement = document.getElementById('board-error');
        errorElement.textContent = 'Board name cannot be empty';
        errorElement.classList.remove('d-none');
      }
    });
  }
  
  // Handle rename board form
  const renameBoardForm = document.getElementById('rename-board-form');
  if (renameBoardForm) {
    renameBoardForm.addEventListener('submit', function(e) {
      const boardNameInput = document.getElementById('edit-board-name');
      if (!boardNameInput.value.trim()) {
        e.preventDefault();
        // Show error message
        const errorElement = document.getElementById('rename-error');
        errorElement.textContent = 'Board name cannot be empty';
        errorElement.classList.remove('d-none');
      }
    });
  }
  
  // Handle add user form
  const addUserForm = document.getElementById('add-user-form');
  if (addUserForm) {
    addUserForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const emailInput = document.getElementById('user-email');
      const email = emailInput.value.trim();
      
      if (!email) {
        // Show error message
        const errorElement = document.getElementById('add-user-error');
        errorElement.textContent = 'Email cannot be empty';
        errorElement.classList.remove('d-none');
        return;
      }
      
      // Show loading state
      const submitBtn = document.querySelector('#add-user-form button[type="submit"]');
      const originalBtnText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="loading-spinner"></span> Adding...';
      
      try {
        // Get ID token
        const idToken = await firebaseAuth.getIdToken();
        
        // Add hidden input for ID token
        let tokenInput = document.getElementById('id-token');
        if (!tokenInput) {
          tokenInput = document.createElement('input');
          tokenInput.type = 'hidden';
          tokenInput.id = 'id-token';
          tokenInput.name = 'id_token';
          addUserForm.appendChild(tokenInput);
        }
        tokenInput.value = idToken;
        
        // Submit the form
        addUserForm.submit();
      } catch (error) {
        // Show error message
        const errorElement = document.getElementById('add-user-error');
        errorElement.textContent = error.message || 'Failed to add user';
        errorElement.classList.remove('d-none');
        
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }
    });
  }
  
  // Handle delete board confirmation
  const deleteBoardBtn = document.getElementById('delete-board-btn');
  if (deleteBoardBtn) {
    deleteBoardBtn.addEventListener('click', function(e) {
      if (!confirm('Are you sure you want to delete this board? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  }
  
  // Handle remove user confirmation
  const removeUserBtns = document.querySelectorAll('.remove-user-btn');
  if (removeUserBtns.length > 0) {
    removeUserBtns.forEach(btn => {
      btn.addEventListener('click', function(e) {
        const userName = this.getAttribute('data-user-name');
        if (!confirm(`Are you sure you want to remove ${userName} from this board?`)) {
          e.preventDefault();
        }
      });
    });
  }
});

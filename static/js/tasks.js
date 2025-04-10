// Tasks functionality

document.addEventListener('DOMContentLoaded', function() {
  // Initialize date picker for task forms
  const dueDateInputs = document.querySelectorAll('.due-date-input');
  if (dueDateInputs.length > 0) {
    dueDateInputs.forEach(input => {
      // Set min date to today
      const today = new Date();
      today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
      input.min = today.toISOString().slice(0, 16);
      
      // Set default value to today + 1 day if empty
      if (!input.value) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset());
        input.value = tomorrow.toISOString().slice(0, 16);
      }
    });
  }
  
  // Handle create task form validation
  const createTaskForm = document.getElementById('create-task-form');
  if (createTaskForm) {
    createTaskForm.addEventListener('submit', function(e) {
      const taskTitleInput = document.getElementById('task-title');
      const dueDateInput = document.getElementById('task-due-date');
      
      if (!taskTitleInput.value.trim()) {
        e.preventDefault();
        // Show error message
        const errorElement = document.getElementById('task-error');
        errorElement.textContent = 'Task title cannot be empty';
        errorElement.classList.remove('d-none');
      }
      
      if (!dueDateInput.value) {
        e.preventDefault();
        // Show error message
        const errorElement = document.getElementById('task-error');
        errorElement.textContent = 'Due date is required';
        errorElement.classList.remove('d-none');
      }
    });
  }
  
  // Handle edit task form validation
  const editTaskForms = document.querySelectorAll('.edit-task-form');
  if (editTaskForms.length > 0) {
    editTaskForms.forEach(form => {
      form.addEventListener('submit', function(e) {
        const taskTitleInput = this.querySelector('.task-title-input');
        const dueDateInput = this.querySelector('.due-date-input');
        
        if (!taskTitleInput.value.trim()) {
          e.preventDefault();
          // Show error message
          alert('Task title cannot be empty');
        }
        
        if (!dueDateInput.value) {
          e.preventDefault();
          // Show error message
          alert('Due date is required');
        }
      });
    });
  }
  
  // Handle task completion toggle
  const taskCheckboxes = document.querySelectorAll('.task-complete-checkbox');
  if (taskCheckboxes.length > 0) {
    taskCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
        // Submit the parent form
        this.closest('form').submit();
      });
    });
  }
  
  // Handle task assignment
  const assignTaskForms = document.querySelectorAll('.assign-task-form');
  if (assignTaskForms.length > 0) {
    assignTaskForms.forEach(form => {
      const select = form.querySelector('select[name="assigned_to"]');
      if (select) {
        // Initialize Select2
        $(select).select2({
          placeholder: 'Select members',
          allowClear: true,
          width: '100%',
          theme: "bootstrap-5"
        });
        
        // Auto-submit when selection changes
        $(select).on('change', function() {
          form.submit();
        });
      }
    });
  }
  
  // Handle delete task confirmation
  const deleteTaskBtns = document.querySelectorAll('.delete-task-btn');
  if (deleteTaskBtns.length > 0) {
    deleteTaskBtns.forEach(btn => {
      btn.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to delete this task?')) {
          e.preventDefault();
        }
      });
    });
  }
  
  // Format due dates to show "X days left" or "Overdue"
  const formatDueDates = () => {
    const dueDateElements = document.querySelectorAll('.due-date-display');
    
    if (dueDateElements.length > 0) {
      const now = new Date();
      
      dueDateElements.forEach(element => {
        const dueDateStr = element.getAttribute('data-due-date');
        const dueDate = new Date(dueDateStr);
        
        // Check if date is valid
        if (isNaN(dueDate.getTime())) {
          return;
        }
        
        // Calculate days difference
        const diffTime = dueDate - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        // Format the display text
        let displayText = '';
        
        if (diffDays < 0) {
          // Overdue
          element.classList.add('overdue');
          displayText = `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''}`;
        } else if (diffDays === 0) {
          // Due today
          displayText = 'Due today';
        } else {
          // Due in the future
          displayText = `Due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
        }
        
        element.textContent = displayText;
      });
    }
  };
  
  // Call once on page load
  formatDueDates();
});

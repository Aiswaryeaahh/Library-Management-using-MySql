// ==========================================
// UI Utilities
// ==========================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;font-size:1.2rem">&times;</button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// ==========================================
// API Calls & Rendering Core
// ==========================================

async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }
        
        return data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// ==========================================
// Dashboard Logic
// ==========================================

async function loadDashboardStats() {
    try {
        const stats = await fetchAPI('/api/stats');
        document.getElementById('stat-total-books').textContent = stats.total_books;
        document.getElementById('stat-available-books').textContent = stats.available_books;
        document.getElementById('stat-total-members').textContent = stats.total_members;
        document.getElementById('stat-active-loans').textContent = stats.active_loans;
    } catch (e) {
        console.error("Failed to load stats", e);
    }
}

async function loadDashboardRecentIssues() {
    try {
        const issues = await fetchAPI('/api/issues');
        const tbody = document.querySelector('#recent-issues-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        // Take only top 5 recent issues
        const recentIssues = issues.slice(0, 5);
        
        if (recentIssues.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No recent issues found</td></tr>';
            return;
        }
        
        recentIssues.forEach(issue => {
            const statusClass = issue.status === 'issued' ? 'status-issued' : 'status-returned';
            const statusText = issue.status.charAt(0).toUpperCase() + issue.status.slice(1);
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${issue.book_title}</strong></td>
                <td>${issue.member_name}</td>
                <td>${issue.issue_date}</td>
                <td>${issue.due_date}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load recent issues", e);
    }
}

// ==========================================
// Books Logic
// ==========================================

async function loadBooks(searchQuery = '') {
    try {
        const url = searchQuery ? `/api/books?search=${encodeURIComponent(searchQuery)}` : '/api/books';
        const books = await fetchAPI(url);
        
        const tbody = document.querySelector('#books-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (books.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">No books found</td></tr>';
            return;
        }
        
        books.forEach(book => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${book.id}</td>
                <td><strong>${book.title}</strong></td>
                <td>${book.author}</td>
                <td>${book.total_copies}</td>
                <td><span style="color: ${book.available_copies > 0 ? 'var(--secondary)' : 'var(--danger)'}; font-weight: 600;">${book.available_copies}</span></td>
                <td>
                    <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem" onclick='openEditBookModal(${JSON.stringify(book).replace(/'/g, "&#39;")})'>Edit</button>
                    <button class="btn btn-danger" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; margin-left: 0.5rem" onclick="deleteBook(${book.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load books", e);
    }
}

function searchBooks() {
    const query = document.getElementById('search-book-input').value;
    loadBooks(query);
}

async function addBook(event) {
    event.preventDefault();
    try {
        const data = {
            title: document.getElementById('add-book-title').value,
            author: document.getElementById('add-book-author').value,
            total_copies: parseInt(document.getElementById('add-book-copies').value)
        };
        
        const result = await fetchAPI('/api/books', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast(result.message);
        closeModal('addBookModal');
        document.getElementById('addBookForm').reset();
        loadBooks();
    } catch (e) {
        // Error handled in fetchAPI
    }
}

function openEditBookModal(book) {
    document.getElementById('edit-book-id').value = book.id;
    document.getElementById('edit-book-title').value = book.title;
    document.getElementById('edit-book-author').value = book.author;
    document.getElementById('edit-book-copies').value = book.total_copies;
    openModal('editBookModal');
}

async function editBook(event) {
    event.preventDefault();
    try {
        const id = document.getElementById('edit-book-id').value;
        const data = {
            title: document.getElementById('edit-book-title').value,
            author: document.getElementById('edit-book-author').value,
            total_copies: parseInt(document.getElementById('edit-book-copies').value)
        };
        
        const result = await fetchAPI(`/api/books/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        showToast(result.message);
        closeModal('editBookModal');
        loadBooks();
    } catch (e) {
        // Error handled in fetchAPI
    }
}

async function deleteBook(id) {
    if (!confirm('Are you sure you want to delete this book?')) return;
    
    try {
        const result = await fetchAPI(`/api/books/${id}`, {
            method: 'DELETE'
        });
        showToast(result.message);
        loadBooks();
    } catch (e) {
        // Error handled
    }
}

// ==========================================
// Members Logic
// ==========================================

async function loadMembers() {
    try {
        const members = await fetchAPI('/api/members');
        const tbody = document.querySelector('#members-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (members.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No members found</td></tr>';
            return;
        }
        
        members.forEach(member => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${member.id}</td>
                <td><strong>${member.name}</strong></td>
                <td>${member.email}</td>
                <td>${member.phone || '-'}</td>
                <td>${member.registered_date}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load members", e);
    }
}

async function addMember(event) {
    event.preventDefault();
    try {
        const data = {
            name: document.getElementById('add-member-name').value,
            email: document.getElementById('add-member-email').value,
            phone: document.getElementById('add-member-phone').value
        };
        
        const result = await fetchAPI('/api/members', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast(result.message);
        closeModal('addMemberModal');
        document.getElementById('addMemberForm').reset();
        loadMembers();
    } catch (e) {
        // Error handled in fetchAPI
    }
}

// ==========================================
// Issues Logic
// ==========================================

async function loadIssues() {
    try {
        const issues = await fetchAPI('/api/issues');
        const tbody = document.querySelector('#issues-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (issues.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">No issues found</td></tr>';
            return;
        }
        
        issues.forEach(issue => {
            const statusClass = issue.status === 'issued' ? 'status-issued' : 'status-returned';
            const statusText = issue.status.charAt(0).toUpperCase() + issue.status.slice(1);
            
            const actionBtn = issue.status === 'issued' 
                ? `<button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem" onclick="returnBook(${issue.id})">Return Book</button>`
                : `<span style="color:var(--gray-500);font-size:0.875rem">Returned on ${issue.return_date}</span>`;
                
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${issue.id}</td>
                <td><strong>${issue.book_title}</strong></td>
                <td>${issue.member_name}</td>
                <td>${issue.issue_date}</td>
                <td>${issue.due_date}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${actionBtn}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load issues", e);
    }
}

async function openIssueModal() {
    try {
        // Load dropdowns
        const [books, members] = await Promise.all([
            fetchAPI('/api/books'),
            fetchAPI('/api/members')
        ]);
        
        const bookSelect = document.getElementById('issue-book-id');
        const memberSelect = document.getElementById('issue-member-id');
        
        bookSelect.innerHTML = '<option value="">-- Select Book --</option>';
        books.filter(b => b.available_copies > 0).forEach(book => {
            bookSelect.innerHTML += `<option value="${book.id}">${book.title} (Available: ${book.available_copies})</option>`;
        });
        if(books.filter(b => b.available_copies > 0).length === 0) {
            bookSelect.innerHTML += `<option value="" disabled>No books available</option>`;
        }
        
        memberSelect.innerHTML = '<option value="">-- Select Member --</option>';
        members.forEach(member => {
            memberSelect.innerHTML += `<option value="${member.id}">${member.name} (${member.email})</option>`;
        });
        
        openModal('issueBookModal');
    } catch (e) {
        console.error("Failed to load resources for issuing", e);
    }
}

async function issueBook(event) {
    event.preventDefault();
    try {
        const data = {
            book_id: document.getElementById('issue-book-id').value,
            member_id: document.getElementById('issue-member-id').value
        };
        
        const result = await fetchAPI('/api/issues', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast(result.message);
        closeModal('issueBookModal');
        document.getElementById('issueBookForm').reset();
        loadIssues();
    } catch (e) {
        // Error handled in fetchAPI
    }
}

async function returnBook(issueId) {
    if (!confirm('Confirm return of this book?')) return;
    
    try {
        const result = await fetchAPI(`/api/issues/${issueId}/return`, {
            method: 'POST'
        });
        showToast(result.message);
        loadIssues();
    } catch (e) {
        // Error handled in fetchAPI
    }
}

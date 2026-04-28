const API_URL = 'https://project-tim-api.onrender.com';

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

function showModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function hideModal(id) {
    document.getElementById(id).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

async function registerUser(e) {
    e.preventDefault();
    const data = {
        full_name: document.getElementById('reg-name').value,
        email: document.getElementById('reg-email').value,
        university: document.getElementById('reg-university').value || null,
        faculty: document.getElementById('reg-faculty').value || null,
        course: parseInt(document.getElementById('reg-course').value) || null,
        skills: document.getElementById('reg-skills').value.split(',').map(s => s.trim()).filter(Boolean),
        role: document.getElementById('reg-role').value || null,
        about: document.getElementById('reg-about').value || null,
        soft_skills: [],
        portfolio_links: [],
        interests: []
    };
    
    const result = await apiCall('/users/', 'POST', data);
    if (result && result.id) {
        alert('Регистрация успешна! Ваш ID: ' + result.id);
        hideModal('register-modal');
        loadUsers();
    } else {
        alert('Ошибка регистрации. Возможно, такой email уже используется.');
    }
}

async function loadUsers() {
    const container = document.getElementById('users-container');
    container.innerHTML = '<p class="placeholder-text">Загрузка...</p>';
    
    const users = await apiCall('/users/');
    if (!users || users.length === 0) {
        container.innerHTML = '<p class="placeholder-text">Пользователи не найдены. Зарегистрируйтесь первым!</p>';
        return;
    }
    
    document.getElementById('stat-users').textContent = users.length;
    
    container.innerHTML = users.map(u => `
        <div class="user-card">
            <h3>${u.full_name}</h3>
            <p class="university">${u.university || '—'}, ${u.course || '?'} курс</p>
            <div class="skills-tags">${(u.skills || []).slice(0, 5).map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>
            <p class="rating">⭐ ${u.rating.toFixed(1)}</p>
            <p class="level">🔰 Уровень ${u.level} | 🪙 ${u.team_coins} тим-койнов</p>
            <p style="font-size:13px;color:#b0b0d0;margin-top:8px;">${u.about || ''}</p>
            <div class="actions">
                <button class="btn-primary btn-small" onclick="viewUser(${u.id})">Профиль</button>
                <button class="btn-small btn-review" onclick="openReview(${u.id})">Оставить отзыв</button>
            </div>
        </div>
    `).join('');
}

async function searchUsers() {
    const container = document.getElementById('users-container');
    container.innerHTML = '<p class="placeholder-text">Поиск...</p>';
    
    const search = document.getElementById('search-input').value;
    const role = document.getElementById('role-filter').value;
    const rating = document.getElementById('rating-filter').value;
    
    let params = [];
    if (search) params.push(`search=${encodeURIComponent(search)}`);
    if (role) params.push(`role=${encodeURIComponent(role)}`);
    if (rating) params.push(`min_rating=${rating}`);
    
    const query = params.length ? '?' + params.join('&') : '';
    const users = await apiCall('/users/' + query);
    
    if (!users || users.length === 0) {
        container.innerHTML = '<p class="placeholder-text">Ничего не найдено. Попробуйте изменить параметры поиска.</p>';
        return;
    }
    
    container.innerHTML = users.map(u => `
        <div class="user-card">
            <h3>${u.full_name}</h3>
            <p class="university">${u.university || '—'}, ${u.course || '?'} курс</p>
            <div class="skills-tags">${(u.skills || []).slice(0, 5).map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>
            <p class="rating">⭐ ${u.rating.toFixed(1)}</p>
            <p class="level">🔰 Уровень ${u.level} | 🪙 ${u.team_coins} тим-койнов</p>
            <p style="font-size:13px;color:#b0b0d0;margin-top:8px;">${u.about || ''}</p>
            <div class="actions">
                <button class="btn-primary btn-small" onclick="viewUser(${u.id})">Профиль</button>
                <button class="btn-small btn-review" onclick="openReview(${u.id})">Оставить отзыв</button>
            </div>
        </div>
    `).join('');
}

async function viewUser(id) {
    const user = await apiCall(`/users/${id}`);
    if (user) {
        const reviews = await apiCall(`/reviews/user/${id}`);
        const badges = await apiCall(`/badges/user/${id}`);
        alert(`Профиль: ${user.full_name}\nВуз: ${user.university || '—'}\nРейтинг: ${user.rating}\nУровень: ${user.level}\nНавыки: ${(user.skills||[]).join(', ')}\nРоль: ${user.role || '—'}\nОтзывов: ${(reviews||[]).length}\nБейджей: ${(badges||[]).length}`);
    }
}

function openReview(userId) {
    document.getElementById('review-reviewee-id').value = userId;
    showModal('review-modal');
}

async function submitReview(e) {
    e.preventDefault();
    const data = {
        reviewee_id: parseInt(document.getElementById('review-reviewee-id').value),
        project_id: 1,
        professionalism: parseInt(document.getElementById('review-prof').value),
        deadline_compliance: parseInt(document.getElementById('review-deadline').value),
        communication: parseInt(document.getElementById('review-comm').value),
        comment: document.getElementById('review-comment').value || null
    };
    
    const result = await apiCall('/reviews/?reviewer_id=1', 'POST', data);
    if (result && result.message) {
        alert('Отзыв успешно создан! Новый рейтинг пользователя: ' + result.new_rating);
        hideModal('review-modal');
        loadUsers();
    } else {
        alert('Ошибка при создании отзыва.');
    }
}

async function loadProjects() {
    const container = document.getElementById('projects-container');
    const projects = await apiCall('/projects/');
    if (!projects || projects.length === 0) {
        container.innerHTML = '<p class="placeholder-text">Пока нет активных проектов. Создайте первый!</p>';
        return;
    }
    document.getElementById('stat-projects').textContent = projects.length;
    container.innerHTML = projects.map(p => `
        <div class="project-card">
            <h3>${p.title}</h3>
            <span class="status status-open">${p.status === 'open' ? 'Открыт' : p.status}</span>
            <p style="color:#b0b0d0;margin:10px 0;">${p.description}</p>
            <div class="skills-tags">${(p.required_skills || []).map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>
            <p style="font-size:12px;color:#8080a0;margin-top:8px;">Создан: ${p.created_at?.split('T')[0] || '—'}</p>
        </div>
    `).join('');
}

async function createProject(e) {
    e.preventDefault();
    const data = {
        title: document.getElementById('proj-title').value,
        description: document.getElementById('proj-description').value,
        required_skills: document.getElementById('proj-skills').value.split(',').map(s => s.trim()).filter(Boolean),
        required_roles: document.getElementById('proj-roles').value.split(',').map(s => s.trim()).filter(Boolean),
        status: 'open'
    };
    const result = await apiCall('/projects/?creator_id=1', 'POST', data);
    if (result && result.id) {
        alert('Проект создан!');
        hideModal('project-modal');
        loadProjects();
    } else {
        alert('Ошибка создания проекта.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    loadProjects();
});

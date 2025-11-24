let currentTab = 'users';

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(tabName).classList.remove('hidden');

    document.querySelectorAll('button[id^="tab-"]').forEach(btn => {
        btn.classList.remove('tab-active', 'text-white');
        btn.classList.add('bg-gray-100', 'text-gray-700', 'hover:bg-gray-200');
    });
    document.getElementById(`tab-${tabName}`).classList.add('tab-active', 'text-white');
    document.getElementById(`tab-${tabName}`).classList.remove('bg-gray-100', 'text-gray-700');

    currentTab = tabName;
    loadData();
}

function loadData() {
    if (currentTab === 'users') {
        fetch('/api/all_users').then(r => r.json()).then(d => displayUsers(d.users));
    } else if (currentTab === 'solutions') {
        fetch('/api/all_solutions').then(r => r.json()).then(d => displaySolutions(d.solutions));
    } else if (currentTab === 'points') {
        fetch('/api/all_points').then(r => r.json()).then(d => displayPoints(d.points));
    } else if (currentTab === 'roles') {
        fetch('/api/all_roles').then(r => r.json()).then(d => displayRoles(d.roles));
    }
}

function displayUsers(users) {
    document.getElementById('users-list').innerHTML = users.map(u => `
        <tr class="border-b">
            <td class="px-4 py-3 font-medium">${u.username}</td>
            <td class="px-4 py-3">${u.email}</td>
            <td class="px-4 py-3 text-sm text-gray-600">${u.created_at}</td>
            <td class="px-4 py-3">
                <button onclick="deleteUser('${u.username}')" class="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded text-sm">
                    <i class="fas fa-trash"></i> Xóa
                </button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="4" class="text-center py-8 text-gray-500">Không có người dùng</td></tr>';
}

function displaySolutions(solutions) {
    document.getElementById('solutions-list').innerHTML = solutions.map(s => `
        <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition">
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-semibold text-lg"><a href="/view_solution/${s.id}" class="text-blue-600 hover:underline">${s.title}</a></h4>
                    <p class="text-sm text-gray-600">User: <strong>${s.username}</strong> • ${s.created_at}</p>
                    <p class="text-sm"><a href="${s.url}" target="_blank" class="text-blue-500 hover:underline">${s.url}</a></p>
                </div>
                <div class="flex gap-2">
                    <span class="px-3 py-1 rounded text-xs ${s.isac ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                        ${s.isac ? 'AC' : 'Chưa AC'}
                    </span>
                    <span class="px-3 py-1 rounded text-xs ${s.ispublic ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700'}">
                        ${s.ispublic ? 'Công khai' : 'Riêng tư'}
                    </span>
                </div>
            </div>
        </div>
    `).join('') || '<p class="text-center py-8 text-gray-500">Chưa có solution nào</p>';
}

function displayPoints(points) {
    document.getElementById('points-list').innerHTML = points.map(p => `
        <tr class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">${p.username}</td>
            <td class="px-4 py-3 text-center">${p.point}</td>
            <td class="px-4 py-3 text-center font-semibold text-blue-600">${p.total_point}</td>
            <td class="px-4 py-3 text-center">
                <button onclick="openEditPointModal('${p.username}', ${p.point}, ${p.total_point})" 
                        class="bg-indigo-100 text-indigo-700 hover:bg-indigo-200 px-4 py-2 rounded text-sm font-medium">
                    <i class="fas fa-edit mr-1"></i>Chỉnh
                </button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="4" class="text-center py-8 text-gray-500">Chưa có dữ liệu điểm</td></tr>';
}

function openEditPointModal(username, currentPoint, totalPoint) {
    const modalHtml = `
        <div id="edit-point-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md">
                <h3 class="text-xl font-bold mb-4">Chỉnh điểm cho <span class="text-blue-600">${username}</span></h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Point hiện tại</label>
                        <input type="number" id="new-point" value="${currentPoint}" min="0"
                               class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Tổng điểm (total_point)</label>
                        <input type="number" id="new-total" value="${totalPoint}" min="0"
                               class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div id="point-error" class="text-red-600 text-sm hidden">
                        <i class="fas fa-exclamation-triangle"></i> Point hiện tại không được lớn hơn Tổng điểm!
                    </div>
                </div>
                <div class="flex justify-end space-x-3 mt-6">
                    <button onclick="closeEditPointModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                        Hủy
                    </button>
                    <button onclick="savePoints('${username}')" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                        Lưu
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeEditPointModal() {
    const modal = document.getElementById('edit-point-modal');
    if (modal) modal.remove();
}

function savePoints(username) {
    const newPoint = parseInt(document.getElementById('new-point').value) || 0;
    const newTotal = parseInt(document.getElementById('new-total').value) || 0;
    const errorEl = document.getElementById('point-error');

    if (newPoint < 0 || newTotal < 0) {
        errorEl.textContent = 'Điểm không được âm!';
        errorEl.classList.remove('hidden');
        return;
    }

    if (newPoint > newTotal) {
        errorEl.textContent = 'Point hiện tại không được lớn hơn Tổng điểm!';
        errorEl.classList.remove('hidden');
        return;
    }

    errorEl.classList.add('hidden');

    fetch('/api/admin_set_points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: username,
            point: newPoint,
            total_point: newTotal
        })
    })
    .then(r => r.json())
    .then(d => {
        if (d.success) {
            closeEditPointModal();
            loadData();
        } else {
            alert('Lỗi: ' + (d.message || 'Không thể cập nhật điểm'));
        }
    })
    .catch(() => alert('Lỗi kết nối server'));
}

function displayRoles(roles) {
    document.getElementById('roles-list').innerHTML = roles.map(r => `
        <tr class="border-b">
            <td class="px-4 py-3 font-medium">${r.username}</td>
            <td class="px-4 py-3">
                <select onchange="setRole('${r.username}', this.value)" class="border rounded px-2 py-1 text-sm">
                    <option value="default" ${r.role === 'default' ? 'selected' : ''}>default</option>
                    <option value="admin" ${r.role === 'admin' ? 'selected' : ''}>admin</option>
                </select>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">${r.role}</td>
        </tr>
    `).join('');
}

function setRole(username, role) {
    fetch(`/api/set_role/${username}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role })
    }).then(() => loadData());
}

function deleteUser(username) {
    if (confirm(`Bạn có chắc chắn muốn XÓA hoàn toàn user "${username}"? Dữ liệu sẽ mất vĩnh viễn!`)) {
        fetch(`/api/delete_user/${username}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(d => {
                if (d.success) loadData();
                else alert(d.message || 'Lỗi khi xóa');
            });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    showTab('users');
});
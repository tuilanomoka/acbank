let currentTab = 'my-solutions';
let myCurrentPage = 1;
let publicCurrentPage = 1;
let allCurrentPage = 1;
let currentSearch = '';

const socket = io();

socket.on('new_solution', function(data) {
    loadSolutions();
});

socket.on('update_solution', function(data) {
    loadSolutions();
});

socket.on('delete_solution', function(data) {
    loadSolutions();
});

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    document.getElementById(tabName).style.display = 'block';
    currentTab = tabName;
    loadSolutions();
}

function search() {
    currentSearch = document.getElementById('search-input').value;
    myCurrentPage = 1;
    publicCurrentPage = 1;
    allCurrentPage = 1;
    loadSolutions();
}

function prevPage(type) {
    if (type === 'my' && myCurrentPage > 1) {
        myCurrentPage--;
        loadSolutions();
    } else if (type === 'public' && publicCurrentPage > 1) {
        publicCurrentPage--;
        loadSolutions();
    } else if (type === 'all' && allCurrentPage > 1) {
        allCurrentPage--;
        loadSolutions();
    }
}

function nextPage(type) {
    if (type === 'my') {
        myCurrentPage++;
        loadSolutions();
    } else if (type === 'public') {
        publicCurrentPage++;
        loadSolutions();
    } else if (type === 'all') {
        allCurrentPage++;
        loadSolutions();
    }
}

function loadSolutions() {
    if (currentTab === 'my-solutions') {
        fetch(`/api/my_solutions?page=${myCurrentPage}&search=${currentSearch}`)
            .then(response => response.json())
            .then(data => {
                displayMySolutions(data.solutions);
                document.getElementById('my-page-info').textContent = `Trang ${myCurrentPage}`;
            });
    } else if (currentTab === 'public-solutions') {
        fetch(`/api/public_solutions?page=${publicCurrentPage}&search=${currentSearch}`)
            .then(response => response.json())
            .then(data => {
                displayPublicSolutions(data.solutions);
                document.getElementById('public-page-info').textContent = `Trang ${publicCurrentPage}`;
            });
    } else if (currentTab === 'all-solutions') {
        fetch(`/api/all_solutions?page=${allCurrentPage}&search=${currentSearch}`)
            .then(response => response.json())
            .then(data => {
                displayAllSolutions(data.solutions);
                document.getElementById('all-page-info').textContent = `Trang ${allCurrentPage}`;
            });
    }
}

function displayMySolutions(solutions) {
    const container = document.getElementById('my-solutions-list');
    if (solutions.length === 0) {
        container.innerHTML = '<p>Chưa có solution nào.</p>';
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div style="border: 1px solid #ccc; margin: 10px 0; padding: 10px;">
            <h4>${solution.title || 'Không có tiêu đề'}</h4>
            <p><strong>URL:</strong> <a href="${solution.url}" target="_blank">${solution.url}</a></p>
            <p><strong>Trạng thái:</strong> ${solution.isac ? 'Đã AC' : 'Chưa AC'}</p>
            <p><strong>Công khai:</strong> ${solution.ispublic ? 'Có' : 'Không'}</p>
            <p><small>Ngày tạo: ${new Date(solution.created_at).toLocaleString()}</small></p>
            <button onclick="viewSolution(${solution.id})">Xem</button>
            <button onclick="editSolution(${solution.id})">Chỉnh sửa</button>
            <button onclick="deleteSolution(${solution.id})" style="background: #ff4444; color: white;">Xoá</button>
        </div>
    `).join('');
}

function displayPublicSolutions(solutions) {
    const container = document.getElementById('public-solutions-list');
    if (solutions.length === 0) {
        container.innerHTML = '<p>Chưa có solution công khai nào.</p>';
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div style="border: 1px solid #ccc; margin: 10px 0; padding: 10px;">
            <h4>${solution.title || 'Không có tiêu đề'}</h4>
            <p><strong>Người đăng:</strong> ${solution.username}</p>
            <p><strong>URL:</strong> <a href="${solution.url}" target="_blank">${solution.url}</a></p>
            <p><strong>Trạng thái:</strong> ${solution.isac ? 'Đã AC' : 'Chưa AC'}</p>
            <p><small>Ngày tạo: ${new Date(solution.created_at).toLocaleString()}</small></p>
            <button onclick="viewSolution(${solution.id})">Xem</button>
        </div>
    `).join('');
}

function displayAllSolutions(solutions) {
    const container = document.getElementById('all-solutions-list');
    if (solutions.length === 0) {
        container.innerHTML = '<p>Chưa có solution nào.</p>';
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div style="border: 1px solid #ccc; margin: 10px 0; padding: 10px;">
            <h4>${solution.title || 'Không có tiêu đề'}</h4>
            <p><strong>Người đăng:</strong> ${solution.username}</p>
            <p><strong>URL:</strong> <a href="${solution.url}" target="_blank">${solution.url}</a></p>
            <p><strong>Trạng thái:</strong> ${solution.isac ? 'Đã AC' : 'Chưa AC'}</p>
            <p><strong>Công khai:</strong> ${solution.ispublic ? 'Có' : 'Không'}</p>
            <p><small>Ngày tạo: ${new Date(solution.created_at).toLocaleString()}</small></p>
            <button onclick="viewSolution(${solution.id})">Xem</button>
            <button onclick="editSolution(${solution.id})">Chỉnh sửa</button>
            <button onclick="deleteSolution(${solution.id})" style="background: #ff4444; color: white;">Xoá</button>
        </div>
    `).join('');
}

function viewSolution(solutionId) {
    window.location.href = `/view_solution/${solutionId}`;
}

function editSolution(solutionId) {
    window.location.href = `/edit_solution/${solutionId}`;
}

function deleteSolution(solutionId) {
    if (confirm('Bạn có chắc muốn xoá solution này?')) {
        fetch(`/api/delete_solution/${solutionId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                socket.emit('delete_solution', {message: 'Solution deleted'});
                loadSolutions();
            } else {
                alert('Xoá thất bại: ' + data.message);
            }
        })
        .catch(error => {
            alert('Lỗi: ' + error);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadSolutions();
});
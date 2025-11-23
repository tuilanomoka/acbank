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
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-inbox text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">Chưa có solution nào.</p>
            </div>`;
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div class="bg-white border border-gray-200 rounded-xl p-6 mb-4 card-hover shadow-sm">
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between">
                <div class="flex-1">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">${solution.title || 'Không có tiêu đề'}</h4>
                    <p class="text-gray-600 mb-2"><strong>URL:</strong> <a href="${solution.url}" target="_blank" class="text-blue-600 hover:text-blue-800 break-all">${solution.url}</a></p>
                    <div class="flex flex-wrap gap-2 mb-3">
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${solution.isac ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                            <i class="fas ${solution.isac ? 'fa-check-circle' : 'fa-clock'} mr-1"></i>
                            ${solution.isac ? 'Đã AC' : 'Chưa AC'}
                        </span>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${solution.ispublic ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}">
                            <i class="fas ${solution.ispublic ? 'fa-eye' : 'fa-eye-slash'} mr-1"></i>
                            ${solution.ispublic ? 'Công khai' : 'Riêng tư'}
                        </span>
                    </div>
                    <p class="text-sm text-gray-500"><i class="far fa-clock mr-1"></i>${new Date(solution.created_at).toLocaleString()}</p>
                </div>
                <div class="flex space-x-2 mt-4 lg:mt-0 lg:ml-4">
                    <button onclick="viewSolution(${solution.id})" class="bg-blue-100 text-blue-600 py-2 px-4 rounded-lg font-semibold hover:bg-blue-200 transition-all duration-300">
                        <i class="fas fa-eye mr-1"></i>Xem
                    </button>
                    <button onclick="editSolution(${solution.id})" class="bg-green-100 text-green-600 py-2 px-4 rounded-lg font-semibold hover:bg-green-200 transition-all duration-300">
                        <i class="fas fa-edit mr-1"></i>Sửa
                    </button>
                    <button onclick="deleteSolution(${solution.id})" class="bg-red-100 text-red-600 py-2 px-4 rounded-lg font-semibold hover:bg-red-200 transition-all duration-300">
                        <i class="fas fa-trash mr-1"></i>Xoá
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayPublicSolutions(solutions) {
    const container = document.getElementById('public-solutions-list');
    if (solutions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-inbox text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">Chưa có solution công khai nào.</p>
            </div>`;
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div class="bg-white border border-gray-200 rounded-xl p-6 mb-4 card-hover shadow-sm">
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between">
                <div class="flex-1">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">${solution.title || 'Không có tiêu đề'}</h4>
                    <p class="text-gray-600 mb-2"><strong>Người đăng:</strong> <span class="font-medium">${solution.username}</span></p>
                    <p class="text-gray-600 mb-2"><strong>URL:</strong> <a href="${solution.url}" target="_blank" class="text-blue-600 hover:text-blue-800 break-all">${solution.url}</a></p>
                    <div class="mb-3">
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${solution.isac ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                            <i class="fas ${solution.isac ? 'fa-check-circle' : 'fa-clock'} mr-1"></i>
                            ${solution.isac ? 'Đã AC' : 'Chưa AC'}
                        </span>
                    </div>
                    <p class="text-sm text-gray-500"><i class="far fa-clock mr-1"></i>${new Date(solution.created_at).toLocaleString()}</p>
                </div>
                <div class="mt-4 lg:mt-0 lg:ml-4">
                    <button onclick="viewSolution(${solution.id})" class="bg-blue-100 text-blue-600 py-2 px-4 rounded-lg font-semibold hover:bg-blue-200 transition-all duration-300">
                        <i class="fas fa-eye mr-1"></i>Xem
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAllSolutions(solutions) {
    const container = document.getElementById('all-solutions-list');
    if (solutions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-inbox text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">Chưa có solution nào.</p>
            </div>`;
        return;
    }

    container.innerHTML = solutions.map(solution => `
        <div class="bg-white border border-gray-200 rounded-xl p-6 mb-4 card-hover shadow-sm">
            <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between">
                <div class="flex-1">
                    <div class="flex items-start justify-between mb-3">
                        <h4 class="text-lg font-semibold text-gray-800">${solution.title || 'Không có tiêu đề'}</h4>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 ml-4">
                            <i class="fas fa-user-shield mr-1"></i>${solution.username}
                        </span>
                    </div>
                    <p class="text-gray-600 mb-2"><strong>URL:</strong> <a href="${solution.url}" target="_blank" class="text-blue-600 hover:text-blue-800 break-all">${solution.url}</a></p>
                    <div class="flex flex-wrap gap-2 mb-3">
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${solution.isac ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                            <i class="fas ${solution.isac ? 'fa-check-circle' : 'fa-clock'} mr-1"></i>
                            ${solution.isac ? 'Đã AC' : 'Chưa AC'}
                        </span>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${solution.ispublic ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}">
                            <i class="fas ${solution.ispublic ? 'fa-eye' : 'fa-eye-slash'} mr-1"></i>
                            ${solution.ispublic ? 'Công khai' : 'Riêng tư'}
                        </span>
                    </div>
                    <p class="text-sm text-gray-500"><i class="far fa-clock mr-1"></i>${new Date(solution.created_at).toLocaleString()}</p>
                </div>
                <div class="flex space-x-2 mt-4 lg:mt-0 lg:ml-4">
                    <button onclick="viewSolution(${solution.id})" class="bg-blue-100 text-blue-600 py-2 px-4 rounded-lg font-semibold hover:bg-blue-200 transition-all duration-300">
                        <i class="fas fa-eye mr-1"></i>Xem
                    </button>
                    <button onclick="editSolution(${solution.id})" class="bg-green-100 text-green-600 py-2 px-4 rounded-lg font-semibold hover:bg-green-200 transition-all duration-300">
                        <i class="fas fa-edit mr-1"></i>Sửa
                    </button>
                    <button onclick="deleteSolution(${solution.id})" class="bg-red-100 text-red-600 py-2 px-4 rounded-lg font-semibold hover:bg-red-200 transition-all duration-300">
                        <i class="fas fa-trash mr-1"></i>Xoá
                    </button>
                </div>
            </div>
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

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    document.querySelectorAll('button[id^="tab-"]').forEach(btn => {
        btn.classList.remove('tab-active', 'text-white');
        btn.classList.add('bg-gray-100', 'text-gray-700', 'hover:bg-gray-200');
    });
    
    document.getElementById(tabName).style.display = 'block';
    const activeTabBtn = document.getElementById('tab-' + tabName.split('-')[0]);
    if (activeTabBtn) {
        activeTabBtn.classList.add('tab-active', 'text-white');
        activeTabBtn.classList.remove('bg-gray-100', 'text-gray-700', 'hover:bg-gray-200');
    }
    
    currentTab = tabName;
    loadSolutions();
}

document.addEventListener('DOMContentLoaded', function() {
    loadSolutions();
});
document.addEventListener('DOMContentLoaded', function() {
    loadRankings();
});

function loadRankings() {
    fetch('/api/rankings')
        .then(response => response.json())
        .then(data => {
            displayRankings(data.rankings);
        })
        .catch(error => {
            console.error('Error loading rankings:', error);
            document.getElementById('rank-list').innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">Lỗi khi tải bảng xếp hạng</p>
                </div>
            `;
        });
}

function displayRankings(rankings) {
    const container = document.getElementById('rank-list');
    
    if (rankings.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-users text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">Chưa có dữ liệu xếp hạng</p>
            </div>
        `;
        return;
    }

    container.innerHTML = rankings.map((user, index) => {
        const rank = index + 1;
        let rankClass = '';
        let medalHtml = '';
        
        if (rank === 1) {
            rankClass = 'rank-1';
            medalHtml = `<div class="medal medal-gold"><i class="fas fa-crown"></i></div>`;
        } else if (rank === 2) {
            rankClass = 'rank-2';
            medalHtml = `<div class="medal medal-silver">2</div>`;
        } else if (rank === 3) {
            rankClass = 'rank-3';
            medalHtml = `<div class="medal medal-bronze">3</div>`;
        } else {
            medalHtml = `<div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center font-semibold text-gray-600 mr-3">${rank}</div>`;
        }

        return `
            <div class="bg-white border border-gray-200 rounded-xl p-6 card-hover shadow-sm ${rankClass}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        ${medalHtml}
                        <div>
                            <h4 class="text-lg font-semibold text-gray-800">${user.username}</h4>
                            <p class="text-sm text-gray-600">${user.email || 'Không có email'}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl font-bold text-blue-600">${user.total_point}</div>
                        <div class="text-sm text-gray-500">Tổng điểm</div>
                    </div>
                </div>
                ${user.current_point !== undefined ? `
                <div class="mt-3 pt-3 border-t border-gray-200">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Điểm hiện tại:</span>
                        <span class="font-semibold text-green-600">${user.current_point}</span>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }).join('');
}
document.addEventListener('DOMContentLoaded', function() {
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        }
    });

    function renderMarkdown(text) {
        if (!text || !text.trim()) return '<p><em>Không có</em></p>';
        return marked.parse(text);
    }

    const summaryElement = document.getElementById('summary-content');
    const codeElement = document.getElementById('code-content');
    
    const summaryText = summaryElement.textContent || summaryElement.innerText;
    const codeText = codeElement.textContent || codeElement.innerText;
    
    summaryElement.innerHTML = renderMarkdown(summaryText);
    codeElement.innerHTML = renderMarkdown(codeText);

    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
});

function deleteSolution(solutionId) {
    if (confirm('Bạn có chắc muốn xoá solution này?')) {
        fetch('/api/delete_solution/' + solutionId, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Xoá solution thành công!');
                window.location.href = '/home';
            } else {
                alert('Xoá thất bại: ' + data.message);
            }
        })
        .catch(error => {
            alert('Lỗi: ' + error);
        });
    }
}
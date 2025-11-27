document.addEventListener('DOMContentLoaded', function() {
    initializeView();
});

function initializeView() {
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (err) {
                    return hljs.highlightAuto(code).value;
                }
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });

    const summaryElement = document.getElementById('summary-content');
    const codeElement = document.getElementById('code-content');
    
    if (!summaryElement || !codeElement) {
        console.error('Không tìm thấy elements');
        return;
    }

    const summaryText = summaryElement.textContent || summaryElement.innerText;
    const codeText = codeElement.textContent || codeElement.innerText;

    try {
        summaryElement.innerHTML = marked.parse(summaryText);
        codeElement.innerHTML = marked.parse(codeText);

        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        if (typeof renderMathInElement !== 'undefined') {
            renderMathInElement(document.body, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false
            });
            
        } else {
            console.error('KaTeX vẫn chưa load');
        }
    } catch (error) {
        console.error('Lỗi khi render:', error);
    }
}

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
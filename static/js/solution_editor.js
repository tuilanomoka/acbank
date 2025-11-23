let summaryEditor;
let codeEditor;

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initializeEditors, 100);
});

function initializeEditors() {
    const summaryContainer = document.getElementById('summary-container');
    const codeContainer = document.getElementById('code-container');
    
    if (!summaryContainer || !codeContainer) {
        console.error('Không tìm thấy editor containers');
        return;
    }

    try {
        summaryEditor = new toastui.Editor({
            el: summaryContainer,
            height: '500px',
            initialEditType: 'markdown',
            previewStyle: 'tab',
            placeholder: 'Nhập tóm tắt giải pháp (Markdown)...',
            usageStatistics: false,
            hideModeSwitch: true,
            toolbarItems: [
                ['heading', 'bold', 'italic'],
                ['hr', 'quote'],
                ['ul', 'ol'],
                ['table', 'link'],
                ['code', 'codeblock']
            ]
        });

        codeEditor = new toastui.Editor({
            el: codeContainer,
            height: '500px',
            initialEditType: 'markdown',
            previewStyle: 'tab',
            placeholder: 'Nhập code giải pháp của bạn...',
            usageStatistics: false,
            hideModeSwitch: true,
            toolbarItems: [
                ['heading', 'bold', 'italic'],
                ['hr', 'quote'],
                ['ul', 'ol'],
                ['table', 'link'],
                ['code', 'codeblock']
            ]
        });

        setTimeout(initializeEditorContent, 200);
        
    } catch (error) {
        console.error('Lỗi khởi tạo editor:', error);
        alert('Có lỗi khi khởi tạo trình soạn thảo. Vui lòng tải lại trang.');
    }
}

function initializeEditorContent() {
    const solutionDataElement = document.getElementById('solution-data');
    if (!solutionDataElement) return;

    const summary = solutionDataElement.dataset.summary || '';
    const code = solutionDataElement.dataset.code || '';
    
    const decodedSummary = decodeHTML(summary);
    const decodedCode = decodeHTML(code);
    
    try {
        if (summaryEditor && decodedSummary) {
            summaryEditor.setMarkdown(decodedSummary);
        }
        
        if (codeEditor && decodedCode) {
            codeEditor.setMarkdown(decodedCode);
        }
    } catch (error) {
        console.error('Lỗi khi set editor content:', error);
    }
}


function decodeHTML(html) {
    if (!html) return '';
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

document.getElementById('solution-form').addEventListener('submit', function(e) {
    if (!codeEditor || !summaryEditor) {
        e.preventDefault();
        alert('Editor đang khởi tạo, vui lòng thử lại sau!');
        return;
    }

    try {
        const codeValue = codeEditor.getMarkdown();
        const summaryValue = summaryEditor.getMarkdown();
        
        if (!codeValue.trim()) {
            e.preventDefault();
            alert('Vui lòng nhập phần giải!');
            return;
        }
        
        let codeHiddenInput = document.querySelector('input[name="code"]');
        let summaryHiddenInput = document.querySelector('input[name="summary"]');
        
        if (!codeHiddenInput) {
            codeHiddenInput = document.createElement('input');
            codeHiddenInput.type = 'hidden';
            codeHiddenInput.name = 'code';
            this.appendChild(codeHiddenInput);
        }
        
        if (!summaryHiddenInput) {
            summaryHiddenInput = document.createElement('input');
            summaryHiddenInput.type = 'hidden';
            summaryHiddenInput.name = 'summary';
            this.appendChild(summaryHiddenInput);
        }
        
        codeHiddenInput.value = codeValue;
        summaryHiddenInput.value = summaryValue;
        
    } catch (error) {
        e.preventDefault();
        console.error('Lỗi khi submit form:', error);
        alert('Có lỗi xảy ra khi xử lý dữ liệu. Vui lòng thử lại.');
    }
});
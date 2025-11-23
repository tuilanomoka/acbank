let summaryEditor;
let codeEditor;

document.addEventListener('DOMContentLoaded', function() {
    initializeEditors();
});

function initializeEditors() {
    summaryEditor = editormd("summary-container", {
        placeholder: "Nhập tóm tắt giải pháp (Markdown)...",
        height: 200,
        path: "https://cdn.jsdelivr.net/npm/editor.md@1.5.0/lib/",
        toolbarIcons: function() {
            return [
                "bold", "italic", "quote", "|",
                "list-ul", "list-ol", "hr", "|",
                "link", "image", "code", "|",
                "preview", "fullscreen"
            ]
        },
        toolbarIconTexts: {
            "bold": "Đậm",
            "italic": "Nghiêng", 
            "quote": "Trích dẫn",
            "list-ul": "Danh sách",
            "list-ol": "Số thứ tự",
            "hr": "Đường kẻ",
            "link": "Liên kết",
            "image": "Hình ảnh",
            "code": "Code",
            "preview": "Xem trước",
            "fullscreen": "Toàn màn hình"
        }
    });

    codeEditor = editormd("code-container", {
        placeholder: "Nhập code giải pháp của bạn...",
        height: 400,
        path: "https://cdn.jsdelivr.net/npm/editor.md@1.5.0/lib/",
        toolbarIcons: function() {
            return [
                "bold", "italic", "quote", "|",
                "list-ul", "list-ol", "hr", "|", 
                "link", "code-block", "code", "|",
                "preview", "fullscreen"
            ]
        },
        toolbarIconTexts: {
            "bold": "Đậm",
            "italic": "Nghiêng",
            "quote": "Trích dẫn", 
            "list-ul": "Danh sách",
            "list-ol": "Số thứ tự",
            "hr": "Đường kẻ",
            "link": "Liên kết",
            "code-block": "Code Block",
            "code": "Inline Code",
            "preview": "Xem trước",
            "fullscreen": "Toàn màn hình"
        }
    });

    setTimeout(() => {
        initializeEditorContent();
    }, 500);
}

function initializeEditorContent() {
    const urlPath = window.location.pathname;
    if (urlPath.includes('/edit_solution/')) {
        const solutionDataElement = document.getElementById('solution-data');
        if (solutionDataElement) {
            const summary = solutionDataElement.dataset.summary || '';
            const code = solutionDataElement.dataset.code || '';
            
            if (summaryEditor && summary) {
                summaryEditor.setMarkdown(summary);
            }
            if (codeEditor && code) {
                codeEditor.setMarkdown(code);
            }
        }
    }
}

document.getElementById('solution-form').addEventListener('submit', function(e) {
    if (!codeEditor || !summaryEditor) {
        e.preventDefault();
        alert('Editor đang khởi tạo, vui lòng thử lại sau!');
        return;
    }

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
});
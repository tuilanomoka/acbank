let summaryEditor, codeEditor;

document.addEventListener('DOMContentLoaded', function() {
    initializeEditors();
});

function initializeEditors() {
    const summaryContainer = document.getElementById('summary-container');
    const codeContainer = document.getElementById('code-container');
    
    if (summaryContainer) {
        summaryEditor = createEditor(summaryContainer, 'Nhập tóm tắt giải pháp (Markdown + LaTeX)...');
    }
    
    if (codeContainer) {
        codeEditor = createEditor(codeContainer, 'Nhập code giải pháp của bạn (Markdown + LaTeX)...');
    }
    
    setTimeout(loadExistingContent, 100);
}

function createEditor(container, placeholder) {
    const editor = document.createElement('div');
    editor.className = 'editor-container border rounded-lg bg-white';
    editor.innerHTML = `
        <div class="editor-tabs flex border-b">
            <button type="button" class="tab-btn active px-4 py-2 font-medium text-blue-600 border-b-2 border-blue-600" data-tab="edit">Viết</button>
            <button type="button" class="tab-btn px-4 py-2 font-medium text-gray-600 hover:text-gray-800" data-tab="preview">Xem trước</button>
        </div>
        <div class="editor-content">
            <div class="edit-area active p-4">
                <textarea class="w-full h-96 p-4 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="${placeholder}"></textarea>
            </div>
            <div class="preview-area hidden p-4 prose max-w-none">
                <div class="preview-content min-h-96 border rounded-lg p-4 bg-gray-50"></div>
            </div>
        </div>
    `;
    
    container.innerHTML = '';
    container.appendChild(editor);
    
    const tabs = editor.querySelectorAll('.tab-btn');
    const editArea = editor.querySelector('.edit-area');
    const previewArea = editor.querySelector('.preview-area');
    const textarea = editor.querySelector('textarea');
    const previewContent = editor.querySelector('.preview-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabType = this.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active', 'text-blue-600', 'border-blue-600'));
            this.classList.add('active', 'text-blue-600', 'border-blue-600');
            
            if (tabType === 'edit') {
                editArea.classList.remove('hidden');
                editArea.classList.add('active');
                previewArea.classList.add('hidden');
                previewArea.classList.remove('active');
            } else {
                editArea.classList.add('hidden');
                editArea.classList.remove('active');
                previewArea.classList.remove('hidden');
                previewArea.classList.add('active');
                
                renderMarkdownWithLatex(textarea.value, previewContent);
            }
        });
    });
    
    let previewTimeout;
    textarea.addEventListener('input', function() {
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
            if (previewArea.classList.contains('active')) {
                renderMarkdownWithLatex(this.value, previewContent);
            }
        }, 500);
    });
    
    return {
        getValue: () => textarea.value,
        setValue: (value) => {
            textarea.value = value;
            if (previewArea.classList.contains('active')) {
                renderMarkdownWithLatex(value, previewContent);
            }
        },
        focus: () => textarea.focus()
    };
}

function renderMarkdownWithLatex(text, container) {
    if (!text || !text.trim()) {
        container.innerHTML = '<p class="text-gray-500 italic">Chưa có nội dung...</p>';
        return;
    }
    
    try {
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });
        
        const html = marked.parse(text);
        container.innerHTML = html;
        
        renderMathInElement(container, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\]', display: true}
            ],
            throwOnError: false,
            output: 'html'
        });
        
        container.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
    } catch (error) {
        console.error('Lỗi render markdown:', error);
        container.innerHTML = '<p class="text-red-500">Lỗi khi hiển thị nội dung</p>';
    }
}

function loadExistingContent() {
    const solutionDataElement = document.getElementById('solution-data');
    if (!solutionDataElement) return;

    const summary = solutionDataElement.dataset.summary || '';
    const code = solutionDataElement.dataset.code || '';
    
    const decodedSummary = decodeHTML(summary);
    const decodedCode = decodeHTML(code);
    
    if (summaryEditor && decodedSummary) {
        summaryEditor.setValue(decodedSummary);
    }
    
    if (codeEditor && decodedCode) {
        codeEditor.setValue(decodedCode);
    }
}

function decodeHTML(html) {
    if (!html) return '';
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('solution-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!codeEditor) {
                e.preventDefault();
                alert('Editor đang khởi tạo, vui lòng thử lại sau!');
                return;
            }

            try {
                const codeValue = codeEditor.getValue();
                const summaryValue = summaryEditor ? summaryEditor.getValue() : '';
                
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
    }
});
let summaryEditor;
let codeEditor;

document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/create_solution') {
        localStorage.removeItem('smde_solution-editor');  
        localStorage.removeItem('smde_solution-editor-code');
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('smde_')) {
                localStorage.removeItem(key);
            }
        });
    }
    const easyMDEConfig = {
        autosave: {
            enabled: true,
            uniqueId: "solution-editor",
            delay: 1000,
        },
        toolbar: [
            "bold", "italic", "heading", "|",
            "quote", "unordered-list", "ordered-list", "|",
            "link", "image", "|",
            "preview", "side-by-side", "fullscreen", "|",
            "guide"
        ],
        spellChecker: false,
        renderingConfig: {
            singleLineBreaks: false,
            codeSyntaxHighlighting: true,
        },
        placeholder: "Nhập nội dung Markdown ở đây...",
    };

    summaryEditor = new EasyMDE({
        element: document.getElementById('summary-editor'),
        ...easyMDEConfig,
        minHeight: "200px",
    });

    codeEditor = new EasyMDE({
        element: document.getElementById('code-editor'),
        ...easyMDEConfig,
        minHeight: "300px",
    });
});

document.getElementById('solution-form').addEventListener('submit', function(e) {
    const codeValue = codeEditor.value();
    const summaryValue = summaryEditor.value();
    
    if (!codeValue.trim()) {
        e.preventDefault();
        alert('Vui lòng nhập phần giải!');
        codeEditor.codemirror.focus();
        return;
    }
    
    const codeTextarea = document.querySelector('textarea[name="code"]');
    const summaryTextarea = document.querySelector('textarea[name="summary"]');
    
    codeTextarea.style.display = 'block';
    summaryTextarea.style.display = 'block';
    
    codeTextarea.value = codeValue;
    summaryTextarea.value = summaryValue;
    
    setTimeout(() => {
        codeTextarea.style.display = 'none';
        summaryTextarea.style.display = 'none';
    }, 100);
});


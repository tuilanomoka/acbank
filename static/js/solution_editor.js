let summaryEditor;
let codeEditor;

document.addEventListener('DOMContentLoaded', function() {
    const easyMDEConfig = {
        autosave: {
                enabled: true,
                uniqueId: window.location.pathname.includes('/create_solution') 
                        ? "temp-create-" + Date.now() 
                        : "solution-editor", 
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


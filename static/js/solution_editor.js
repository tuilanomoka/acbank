document.addEventListener('DOMContentLoaded', function() {
    const summaryEditor = new EasyMDE({
        element: document.getElementById('summary-editor'),
        spellChecker: false,
        placeholder: 'Tóm tắt về bài tập...'
    });

    const codeEditor = new EasyMDE({
        element: document.getElementById('code-editor'),
        spellChecker: false,
        placeholder: 'Phần giải bài tập...'
    });

    document.getElementById('solution-form').addEventListener('submit', function(e) {
        const codeValue = codeEditor.value();
        if (!codeValue.trim()) {
            e.preventDefault();
            alert('Vui lòng nhập phần giải!');
            return;
        }
        
        document.querySelector('textarea[name="summary"]').value = summaryEditor.value();
        document.querySelector('textarea[name="code"]').value = codeValue;
    });
});
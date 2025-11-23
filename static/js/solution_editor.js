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
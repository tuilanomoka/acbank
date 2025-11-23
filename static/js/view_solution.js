document.addEventListener('DOMContentLoaded', function() {
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        }
    });

    function renderMarkdownWithLatex(text) {
        if (!text || !text.trim()) return '<p><em>Không có</em></p>';
        return marked.parse(text);
    }

    const summaryElement = document.getElementById('summary-content');
    const codeElement = document.getElementById('code-content');
    
    const summaryText = summaryElement.textContent || summaryElement.innerText;
    const codeText = codeElement.textContent || codeElement.innerText;
    
    summaryElement.innerHTML = renderMarkdownWithLatex(summaryText);
    codeElement.innerHTML = renderMarkdownWithLatex(codeText);

    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false,
        output: 'html'
    });
});
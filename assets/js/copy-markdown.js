const copyButton = document.getElementById('copy-markdown');
const markdown = document.getElementById('recipe-markdown');
const copyStatus = document.getElementById('copy-status');

copyButton.hidden = false;
copyButton.addEventListener('click', async () => {
  copyButton.disabled = true;
  try {
    await navigator.clipboard.writeText(markdown.value);
    markdown.hidden = true;
    copyStatus.textContent = 'Markdown copied.';
  } catch {
    markdown.hidden = false;
    markdown.focus();
    markdown.select();
    copyStatus.textContent = 'Automatic copy is unavailable. Select and copy the Markdown below.';
  } finally {
    copyButton.disabled = false;
  }
});

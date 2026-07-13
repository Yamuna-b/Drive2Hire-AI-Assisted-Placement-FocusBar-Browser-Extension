document.addEventListener('DOMContentLoaded', () => {
  const content = document.getElementById('content');
  const tabs = document.querySelectorAll('nav ul li');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      content.innerHTML = `<p>${tab.innerText} tab content will appear here.</p>`;
    });
  });
});

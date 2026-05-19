// EduComp — Main JS

// Auto-dismiss messages after 4s
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.message').forEach(m => {
      m.style.transition = 'opacity 0.5s';
      m.style.opacity = '0';
      setTimeout(() => m.remove(), 500);
    });
  }, 4000);
});

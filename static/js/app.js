document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-confirm]");
  if (button && !window.confirm(button.dataset.confirm)) {
    event.preventDefault();
  }
});
setTimeout(() => document.querySelectorAll(".flash").forEach(el => el.remove()), 5000);

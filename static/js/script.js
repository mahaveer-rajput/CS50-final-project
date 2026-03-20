// Toggle dropdown on click
const userBtn = document.getElementById("userBtn");
const userDropdown = document.getElementById("userDropdown");

// Toggle dropdown on click
userBtn.addEventListener("click", (e) => {
  e.stopPropagation(); // prevent click from closing immediately
  userDropdown.classList.toggle("show");
});

// Close dropdown if click outside
document.addEventListener("click", () => {
  userDropdown.classList.remove("show");
});

// CLOSE DROPDOWN ON SCROLL
window.addEventListener("scroll", () => {
  userDropdown.classList.remove("show");
});
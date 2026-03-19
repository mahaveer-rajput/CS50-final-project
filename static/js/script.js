window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");

  if (window.scrollY > 50) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
});

function toggleMenu() {
  document.getElementById("navLinks").classList.toggle("active");
}

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
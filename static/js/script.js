window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");

  if (window.scrollY > 50) {
    navbar.classList.add("scrolled");
    navbar.style.color = 'Black';
  } else {
    navbar.classList.remove("scrolled");
    navbar.style.color = "white";

  }
});

function toggleMenu() {
  document.getElementById("navLinks").classList.toggle("active");
}


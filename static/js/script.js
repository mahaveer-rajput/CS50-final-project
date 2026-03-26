const likeBtn = document.getElementById("likeBtn");

if (likeBtn) {
  likeBtn.addEventListener("click", async () => {
    const artId = likeBtn.dataset.id;

    // 🔹 Get CSRF token from meta tag
    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute("content");

    try {
      const response = await fetch(`/like/${artId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken, // required for Flask-WTF
        },
        body: JSON.stringify({}), // empty body, we just need POST
      });

      const data = await response.json();

      if (data.error) {
        alert("Please login first");
        return;
      }

      // Update button UI
      if (data.liked) {
        likeBtn.classList.add("liked");
        likeBtn.innerHTML = "❤️ Liked";
      } else {
        likeBtn.classList.remove("liked");
        likeBtn.innerHTML = "🤍 Like";
      }

      // Update like count
      document.getElementById("likeCount").innerText = `❤️ ${data.count} likes`;
    } catch (error) {
      console.error("Error:", error);
    }
  });
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

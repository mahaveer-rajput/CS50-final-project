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

// API artwork

async function loadArtworks() {
  const res = await fetch("/api/artworks");
  const data = await res.json();

  const grid = document.querySelector(".masonry-grid");
  grid.innerHTML = "";

  data.forEach((art) => {
    grid.innerHTML += `
        <div class="masonry-item">
            <div class="image-container">
                <img src="/static/uploads/${art.image}" />

                <div class="overlay">
                    <h3>${art.title}</h3>
                    <p>${art.artist}</p>
                    <span>❤️ ${art.likes || 0}</span>
                </div>
            </div>
        </div>
        `;
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
 
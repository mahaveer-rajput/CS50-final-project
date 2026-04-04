const likeBtn = document.getElementById("likeBtn");

if (likeBtn) {
  likeBtn.addEventListener("click", async () => {
    const artId = likeBtn.dataset.id;

    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute("content");

    try {
      const response = await fetch(`/like/${artId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({}),
      });

      const data = await response.json();

      if (data.error) {
        alert("Please login first");
        return;
      }

      if (data.liked) {
        likeBtn.classList.add("liked");
        likeBtn.innerHTML = "❤️ Liked";
      } else {
        likeBtn.classList.remove("liked");
        likeBtn.innerHTML = "🤍 Like";
      }

      document.getElementById("likeCount").innerText = `❤️ ${data.count} likes`;
    } catch (error) {
      console.error("Error:", error);
    }
  });
}

const userBtn = document.getElementById("userBtn");
const userDropdown = document.getElementById("userDropdown");

if (userBtn && userDropdown) {
  userBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle("show");
  });

  document.addEventListener("click", () => {
    userDropdown.classList.remove("show");
  });
}

let offset = 0;
let loading = false;
let allLoaded = false;

const grid = document.getElementById("feedGrid");

function showSkeletons(count = 10) {
  if (!grid) return;
  for (let i = 0; i < count; i++) {
    const div = document.createElement("div");
    div.className = "masonry-item skeleton";
    div.style.height = `${200 + Math.random() * 150}px`;
    grid.appendChild(div);
  }
}

function removeSkeletons() {
  document.querySelectorAll(".skeleton").forEach((el) => el.remove());
}

async function loadMore() {
  if (loading || allLoaded) return;

  loading = true;
  showSkeletons();

  const res = await fetch(`/api/feed?offset=${offset}`);
  const data = await res.json();

  removeSkeletons();

  if (data.length === 0) {
    allLoaded = true;
    const end = document.createElement("div");
    end.innerHTML = `
      <div class="end-message">
        <div class="end-line"></div>
        <span>You're all caught up</span>
        <div class="end-line"></div>
      </div>
    `;
    grid.appendChild(end);
    return;
  }

  data.forEach((art) => {
    const div = document.createElement("div");
    div.className = "masonry-item";

    const imageSrc =
      art.source === "pixabay" ? art.image : `/static/uploads/${art.image}`;

    let artUrl;
    if (art.source === "pixabay") {
      const params = new URLSearchParams({
        title: art.title,
        artist: art.artist,
        image: art.image,
        likes: art.like_count,
      });
      artUrl = `/pixabay/${art.id}?${params}`;
    } else {
      artUrl = `/artwork/${art.id}`;
    }

    div.innerHTML = `
      <div class="image-container">
        <a href="${artUrl}">
          <img src="${imageSrc}" alt="${art.title}" loading="lazy" />
          <div class="overlayy">
            <div class="overlay-content">
              <h4>${art.title}</h4>
              <p>${art.artist}</p>
              <div class="overlay-stats">
                <span><i class="fa-solid fa-heart"></i> <span class="like-count">${art.like_count}</span></span>
                <span><i class="fa-solid fa-download"></i></span>
              </div>
              <div class="mobile-stats">
                <span><i class="fa-solid fa-heart"></i> ${art.like_count}</span>
                <span><i class="fa-solid fa-download"></i></span>
              </div>
            </div>
          </div>
        </a>
      </div>
    `;

    grid.appendChild(div);
  });

  offset += data.length;
  loading = false;
}

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
    loadMore();
  }
});

setInterval(async () => {
  const res = await fetch(`/api/feed?offset=0&limit=${offset}`);
  const data = await res.json();

  data.forEach((art) => {
    const likeEl = document.querySelector(`[data-id="${art.id}"] .like-count`);
    if (likeEl) likeEl.textContent = `❤️ ${art.like_count}`;
  });
}, 5000);

loadMore();

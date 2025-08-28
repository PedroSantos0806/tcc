// Toggle visualizar senha (login/cadastro)
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggleSenha");
  const senhaInput = document.getElementById("senha");

  if (toggleBtn && senhaInput) {
    toggleBtn.addEventListener("click", () => {
      const isPass = senhaInput.type === "password";
      senhaInput.type = isPass ? "text" : "password";
      toggleBtn.textContent = isPass ? "🙈" : "👁️";
    });
  }

  // Carrossel da home (qualquer container com data-carousel)
  const carousels = document.querySelectorAll("[data-carousel]");
  carousels.forEach(initCarousel);
});

function initCarousel(root) {
  const slides = root.querySelectorAll(".slide");
  const dotsBox = root.querySelector(".dots");

  if (!slides.length || !dotsBox) return;

  // cria pontinhos
  slides.forEach((_, i) => {
    const b = document.createElement("button");
    b.className = "dot" + (i === 0 ? " active" : "");
    b.setAttribute("aria-label", `Ir para slide ${i + 1}`);
    b.addEventListener("click", () => go(i));
    dotsBox.appendChild(b);
  });

  let i = 0;
  let timer;
  const dots = dotsBox.querySelectorAll(".dot");

  function go(n) {
    slides[i].classList.remove("active");
    dots[i].classList.remove("active");
    i = n;
    slides[i].classList.add("active");
    dots[i].classList.add("active");
    reset();
  }
  function next() {
    go((i + 1) % slides.length);
  }
  function reset() {
    clearInterval(timer);
    timer = setInterval(next, 4500);
  }

  // inicia
  slides[0].classList.add("active");
  reset();
}

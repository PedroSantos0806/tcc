// =======================
// Utilidades gerais
// =======================
document.addEventListener("DOMContentLoaded", () => {
  // Visualizar/ocultar senha
  document.querySelectorAll("#toggleSenha").forEach((btn) => {
    const input = btn?.parentElement?.querySelector(
      "input[type='password'], input[type='text']"
    );
    if (!input) return;
    btn.addEventListener("click", () => {
      const isPass = input.type === "password";
      input.type = isPass ? "text" : "password";
      btn.textContent = isPass ? "🙈" : "👁️";
    });
  });

  // Carrossel da home
  document.querySelectorAll("[data-carousel]").forEach(initCarousel);

  // Campos dinâmicos do cadastro de produto
  setupProdutoDinamico();

  // Menus em “pastas” (dropdown por clique)
  initFolderMenus();

  // Auto-hide dos flashes
  setTimeout(() => {
    document.querySelectorAll(".flash")?.forEach((f) => (f.style.display = "none"));
  }, 6000);
});

// =======================
// Carrossel
// =======================
function initCarousel(root) {
  const slides = root.querySelectorAll(".slide");
  const dotsBox = root.querySelector(".dots");
  const prev = root.querySelector(".nav.prev");
  const next = root.querySelector(".nav.next");
  if (!slides.length || !dotsBox) return;

  let idx = 0;
  function show(i) {
    slides.forEach((s, j) => s.classList.toggle("active", j === i));
    dotsBox.querySelectorAll(".dot").forEach((d, j) => d.classList.toggle("active", j === i));
    idx = i;
  }

  slides.forEach((_, i) => {
    const b = document.createElement("button");
    b.className = "dot" + (i === 0 ? " active" : "");
    b.setAttribute("aria-label", `Ir ao slide ${i + 1}`);
    b.addEventListener("click", () => show(i));
    dotsBox.appendChild(b);
  });

  prev?.addEventListener("click", () => show((idx - 1 + slides.length) % slides.length));
  next?.addEventListener("click", () => show((idx + 1) % slides.length));
  show(0);

  let timer = setInterval(() => next?.click(), 6000);
  root.addEventListener("mouseenter", () => clearInterval(timer));
  root.addEventListener("mouseleave", () => (timer = setInterval(() => next?.click(), 6000)));
}

// =======================
// Campos dinâmicos do produto
// =======================
function setupProdutoDinamico() {
  const cat = document.getElementById("categoria");
  const gSub = document.getElementById("grupo-subcategoria");
  const gTam = document.getElementById("grupo-tamanho");
  const sub = document.getElementById("subcategoria");
  const tam = document.getElementById("tamanho");
  if (!cat || !gSub || !gTam || !sub || !tam) return;

  const opcoes = {
    "Vestuário": { subcategorias: ["Camisetas", "Calças", "Jaquetas", "Acessórios"], tamanhos: ["PP","P","M","G","GG"] },
    "Calçados":  { subcategorias: null, tamanhos: ["34","35","36","37","38","39","40","41","42","43","44"] },
    "Tecnologia":{ subcategorias: ["Periféricos","Áudio","Câmeras","Acessórios"], tamanhos: null }
  };

  function popularSelect(select, valores) {
    select.innerHTML = "";
    valores.forEach((v) => {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      select.appendChild(o);
    });
  }

  cat.addEventListener("change", () => {
    const v = cat.value;
    if (!v) {
      gSub.style.display = "none";
      gTam.style.display = "none";
      return;
    }
    const cfg = opcoes[v];

    if (v === "Vestuário") {
      if (cfg.subcategorias) {
        popularSelect(sub, cfg.subcategorias);
        gSub.style.display = "block";
      } else {
        gSub.style.display = "none";
      }
      gTam.style.display = "none";
      sub.onchange = () => {
        if (cfg.tamanhos) {
          popularSelect(tam, cfg.tamanhos);
          gTam.style.display = "block";
        }
      };
    } else if (v === "Calçados") {
      gSub.style.display = "none";
      if (cfg.tamanhos) {
        popularSelect(tam, cfg.tamanhos);
        gTam.style.display = "block";
      } else {
        gTam.style.display = "none";
      }
    } else if (v === "Tecnologia") {
      if (cfg.subcategorias) {
        popularSelect(sub, cfg.subcategorias);
        gSub.style.display = "block";
      } else {
        gSub.style.display = "none";
      }
      gTam.style.display = "none";
    }
  });
}

// =======================
// Pastas (dropdown por clique)
// =======================
function initFolderMenus() {
  const folders = document.querySelectorAll(".folder");

  function closeAll(except = null) {
    folders.forEach((f) => {
      if (f !== except) {
        f.classList.remove("open");
        const btn = f.querySelector(".folder-btn");
        if (btn) btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  folders.forEach((folder) => {
    const btn = folder.querySelector(".folder-btn");
    const menu = folder.querySelector(".folder-menu");
    if (!btn || !menu) return;

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = folder.classList.contains("open");
      closeAll(folder);
      folder.classList.toggle("open", !isOpen);
      btn.setAttribute("aria-expanded", String(!isOpen));
    });
  });

  // Fecha ao clicar fora
  document.addEventListener("click", () => closeAll(null));

  // Fecha com ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAll(null);
  });
}

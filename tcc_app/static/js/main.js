// Arquivo principal de comportamentos (toggle senha, flash, dinâmicos)
document.addEventListener("DOMContentLoaded", () => {
  // Toggle visualizar senha (qualquer página com .toggle-senha)
  document.querySelectorAll(".toggle-senha").forEach(btn => {
    const input = btn.parentElement.querySelector("input[type='password'], input[type='text']");
    if (!input) return;
    btn.addEventListener("click", () => {
      const isPass = input.type === "password";
      input.type = isPass ? "text" : "password";
      btn.textContent = isPass ? "🙈" : "👁️";
    });
  });

  // Auto-hide dos flashes
  setTimeout(() => {
    document.querySelectorAll(".flash").forEach(f => f.style.display = "none");
  }, 6000);

  // Campos dinâmicos do cadastro de produto (se existir)
  setupProdutoDinamico();

  // Carrossel genérico (se um dia usar na home)
  document.querySelectorAll("[data-carousel]").forEach(initCarousel);
});

function setupProdutoDinamico(){
  const nome = document.getElementById('nome');
  const cat = document.getElementById('categoria');
  const gSub = document.getElementById('grupo-subcategoria') || document.getElementById('subcategoria-group');
  const gTam = document.getElementById('grupo-tamanho') || document.getElementById('tamanho-group');
  const sub = document.getElementById('subcategoria');
  const tam = document.getElementById('tamanho');

  if (!cat || !sub || !tam || !gSub || !gTam) return;

  const opcoes = {
    'Vestuário': {
      subs: ['Camisetas','Calças','Jaquetas','Acessórios'],
      sizes: ['PP','P','M','G','GG']
    },
    'Calçados': {
      subs: null,
      sizes: ['34','35','36','37','38','39','40','41','42','43','44']
    },
    'Tecnologia': {
      subs: ['Periféricos','Áudio','Câmeras','Acessórios'],
      sizes: null
    },
    // fallback (sinônimos)
    'Vestimenta': { subs: ['Camisetas','Calças','Jaquetas','Acessórios'], sizes:['PP','P','M','G','GG'] },
    'Calçado':   { subs: null, sizes:['34','35','36','37','38','39','40','41','42','43','44'] }
  };

  function fill(select, items){
    select.innerHTML = '';
    const opt0 = document.createElement('option');
    opt0.value = ''; opt0.textContent = 'Selecione...';
    select.appendChild(opt0);
    (items || []).forEach(v=>{
      const o = document.createElement('option');
      o.value = v; o.textContent = v;
      select.appendChild(o);
    });
  }

  function setRequired(subReq, tamReq){
    sub.required = !!subReq;
    tam.required = !!tamReq;
  }

  function update(){
    const v = cat.value;
    const cfg = opcoes[v] || { subs:null, sizes:null };
    gSub.style.display = 'none';
    gTam.style.display = 'none';
    sub.value = ''; tam.value = '';
    setRequired(false, false);

    if (v === 'Vestuário' || v === 'Vestimenta'){
      if (cfg.subs){ fill(sub, cfg.subs); gSub.style.display = 'block'; setRequired(true, false); }
      sub.onchange = () => {
        if (sub.value){ fill(tam, cfg.sizes); gTam.style.display = 'block'; setRequired(true, true); }
        else { gTam.style.display = 'none'; tam.value=''; setRequired(true, false); }
      };
    } else if (v === 'Calçados' || v === 'Calçado'){
      fill(tam, cfg.sizes); gTam.style.display = 'block'; setRequired(false, true);
    } else if (v === 'Tecnologia'){
      fill(sub, cfg.subs); gSub.style.display = 'block'; setRequired(true, false);
    } else {
      // Nenhuma seleção: nada é obrigatório além de categoria
      setRequired(false, false);
    }
  }

  cat.addEventListener('change', update);
  update();

  // Sugestão "IA" (heurística por palavras-chave) com base no NOME
  if (nome) {
    nome.addEventListener('input', () => {
      const t = (nome.value || '').toLowerCase();

      // tecnologia
      if (/\b(mouse|teclado|headset|fone|webcam|camera|ssd|hd|pendrive|usb|monitor)\b/.test(t)) {
        cat.value = 'Tecnologia';
        update();
        // subcategoria dentro de tecnologia
        if (/\b(mouse|teclado|teclado mec[aá]nico|mousepad)\b/.test(t)) sub.value = 'Periféricos';
        else if (/\b(headset|fone|auricular|bluetooth)\b/.test(t)) sub.value = 'Áudio';
        else if (/\b(webcam|camera)\b/.test(t)) sub.value = 'Câmeras';
        else sub.value = 'Acessórios';

      // calçados
      } else if (/\b(t[eê]nis|bota|sand[aá]lia|sapatilha|sapato)\b/.test(t)) {
        cat.value = 'Calçados';
        update(); // tamanho passa a ser mostrado e exigido

      // vestuário
      } else if (/\b(camisa|camiseta|cal[cç]a|jaqueta|moletom|short|bon[eé]|cinto|meia)\b/.test(t)) {
        cat.value = 'Vestuário';
        update();
        // sub básica para exemplo
        if (/\b(camiseta|camisa|moletom)\b/.test(t)) sub.value = 'Camisetas';
        else if (/\b(cal[cç]a|short)\b/.test(t)) sub.value = 'Calças';
        else if (/\b(jaqueta)\b/.test(t)) sub.value = 'Jaquetas';
        else sub.value = 'Acessórios';
      }
      // (para outros nomes, não preenche nada automaticamente)
    });
  }
}

function initCarousel(root){
  const slides = root.querySelectorAll(".slide");
  const dotsBox = root.querySelector(".dots");
  if (!slides.length || !dotsBox) return;

  slides.forEach((_, i) => {
    const b = document.createElement("button");
    b.className = "dot" + (i === 0 ? " active" : "");
    b.setAttribute("aria-label", `Ir para slide ${i+1}`);
    b.addEventListener("click", () => go(i));
    dotsBox.appendChild(b);
  });

  let i = 0, timer;
  const dots = dotsBox.querySelectorAll(".dot");

  function go(n){
    slides[i].classList.remove("active");
    dots[i].classList.remove("active");
    i = n;
    slides[i].classList.add("active");
    dots[i].classList.add("active");
    reset();
  }
  function next(){ go((i+1) % slides.length); }
  function reset(){ clearInterval(timer); timer = setInterval(next, 4500); }

  slides[0].classList.add("active");
  reset();
}

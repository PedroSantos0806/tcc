document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("toggleSenha");
    const senhaInput = document.getElementById("senha");

    if (toggleBtn && senhaInput) {
        toggleBtn.addEventListener("click", () => {
            if (senhaInput.type === "password") {
                senhaInput.type = "text";
                toggleBtn.textContent = "🙈";
            } else {
                senhaInput.type = "password";
                toggleBtn.textContent = "👁️";
            }
        });
    }
});

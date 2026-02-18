    (() => {
    //const isMobile = () => window.matchMedia("(max-width: 700px)").matches;
      const isMobile = () => true;

      const header = document.querySelector(".site-header");
    const brandLogo = document.querySelector(".brand-logo");

    if (!header || !brandLogo) return;

    // creează floating logo
    const wrap = document.createElement("div");
    wrap.className = "floating-home";
    wrap.innerHTML = `
    <a href="#home" aria-label="Back to top (Home)">
      <img src="${brandLogo.getAttribute("src")}" alt="Home">
    </a>
  `;
    document.body.appendChild(wrap);

    const toggle = () => {
    if (!isMobile()) {
    wrap.classList.remove("is-visible");
    return;
}
    const headerBottom = header.getBoundingClientRect().bottom;
    // apare când headerul nu mai e vizibil (ai trecut de el)
    if (headerBottom <= 0) wrap.classList.add("is-visible");
    else wrap.classList.remove("is-visible");
};

    window.addEventListener("scroll", toggle, { passive: true });
    window.addEventListener("resize", toggle);
    toggle();
})();


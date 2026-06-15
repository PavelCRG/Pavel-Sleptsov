(function () {
    var grid = document.querySelector(".site-grid");
    var toggle = document.querySelector(".nav-toggle");
    var backdrop = document.querySelector(".nav-backdrop");
    if (!grid || !toggle) return;

    function setOpen(open) {
        grid.classList.toggle("site-grid--nav-open", open);
        toggle.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        toggle.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
        document.body.style.overflow = open ? "hidden" : "";
    }

    toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        setOpen(!grid.classList.contains("site-grid--nav-open"));
    });

    if (backdrop) {
        backdrop.addEventListener("click", function () {
            setOpen(false);
        });
    }

    grid.querySelectorAll(".site-sidebar a").forEach(function (link) {
        link.addEventListener("click", function () {
            if (window.matchMedia("(max-width: 960px)").matches) {
                setOpen(false);
            }
        });
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && grid.classList.contains("site-grid--nav-open")) {
            setOpen(false);
        }
    });
})();

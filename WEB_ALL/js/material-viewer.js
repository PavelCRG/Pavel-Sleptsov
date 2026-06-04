/**
 * Просмотр HTML-материалов внутри портала (лабораторные, лекции).
 */
(function () {
    var frame = document.getElementById("material-frame");
    var placeholder = document.getElementById("material-placeholder");
    var titleEl = document.getElementById("material-viewer-title");
    var openNew = document.getElementById("material-open-new");
    if (!frame || !placeholder) {
        return;
    }

    var links = document.querySelectorAll(".lab-files a[data-material-src]");

    function setActiveLink(active) {
        links.forEach(function (a) {
            a.classList.toggle("is-active", a === active);
        });
    }

    function openWork(src, label, linkEl) {
        frame.src = src;
        frame.classList.add("is-active");
        placeholder.hidden = true;
        titleEl.textContent = label || src.split("/").pop();
        if (openNew) {
            openNew.href = src;
            openNew.hidden = false;
        }
        setActiveLink(linkEl || null);
        if (linkEl) {
            try {
                history.replaceState(null, "", "#" + encodeURIComponent(src.replace(/^\.\.\//, "")));
            } catch (e) { /* ignore */ }
        }
    }

    links.forEach(function (a) {
        a.addEventListener("click", function (e) {
            e.preventDefault();
            openWork(a.getAttribute("data-material-src"), a.textContent.trim(), a);
        });
    });

    function openFromHash() {
        var hash = location.hash.replace(/^#/, "");
        if (!hash) {
            return;
        }
        var path = decodeURIComponent(hash);
        var found = null;
        links.forEach(function (a) {
            var src = a.getAttribute("data-material-src") || "";
            if (src.indexOf(path) !== -1 || path.indexOf(src.replace(/^\.\.\//, "")) !== -1) {
                found = a;
            }
        });
        if (found) {
            openWork(found.getAttribute("data-material-src"), found.textContent.trim(), found);
        }
    }

    openFromHash();
    window.addEventListener("hashchange", openFromHash);
})();

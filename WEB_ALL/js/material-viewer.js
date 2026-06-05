/**
 * Просмотр HTML-работ внутри портала — без iframe.
 * PDF (условия) открываются на отдельной странице view-pdf.html.
 */
(function () {
    var contentEl = document.getElementById("material-content");
    var placeholder = document.getElementById("material-placeholder");
    var loadingEl = document.getElementById("material-loading");
    var titleEl = document.getElementById("material-viewer-title");
    var openNew = document.getElementById("material-open-new");
    var viewer = document.querySelector(".material-viewer");

    if (!contentEl || !placeholder) {
        return;
    }

    var links = document.querySelectorAll('.lab-files a[data-material-src]');

    function isHtmlSrc(src) {
        return /\.html?(\?|#|$)/i.test(src);
    }

    function setActiveLink(active) {
        links.forEach(function (a) {
            a.classList.toggle("is-active", a === active);
        });
    }

    function openParentDetails(el) {
        var node = el;
        while (node && node !== document.body) {
            if (node.tagName === "DETAILS" && !node.open) {
                node.open = true;
            }
            node = node.parentElement;
        }
    }

    function baseUrlFrom(src) {
        var url = new URL(src, window.location.href);
        var path = url.pathname.replace(/\/[^/]*$/, "/");
        return url.origin + path;
    }

    function resolveUrl(value, base) {
        if (!value || value.indexOf("data:") === 0 || value.indexOf("#") === 0) {
            return value;
        }
        try {
            return new URL(value, base).href;
        } catch (e) {
            return value;
        }
    }

    function fixRelativeUrls(root, base) {
        root.querySelectorAll("[src]").forEach(function (el) {
            var src = el.getAttribute("src");
            if (src) {
                el.setAttribute("src", resolveUrl(src, base));
            }
        });
        root.querySelectorAll("a[href]").forEach(function (el) {
            var href = el.getAttribute("href");
            if (href && href.indexOf("#") !== 0 && href.indexOf("mailto:") !== 0) {
                el.setAttribute("href", resolveUrl(href, base));
            }
        });
    }

    function runScripts(container, base) {
        container.querySelectorAll("script").forEach(function (oldScript) {
            var script = document.createElement("script");
            Array.prototype.slice.call(oldScript.attributes).forEach(function (attr) {
                if (attr.name === "src") {
                    script.setAttribute("src", resolveUrl(attr.value, base));
                } else {
                    script.setAttribute(attr.name, attr.value);
                }
            });
            if (!oldScript.src) {
                script.textContent = oldScript.textContent;
            }
            oldScript.parentNode.replaceChild(script, oldScript);
        });
    }

    function showLoading(show) {
        if (loadingEl) {
            loadingEl.hidden = !show;
        }
    }

    function clearContent() {
        contentEl.innerHTML = "";
        contentEl.hidden = true;
        contentEl.classList.remove("is-active");
    }

    function injectHtml(html, base) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        clearContent();

        doc.querySelectorAll("style").forEach(function (style) {
            contentEl.appendChild(style.cloneNode(true));
        });

        doc.querySelectorAll('link[rel="stylesheet"]').forEach(function (link) {
            var el = document.createElement("link");
            el.rel = "stylesheet";
            el.href = resolveUrl(link.getAttribute("href"), base);
            contentEl.appendChild(el);
        });

        var wrap = document.createElement("div");
        wrap.className = "material-viewer__injected";
        wrap.innerHTML = doc.body.innerHTML;
        fixRelativeUrls(wrap, base);
        contentEl.appendChild(wrap);
        runScripts(wrap, base);

        contentEl.hidden = false;
        contentEl.classList.add("is-active");
    }

    function showError(src, message) {
        clearContent();
        var err = document.createElement("p");
        err.className = "material-viewer__error";
        err.textContent = message || "Не удалось загрузить материал.";
        contentEl.appendChild(err);
        var link = document.createElement("a");
        link.href = src;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Открыть в новой вкладке";
        contentEl.appendChild(document.createElement("br"));
        contentEl.appendChild(link);
        contentEl.hidden = false;
        contentEl.classList.add("is-active");
    }

    function openWork(src, label, linkEl) {
        if (!isHtmlSrc(src)) {
            return;
        }

        placeholder.hidden = true;
        titleEl.textContent = label || src.split("/").pop();
        if (openNew) {
            openNew.href = src;
            openNew.hidden = false;
        }
        setActiveLink(linkEl || null);
        if (linkEl) {
            openParentDetails(linkEl);
            try {
                history.replaceState(null, "", "#" + encodeURIComponent(src.replace(/^\.\.\//, "")));
            } catch (e) { /* ignore */ }
        }
        if (viewer && viewer.scrollIntoView) {
            viewer.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        var base = baseUrlFrom(src);

        showLoading(true);
        clearContent();

        fetch(src)
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.text();
            })
            .then(function (html) {
                showLoading(false);
                injectHtml(html, base);
            })
            .catch(function () {
                showLoading(false);
                showError(src, "Не удалось загрузить файл. Проверьте, что сайт открыт через веб-сервер (не file://).");
            });
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
        if (/\.pdf(\?|#|$)/i.test(path)) {
            return;
        }
        var found = null;
        links.forEach(function (a) {
            var src = a.getAttribute("data-material-src") || "";
            var normalized = src.replace(/^\.\.\//, "");
            if (normalized === path || normalized.indexOf(path) !== -1 || path.indexOf(normalized) !== -1) {
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
